#!/usr/bin/env node
/** Add Tor resource bundle to tauri.conf.json when tor.exe is staged (release builds). */
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';

const root = path.join(path.dirname(fileURLToPath(import.meta.url)), '..');
const configPath = path.join(root, 'src-tauri', 'tauri.conf.json');
const torExe = path.join(root, 'src-tauri', 'resources', 'tor', 'tor.exe');

const cfg = JSON.parse(fs.readFileSync(configPath, 'utf8'));
if (fs.existsSync(torExe)) {
  cfg.bundle.resources = ['resources/tor/*'];
  console.log('patch-tauri-tor-resources: bundling resources/tor/*');
} else if (cfg.bundle.resources) {
  delete cfg.bundle.resources;
  console.log('patch-tauri-tor-resources: no tor.exe — removed bundle.resources');
}
fs.writeFileSync(configPath, JSON.stringify(cfg, null, 2) + '\n');
