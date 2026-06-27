import type { WalletSecurityStatus } from '$lib/api';
import type { AdvisorTip, SecurityCheckItem } from './types';

export function securityCheckItems(
	security: WalletSecurityStatus | null,
	network?: string,
	settings?: Record<string, string>
): SecurityCheckItem[] {
	const items: SecurityCheckItem[] = [];

	items.push({
		id: 'passphrase',
		label: 'Wallet passphrase configured',
		passed: Boolean(security?.has_wallet_passphrase),
		severity: 'critical',
		detail: security?.has_wallet_passphrase
			? 'Mnemonics are encrypted with your passphrase.'
			: 'Create a wallet passphrase in Security before mainnet.'
	});

	items.push({
		id: 'unlocked',
		label: 'Wallet unlocked for this session',
		passed: Boolean(security?.unlocked),
		severity: 'warning',
		detail: security?.unlocked
			? 'Session auto-locks after idle timeout.'
			: 'Unlock when you need to send or sign.'
	});

	items.push({
		id: 'legacy',
		label: 'All wallets use v2 encryption',
		passed: (security?.legacy_wallet_count ?? 0) === 0,
		severity: 'warning',
		detail:
			(security?.legacy_wallet_count ?? 0) === 0
				? 'No legacy v1 wallets remain.'
				: `${security!.legacy_wallet_count} wallet(s) need migration in Security.`
	});

	const onMainnet = network === 'mainnet' || settings?.network === 'mainnet';
	if (onMainnet) {
		items.push({
			id: 'mainnet_ack',
			label: 'Mainnet risks acknowledged',
			passed: Boolean(security?.mainnet_acknowledged),
			severity: 'critical',
			detail: security?.mainnet_acknowledged
				? 'You accepted mainnet responsibility for this account.'
				: 'Acknowledge mainnet risks in Security while unlocked.'
		});
	}

	items.push({
		id: 'idle_ttl',
		label: 'Auto-lock idle timeout configured',
		passed: (security?.unlock_ttl_seconds ?? 900) >= 60,
		severity: 'info',
		detail: `Wallet locks after ${security?.unlock_ttl_seconds ?? 900}s without API activity.`
	});

	return items;
}

export function securityChecklist(
	security: WalletSecurityStatus | null,
	network?: string,
	settings?: Record<string, string>
): AdvisorTip[] {
	const tips: AdvisorTip[] = [];

	for (const item of securityCheckItems(security, network, settings)) {
		if (item.passed) continue;
		tips.push({
			id: item.id,
			severity: item.severity,
			title: item.label,
			detail: item.detail ?? ''
		});
	}

	if (tips.length === 0) {
		tips.push({
			id: 'security_posture_ok',
			severity: 'info',
			title: 'Security checklist complete',
			detail: 'Passphrase, encryption, and session posture look good for this wallet.'
		});
	}

	if (network === 'mainnet') {
		tips.push({
			id: 'mainnet_caution',
			severity: 'critical',
			title: 'Mainnet enabled',
			detail: 'Real funds at stake — verify every address and amount before sending.'
		});
	} else {
		tips.push({
			id: 'testnet_default',
			severity: 'info',
			title: 'Test/stagenet practice mode',
			detail: 'Practice sends and privacy workflows before enabling mainnet.'
		});
	}

	tips.push({
		id: 'backup_mnemonic',
		severity: 'info',
		title: 'Back up your seed phrase offline',
		detail: 'Recovery phrases are shown once at wallet creation — no cloud backup exists.'
	});

	tips.push({
		id: 'db_at_rest',
		severity: 'info',
		title: 'Database at-rest sealing',
		detail:
			'Set WALLET_DB_KEY in production to seal wallet.db as wallet.db.cwenc on API shutdown. User mnemonics are already encrypted per-wallet.'
	});

	return tips;
}

export function securityChecklistSummary(
	security: WalletSecurityStatus | null,
	network?: string,
	settings?: Record<string, string>
): string {
	const items = securityCheckItems(security, network, settings);
	const passed = items.filter((i) => i.passed).length;
	return `${passed}/${items.length} security checks passing`;
}
