import { createApp } from 'vue'
import { createPinia } from 'pinia'
import App from './App.vue'
import './style.css'


const app = createApp(App)
app.use(createPinia())

// Mount app - native WebSocket client initializes automatically
// The WebSocket connection status will update via event listeners
app.mount('#app')


