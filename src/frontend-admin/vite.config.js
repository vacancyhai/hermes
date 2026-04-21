import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';

const BACKEND_ORIGIN = process.env.VITE_PROXY_TARGET || 'http://backend:8000';

export default defineConfig({
  plugins: [react()],
  server: {
    host: '0.0.0.0',
    port: 4000,
    proxy: {
      '/api': {
        target: BACKEND_ORIGIN,
        changeOrigin: true,
      },
    },
  },
  preview: {
    host: '0.0.0.0',
    port: 4000,
  },
});
