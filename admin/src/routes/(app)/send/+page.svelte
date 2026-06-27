<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type SendPreview, type Utxo, type UtxoRef, type AssetType } from '$lib/api';
	import { activeWalletId, bumpAppRefresh } from '$lib/stores/wallet';
	import WalletLockedGate from '$lib/components/WalletLockedGate.svelte';
	import {
		formatBtc,
		formatSats,
		formatXmr,
		formatWalletBalance,
		assetLabel,
		explorerTxUrl,
		explorerXmrTxUrl
	} from '$lib/utils';
	import { feeTips } from '$lib/advisor';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';

	let address = $state('');
	let amountBtc = $state('');
	let amountXmr = $state('');
	let feeRate = $state('');
	let xmrPriority = $state('1');
	let assetType: AssetType = $state('btc');
	let spendableUtxos: Utxo[] = $state([]);
	let selectedKeys = $state<Set<string>>(new Set());
	let useCoinControl = $state(false);
	let preview: SendPreview | null = $state(null);
	let selectedForSend: UtxoRef[] | undefined = $state(undefined);
	let txid = $state('');
	let network = $state('testnet');
	let legacyWalletCount = $state(0);
	let error = $state('');
	let loading = $state(false);

	function utxoKey(u: Utxo) {
		return `${u.txid}:${u.vout}`;
	}

	function selectedUtxos(): UtxoRef[] | undefined {
		if (!useCoinControl || selectedKeys.size === 0) return undefined;
		return spendableUtxos
			.filter((u) => selectedKeys.has(utxoKey(u)))
			.map((u) => ({ txid: u.txid, vout: u.vout }));
	}

	function amountSats(): number {
		if (assetType === 'xmr') {
			const xmr = parseFloat(amountXmr);
			if (!Number.isFinite(xmr) || xmr <= 0) return 0;
			return Math.round(xmr * 1_000_000_000_000);
		}
		const btc = parseFloat(amountBtc);
		if (!Number.isFinite(btc) || btc <= 0) return 0;
		return Math.round(btc * 100_000_000);
	}

	function feeRateForPreview(): number | undefined {
		if (assetType === 'xmr') {
			return Number(xmrPriority) >= 2 ? 3 : 1;
		}
		return feeRate ? Number(feeRate) : undefined;
	}

	async function loadWalletMeta() {
		if ($activeWalletId == null) return;
		try {
			const [wallets, status] = await Promise.all([api.wallets(), api.status()]);
			const w = wallets.find((x) => x.id === $activeWalletId);
			network = w?.network ?? 'testnet';
			assetType = w?.asset_type ?? 'btc';
			legacyWalletCount = status.wallet_security?.legacy_wallet_count ?? 0;
		} catch {
			network = 'testnet';
			assetType = 'btc';
			legacyWalletCount = 0;
		}
	}

	async function loadUtxos() {
		if ($activeWalletId == null || assetType === 'xmr') {
			spendableUtxos = [];
			return;
		}
		try {
			const all = await api.walletUtxos($activeWalletId);
			spendableUtxos = all.filter((u) => !u.frozen);
		} catch {
			spendableUtxos = [];
		}
	}

	function toggleUtxo(key: string, checked: boolean) {
		const next = new Set(selectedKeys);
		if (checked) next.add(key);
		else next.delete(key);
		selectedKeys = next;
	}

	async function doPreview() {
		if ($activeWalletId == null) return;
		loading = true;
		error = '';
		preview = null;
		txid = '';
		try {
			const sats = amountSats();
			if (sats <= 0) throw new Error('Enter a valid amount');
			const utxos = selectedUtxos();
			if (useCoinControl && (!utxos || utxos.length === 0)) {
				throw new Error('Select at least one UTXO for coin control');
			}
			selectedForSend = utxos;
			preview = await api.sendPreview(
				$activeWalletId,
				address.trim(),
				sats,
				feeRateForPreview(),
				utxos
			);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Preview failed';
		} finally {
			loading = false;
		}
	}

	async function doSend() {
		if ($activeWalletId == null || !preview) return;
		loading = true;
		error = '';
		try {
			const res = await api.sendFunds(
				$activeWalletId,
				address.trim(),
				preview.amount_sats,
				preview.fee_rate_sat_vb,
				selectedForSend
			);
			txid = res.txid;
			preview = null;
			selectedKeys = new Set();
			await api.syncWallet($activeWalletId);
			bumpAppRefresh();
			await loadUtxos();
		} catch (e) {
			error = e instanceof Error ? e.message : 'Send failed';
		} finally {
			loading = false;
		}
	}

	onMount(async () => {
		await loadWalletMeta();
		await loadUtxos();
	});
	$effect(() => {
		if ($activeWalletId != null) {
			loadWalletMeta().then(loadUtxos);
		}
	});
</script>

<WalletLockedGate action="send {assetLabel(assetType)}">
<Card.Root class="w-full max-w-lg">
	<Card.Header>
		<Card.Title>Send {assetLabel(assetType)}</Card.Title>
		<Card.Description>
			{#if assetType === 'xmr'}
				Preview fee via wallet-rpc before broadcasting on {network}
			{:else}
				Preview fees before broadcasting on {network}
			{/if}
		</Card.Description>
	</Card.Header>
	<Card.Content class="space-y-4">
		{#if $activeWalletId == null}
			<p class="text-sm text-muted-foreground">Select a wallet first.</p>
		{:else if legacyWalletCount > 0}
			<Alert.Root variant="destructive">
				<Alert.Title>Legacy wallet encryption</Alert.Title>
				<Alert.Description>
					{legacyWalletCount} wallet(s) must be migrated to v2 encryption in
					<a href="/security" class="underline">Security</a> before you can send funds.
				</Alert.Description>
			</Alert.Root>
		{:else}
			<div class="space-y-2">
				<Label for="address">Recipient address</Label>
				<Input
					id="address"
					bind:value={address}
					placeholder={assetType === 'xmr' ? '4... or 8...' : 'tb1...'}
				/>
			</div>
			{#if assetType === 'xmr'}
				<div class="space-y-2">
					<Label for="amount-xmr">Amount (XMR)</Label>
					<Input id="amount-xmr" bind:value={amountXmr} type="number" step="0.000000000001" min="0" />
				</div>
				<div class="space-y-2">
					<Label for="priority">Transaction priority</Label>
					<Select.Root
						type="single"
						value={xmrPriority}
						onValueChange={(v) => (xmrPriority = v ?? '1')}
					>
						<Select.Trigger id="priority" class="w-full">
							{xmrPriority === '2' ? 'Elevated' : 'Normal'}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="1">Normal</Select.Item>
							<Select.Item value="2">Elevated</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
			{:else}
				<div class="space-y-2">
					<Label for="amount">Amount (BTC)</Label>
					<Input id="amount" bind:value={amountBtc} type="number" step="0.00000001" min="0" />
				</div>
				<div class="space-y-2">
					<Label for="fee">Fee rate (sat/vB, optional)</Label>
					<Input id="fee" bind:value={feeRate} type="number" min="1" placeholder="Auto" />
				</div>

				<div class="space-y-2 rounded-md border border-border p-3">
					<div class="flex items-center gap-2">
						<Checkbox id="coin-control" bind:checked={useCoinControl} />
						<Label for="coin-control" class="font-normal">Manual coin control</Label>
					</div>
					{#if useCoinControl}
						{#if spendableUtxos.length === 0}
							<p class="text-sm text-muted-foreground">No spendable UTXOs available.</p>
						{:else}
							<ul class="max-h-40 space-y-2 overflow-y-auto text-sm">
								{#each spendableUtxos as u (utxoKey(u))}
									<li class="flex items-center gap-2">
										<Checkbox
											checked={selectedKeys.has(utxoKey(u))}
											onCheckedChange={(v) => toggleUtxo(utxoKey(u), v === true)}
										/>
										<span>{formatBtc(u.amount_sats)} · {u.txid.slice(0, 8)}:{u.vout}</span>
									</li>
								{/each}
							</ul>
						{/if}
					{/if}
				</div>
			{/if}

			{#if error}
				<Alert.Root variant="destructive">
					<Alert.Title>Error</Alert.Title>
					<Alert.Description>{error}</Alert.Description>
				</Alert.Root>
			{/if}
			{#if txid}
				<Alert.Root>
					<Alert.Title>Transaction broadcast</Alert.Title>
					<Alert.Description class="space-y-2">
						<p class="break-all font-mono text-xs">{txid}</p>
						<a
							href={assetType === 'xmr' ? explorerXmrTxUrl(txid, network) : explorerTxUrl(txid, network)}
							target="_blank"
							rel="noopener noreferrer"
							class="text-sm text-primary underline"
						>
							{assetType === 'xmr' ? 'View on xmrchain' : 'View on Blockstream'}
						</a>
					</Alert.Description>
				</Alert.Root>
			{/if}
			{#if preview}
				<div class="rounded-md border border-border p-3 text-sm space-y-1">
					<p>
						Amount: {formatWalletBalance(assetType, preview.amount_sats)}
						{#if assetType === 'btc'}
							({formatSats(preview.amount_sats)} sats)
						{/if}
					</p>
					<p>
						Fee: {assetType === 'xmr' ? formatXmr(preview.fee_sats) : `${formatSats(preview.fee_sats)} sats`}
						{#if assetType === 'btc'}
							@ {preview.fee_rate_sat_vb} sat/vB
						{/if}
					</p>
					{#if assetType === 'btc'}
						<p>Change: {formatSats(preview.change_sats)} sats</p>
						<p>Inputs: {preview.input_count}</p>
					{/if}
				</div>
				{#if assetType === 'btc'}
					{#each feeTips(preview) as tip (tip.id)}
						<Alert.Root variant={tip.severity === 'critical' ? 'destructive' : 'default'}>
							<Alert.Title>{tip.title}</Alert.Title>
							<Alert.Description>{tip.detail}</Alert.Description>
						</Alert.Root>
					{/each}
				{/if}
				<div class="flex flex-col gap-2 sm:flex-row">
					<Button variant="outline" class="w-full sm:w-auto" onclick={() => (preview = null)}>Cancel</Button>
					<Button class="w-full sm:w-auto" disabled={loading} onclick={doSend}>Confirm send</Button>
				</div>
			{:else}
				<Button class="w-full" disabled={loading} onclick={doPreview}>
					{loading ? 'Loading...' : 'Preview transaction'}
				</Button>
			{/if}
		{/if}
	</Card.Content>
</Card.Root>
</WalletLockedGate>
