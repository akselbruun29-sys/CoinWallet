import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig } from 'vite';

const desktopBuild =
  process.env.COINWALLET_DESKTOP === '1' ||
  process.env.npm_lifecycle_event === 'build:desktop';

export default defineConfig({
  plugins: [tailwindcss(), sveltekit()],
  base: desktopBuild ? './' : undefined,
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://127.0.0.1:8002',
        changeOrigin: true,
        ws: true
      }
    }
  }
});
