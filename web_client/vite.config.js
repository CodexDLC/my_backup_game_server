import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';


export default defineConfig({
  plugins: [react()],
  server: {
    // Эта секция нужна для разработки, чтобы сервер Vite
    // правильно работал с Docker
    host: '0.0.0.0',
    port: 5173, // Стандартный порт Vite
    watch: {
      usePolling: true,
    },
  },
  build: {
    // Указываем, что итоговая папка для сборки будет называться 'build'
    outDir: 'build',
  },
});