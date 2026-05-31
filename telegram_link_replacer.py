"""
Telegram grup/kanal mesajlarını izler, linkleri links.txt'e göre değiştirir
ve hedef gruplara iletir.

Kaynak ve hedef gruplar web panel üzerinden yönetilir (SQLite DB).
Bot, mesaj aldığı her grubu otomatik olarak DB'ye kaydeder.
"""

import asyncio
import logging
import os
import re
import sqlite3
from pathlib import Path

from aiogram import Bot, Dispatcher, Router
from aiogram.enums import ParseMode
from aiogram.types import Message
from aiogram.client.default import DefaultBotProperties

# ── Yapılandırma ──────────────────────────────────────────────────────────────

BOT_TOKEN  = os.environ["BOT_TOKEN"]
LINKS_FILE = Path(os.environ.get("LINKS_FILE", "links.txt"))
DB_FILE    = Path(os.environ.get("DB_FILE",    "db.sqlite3"))

# ── Logging ───────────────────────────────────────────────────────────────────

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
)
log = logging.getLogger(__name__)

# ── DB helpers ────────────────────────────────────────────────────────────────

def _get_db() -> sqlite3.Connection:
    DB_FILE.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(DB_FILE, timeout=10)
    conn.row_factory = sqlite3.Row
    return conn


def _ensure_table():
    with _get_db() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS chat_groups (
                id            INTEGER PRIMARY KEY AUTOINCREMENT,
                chat_id       INTEGER UNIQUE NOT NULL,
                title         TEXT NOT NULL DEFAULT '',
                chat_type     TEXT NOT NULL DEFAULT 'unknown',
                role          TEXT NOT NULL DEFAULT 'none',
                is_active     INTEGER NOT NULL DEFAULT 1,
                discovered_at DATETIME DEFAULT CURRENT_TIMESTAMP,
                last_seen_at  DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        """)


def _register_chat(chat_id: int, title: str, chat_type: str) -> None:
    with _get_db() as conn:
        conn.execute(
            "INSERT OR IGNORE INTO chat_groups (chat_id, title, chat_type) VALUES (?, ?, ?)",
            (chat_id, title or "", chat_type or "unknown"),
        )
        conn.execute(
            "UPDATE chat_groups"
            "   SET title = ?, chat_type = ?, last_seen_at = CURRENT_TIMESTAMP"
            " WHERE chat_id = ?",
            (title or "", chat_type or "unknown", chat_id),
        )


def _get_source_ids() -> list[int]:
    try:
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT chat_id FROM chat_groups WHERE role = 'source' AND is_active = 1"
            ).fetchall()
        return [r["chat_id"] for r in rows]
    except Exception as e:
        log.error("Kaynak gruplar alınamadı: %s", e)
        return []


def _get_target_ids() -> list:
    """DB'deki hedef gruplar; yoksa .env TARGET_CHANNEL fallback."""
    try:
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT chat_id FROM chat_groups WHERE role = 'target' AND is_active = 1"
            ).fetchall()
        if rows:
            return [r["chat_id"] for r in rows]
    except Exception as e:
        log.error("Hedef gruplar alınamadı: %s", e)

    # Geriye uyumluluk — .env'deki TARGET_CHANNEL
    fallback = os.environ.get("TARGET_CHANNEL", "").strip()
    return [fallback] if fallback else []


def _migrate_from_env() -> None:
    """Eski .env SOURCE_CHAT_ID'yi DB'ye kaynak grup olarak ekle."""
    source_ids = _get_source_ids()
    if source_ids:
        return  # Zaten DB'de var

    raw = os.environ.get("SOURCE_CHAT_ID", "").strip()
    if not raw:
        return
    try:
        sid = int(raw)
        _register_chat(sid, f"Grup {sid}", "supergroup")
        with _get_db() as conn:
            conn.execute(
                "UPDATE chat_groups SET role = 'source' WHERE chat_id = ?", (sid,)
            )
        log.info("Migration: SOURCE_CHAT_ID=%s → kaynak grup olarak eklendi", sid)
    except (ValueError, Exception) as e:
        log.warning("Migration başarısız: %s", e)


# ── Link helpers ──────────────────────────────────────────────────────────────

def load_links(path: Path) -> dict[str, str]:
    mapping: dict[str, str] = {}
    if not path.exists():
        log.warning("links.txt bulunamadı.")
        return mapping
    for line in path.read_text(encoding="utf-8").splitlines():
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        if " : " in line:
            keyword, new_link = line.split(" : ", 1)
        elif ":" in line:
            keyword, new_link = line.split(":", 1)
        else:
            continue
        mapping[keyword.strip().lower()] = new_link.strip()
    log.info("%d eşleşme yüklendi.", len(mapping))
    return mapping


def extract_urls(text: str) -> list[str]:
    return re.findall(r"https?://\S+", text)


def slug_after_slash(url: str) -> str:
    clean = re.split(r"[?#]", url)[0]
    parts = clean.rstrip("/").split("/")
    return parts[-1].lower() if parts else ""


def find_replacement(
    text: str, urls: list[str], mapping: dict[str, str]
) -> str | None:
    text_lower = text.lower()
    for keyword, new_link in mapping.items():
        if keyword in text_lower:
            return new_link
        for url in urls:
            if slug_after_slash(url) == keyword:
                return new_link
    return None


def replace_links(text: str, urls: list[str], new_link: str) -> str:
    for url in urls:
        text = text.replace(url, new_link)
    return text


# ── Handler ───────────────────────────────────────────────────────────────────

router = Router()


@router.message()
@router.channel_post()
async def handle_any_message(message: Message, bot: Bot) -> None:
    chat  = message.chat
    title = getattr(chat, "title", "") or ""
    text  = message.text or message.caption or ""

    # Grubu kayıt et / güncelle
    _register_chat(chat.id, title, str(chat.type))

    # Kaynak kontrol
    source_ids = _get_source_ids()
    if not source_ids:
        log.info("Kaynak grup yok | chat_id=%s | title=%s", chat.id, title)
        return

    if chat.id not in source_ids:
        return

    if not text:
        return

    mapping  = load_links(LINKS_FILE)
    urls     = extract_urls(text)
    new_link = find_replacement(text, urls, mapping)

    if new_link is None:
        log.info("Eşleşme bulunamadı, mesaj iletilmedi.")
        return

    modified_text = replace_links(text, urls, new_link) if urls else text
    log.info("Eşleşme bulundu → %s", new_link)

    target_ids = _get_target_ids()
    if not target_ids:
        log.warning("Hedef grup yok, mesaj gönderilemedi.")
        return

    for target_id in target_ids:
        try:
            await bot.send_message(
                chat_id=target_id,
                text=modified_text,
                parse_mode=None,
            )
            log.info("Mesaj %s'e gönderildi.", target_id)
        except Exception as e:
            log.error("Gönderilemedi → %s: %s", target_id, e)


# ── Main ──────────────────────────────────────────────────────────────────────

async def main() -> None:
    _ensure_table()
    _migrate_from_env()

    bot = Bot(
        token=BOT_TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML),
    )
    dp = Dispatcher()
    dp.include_router(router)

    log.info(
        "Bot başlatılıyor | Kaynak: %d | Hedef: %d",
        len(_get_source_ids()), len(_get_target_ids()),
    )

    await dp.start_polling(
        bot,
        allowed_updates=["message", "channel_post"],
    )


if __name__ == "__main__":
    asyncio.run(main())
