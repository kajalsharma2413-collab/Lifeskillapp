import { createApp } from 'vue'
import App from './App.vue'
import './assets/main.css'

import router from './router'
import { createPinia } from 'pinia'

// ── Global fetch interceptor — rewrites /api/* to backend URL in production ──
const API_BASE = import.meta.env.VITE_API_BASE_URL || ''

if (API_BASE) {
  const _originalFetch = window.fetch.bind(window)
  window.fetch = (input, init) => {
    if (typeof input === 'string' && input.startsWith('/api/')) {
      input = `${API_BASE}${input}`
    } else if (input instanceof Request && input.url.startsWith('/api/')) {
      input = new Request(`${API_BASE}${input.url}`, input)
    }
    return _originalFetch(input, init)
  }
}
// ─────────────────────────────────────────────────────────────────────────────

const app = createApp(App)

app.use(createPinia())
app.use(router)

app.mount('#app')
