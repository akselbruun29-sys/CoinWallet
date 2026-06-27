import type { Balance, WalletTransaction } from '$lib/api';
import { formatBtc, formatSats } from '$lib/utils';
import type { AdvisorTip } from './types';

export function formatBalanceBrief(balance: Balance, walletName?: string): string {
	const label = walletName ? `${walletName} holds` : 'Your wallet holds';
	const unconfirmed = balance.unconfirmed_sats;
	if (unconfirmed > 0) {
		return `${label} ${formatBtc(balance.total_sats)} (${formatSats(balance.total_sats)} sats), including ${formatBtc(unconfirmed)} unconfirmed.`;
	}
	return `${label} ${formatBtc(balance.total_sats)} (${formatSats(balance.total_sats)} sats), all confirmed.`;
}

export function explainRecentTransactions(transactions: WalletTransaction[]): string {
	if (transactions.length === 0) {
		return 'No transactions yet. Receive testnet coins from a faucet, then sync your wallet.';
	}

	const parts = transactions.slice(0, 5).map((tx) => {
		const dir = tx.direction === 'receive' ? 'received' : tx.direction === 'send' ? 'sent' : 'moved';
		const when = tx.timestamp ? tx.timestamp.slice(0, 10) : 'unknown date';
		return `${when}: ${dir} ${formatBtc(Math.abs(tx.amount_sats))}`;
	});

	return `Recent activity — ${parts.join('; ')}.`;
}

export function balanceTips(
	balance: Balance | null,
	transactions: WalletTransaction[]
): AdvisorTip[] {
	const tips: AdvisorTip[] = [];

	if (!balance) {
		tips.push({
			id: 'balance_unavailable',
			severity: 'info',
			title: 'Balance not loaded',
			detail: 'Select a wallet and sync to see balance guidance.'
		});
		return tips;
	}

	if (balance.total_sats === 0) {
		tips.push({
			id: 'empty_wallet',
			severity: 'info',
			title: 'Wallet is empty',
			detail: 'Use Receive to generate an address. On testnet, fund from a faucet before sending.'
		});
	}

	if (balance.unconfirmed_sats > 0) {
		tips.push({
			id: 'unconfirmed',
			severity: 'warning',
			title: 'Unconfirmed funds',
			detail: `${formatBtc(balance.unconfirmed_sats)} is still confirming. Wait for at least 1 confirmation before spending.`
		});
	}

	const recentReceive = transactions.find((t) => t.direction === 'receive');
	if (recentReceive && balance.total_sats > 0) {
		tips.push({
			id: 'recent_receive',
			severity: 'info',
			title: 'Latest receive',
			detail: `Most recent incoming payment: ${formatBtc(recentReceive.amount_sats)}${recentReceive.timestamp ? ` on ${recentReceive.timestamp.slice(0, 10)}` : ''}.`
		});
	}

	return tips;
}
