import './style.css'
import Alpine from 'alpinejs'
import * as bootstrap from 'bootstrap'

// Globally expose — Jinja2 inline scripts use window.Alpine / window.bootstrap
window.bootstrap = bootstrap
window.Alpine    = Alpine

// type="module" is deferred, so all inline <script> tags in the body
// (including {% block scripts %} component registrations) run BEFORE
// this module executes. Alpine.start() fires alpine:init here, after
// all listeners are already registered.
Alpine.start()
