import { sveltekit } from '@sveltejs/kit/vite';
import tailwindcss from '@tailwindcss/vite';
import { defineConfig, type Plugin } from 'vite';

const desktopBuild =
  process.env.COINWALLET_DESKTOP === '1' ||
  process.env.npm_lifecycle_event === 'build:desktop';

function desktopCspPlugin(): Plugin {
  return {
    name: 'coinwallet-desktop-csp',
    transformIndexHtml(html) {
      if (!desktopBuild) return html;
      const remote = (process.env.VITE_REMOTE_SERVICES_URL ?? 'https://coinwallet.pages.dev').replace(
        /\/$/,
        ''
      );
      const connectSrc = [
        "'self'",
        'http://127.0.0.1:*',
        'http://localhost:*',
        'ws://127.0.0.1:*',
        'ws://localhost:*',
        remote,
      ].join(' ');
      const csp = [
        "default-src 'self'",
        "script-src 'self'",
        "style-src 'self' 'unsafe-inline'",
        "img-src 'self' data: blob:",
        `connect-src ${connectSrc}`,
        "font-src 'self'",
        "object-src 'none'",
        "base-uri 'self'",
        "form-action 'self'",
        "frame-ancestors 'none'",
      ].join('; ');
      return html.replace(
        '<head>',
        `<head>\n    <meta http-equiv="Content-Security-Policy" content="${csp}" />`
      );
    },
  };
}

export default defineConfig({
  plugins: [tailwindcss(), sveltekit(), desktopCspPlugin()],
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
