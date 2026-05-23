// vite.config.js
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';

// import vueDevTools from 'vite-plugin-vue-devtools'; // Uncomment if needed

export default defineConfig({
  plugins: [
    vue(),
    // vueDevTools() // Uncomment this if you want to use Vue DevTools
  ],
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url))
    }
  },
  server: {
    proxy: {
      '/api': {
        target: 'https://lifeskillapp.onrender.com',
        changeOrigin: true,
        // rewrite: path => path.replace(/^\/api/, '') // Ensures API requests are correctly forwarded
      }
    }
  },
  assetsInclude: ['**/*.{JPG,jpg,png,svg}'],
  define: {
    'process.env': {}
  },
  // Pre-bundle CJS dependencies so Rollup can handle them in production
  optimizeDeps: {
    include: ['pdfjs-dist', '@vapi-ai/web'],
  },
  build: {
    // Tell Rollup's built-in commonjs plugin to process @vapi-ai/web
    commonjsOptions: {
      include: [/@vapi-ai\/web/, /node_modules/],
    },
  },
});
