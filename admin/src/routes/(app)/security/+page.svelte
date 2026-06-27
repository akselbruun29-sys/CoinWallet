<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { refreshWalletSecurity, walletSecurity } from '$lib/stores/security';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import ShieldCheckIcon from '@lucide/svelte/icons/shield-check';
	import LockIcon from '@lucide/svelte/icons/lock';

	let security = $state($walletSecurity);
	let currentPass = $state('');
	let newPass = $state('');
	let confirmPass = $state('');
	let setupPass = $state('');
	let unlockPass = $state('');
	let migratePass = $state('');
	let mainnetAckSaving = $state(false);
	let mainnetAckError = $state('');
	let allowMainnet = $state(false);
	let error = $state('');
	let saved = $state(false);
	let loading = $state(false);

	walletSecurity.subscribe((v) => (security = v));

	async function load() {
		await refreshWalletSecurity();
		try {
			const s = await api.settings();
			allowMainnet = s.allow_mainnet === 'true';
		} catch {
			allowMainnet = false;
		}
	}

	async function acknowledgeMainnet() {
		mainnetAckSaving = true;
		mainnetAckError = '';
		try {
			await api.acknowledgeMainnetRisks();
			await load();
		} catch (err) {
			mainnetAckError = err instanceof Error ? err.message : 'Acknowledgment failed';
		} finally {
			mainnetAckSaving = false;
		}
	}

	async function setup(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		saved = false;
		try {
			await api.setupWalletPassphrase(setupPass);
			setupPass = '';
			saved = true;
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Setup failed';
		} finally {
			loading = false;
		}
	}

	async function unlock(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			await api.unlockWallet(unlockPass);
			unlockPass = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unlock failed';
		} finally {
			loading = false;
		}
	}

	async function lock() {
		await api.lockWallet();
		await load();
	}

	async function changePass(e: Event) {
		e.preventDefault();
		if (newPass !== confirmPass) {
			error = 'New passphrases do not match';
			return;
		}
		loading = true;
		error = '';
		saved = false;
		try {
			await api.changeWalletPassphrase(currentPass, newPass);
			currentPass = '';
			newPass = '';
			confirmPass = '';
			saved = true;
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Change failed';
		} finally {
			loading = false;
		}
	}

	onMount(load);
</script>

<div class="mx-auto max-w-lg space-y-6">
	<Card.Root>
		<Card.Header>
			<Card.Title class="flex items-center gap-2">
				<ShieldCheckIcon class="size-5" />
				Wallet encryption
			</Card.Title>
			<Card.Description>
				Your wallet passphrase encrypts mnemonics with a key only you know. The server admin
				cannot decrypt your wallets without it.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4 text-sm">
			{#if security}
				<p>
					<span class="text-muted-foreground">Status:</span>
					{#if !security.has_wallet_passphrase}
						Not configured
					{:else if security.unlocked}
						Unlocked for this session
					{:else}
						Locked
					{/if}
				</p>
				{#if security.unlocked && security.expires_at}
					<p class="text-muted-foreground">
						Session expires {new Date(security.expires_at * 1000).toLocaleTimeString()} (idle timeout
						{Math.round((security.unlock_ttl_seconds ?? 900) / 60)} min)
					</p>
				{/if}
				{#if security.legacy_wallet_count > 0}
					<Alert.Root>
						<Alert.Title>Legacy wallets detected</Alert.Title>
						<Alert.Description class="space-y-3">
							<p>
								{security.legacy_wallet_count} wallet(s) still use server-only encryption. Enter your
								passphrase to migrate them.
							</p>
							<form
								class="flex flex-wrap gap-2"
								onsubmit={async (e) => {
									e.preventDefault();
									loading = true;
									error = '';
									try {
										await api.migrateLegacyWallets(migratePass);
										migratePass = '';
										saved = true;
										await load();
									} catch (err) {
										error = err instanceof Error ? err.message : 'Migration failed';
									} finally {
										loading = false;
									}
								}}
							>
								<Input
									type="password"
									bind:value={migratePass}
									placeholder="Wallet passphrase"
									class="max-w-xs"
									minlength={8}
									required
								/>
								<Button type="submit" disabled={loading}>Migrate now</Button>
							</form>
						</Alert.Description>
					</Alert.Root>
				{/if}
			{/if}

			{#if security && !security.has_wallet_passphrase}
				<form class="space-y-4" onsubmit={setup}>
					<div class="space-y-2">
						<Label for="setup-pass">Create wallet passphrase</Label>
						<Input
							id="setup-pass"
							type="password"
							bind:value={setupPass}
							minlength={8}
							required
							placeholder="At least 8 characters"
						/>
					</div>
					<Button type="submit" disabled={loading}>
						{loading ? 'Saving...' : 'Set wallet passphrase'}
					</Button>
				</form>
			{:else if security && !security.unlocked}
				<form class="space-y-4" onsubmit={unlock}>
					<div class="space-y-2">
						<Label for="unlock-pass">Wallet passphrase</Label>
						<Input
							id="unlock-pass"
							type="password"
							bind:value={unlockPass}
							minlength={8}
							required
						/>
					</div>
					<Button type="submit" disabled={loading}>{loading ? 'Unlocking...' : 'Unlock'}</Button>
				</form>
			{:else if security}
				<Button variant="outline" onclick={lock}>
					<LockIcon class="mr-2 size-4" />
					Lock wallet now
				</Button>
			{/if}

			{#if error}
				<p class="text-destructive">{error}</p>
			{/if}
			{#if saved}
				<p class="text-success">Wallet security updated.</p>
			{/if}
		</Card.Content>
	</Card.Root>

	{#if allowMainnet}
		<Card.Root>
			<Card.Header>
				<Card.Title>Mainnet acknowledgment</Card.Title>
				<Card.Description>
					Required before creating or sending on mainnet. Wallet must be unlocked with v2 encryption.
				</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-3 text-sm">
				{#if security?.mainnet_acknowledged}
					<p class="text-success">
						Mainnet risks acknowledged
						{#if security.mainnet_ack_at}
							<span class="text-muted-foreground">({security.mainnet_ack_at.slice(0, 19)} UTC)</span>
						{/if}
					</p>
				{:else if security?.unlocked}
					<p class="text-muted-foreground">
						Mainnet is enabled on this instance. Acknowledge that real bitcoin is at risk and that
						you are responsible for backups and transaction verification.
					</p>
					{#if mainnetAckError}
						<p class="text-destructive">{mainnetAckError}</p>
					{/if}
					<Button disabled={mainnetAckSaving} onclick={acknowledgeMainnet}>
						{mainnetAckSaving ? 'Saving...' : 'I understand — enable mainnet for my account'}
					</Button>
				{:else}
					<p class="text-warning">Unlock your wallet to acknowledge mainnet risks.</p>
				{/if}
			</Card.Content>
		</Card.Root>
	{/if}

	{#if security?.has_wallet_passphrase}
		<Card.Root>
			<Card.Header>
				<Card.Title>Change wallet passphrase</Card.Title>
				<Card.Description>Re-encrypts all your wallets with the new passphrase.</Card.Description>
			</Card.Header>
			<Card.Content>
				<form class="space-y-4" onsubmit={changePass}>
					<div class="space-y-2">
						<Label for="current-pass">Current passphrase</Label>
						<Input id="current-pass" type="password" bind:value={currentPass} required />
					</div>
					<div class="space-y-2">
						<Label for="new-pass">New passphrase</Label>
						<Input id="new-pass" type="password" bind:value={newPass} minlength={8} required />
					</div>
					<div class="space-y-2">
						<Label for="confirm-pass">Confirm new passphrase</Label>
						<Input
							id="confirm-pass"
							type="password"
							bind:value={confirmPass}
							minlength={8}
							required
						/>
					</div>
					<Button type="submit" disabled={loading}>Update passphrase</Button>
				</form>
			</Card.Content>
		</Card.Root>
	{/if}

	<Card.Root>
		<Card.Header><Card.Title>What admins can and cannot do</Card.Title></Card.Header>
		<Card.Content class="space-y-2 text-sm text-muted-foreground">
			<p>Admins can manage users, approve registrations, and configure the instance.</p>
			<p>
				Admins cannot list other users' wallets, decrypt mnemonics, or sign transactions on their
				behalf.
			</p>
			<p>
				Your wallet passphrase is never stored on the server — only a verifier hash is kept.
			</p>
		</Card.Content>
	</Card.Root>
</div>
