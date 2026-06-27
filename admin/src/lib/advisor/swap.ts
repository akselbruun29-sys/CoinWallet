import type { SwapQuote, SwapRecord } from '$lib/api';
import { assetLabel, formatWalletBalance } from '$lib/utils';
import type { AdvisorTip } from './types';

export function swapTips(quote: SwapQuote): AdvisorTip[] {
	const tips: AdvisorTip[] = [];
	const providerPct =
		quote.receive_amount_atomic + quote.fees.provider > 0
			? (quote.fees.provider / (quote.receive_amount_atomic + quote.fees.provider)) * 100
			: 0;

	tips.push({
		id: 'swap-manual',
		severity: 'info',
		title: 'You confirm every swap',
		detail:
			'CoinWallet never auto-converts received funds. Each swap requires an explicit quote review and confirmation.'
	});

	if (quote.provider === 'rate_table') {
		tips.push({
			id: 'swap-dev-provider',
			severity: 'warning',
			title: 'Dev rate table provider',
			detail:
				'This quote uses a local reference rate for testnet/stagenet only — not live market liquidity. Use Haveno or a disclosed API for production.'
		});
	}

	if (providerPct >= 1) {
		tips.push({
			id: 'swap-provider-fee',
			severity: providerPct >= 3 ? 'warning' : 'info',
			title: 'Provider fee',
			detail: `Provider fee is ~${providerPct.toFixed(2)}% of gross receive (${formatWalletBalance(quote.to_asset, quote.fees.provider)}). Compare with network fee ${formatWalletBalance(quote.from_asset, quote.fees.network)} before confirming.`
		});
	}

	if (quote.from_asset === 'btc' && quote.to_asset === 'xmr') {
		tips.push({
			id: 'swap-privacy-exit',
			severity: 'info',
			title: 'Privacy exit timing',
			detail:
				'Swapping BTC→XMR can break on-chain traceability for future XMR spends, but the swap itself may be observable depending on provider. Prefer non-custodial P2P when possible.'
		});
	}

	return tips;
}

export function swapHistoryTips(records: SwapRecord[]): AdvisorTip[] {
	const pending = records.filter(
		(r) => r.status === 'awaiting_user_send' || r.status === 'awaiting_deposit'
	);
	if (pending.length === 0) return [];
	return [
		{
			id: 'swap-pending-tx',
			severity: 'warning',
			title: `${pending.length} swap(s) awaiting your send`,
			detail:
				'Complete the outbound transaction via Send, then attach the transaction ID in Swap history for explorer tracking.'
		}
	];
}

export function formatSwapBrief(quote: SwapQuote): string {
	return `Swap ${formatWalletBalance(quote.from_asset, quote.send_amount_atomic)} ${assetLabel(quote.from_asset)} → ${formatWalletBalance(quote.to_asset, quote.receive_amount_atomic)} ${assetLabel(quote.to_asset)} at rate ${quote.rate}.`;
}
