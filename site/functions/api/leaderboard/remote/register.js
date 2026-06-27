import { handleOptions, register, withCors } from '../../../_lib/leaderboard.js';

/** @type {import('@cloudflare/workers-types').PagesFunction} */
export async function onRequestOptions(context) {
  return handleOptions(context.request);
}

/** @type {import('@cloudflare/workers-types').PagesFunction} */
export async function onRequestPost(context) {
  try {
    const body = await context.request.json();
    const response = await register(body, context.env);
    return withCors(context.request, response);
  } catch (err) {
    const message = err instanceof Error ? err.message : 'Request failed';
    return withCors(context.request, new Response(JSON.stringify({ detail: message }), {
      status: 400,
      headers: { 'Content-Type': 'application/json' },
    }));
  }
}
