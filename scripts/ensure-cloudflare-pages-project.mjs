#!/usr/bin/env node
/** Create Cloudflare Pages project coinwallet if missing (non-interactive). */
import { spawnSync } from 'node:child_process';
import { dirname, join } from 'node:path';
import { fileURLToPath } from 'node:url';

const projectName = 'coinwallet';
const productionBranch = 'master';
const siteDir = join(dirname(fileURLToPath(import.meta.url)), '..', 'site');

function run(args, { allowFail = false } = {}) {
  const result = spawnSync('npx', ['wrangler', ...args], {
    cwd: siteDir,
    shell: true,
    encoding: 'utf8',
  });
  const out = `${result.stdout ?? ''}${result.stderr ?? ''}`;
  if (result.status !== 0 && !allowFail) {
    console.error(out);
    process.exit(result.status ?? 1);
  }
  return out;
}

const list = run(['pages', 'project', 'list'], { allowFail: true });
if (list.includes(projectName)) {
  console.log(`Cloudflare Pages project '${projectName}' already exists.`);
  process.exit(0);
}

console.log(`Creating Cloudflare Pages project '${projectName}'...`);
run(['pages', 'project', 'create', projectName, '--production-branch', productionBranch]);
console.log(`Created project '${projectName}'.`);
