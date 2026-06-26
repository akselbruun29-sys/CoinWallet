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
	const btc = sats / 100_000_000;
	return `${btc.toFixed(8)} BTC`;
}

export function explorerTxUrl(txid: string, network = 'testnet'): string {
	if (network === 'mainnet') return `https://blockstream.info/tx/${txid}`;
	if (network === 'signet') return `https://blockstream.info/signet/tx/${txid}`;
	if (network === 'regtest') return `https://blockstream.info/testnet/tx/${txid}`;
	return `https://blockstream.info/testnet/tx/${txid}`;
}
