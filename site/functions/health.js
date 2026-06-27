/** @type {import('@cloudflare/workers-types').PagesFunction} */
export async function onRequestGet() {
  return new Response(JSON.stringify({ status: 'ok', service: 'coinwallet-cloud' }), {
    headers: { 'Content-Type': 'application/json' },
  });
}
