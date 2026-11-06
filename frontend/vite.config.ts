import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig(({ mode }) => ({
  base: mode === 'production' ? '/app/' : '/',
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/query': 'http://127.0.0.1:8000',
      '/health': 'http://127.0.0.1:8000',
      '/sources': 'http://127.0.0.1:8000',
      '/metrics': 'http://127.0.0.1:8000',
    },
  },
  build: {
    outDir: 'dist',
    emptyOutDir: true,
  },
}))
