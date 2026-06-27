const NETWORKS = new Set(['testnet', 'signet', 'regtest', 'mainnet']);
const DISPLAY_NAME = /^[A-Za-z0-9 _-]{2,32}$/;
const RESERVED = [
  'admin',
  'administrator',
  'coinwallet',
  'official',
  'support',
  'moderator',
  'staff',
  'system',
  'root',
];
const CACHE_TTL = 30;

/** @typedef {{ DB: D1Database }} LeaderboardEnv */

const listCache = new Map();

/** @param {unknown} data @param {number} [status] @param {Record<string, string>} [extraHeaders] */
export function json(data, status = 200, extraHeaders = {}) {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...extraHeaders,
    },
  });
}

/** @param {string | null} origin */
export function corsHeaders(origin) {
  if (!origin) {
    return { 'Access-Control-Allow-Origin': '*' };
  }
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

/** @param {string} value */
export async function sha256Hex(value) {
  const data = new TextEncoder().encode(value.trim());
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

/** @param {string} name */
export function validateDisplayName(name) {
  const cleaned = name.trim();
  if (!DISPLAY_NAME.test(cleaned)) {
    throw new Error('Display name must be 2–32 characters: letters, numbers, spaces, hyphen, underscore');
  }
  const normalized = cleaned.toLowerCase().replace(/[\s_-]/g, '');
  for (const word of RESERVED) {
    if (normalized.includes(word)) {
      throw new Error('Display name cannot impersonate admin or CoinWallet staff');
    }
  }
  return cleaned;
}

/** @param {URL} url */
export function parseNetwork(url) {
  const network = url.searchParams.get('network') ?? 'testnet';
  if (!NETWORKS.has(network)) {
    throw new Error('Invalid network');
  }
  return network;
}

/** @param {LeaderboardEnv} env @param {string} network @param {number} limit */
export async function getLeaderboard(env, network, limit) {
  const cacheKey = `${network}:${limit}`;
  const cached = listCache.get(cacheKey);
  if (cached && cached.expires > Date.now()) {
    return json(cached.payload, 200, {
      'Cache-Control': `public, max-age=${CACHE_TTL}`,
    });
  }

  const rows = await env.DB.prepare(
    `SELECT display_name, balance_sats, updated_at
     FROM global_leaderboard_entries
     WHERE network = ? AND opted_in = 1
     ORDER BY balance_sats DESC, updated_at ASC
     LIMIT ?`
  )
    .bind(network, limit)
    .all();

  const payload = {
    network,
    entries: (rows.results ?? []).map((row, idx) => ({
      rank: idx + 1,
      display_name: row.display_name,
      balance_sats: row.balance_sats,
      updated_at: row.updated_at,
    })),
  };

  listCache.set(cacheKey, { expires: Date.now() + CACHE_TTL * 1000, payload });
  return json(payload, 200, { 'Cache-Control': `public, max-age=${CACHE_TTL}` });
}

/** @param {LeaderboardEnv} env @param {string} tokenHash @param {string} network */
export async function getRank(env, tokenHash, network) {
  const row = await env.DB.prepare(
    `SELECT balance_sats FROM global_leaderboard_entries
     WHERE token_hash = ? AND network = ? AND opted_in = 1`
  )
    .bind(tokenHash, network)
    .first();
  if (!row) return null;

  const rankRow = await env.DB.prepare(
    `SELECT COUNT(*) + 1 AS rank FROM global_leaderboard_entries
     WHERE network = ? AND opted_in = 1 AND balance_sats > ?`
  )
    .bind(network, row.balance_sats)
    .first();

  return rankRow?.rank ?? null;
}

/** @param {Record<string, unknown>} body @param {LeaderboardEnv} env */
export async function register(body, env) {
  const token = String(body.token ?? '');
  const displayName = validateDisplayName(String(body.display_name ?? ''));
  const network = String(body.network ?? '');
  const balanceSats = Number(body.balance_sats ?? 0);

  if (token.length < 16 || token.length > 128) {
    return json({ detail: 'Invalid token' }, 400);
  }
  if (!NETWORKS.has(network)) {
    return json({ detail: 'Invalid network' }, 400);
  }
  if (!Number.isFinite(balanceSats) || balanceSats < 0) {
    return json({ detail: 'Invalid balance' }, 400);
  }

  const tokenHash = await sha256Hex(token);
  await env.DB.prepare(
    `INSERT INTO global_leaderboard_entries (token_hash, display_name, balance_sats, network, opted_in, updated_at)
     VALUES (?, ?, ?, ?, 1, datetime('now'))
     ON CONFLICT(token_hash, network) DO UPDATE SET
       display_name = excluded.display_name,
       balance_sats = excluded.balance_sats,
       opted_in = 1,
       updated_at = datetime('now')`
  )
    .bind(tokenHash, displayName, balanceSats, network)
    .run();

  listCache.clear();
  const rank = await getRank(env, tokenHash, network);
  return json({ network, display_name: displayName, balance_sats: balanceSats, rank });
}

/** @param {Record<string, unknown>} body @param {LeaderboardEnv} env */
export async function update(body, env) {
  const token = String(body.token ?? '');
  const network = String(body.network ?? '');
  const balanceSats = Number(body.balance_sats ?? 0);

  if (!NETWORKS.has(network)) {
    return json({ detail: 'Invalid network' }, 400);
  }
  if (!Number.isFinite(balanceSats) || balanceSats < 0) {
    return json({ detail: 'Invalid balance' }, 400);
  }

  const tokenHash = await sha256Hex(token);
  const entry = await env.DB.prepare(
    `SELECT balance_sats FROM global_leaderboard_entries
     WHERE token_hash = ? AND network = ? AND opted_in = 1`
  )
    .bind(tokenHash, network)
    .first();

  if (!entry) {
    return json({ detail: 'Leaderboard entry not found' }, 404);
  }

  const previous = Number(entry.balance_sats ?? 0);
  const tolerance = Math.max(10_000, Math.floor(previous * 0.05));
  if (previous > 0 && balanceSats > previous * 2 + tolerance) {
    return json({ detail: 'Impossible balance increase rejected' }, 400);
  }
  if (previous > 0 && Math.abs(balanceSats - previous) > tolerance) {
    return json({ detail: 'Balance change exceeds tolerance' }, 400);
  }

  await env.DB.prepare(
    `UPDATE global_leaderboard_entries
     SET balance_sats = ?, updated_at = datetime('now')
     WHERE token_hash = ? AND network = ? AND opted_in = 1`
  )
    .bind(balanceSats, tokenHash, network)
    .run();

  listCache.clear();
  const rank = await getRank(env, tokenHash, network);
  return json({ network, balance_sats: balanceSats, rank });
}

/** @param {Record<string, unknown>} body @param {LeaderboardEnv} env */
export async function optOut(body, env) {
  const token = String(body.token ?? '');
  const network = String(body.network ?? '');
  if (!NETWORKS.has(network)) {
    return json({ detail: 'Invalid network' }, 400);
  }

  const tokenHash = await sha256Hex(token);
  await env.DB.prepare(
    `DELETE FROM global_leaderboard_entries WHERE token_hash = ? AND network = ?`
  )
    .bind(tokenHash, network)
    .run();

  listCache.clear();
  return json({ network, opted_in: false });
}

/** @param {Request} request @param {Response} response */
export function withCors(request, response) {
  const headers = corsHeaders(request.headers.get('Origin'));
  for (const [key, value] of Object.entries(headers)) {
    response.headers.set(key, value);
  }
  return response;
}

/** @param {Request} request */
export function handleOptions(request) {
  return new Response(null, { status: 204, headers: corsHeaders(request.headers.get('Origin')) });
}
