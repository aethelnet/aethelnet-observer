import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import { VitePWA } from 'vite-plugin-pwa'
import { fileURLToPath, URL } from 'node:url'

// https://vitejs.dev/config/
export default defineConfig({
    plugins: [
        vue(),
        VitePWA({
            registerType: 'autoUpdate',
            injectRegister: 'auto',
            devOptions: {
                enabled: false
            },
            manifest: {
                name: 'Sovereign Neural Manifold',
                short_name: 'LGNN Hub',
                description: 'The minimalist reality anchor and neural manifold UI',
                theme_color: '#f8f9fa',
                background_color: '#f8f9fa',
                display: 'standalone',
                icons: [
                    {
                        src: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect width="200" height="200" fill="%23f8f9fa"/><circle cx="100" cy="100" r="90" fill="url(%23g)"/><defs><radialGradient id="g"><stop offset="0%" stop-color="%23c8c8ff" stop-opacity="0.5"/><stop offset="100%" stop-color="%23ffffff" stop-opacity="0"/></radialGradient></defs><circle cx="100" cy="100" r="60" fill="%23ffffff" stroke="%23c678dd" stroke-width="2"/></svg>',
                        sizes: '192x192',
                        type: 'image/svg+xml',
                        purpose: 'any maskable'
                    },
                    {
                        src: 'data:image/svg+xml;utf8,<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 200 200"><rect width="200" height="200" fill="%23f8f9fa"/><circle cx="100" cy="100" r="60" fill="%23ffffff" stroke="%23c678dd" stroke-width="2"/></svg>',
                        sizes: '512x512',
                        type: 'image/svg+xml',
                        purpose: 'any maskable'
                    }
                ]
            }
        })
    ],
    // NOTE: Add a watch configuration to avoid hitting the OS file-watcher limit
    // by excluding large/backup/build folders (e.g. src-tauri target output, input backups).
    // This prevents Vite from watching those paths and reduces inotify usage.
    server: {
        host: '127.0.0.1',
        port: 1420,
        strictPort: true,
        open: false,
        // chokidar options passed to Vite's watcher. Adjust ignored patterns to match
        // project-specific directories that should not be watched.
        watch: {
            // Do not watch common noisy or large folders (backups, build outputs, node_modules, git)
            ignored: [
                '**/node_modules/**',
                '**/.git/**',
                '**/input/**',
                '**/input/**/**',
                '**/input/backups/**',
                '**/src-tauri/**',
                '**/target/**',
                '**/dist/**'
            ],
            // Ensure polling is disabled (polling increases watcher usage); keep defaults otherwise.
            usePolling: false
        },
        proxy: {
            '/api/v3': {
                target: 'https://api.binance.com',
                changeOrigin: true,
                secure: false
            },
            '/api': {
                target: 'http://127.0.0.1:8001',
                changeOrigin: true,
                ws: true
            },
            '/aethelnet': {
                target: 'http://127.0.0.1:8001',
                changeOrigin: true,
                ws: true
            },
            '/ws': {
                target: 'ws://127.0.0.1:8001',
                ws: true
            }
        }
    },
    resolve: {
        alias: {
            '@': fileURLToPath(new URL('./src', import.meta.url))
        }
    },
    optimizeDeps: {
        include: ['three', 'gsap', 'vue', 'pinia']
    },
    build: {
        target: 'esnext',
        minify: 'esbuild',
        sourcemap: false,
        rollupOptions: {
            output: {
                manualChunks: {
                    'vendor-vue': ['vue', 'pinia'],
                    'vendor-charts': ['lightweight-charts', 'echarts', 'vue-echarts'],
                    'vendor-3d': ['three'],
                    'vendor-animation': ['gsap'],
                    'vendor-d3': ['d3']
                }
            }
        }
    },
    worker: {
        format: 'es'
    }
})



