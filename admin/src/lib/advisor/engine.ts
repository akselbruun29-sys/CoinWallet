import { balanceTips, explainRecentTransactions, formatBalanceBrief } from './balance';
import { feeTips, formatFeeBrief } from './fees';
import { BITCOIN_FAQ } from './faq';
import { formatPrivacyBrief, privacyTips } from './privacy';
import { securityCheckItems, securityChecklist, securityChecklistSummary } from './security';
import { formatSwapBrief, swapHistoryTips, swapTips } from './swap';
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
		summary: securityChecklistSummary(ctx.security, ctx.network ?? ctx.status?.network, ctx.settings),
		checklist: securityCheckItems(ctx.security, ctx.network ?? ctx.status?.network, ctx.settings),
		tips: securityChecklist(ctx.security, ctx.network ?? ctx.status?.network, ctx.settings)
	});

	if (ctx.sendPreview) {
		sections.push({
			id: 'fees',
			title: 'Send fee review',
			summary: formatFeeBrief(ctx.sendPreview),
			tips: feeTips(ctx.sendPreview)
		});
	}

	if (ctx.swapQuote) {
		sections.push({
			id: 'swap',
			title: 'Swap review',
			summary: formatSwapBrief(ctx.swapQuote),
			tips: swapTips(ctx.swapQuote)
		});
	}

	if (ctx.swapHistory?.length) {
		const historyTips = swapHistoryTips(ctx.swapHistory);
		if (historyTips.length) {
			sections.push({
				id: 'swap-history',
				title: 'Open swaps',
				summary: 'Pending swaps need your outbound transaction.',
				tips: historyTips
			});
		}
	}

	return {
		intro: INTRO,
		sections: sections.filter((s) => s.tips.length > 0 || s.summary),
		faq: BITCOIN_FAQ
	};
}
