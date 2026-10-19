import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In development the backend runs on :5000; API, uploads and Socket.IO are proxied.
export default defineConfig({
  plugins: [react()],
  server: {
    port: 5175,
    strictPort: true,
    proxy: {
      '/api': 'http://127.0.0.1:5002',
      '/socket.io': { target: 'http://127.0.0.1:5002', ws: true },
    },
  },
})
