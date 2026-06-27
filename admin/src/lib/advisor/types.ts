import type {
	Balance,
	PrivacySummary,
	SendPreview,
	StatusResponse,
	SwapQuote,
	SwapRecord,
	WalletSecurityStatus,
	WalletTransaction
} from '$lib/api';

export type AdvisorSeverity = 'info' | 'warning' | 'critical';

export interface AdvisorTip {
	id: string;
	severity: AdvisorSeverity;
	title: string;
	detail: string;
}

export interface AdvisorSection {
	id: string;
	title: string;
	summary: string;
	tips: AdvisorTip[];
	checklist?: SecurityCheckItem[];
}

export interface SecurityCheckItem {
	id: string;
	label: string;
	passed: boolean;
	severity: AdvisorSeverity;
	detail?: string;
}

export interface FaqItem {
	id: string;
	question: string;
	answer: string;
}

export interface AdvisorContext {
	walletId: number | null;
	walletName?: string;
	network?: string;
	balance: Balance | null;
	transactions: WalletTransaction[];
	privacy: PrivacySummary | null;
	security: WalletSecurityStatus | null;
	status: StatusResponse | null;
	settings?: Record<string, string>;
	sendPreview?: SendPreview | null;
	swapQuote?: SwapQuote | null;
	swapHistory?: SwapRecord[];
}

export interface AdvisorReport {
	intro: string;
	sections: AdvisorSection[];
	faq: FaqItem[];
}
