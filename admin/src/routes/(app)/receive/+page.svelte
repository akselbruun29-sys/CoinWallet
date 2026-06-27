<script lang="ts">
	import { onMount } from 'svelte';
	import QRCode from 'qrcode';
	import { api, type AssetType } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import WalletLockedGate from '$lib/components/WalletLockedGate.svelte';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import CopyIcon from '@lucide/svelte/icons/copy';
	import { assetLabel } from '$lib/utils';

	let address = $state('');
	let network = $state('testnet');
	let addressType = $state('');
	let assetType: AssetType = $state('btc');
	let useSubaddress = $state(true);
	let qrDataUrl = $state('');
	let error = $state('');
	let copied = $state(false);

	async function loadWalletMeta() {
		if ($activeWalletId == null) return;
		try {
			const wallets = await api.wallets();
			const w = wallets.find((x) => x.id === $activeWalletId);
			assetType = w?.asset_type ?? 'btc';
			network = w?.network ?? 'testnet';
		} catch {
			assetType = 'btc';
			network = 'testnet';
		}
	}

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		qrDataUrl = '';
		try {
			await loadWalletMeta();
			const res = await api.walletReceive($activeWalletId, {
				subaddress: assetType === 'xmr' ? useSubaddress : undefined
			});
			address = res.address;
			network = res.network;
			addressType = res.address_type ?? '';
			assetType = (res.asset_type as AssetType) ?? assetType;
			const qrPayload = assetType === 'btc' ? `bitcoin:${res.address}` : res.address;
			qrDataUrl = await QRCode.toDataURL(qrPayload, {
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
	<Card.Root class="w-full max-w-lg">
	<Card.Header>
		<Card.Title>Receive {assetLabel(assetType)}</Card.Title>
		<Card.Description>
			{#if assetType === 'xmr'}
				Generate a fresh subaddress for the active Monero wallet (requires wallet-rpc)
			{:else}
				Generate a fresh BIP84 receive address for the active wallet
			{/if}
		</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-4">
		{#if $activeWalletId == null}
			<p class="text-sm text-muted-foreground">Select or create a wallet first.</p>
		{:else if error}
			<p class="text-sm text-destructive">{error}</p>
		{:else if address && qrDataUrl}
			<div class="flex justify-center rounded-lg border border-border bg-white p-4">
				<img alt="QR code for {address}" class="size-full max-w-48 object-contain" src={qrDataUrl} />
			</div>
			<p class="break-all rounded-md border border-border bg-muted p-3 font-mono text-sm">{address}</p>
			<div class="flex flex-wrap items-center gap-2">
				<Badge variant="secondary" class="capitalize">{network}</Badge>
				<Badge variant="outline">{assetLabel(assetType)}</Badge>
				{#if addressType}
					<Badge variant="outline" class="capitalize">{addressType}</Badge>
				{/if}
				<Button variant="outline" size="sm" onclick={copy}>
					<CopyIcon class="size-4" />
					{copied ? 'Copied' : 'Copy address'}
				</Button>
				<Button variant="outline" size="sm" onclick={load}>
					{assetType === 'xmr' ? 'New subaddress' : 'New address'}
				</Button>
			</div>
			{#if assetType === 'xmr'}
				<div class="space-y-2 pt-2">
					<Label for="addr-mode">Address type for next refresh</Label>
					<Select.Root
						type="single"
						value={useSubaddress ? 'subaddress' : 'primary'}
						onValueChange={(v) => {
							useSubaddress = v !== 'primary';
						}}
					>
						<Select.Trigger id="addr-mode" class="w-full">
							{useSubaddress ? 'Subaddress (recommended)' : 'Primary address'}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="subaddress">Subaddress (recommended)</Select.Item>
							<Select.Item value="primary">Primary address</Select.Item>
						</Select.Content>
					</Select.Root>
					<p class="text-xs text-muted-foreground">
						Subaddresses improve privacy. Primary is reusable but linkable.
					</p>
				</div>
			{/if}
		{:else}
			<p class="text-sm text-muted-foreground">Loading...</p>
		{/if}
	</Card.Content>
</Card.Root>
</WalletLockedGate>
