/** URLs for optional internet-only services (leaderboard + cloud AI). Wallet API stays local. */
export const REMOTE_SERVICES_URL = (
	import.meta.env.VITE_REMOTE_SERVICES_URL ?? ''
).replace(/\/$/, '');

export const ADVISOR_AI_URL = (import.meta.env.VITE_ADVISOR_AI_URL ?? '').replace(/\/$/, '');

export function remoteServicesEnabled(): boolean {
	return REMOTE_SERVICES_URL.length > 0;
}

export function advisorAiEnabled(): boolean {
	return ADVISOR_AI_URL.length > 0;
}

export async function remoteGet<T>(path: string): Promise<T> {
	const res = await fetch(`${REMOTE_SERVICES_URL}${path}`, {
		method: 'GET',
		headers: { Accept: 'application/json' }
	});
	if (!res.ok) {
		throw new Error(`Remote request failed (${res.status})`);
	}
	return res.json() as Promise<T>;
}

export async function remotePost<T>(path: string, body: unknown): Promise<T> {
	const res = await fetch(`${REMOTE_SERVICES_URL}${path}`, {
		method: 'POST',
		headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
		body: JSON.stringify(body)
	});
	if (!res.ok) {
		const text = await res.text();
		throw new Error(text || `Remote request failed (${res.status})`);
	}
	return res.json() as Promise<T>;
}
