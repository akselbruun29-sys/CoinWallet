<script lang="ts">
	import { onMount } from 'svelte';
	import QRCode from 'qrcode';
	import { api } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import WalletLockedGate from '$lib/components/WalletLockedGate.svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import CopyIcon from '@lucide/svelte/icons/copy';

	let address = $state('');
	let network = $state('testnet');
	let qrDataUrl = $state('');
	let error = $state('');
	let copied = $state(false);

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		qrDataUrl = '';
		try {
			const res = await api.walletReceive($activeWalletId);
			address = res.address;
			network = res.network;
			qrDataUrl = await QRCode.toDataURL(`bitcoin:${res.address}`, {
				width: 200,
				margin: 1,
				color: { dark: '#000000', light: '#ffffff' }
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load address';
		}
	}
	async function copy() {
		await navigator.clipboard.writeText(address);
		copied = true;
		setTimeout(() => (copied = false), 2000);
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

<WalletLockedGate action="generate receive addresses">
	<Card.Root class="mx-auto max-w-lg">
	<Card.Header>
		<Card.Title>Receive Bitcoin</Card.Title>
		<Card.Description>Generate a fresh BIP84 receive address for the active wallet</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-4">
		{#if $activeWalletId == null}
			<p class="text-sm text-muted-foreground">Select or create a wallet first.</p>
		{:else if error}
			<p class="text-sm text-destructive">{error}</p>
		{:else if address && qrDataUrl}
			<div class="flex justify-center rounded-lg border border-border bg-white p-4">
				<img alt="QR code for {address}" class="size-48" src={qrDataUrl} />
			</div>			<p class="break-all rounded-md border border-border bg-muted p-3 font-mono text-sm">{address}</p>
			<div class="flex items-center gap-2">
				<Badge variant="secondary" class="capitalize">{network}</Badge>
				<Button variant="outline" size="sm" onclick={copy}>
					<CopyIcon class="size-4" />
					{copied ? 'Copied' : 'Copy address'}
				</Button>
				<Button variant="outline" size="sm" onclick={load}>New address</Button>
			</div>
		{:else}
			<p class="text-sm text-muted-foreground">Loading...</p>
		{/if}
	</Card.Content>
</Card.Root>
</WalletLockedGate>
