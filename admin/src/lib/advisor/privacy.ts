import type { PrivacySummary } from '$lib/api';
import type { AdvisorTip } from './types';

/** Rule-based privacy tips for the Advisor tab and Privacy page. */
export function privacyTips(summary: PrivacySummary): AdvisorTip[] {
	if (summary.recommendations?.length) {
		return summary.recommendations.map((r) => ({
			id: r.id,
			severity: r.severity,
			title: r.title,
			detail: r.detail
		}));
	}

	const tips: AdvisorTip[] = [];
	if (summary.privacy_score < 70) {
		tips.push({
			id: 'low_score_fallback',
			severity: 'warning',
			title: 'Privacy score needs attention',
			detail: `${summary.non_private_utxos} UTXO(s) may be linkable. Open Coin Control to review flags.`
		});
	}
	if ((summary.exchange_exposure ?? 0) > 0) {
		tips.push({
			id: 'exchange_fallback',
			severity: 'warning',
			title: 'Exchange exposure',
			detail: 'Some labels indicate exchange-linked funds. Segregate before spending.'
		});
	}
	if (tips.length === 0 && summary.private_utxos > 0) {
		tips.push({
			id: 'healthy_fallback',
			severity: 'info',
			title: 'Wallet privacy looks healthy',
			detail: 'Keep receiving to fresh addresses and avoid reusing outputs.'
		});
	}
	return tips;
}

/** One-paragraph brief for Advisor summaries. */
export function formatPrivacyBrief(summary: PrivacySummary): string {
	const tips = privacyTips(summary);
	const headline = `Privacy score ${summary.privacy_score}/100 — ${summary.private_utxos} private, ${summary.non_private_utxos} flagged UTXO(s).`;
	if (tips.length === 0) {
		return headline;
	}
	const top = tips[0];
	return `${headline} Top tip: ${top.title} — ${top.detail}`;
}
