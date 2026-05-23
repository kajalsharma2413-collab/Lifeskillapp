// vite.config.js
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

export default defineConfig({
  plugins: [
    vue(),
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      // Local dev only — ignored in production build
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      }
    }
  },
  assetsInclude: ['**/*.{JPG,jpg,png,svg}'],
  define: {
    'process.env': {}
  },
  optimizeDeps: {
    include: ['pdfjs-dist', '@vapi-ai/web'],
  },
  build: {
    commonjsOptions: {
      include: [/@vapi-ai\/web/, /node_modules/],
    },
  },
});
