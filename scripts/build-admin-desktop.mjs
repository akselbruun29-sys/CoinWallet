#!/usr/bin/env node
/** Desktop (Tauri) admin build — relative asset paths for embedded webview. */
import { readFileSync, writeFileSync } from 'node:fs';
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const adminDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'admin');
const env = { ...process.env, COINWALLET_DESKTOP: '1' };
env.VITE_COINWALLET_DESKTOP = 'true';
if (process.env.VITE_REMOTE_SERVICES_URL) {
  env.VITE_REMOTE_SERVICES_URL = process.env.VITE_REMOTE_SERVICES_URL;
} else if (process.env.COINWALLET_REMOTE_SERVICES_URL) {
  env.VITE_REMOTE_SERVICES_URL = process.env.COINWALLET_REMOTE_SERVICES_URL;
} else {
  env.VITE_REMOTE_SERVICES_URL = 'https://coinwallet.pages.dev';
  env.COINWALLET_REMOTE_SERVICES_URL = 'https://coinwallet.pages.dev';
}
const result = spawnSync('npm', ['exec', 'vite', 'build'], {
  cwd: adminDir,
  stdio: 'inherit',
  shell: true,
  env,
});
if (result.status !== 0) {
  process.exit(result.status ?? 1);
}

const indexPath = join(adminDir, 'build', 'index.html');
let html = readFileSync(indexPath, 'utf8');
html = html
  .replace(/href="\//g, 'href="./')
  .replace(/import\("\//g, 'import("./');
writeFileSync(indexPath, html);
console.log('Patched admin/build/index.html for Tauri relative asset paths');
