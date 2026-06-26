import { API_BASE, getToken } from '$lib/api';
import { bumpAppRefresh } from '$lib/stores/wallet';

let socket: WebSocket | null = null;

function wsBase(): string {
	const base = API_BASE.replace(/^http/, 'ws');
	return `${base}/api/ws/events`;
}

export function connectWalletEvents(): void {
	const token = getToken();
	if (!token || socket) return;

	socket = new WebSocket(`${wsBase()}?token=${encodeURIComponent(token)}`);
	socket.onmessage = (event) => {
		try {
			const data = JSON.parse(event.data) as { event?: string };
			if (data.event === 'wallet_synced' || data.event === 'tx_sent') {
				bumpAppRefresh();
			}
		} catch {
			// ignore malformed payloads
		}
	};
	socket.onclose = () => {
		socket = null;
	};
}

export function disconnectWalletEvents(): void {
	socket?.close();
	socket = null;
}
