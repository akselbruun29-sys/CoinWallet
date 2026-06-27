import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';
import adapter from '@sveltejs/adapter-static';

/** @type {import('@sveltejs/kit').Config} */
const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: undefined,
      precompress: false,
      strict: true,
    }),
    prerender: {
      entries: ['*'],
      handleHttpError: ({ path, message }) => {
        if (path.startsWith('/releases/') && /\.(exe|dmg)$/i.test(path)) {
          console.warn(message);
          return;
        }
        throw new Error(message);
      },
    },
  },
};

export default config;
