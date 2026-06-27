#!/usr/bin/env node
/** Copy releases manifest and desktop artifacts into site/static for deploy. */
import { copyFileSync, existsSync, mkdirSync, readFileSync } from 'node:fs';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const root = join(dirname(fileURLToPath(import.meta.url)), '..');
const releasesDir = join(root, 'releases');
const staticReleases = join(root, 'site', 'static', 'releases');

mkdirSync(staticReleases, { recursive: true });

const manifestSrc = join(releasesDir, 'releases.json');
const manifestDest = join(staticReleases, 'releases.json');
copyFileSync(manifestSrc, manifestDest);
console.log('Synced releases.json → site/static/releases/releases.json');

const signingKeys = join(releasesDir, 'signing-keys.example.json');
if (existsSync(signingKeys)) {
  copyFileSync(signingKeys, join(staticReleases, 'signing-keys.example.json'));
}

const manifest = JSON.parse(readFileSync(manifestSrc, 'utf8'));
const names = new Set(
  Object.values(manifest.platforms ?? {})
    .map((p) => (p.url ?? '').split('/').pop())
    .filter(Boolean)
);

for (const name of names) {
  const src = join(releasesDir, name);
  if (!existsSync(src)) {
    continue;
  }
  const dest = join(staticReleases, name);
  copyFileSync(src, dest);
  console.log(`Synced ${name} → site/static/releases/${name}`);
}
