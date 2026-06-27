export { balanceTips, explainRecentTransactions, formatBalanceBrief } from './balance';
export { feeTips, formatFeeBrief } from './fees';
export { BITCOIN_FAQ } from './faq';
export { runAdvisor } from './engine';
export {
	buildAdvisorAiPayload,
	fetchCloudAdvisorHints,
	runAdvisorWithOptionalCloud
} from './remote-ai';
export { formatPrivacyBrief, privacyTips } from './privacy';
export { securityCheckItems, securityChecklist, securityChecklistSummary } from './security';
export { formatSwapBrief, swapHistoryTips, swapTips } from './swap';
export type {
	AdvisorContext,
	AdvisorReport,
	AdvisorSection,
	AdvisorSeverity,
	AdvisorTip,
	FaqItem
} from './types';
