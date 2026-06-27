import type { WalletSecurityStatus } from '$lib/api';
import type { AdvisorTip } from './types';

export function securityChecklist(
	security: WalletSecurityStatus | null,
	network?: string
): AdvisorTip[] {
	const tips: AdvisorTip[] = [];

	if (!security?.has_wallet_passphrase) {
		tips.push({
			id: 'passphrase_missing',
			severity: 'critical',
			title: 'Set a wallet passphrase',
			detail: 'Your mnemonic is not protected by a user passphrase yet. Open Security and create one before mainnet use.'
		});
	} else if (!security.unlocked) {
		tips.push({
			id: 'wallet_locked',
			severity: 'warning',
			title: 'Wallet is locked',
			detail: 'Unlock with your passphrase to send, sync sensitive operations, or view encrypted data.'
		});
	} else {
		tips.push({
			id: 'wallet_unlocked',
			severity: 'info',
			title: 'Wallet unlocked',
			detail: 'Lock the wallet when you step away. The passphrase is never stored on the server.'
		});
	}

	if ((security?.legacy_wallet_count ?? 0) > 0) {
		tips.push({
			id: 'legacy_migration',
			severity: 'warning',
			title: 'Migrate legacy wallets',
			detail: `${security!.legacy_wallet_count} wallet(s) use older encryption. Migrate them in Security with your passphrase.`
		});
	}

	tips.push({
		id: 'backup_mnemonic',
		severity: 'info',
		title: 'Back up your seed phrase',
		detail: 'Write your recovery phrase offline when you create a wallet. CoinWallet shows it once — there is no cloud backup.'
	});

	if (network === 'mainnet') {
		tips.push({
			id: 'mainnet_caution',
			severity: 'critical',
			title: 'Mainnet enabled',
			detail: 'Real bitcoin is at stake. Double-check addresses, amounts, and fees before confirming any send.'
		});
	} else {
		tips.push({
			id: 'testnet_default',
			severity: 'info',
			title: 'Testnet practice mode',
			detail: 'You are on testnet — coins have no value. Practice sends and privacy workflows before enabling mainnet.'
		});
	}

	return tips;
}
