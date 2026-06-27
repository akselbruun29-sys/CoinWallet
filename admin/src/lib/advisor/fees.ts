import type { SendPreview } from '$lib/api';
import { formatBtc, formatSats } from '$lib/utils';
import type { AdvisorTip } from './types';

export function formatFeeBrief(preview: SendPreview): string {
	const pct =
		preview.amount_sats + preview.fee_sats > 0
			? ((preview.fee_sats / (preview.amount_sats + preview.fee_sats)) * 100).toFixed(2)
			: '0';
	return (
		`Sending ${formatBtc(preview.amount_sats)} with fee ${formatSats(preview.fee_sats)} sats ` +
		`(${preview.fee_rate_sat_vb} sat/vB, ~${pct}% of total). Change back: ${formatBtc(preview.change_sats)}.`
	);
}

/** Rule-based fee guidance from a send preview (no live mempool oracle). */
export function feeTips(preview: SendPreview | null | undefined): AdvisorTip[] {
	if (!preview) return [];

	const tips: AdvisorTip[] = [];
	const rate = preview.fee_rate_sat_vb;

	if (rate < 2) {
		tips.push({
			id: 'fee_low',
			severity: 'warning',
			title: 'Low fee rate',
			detail: `${rate} sat/vB may confirm slowly when the mempool is busy. Raise the fee if this payment is time-sensitive.`
		});
	} else if (rate >= 2 && rate <= 15) {
		tips.push({
			id: 'fee_economy',
			severity: 'info',
			title: 'Economy fee range',
			detail: `${rate} sat/vB is reasonable for non-urgent testnet sends. Mainnet users should check current mempool conditions.`
		});
	} else if (rate > 50) {
		tips.push({
			id: 'fee_high',
			severity: 'warning',
			title: 'High fee rate',
			detail: `${rate} sat/vB is above typical economy rates. Lower it unless you need fast confirmation.`
		});
	}

	if (preview.input_count > 10) {
		tips.push({
			id: 'many_inputs',
			severity: 'info',
			title: 'Many inputs selected',
			detail: `${preview.input_count} inputs increase transaction size and fees. Coin Control can help consolidate later.`
		});
	}

	if (preview.change_sats > 0 && preview.change_sats < 1000) {
		tips.push({
			id: 'dust_change',
			severity: 'warning',
			title: 'Small change output',
			detail: 'Change below ~1000 sats may be uneconomical to spend later. Consider adjusting the send amount.'
		});
	}

	return tips;
}
