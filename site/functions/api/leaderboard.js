import { getLeaderboard, handleOptions, parseNetwork, withCors } from '../_lib/leaderboard.js';

/** @type {import('@cloudflare/workers-types').PagesFunction} */
export async function onRequestOptions(context) {
  return handleOptions(context.request);
}

/** @type {import('@cloudflare/workers-types').PagesFunction} */
export async function onRequestGet(context) {
  try {
    const url = new URL(context.request.url);
    const network = parseNetwork(url);
    const limit = Math.min(100, Math.max(1, Number(url.searchParams.get('limit') ?? 100)));
    const response = await getLeaderboard(context.env, network, limit);
    return withCors(context.request, response);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Request failed';
    return withCors(context.request, new Response(JSON.stringify({ detail: message }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    }));
  }
}
