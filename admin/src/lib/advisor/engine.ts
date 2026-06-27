import { balanceTips, explainRecentTransactions, formatBalanceBrief } from './balance';
import { feeTips, formatFeeBrief } from './fees';
import { BITCOIN_FAQ } from './faq';
import { formatPrivacyBrief, privacyTips } from './privacy';
import { securityChecklist } from './security';
import type { AdvisorContext, AdvisorReport, AdvisorSection } from './types';

const INTRO =
	'Rule-based guidance from your wallet data. CoinWallet never executes trades, market signals, or background swaps.';

export function runAdvisor(ctx: AdvisorContext): AdvisorReport {
	const sections: AdvisorSection[] = [];

	if (ctx.balance) {
		const summary = [
			formatBalanceBrief(ctx.balance, ctx.walletName),
			explainRecentTransactions(ctx.transactions)
		].join(' ');
		sections.push({
			id: 'balance',
			title: 'Balance & activity',
			summary,
			tips: balanceTips(ctx.balance, ctx.transactions)
		});
	}

	if (ctx.privacy) {
		sections.push({
			id: 'privacy',
			title: 'Privacy',
			summary: formatPrivacyBrief(ctx.privacy),
			tips: privacyTips(ctx.privacy)
		});
	}

	sections.push({
		id: 'security',
		title: 'Security checklist',
		summary: 'Passphrase, backup, and network posture for this session.',
		tips: securityChecklist(ctx.security, ctx.network ?? ctx.status?.network)
	});

	if (ctx.sendPreview) {
		sections.push({
			id: 'fees',
			title: 'Send fee review',
			summary: formatFeeBrief(ctx.sendPreview),
			tips: feeTips(ctx.sendPreview)
		});
	}

	return {
		intro: INTRO,
		sections: sections.filter((s) => s.tips.length > 0 || s.summary),
		faq: BITCOIN_FAQ
	};
}
