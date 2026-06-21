import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'
import VueDevTools from 'vite-plugin-vue-devtools'

export default defineConfig({
  plugins: [vue(), tailwindcss(), VueDevTools()],
  server: {
    host: true,
    proxy: {
      '/games': 'http://localhost:8000',
      '/events': 'http://localhost:8000',
    },
  },
})
