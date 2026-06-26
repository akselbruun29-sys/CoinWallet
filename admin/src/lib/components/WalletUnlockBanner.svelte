<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { refreshWalletSecurity } from '$lib/stores/security';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import LockIcon from '@lucide/svelte/icons/lock';
	import ShieldIcon from '@lucide/svelte/icons/shield';

	interface Props {
		hasPassphrase: boolean;
		unlocked: boolean;
	}

	let { hasPassphrase, unlocked }: Props = $props();

	let passphrase = $state('');
	let loading = $state(false);
	let error = $state('');

	async function unlock(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			if (!hasPassphrase) {
				await api.setupWalletPassphrase(passphrase);
			} else {
				await api.unlockWallet(passphrase);
			}
			passphrase = '';
			await refreshWalletSecurity();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Unlock failed';
		} finally {
			loading = false;
		}
	}

	async function lock() {
		await api.lockWallet();
		await refreshWalletSecurity();
	}
</script>

{#if !unlocked}
	<Alert.Root class="mb-4 border-warning/40 bg-warning/5">
		<LockIcon class="size-4" />
		<Alert.Title>
			{hasPassphrase ? 'Wallet locked' : 'Set up wallet encryption'}
		</Alert.Title>
		<Alert.Description class="space-y-3">
			<p class="text-sm">
				{#if hasPassphrase}
					Unlock with your wallet passphrase to sync, receive, send, or create wallets. Admins
					cannot access your keys without this passphrase.
				{:else}
					Choose a wallet passphrase before creating or importing wallets. It encrypts your
					mnemonics so only you can spend — not even the server admin.
				{/if}
			</p>
			<form class="flex flex-col gap-2 sm:flex-row sm:flex-wrap sm:items-end" onsubmit={unlock}>
				<div class="min-w-0 flex-1 space-y-1 sm:min-w-[200px]">
					<Label for="unlock-pass" class="sr-only">Wallet passphrase</Label>
					<Input
						id="unlock-pass"
						type="password"
						bind:value={passphrase}
						placeholder="Wallet passphrase"
						minlength={8}
						required
					/>
				</div>
				<Button type="submit" class="w-full sm:w-auto" disabled={loading}>
					{loading ? 'Working...' : hasPassphrase ? 'Unlock' : 'Set passphrase'}
				</Button>
				<Button variant="outline" type="button" class="w-full sm:w-auto" onclick={() => goto('/security')}>Security</Button>
			</form>
			{#if error}
				<p class="text-sm text-destructive">{error}</p>
			{/if}
		</Alert.Description>
	</Alert.Root>
{:else}
	<Alert.Root class="mb-4 border-success/30 bg-success/5">
		<ShieldIcon class="size-4 text-success" />
		<Alert.Title>Wallet unlocked</Alert.Title>
		<Alert.Description class="flex flex-wrap items-center justify-between gap-2">
			<span class="text-sm">Your keys are available for signing in this session.</span>
			<Button variant="outline" size="sm" onclick={lock}>Lock wallet</Button>
		</Alert.Description>
	</Alert.Root>
{/if}
