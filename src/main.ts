import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'
import { installNodeAuthFetch } from './shared/nodeAuth'

// Node writes carry AETHELNET_AUTH_TOKEN when one is configured (see shared/nodeAuth.ts)
installNodeAuthFetch()

const app = createApp(App)
app.use(createPinia())

// Mount app - native WebSocket client initializes automatically
// The WebSocket connection status will update via event listeners
app.mount('#app')


