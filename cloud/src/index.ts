export interface Env {
  DB: D1Database;
}

const NETWORKS = new Set(['testnet', 'signet', 'regtest', 'mainnet']);
const DISPLAY_NAME = /^[A-Za-z0-9 _-]{2,32}$/;
const RESERVED = ['admin', 'administrator', 'coinwallet', 'official', 'support', 'moderator', 'staff', 'system', 'root'];
const CACHE_TTL = 30;

type EntryRow = {
  token_hash: string;
  display_name: string;
  balance_sats: number;
  network: string;
  opted_in: number;
  updated_at: string;
};

const listCache = new Map<string, { expires: number; payload: unknown }>();

function json(data: unknown, status = 200, extraHeaders: Record<string, string> = {}): Response {
  return new Response(JSON.stringify(data), {
    status,
    headers: {
      'Content-Type': 'application/json',
      ...extraHeaders,
    },
  });
}

function corsHeaders(origin: string | null): Record<string, string> {
  const allowed =
    !origin ||
    origin.endsWith('.pages.dev') ||
    origin.includes('localhost') ||
    origin.includes('127.0.0.1') ||
    origin.endsWith('.workers.dev');
  if (!allowed || !origin) {
    return { 'Access-Control-Allow-Origin': '*' };
  }
  return {
    'Access-Control-Allow-Origin': origin,
    'Access-Control-Allow-Methods': 'GET, POST, OPTIONS',
    'Access-Control-Allow-Headers': 'Content-Type',
  };
}

async function sha256Hex(value: string): Promise<string> {
  const data = new TextEncoder().encode(value.trim());
  const digest = await crypto.subtle.digest('SHA-256', data);
  return [...new Uint8Array(digest)].map((b) => b.toString(16).padStart(2, '0')).join('');
}

function validateDisplayName(name: string): string {
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

function parseNetwork(url: URL): string {
  const network = url.searchParams.get('network') ?? 'testnet';
  if (!NETWORKS.has(network)) {
    throw new Error('Invalid network');
  }
  return network;
}

async function getLeaderboard(env: Env, network: string, limit: number): Promise<Response> {
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
    .all<{ display_name: string; balance_sats: number; updated_at: string }>();

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

async function getRank(env: Env, tokenHash: string, network: string): Promise<number | null> {
  const row = await env.DB.prepare(
    `SELECT balance_sats FROM global_leaderboard_entries
     WHERE token_hash = ? AND network = ? AND opted_in = 1`
  )
    .bind(tokenHash, network)
    .first<{ balance_sats: number }>();
  if (!row) return null;

  const rankRow = await env.DB.prepare(
    `SELECT COUNT(*) + 1 AS rank FROM global_leaderboard_entries
     WHERE network = ? AND opted_in = 1 AND balance_sats > ?`
  )
    .bind(network, row.balance_sats)
    .first<{ rank: number }>();

  return rankRow?.rank ?? null;
}

async function register(body: Record<string, unknown>, env: Env): Promise<Response> {
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

async function update(body: Record<string, unknown>, env: Env): Promise<Response> {
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
    .first<EntryRow>();

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

async function optOut(body: Record<string, unknown>, env: Env): Promise<Response> {
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

export default {
  async fetch(request: Request, env: Env): Promise<Response> {
    const url = new URL(request.url);
    const headers = corsHeaders(request.headers.get('Origin'));

    if (request.method === 'OPTIONS') {
      return new Response(null, { status: 204, headers });
    }

    try {
      if (url.pathname === '/health') {
        return json({ status: 'ok', service: 'coinwallet-cloud' }, 200, headers);
      }

      if (url.pathname === '/api/leaderboard' && request.method === 'GET') {
        const network = parseNetwork(url);
        const limit = Math.min(100, Math.max(1, Number(url.searchParams.get('limit') ?? 100)));
        const res = await getLeaderboard(env, network, limit);
        for (const [k, v] of Object.entries(headers)) res.headers.set(k, v);
        return res;
      }

      if (url.pathname.startsWith('/api/leaderboard/remote/') && request.method === 'POST') {
        const body = (await request.json()) as Record<string, unknown>;
        let res: Response;
        if (url.pathname.endsWith('/register')) {
          res = await register(body, env);
        } else if (url.pathname.endsWith('/update')) {
          res = await update(body, env);
        } else if (url.pathname.endsWith('/opt-out')) {
          res = await optOut(body, env);
        } else {
          return json({ detail: 'Not found' }, 404, headers);
        }
        for (const [k, v] of Object.entries(headers)) res.headers.set(k, v);
        return res;
      }

      return json({ detail: 'Not found' }, 404, headers);
    } catch (err) {
      const message = err instanceof Error ? err.message : 'Request failed';
      return json({ detail: message }, 400, headers);
    }
  },
};
