// vite.config.js
import { fileURLToPath, URL } from 'node:url';
import { defineConfig } from 'vite';
import vue from '@vitejs/plugin-vue';
import commonjs from '@rollup/plugin-commonjs'; // Make sure this is imported

// import vueDevTools from 'vite-plugin-vue-devtools'; // Uncomment if needed

export default defineConfig({
  plugins: [
    vue(),
    commonjs(), // Ensure this is present and correctly placed
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
        target: 'http://127.0.0.1:8000',
        changeOrigin: true,
        // rewrite: path => path.replace(/^\/api/, '') // Ensures API requests are correctly forwarded
      }
    }
  },
  assetsInclude: ['**/*.{JPG,jpg,png,svg}'], // Supports additional image formats
  // ADD THIS BLOCK TO SOLVE "process is not defined" ERROR
  define: {
    'process.env': {}
  },
  // ADD THIS BLOCK for improved dependency pre-bundling with pdf.js
  optimizeDeps: {
    include: ['pdfjs-dist'], // Only need pdfjs-dist if not using vue-pdf wrapper
  }
});