import { writable } from 'svelte/store';
import { api, type WalletSecurityStatus } from '$lib/api';

export const walletSecurity = writable<WalletSecurityStatus | null>(null);

export async function refreshWalletSecurity(): Promise<WalletSecurityStatus> {
	const status = await api.walletSecurity();
	walletSecurity.set(status);
	return status;
}
