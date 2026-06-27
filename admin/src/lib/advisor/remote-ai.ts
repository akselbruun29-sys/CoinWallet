import { ADVISOR_AI_URL, advisorAiEnabled } from '../remote-services';
import type { AdvisorContext, AdvisorReport } from './types';
import { runAdvisor } from './engine';

/** Non-sensitive summary only — never send mnemonics, passphrases, or addresses. */
export type AdvisorAiPayload = {
	network: string;
	wallet_count: number;
	synced: boolean;
	total_sats_band: 'zero' | 'low' | 'mid' | 'high';
	has_open_swaps: boolean;
	mainnet: boolean;
};

function balanceBand(totalSats: number): AdvisorAiPayload['total_sats_band'] {
	if (totalSats <= 0) return 'zero';
	if (totalSats < 100_000) return 'low';
	if (totalSats < 10_000_000) return 'mid';
	return 'high';
}

export function buildAdvisorAiPayload(ctx: AdvisorContext): AdvisorAiPayload {
	const total = ctx.balance?.total_sats ?? 0;
	return {
		network: ctx.network ?? ctx.status?.network ?? 'testnet',
		wallet_count: ctx.status?.wallet_count ?? 0,
		synced: ctx.status?.synced ?? false,
		total_sats_band: balanceBand(total),
		has_open_swaps: (ctx.swapHistory?.length ?? 0) > 0,
		mainnet: (ctx.network ?? ctx.status?.network) === 'mainnet'
	};
}

export async function fetchCloudAdvisorHints(
	ctx: AdvisorContext
): Promise<AdvisorReport['sections'] | null> {
	if (!advisorAiEnabled()) return null;
	const payload = buildAdvisorAiPayload(ctx);
	const res = await fetch(`${ADVISOR_AI_URL}/api/advisor/hints`, {
		method: 'POST',
		headers: { Accept: 'application/json', 'Content-Type': 'application/json' },
		body: JSON.stringify(payload)
	});
	if (!res.ok) return null;
	const data = (await res.json()) as { sections?: AdvisorReport['sections'] };
	return data.sections?.length ? data.sections : null;
}

/** Rule engine offline by default; optional cloud hints when VITE_ADVISOR_AI_URL is set. */
export async function runAdvisorWithOptionalCloud(ctx: AdvisorContext): Promise<AdvisorReport> {
	const local = runAdvisor(ctx);
	if (!advisorAiEnabled()) return local;

	try {
		const cloudSections = await fetchCloudAdvisorHints(ctx);
		if (!cloudSections?.length) return local;
		return {
			...local,
			intro:
				'Rule-based guidance from your wallet, plus optional cloud hints. Keys and seeds never leave this device.',
			sections: [...local.sections, ...cloudSections]
		};
	} catch {
		return local;
	}
}
