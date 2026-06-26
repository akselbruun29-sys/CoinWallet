import { writable } from 'svelte/store';
import { browser } from '$app/environment';

const STORAGE_KEY = 'wv_active_wallet_id';

function loadId(): number | null {
	if (!browser) return null;
	const raw = localStorage.getItem(STORAGE_KEY);
	if (!raw) return null;
	const id = Number(raw);
	return Number.isFinite(id) ? id : null;
}

export const activeWalletId = writable<number | null>(loadId());

export function setActiveWalletId(id: number | null) {
	activeWalletId.set(id);
	if (browser) {
		if (id == null) localStorage.removeItem(STORAGE_KEY);
		else localStorage.setItem(STORAGE_KEY, String(id));
	}
}

/** Reset stale active wallet; pick first wallet when none selected. */
export function validateActiveWallet(wallets: { id: number }[]) {
	activeWalletId.update((id) => {
		let next = id;
		if (next != null && !wallets.some((w) => w.id === next)) {
			next = null;
		}
		if (next == null && wallets.length > 0) {
			next = wallets[0].id;
		}
		if (browser) {
			if (next == null) localStorage.removeItem(STORAGE_KEY);
			else localStorage.setItem(STORAGE_KEY, String(next));
		}
		return next;
	});
}

export function isWalletSynced(wallet: { last_synced_height?: number }): boolean {
	return (wallet.last_synced_height ?? 0) > 0;
}

export const appRefreshTick = writable(0);

export function bumpAppRefresh() {
	appRefreshTick.update((n) => n + 1);
}
