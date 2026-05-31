# LinkBot — Telegram Link Replacer Panel

Telegram gruplarındaki mesajları izler, belirlediğiniz anahtar kelimelere göre linkleri değiştirir ve hedef gruba/kanala iletir. Flask tabanlı web paneli ile tüm yönetim tarayıcıdan yapılabilir.

## İçindekiler

- [Özellikler](#özellikler)
- [Gereksinimler](#gereksinimler)
- [Kurulum — Docker ile (Önerilen)](#kurulum--docker-ile-önerilen)
- [Kurulum — Docker olmadan (Manuel)](#kurulum--docker-olmadan-manuel)
- [Kullanım](#kullanım)
- [Yapılandırma (.env)](#yapılandırma-env)
- [Docker Komutları](#docker-komutları)
- [Proje Yapısı](#proje-yapısı)
- [Teknolojiler](#teknolojiler)

---

## Özellikler

- Telegram mesajlarındaki linkleri anahtar kelimeye göre otomatik değiştirir
- **Birden fazla kaynak ve hedef grup** desteği
- Bot mesaj aldığı grupları **otomatik keşfeder** ve veritabanına kaydeder
- Web panel üzerinden kaynak/hedef rol ataması
- Link ekleme / düzenleme / silme / arama / sayfalama
- CSV, Excel (.xlsx) ve TXT içe/dışa aktarma
- Koyu/Açık tema desteği (Bootstrap 5.3)
- Giriş geçmişi (IP, tarayıcı, işletim sistemi, cihaz)
- Kullanıcı kaydı açma/kapama
- Panel URL ve port `.env` üzerinden yönetimi

---

## Gereksinimler

### Docker ile
- [Docker](https://docs.docker.com/get-docker/) 20+
- [docker-compose](https://docs.docker.com/compose/) v2+

### Manuel kurulum için
- Python 3.11+
- Node.js 18+ ve npm
- pip

---

## Kurulum — Docker ile (Önerilen)

### 1. Repoyu klonla

```bash
git clone https://github.com/Eren-Seyfi/python-telegram-linkbot.git
cd python-telegram-linkbot
```

### 2. `.env` dosyasını oluştur

```bash
cp .env.example .env
```

`.env` dosyasını bir metin editörüyle aç ve `BOT_TOKEN` değerini doldur:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
APP_URL=http://localhost
APP_PORT=5000
```

> **Bot Token nasıl alınır?**
> Telegram'da [@BotFather](https://t.me/BotFather) ile konuş → `/newbot` → token'ı kopyala.

### 3. Konteynerleri başlat

```bash
docker-compose up -d
```

İlk çalıştırmada Docker image'ları build edilir (2-5 dakika sürebilir). Build tamamlandıktan sonra panel `http://localhost:5000` adresinde hazır olur.

### 4. İlk kullanıcıyı oluştur

Tarayıcıda **`http://localhost:5000/register`** adresini aç ve bir yönetici hesabı oluştur.

> İlk kayıttan sonra **Ayarlar → Kullanıcı ve Erişim** bölümünden yeni kayıtları kapatabilirsin.

### 5. Botu gruplara ekle ve yapılandır

1. Telegram botunu dinlemek istediğin gruba/kanala ekle (admin olması önerilir)
2. O gruptan bir mesaj gönder — bot grubu otomatik keşfeder
3. Web panelinde **Gruplar** sayfasına git
4. Grubu **Kaynak** olarak işaretle
5. Mesajların iletileceği kanal/grubu **Hedef** olarak işaretle
6. **Linkler** sayfasından anahtar kelime → hedef URL eşleşmelerini ekle

---

## Kurulum — Docker olmadan (Manuel)

Bu yöntemle botu ve web panelini ayrı ayrı doğrudan çalıştırabilirsin.

### 1. Repoyu klonla

```bash
git clone https://github.com/Eren-Seyfi/python-telegram-linkbot.git
cd python-telegram-linkbot
```

### 2. Python sanal ortamı oluştur ve bağımlılıkları kur

```bash
python -m venv .venv

# Linux / macOS
source .venv/bin/activate

# Windows
.venv\Scripts\activate

pip install -r requirements.txt
```

### 3. Node.js bağımlılıklarını kur ve frontend'i derle

```bash
npm install
npm run build
```

Bu komut `static/dist/` klasörüne CSS ve JS dosyalarını oluşturur. Web paneli bu dosyaları kullanır.

### 4. `.env` dosyasını oluştur

```bash
cp .env.example .env
```

`.env` dosyasını düzenle:

```env
BOT_TOKEN=1234567890:ABCdefGHIjklMNOpqrsTUVwxyz
APP_URL=http://localhost
APP_PORT=5000
```

### 5. Web panelini başlat

Yeni bir terminal penceresi aç:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate

# Linux/macOS
FLASK_SECRET=gizli-bir-anahtar python web_app.py

# Windows (PowerShell)
$env:FLASK_SECRET="gizli-bir-anahtar"; python web_app.py
```

Panel `http://localhost:5000` adresinde çalışmaya başlar.

### 6. Telegram botunu başlat

Başka bir terminal penceresi aç:

```bash
source .venv/bin/activate   # Windows: .venv\Scripts\activate

python telegram_link_replacer.py
```

### 7. İlk kullanıcıyı oluştur

`http://localhost:5000/register` adresine git ve hesabını oluştur.

> **Not:** Manuel çalıştırmada her terminal oturumu kapatıldığında servisler durur.
> Kalıcı çalışma için [pm2](https://pm2.keymetrics.io/), [supervisor](http://supervisord.org/) veya systemd kullanabilirsin.

---

## Kullanım

### Web Panel Sayfaları

Tarayıcıda `http://localhost:5000` (veya `.env`'deki `APP_URL:APP_PORT`) adresini aç.

| Sayfa | Adres | Açıklama |
|-------|-------|----------|
| Dashboard | `/` | Özet: link sayısı, aktif kaynak/hedef gruplar |
| Linkler | `/links` | Link yönetimi — ekle, düzenle, sil, ara, içe/dışa aktar |
| Gruplar | `/groups` | Kaynak/hedef rol ataması, aktif/pasif toggle, düzenle |
| Ayarlar | `/settings` | Bot Token, Panel URL/Port, kayıt ayarları |
| Profil | `/profile` | Kullanıcı bilgileri, şifre, giriş geçmişi |

### Link Tablosu Formatı

```
# anahtar_kelime : hedef_url
marsbahis : https://example.com/ref-link
restbet   : https://example.com/another-link
```

- Anahtar kelime mesaj metninde **veya** URL slug'ında aranır (büyük/küçük harf duyarsız)
- `#` ile başlayan satırlar yorum satırıdır
- Tablo web panelinden yönetilir; değişiklikler `links.txt` ile senkronize tutulur

### İçe/Dışa Aktarma

**Dışa aktar:** Linkler → İndir → `.txt`, `.csv` veya `.xlsx`

**İçe aktar:** Linkler → Yükle → Desteklenen formatlar: `.txt`, `.csv`, `.xlsx`

CSV formatı:
```
keyword,url
marsbahis,https://example.com/ref
```

---

## Yapılandırma (.env)

| Değişken | Varsayılan | Açıklama |
|----------|-----------|----------|
| `BOT_TOKEN` | — | **Zorunlu.** BotFather'dan alınan Telegram API token'ı |
| `APP_URL` | `http://localhost` | Panelin dışarıdan erişilen adresi |
| `APP_PORT` | `5000` | Web panelinin dinlediği port |
| `FLASK_SECRET` | `linkbot-dev-secret` | Flask session şifreleme anahtarı — production'da değiştir! |
| `FLASK_DEBUG` | `false` | `true` yapılırsa geliştirme modu açılır (production'da kullanma) |

> **Güvenlik:** `FLASK_SECRET` değerini mutlaka rastgele ve uzun bir değerle değiştir.
> ```bash
> python -c "import secrets; print(secrets.token_hex(32))"
> ```

---

## Docker Komutları

```bash
# Tüm servisleri arka planda başlat
docker-compose up -d

# Logları canlı izle
docker-compose logs -f

# Sadece web servisini izle
docker-compose logs -f web

# Sadece botu izle
docker-compose logs -f bot

# Kod değişikliği sonrası yeniden build et
docker-compose up -d --build

# Sadece botu yeniden başlat (token değişikliği sonrası)
docker-compose restart bot

# Tüm servisleri durdur (veriler korunur)
docker-compose down

# Tüm servisleri ve verileri tamamen sil
docker-compose down -v
```

---

## Proje Yapısı

```
python-telegram-linkbot/
│
├── telegram_link_replacer.py   # Telegram botu (aiogram 3)
├── web_app.py                  # Flask web paneli + REST API
├── links.txt                   # Anahtar kelime → URL tablosu (bot tarafından okunur)
├── requirements.txt            # Python bağımlılıkları
│
├── frontend/                   # Vite kaynak dosyaları
│   ├── main.js                 # Alpine.js başlatma
│   └── style.css               # Bootstrap 5 + özel CSS
├── package.json                # Node bağımlılıkları
├── vite.config.js              # Vite yapılandırması
│
├── templates/
│   ├── layouts/
│   │   ├── panel.html          # Ana panel layout (sidebar, topbar, Alpine, dark mode)
│   │   └── auth.html           # Giriş/kayıt layout
│   ├── macros/
│   │   └── ui.html             # Flash mesajları, yardımcı makrolar
│   ├── index.html              # Dashboard
│   ├── links.html              # Link yönetimi
│   ├── groups.html             # Grup yönetimi
│   ├── settings.html           # Ayarlar
│   ├── profile.html            # Profil
│   ├── login.html              # Giriş
│   └── register.html           # Kayıt
│
├── Dockerfile                  # Bot servisi Docker image
├── Dockerfile.web              # Web servisi Docker image (multi-stage: Vite → Python)
├── docker-compose.yml          # İki servis: bot + web
│
├── .env.example                # Örnek .env şablonu
├── .gitignore
└── .claude/
    └── settings.json           # Claude Code hook ayarları (otomatik Docker rebuild)
```

---

## Teknolojiler

| Katman | Teknoloji |
|--------|-----------|
| Bot | Python 3.11, [aiogram 3](https://docs.aiogram.dev/) |
| Backend | [Flask 3](https://flask.palletsprojects.com/), Flask-Login, SQLite |
| Frontend | [Alpine.js 3](https://alpinejs.dev/), [Bootstrap 5.3](https://getbootstrap.com/) |
| Build | [Vite 5](https://vitejs.dev/) (multi-stage Docker build) |
| Deployment | Docker, docker-compose |

---

## Lisans

MIT © [Eren Seyfi](https://github.com/Eren-Seyfi)
