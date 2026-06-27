import { clsx, type ClassValue } from "clsx";
import { twMerge } from "tailwind-merge";

export function cn(...inputs: ClassValue[]) {
	return twMerge(clsx(inputs));
}

// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChild<T> = T extends { child?: any } ? Omit<T, "child"> : T;
// eslint-disable-next-line @typescript-eslint/no-explicit-any
export type WithoutChildren<T> = T extends { children?: any } ? Omit<T, "children"> : T;
export type WithoutChildrenOrChild<T> = WithoutChildren<WithoutChild<T>>;
export type WithElementRef<T, U extends HTMLElement = HTMLElement> = T & { ref?: U | null };

export function formatUsd(value: number): string {
	return new Intl.NumberFormat('en-US', {
		style: 'currency',
		currency: 'USD'
	}).format(value);
}

export function formatPct(value: number): string {
	return `${(value * 100).toFixed(1)}%`;
}

export function formatSats(sats: number): string {
	return new Intl.NumberFormat('en-US').format(sats);
}

export function formatBtc(sats: number): string {
	if (sats <= 0) return '0.00 BTC';
	const btc = sats / 100_000_000;
	const trimmed = btc.toFixed(8).replace(/\.?0+$/, '');
	return `${trimmed} BTC`;
}

export function formatXmr(atomic: number): string {
	if (atomic <= 0) return '0.00 XMR';
	const xmr = atomic / 1_000_000_000_000;
	const trimmed = xmr.toFixed(12).replace(/\.?0+$/, '');
	return `${trimmed} XMR`;
}

export function formatWalletBalance(
	assetType: 'btc' | 'xmr' | undefined,
	amount: number
): string {
	return assetType === 'xmr' ? formatXmr(amount) : formatBtc(amount);
}

export function assetLabel(assetType: 'btc' | 'xmr' | undefined): string {
	return assetType === 'xmr' ? 'XMR' : 'BTC';
}

export function explorerTxUrl(txid: string, network = 'testnet'): string {
	if (network === 'mainnet') return `https://blockstream.info/tx/${txid}`;
	if (network === 'signet') return `https://blockstream.info/signet/tx/${txid}`;
	if (network === 'regtest') return `https://blockstream.info/testnet/tx/${txid}`;
	return `https://blockstream.info/testnet/tx/${txid}`;
}

export function explorerUrlForAsset(
	txid: string,
	asset: 'btc' | 'xmr' | undefined,
	network: string
): string {
	return asset === 'xmr' ? explorerXmrTxUrl(txid, network) : explorerTxUrl(txid, network);
}

export function explorerXmrTxUrl(txid: string, network = 'stagenet'): string {
	if (network === 'mainnet') return `https://xmrchain.net/tx/${txid}`;
	if (network === 'testnet') return `https://testnet.xmrchain.net/tx/${txid}`;
	return `https://stagenet.xmrchain.net/tx/${txid}`;
}

/** Client-side deposit address shape check — server validates checksum on execute. */
export function validateDepositAddress(asset: 'btc' | 'xmr', address: string): boolean {
	const a = address.trim();
	if (!a) return false;
	if (asset === 'btc') {
		return /^(bc1[02-9ac-hj-np-z]{11,87}|tb1[02-9ac-hj-np-z]{11,87}|bcrt1[02-9ac-hj-np-z]{11,87}|[13mn2][a-km-zA-HJ-NP-Z1-9]{25,34})$/.test(
			a
		);
	}
	return /^[48][0-9AB][1-9A-HJ-NP-Za-km-z]{93,106}$/.test(a);
}
