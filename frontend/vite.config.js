import { defineConfig } from 'vite'
import vue from '@vitejs/plugin-vue'
import tailwindcss from '@tailwindcss/vite'

const outputDir = process.env.VITE_OUTPUT_DIR || '../static/vue'

export default defineConfig({
  plugins: [vue(), tailwindcss()],
  server: {
    port: 3000,
    proxy: {
      '/api': 'http://localhost:8000',
      '/static': 'http://localhost:8000',
    },
  },
  build: {
    outDir: outputDir,
    emptyOutDir: true,
  },
})
