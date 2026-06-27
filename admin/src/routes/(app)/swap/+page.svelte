<script lang="ts">
	import { onMount } from 'svelte';
	import {
		api,
		type AssetType,
		type SwapProviderInfo,
		type SwapQuote,
		type SwapExecuteResult,
		type SwapRecord,
		type Wallet
	} from '$lib/api';
	import WalletLockedGate from '$lib/components/WalletLockedGate.svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { formatWalletBalance, assetLabel, validateDepositAddress } from '$lib/utils';
	import { swapTips, swapHistoryTips } from '$lib/advisor/swap';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import ScrollTable from '$lib/components/layout/ScrollTable.svelte';
	import ArrowLeftRightIcon from '@lucide/svelte/icons/arrow-left-right';

	let providers: SwapProviderInfo[] = $state([]);
	let wallets: Wallet[] = $state([]);
	let history: SwapRecord[] = $state([]);
	let direction = $state('btc-xmr');
	let amount = $state('');
	let providerId = $state('');
	let destinationWalletId = $state('');
	let quote: SwapQuote | null = $state(null);
	let result: SwapExecuteResult | null = $state(null);
	let error = $state('');
	let loading = $state(false);
	let attachSwapId = $state<number | null>(null);
	let attachFromTxid = $state('');
	let attachToTxid = $state('');
	let showDepositDialog = $state(false);
	let depositAddress = $state('');
	let depositAsset: AssetType = $state('btc');
	let depositChecksumValid = $state<boolean | null>(null);
	let depositAck = $state(false);

	const historyTips = $derived(swapHistoryTips(history));

	const fromAsset = $derived((direction.split('-')[0] as AssetType) ?? 'btc');
	const toAsset = $derived((direction.split('-')[1] as AssetType) ?? 'xmr');

	const destinationWallets = $derived(wallets.filter((w) => w.asset_type === toAsset));

	const enabledProviders = $derived(providers.filter((p) => p.enabled));

	function amountAtomic(): number {
		const value = parseFloat(amount);
		if (!Number.isFinite(value) || value <= 0) return 0;
		if (fromAsset === 'xmr') return Math.round(value * 1_000_000_000_000);
		return Math.round(value * 100_000_000);
	}

	async function loadMeta() {
		const [prov, wlist, hist] = await Promise.all([
			api.swapProviders(),
			api.wallets(),
			api.swapHistory()
		]);
		providers = prov.providers;
		wallets = wlist;
		history = hist.swaps;
		if (!providerId && enabledProviders.length > 0) {
			providerId = enabledProviders[0].id;
		}
		if (!destinationWalletId && destinationWallets.length > 0) {
			destinationWalletId = String(destinationWallets[0].id);
		}
	}

	async function fetchQuote() {
		loading = true;
		error = '';
		quote = null;
		result = null;
		try {
			const atomic = amountAtomic();
			if (atomic <= 0) throw new Error('Enter a valid amount');
			quote = await api.swapQuote(fromAsset, toAsset, atomic, providerId || undefined);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Quote failed';
		} finally {
			loading = false;
		}
	}

	async function confirmSwap() {
		if (!quote) return;
		loading = true;
		error = '';
		try {
			const destId = Number(destinationWalletId);
			if (!Number.isFinite(destId) || destId <= 0) {
				throw new Error('Select a destination wallet');
			}
			result = await api.swapExecute(quote.quote_id, destId);
			quote = null;
			history = (await api.swapHistory()).swaps;
			if (result.deposit_address) {
				depositAddress = result.deposit_address;
				depositAsset = result.from_asset;
				depositChecksumValid =
					result.deposit_address_checksum_valid ??
					validateDepositAddress(result.from_asset, result.deposit_address);
				depositAck = false;
				showDepositDialog = true;
				result = { ...result, deposit_address: undefined };
			}
		} catch (e) {
			error = e instanceof Error ? e.message : 'Execute failed';
		} finally {
			loading = false;
		}
	}

	function closeDepositDialog() {
		showDepositDialog = false;
		depositAddress = '';
		depositAck = false;
		depositChecksumValid = null;
	}

	function flipDirection() {
		direction = direction === 'btc-xmr' ? 'xmr-btc' : 'btc-xmr';
		quote = null;
		result = null;
	}

	function startAttach(s: SwapRecord) {
		attachSwapId = s.id;
		attachFromTxid = s.from_txid ?? '';
		attachToTxid = s.to_txid ?? '';
	}

	async function saveAttachTxids() {
		if (attachSwapId == null) return;
		loading = true;
		error = '';
		try {
			await api.swapAttachTxids(attachSwapId, {
				from_txid: attachFromTxid.trim() || undefined,
				to_txid: attachToTxid.trim() || undefined
			});
			history = (await api.swapHistory()).swaps;
			attachSwapId = null;
			attachFromTxid = '';
			attachToTxid = '';
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to attach transaction IDs';
		} finally {
			loading = false;
		}
	}

	onMount(loadMeta);
	$effect(() => {
		if (destinationWallets.length > 0) {
			const current = Number(destinationWalletId);
			if (!destinationWallets.some((w) => w.id === current)) {
				destinationWalletId = String(destinationWallets[0].id);
			}
		} else {
			destinationWalletId = '';
		}
	});
</script>

<div class="grid gap-6 lg:grid-cols-2">
	<Card.Root class="lg:col-span-1">
		<Card.Header>
			<Card.Title class="flex items-center gap-2">
				<ArrowLeftRightIcon class="size-5" />
				BTC ↔ XMR Swap
			</Card.Title>
			<Card.Description>
				User-initiated only — review the full quote and provider disclosure before confirming.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4">
			<div class="flex items-end gap-2">
				<div class="flex-1 space-y-2">
					<Label>Direction</Label>
					<p class="text-sm font-medium">
						{assetLabel(fromAsset)} → {assetLabel(toAsset)}
					</p>
				</div>
				<Button variant="outline" size="sm" onclick={flipDirection}>Flip</Button>
			</div>

			<div class="space-y-2">
				<Label for="amount">Amount ({assetLabel(fromAsset)})</Label>
				<Input
					id="amount"
					bind:value={amount}
					type="number"
					min="0"
					step={fromAsset === 'xmr' ? '0.000000000001' : '0.00000001'}
					placeholder={fromAsset === 'xmr' ? '0.01' : '0.001'}
				/>
			</div>

			<div class="space-y-2">
				<Label for="provider">Provider</Label>
				<Select.Root
					type="single"
					value={providerId}
					onValueChange={(v) => (providerId = v ?? providerId)}
				>
					<Select.Trigger id="provider" class="w-full">
						{enabledProviders.find((p) => p.id === providerId)?.name ?? 'Select provider'}
					</Select.Trigger>
					<Select.Content>
						{#each enabledProviders as p (p.id)}
							<Select.Item value={p.id}>{p.name}</Select.Item>
						{/each}
					</Select.Content>
				</Select.Root>
				{#if providerId}
					<p class="text-xs text-muted-foreground">
						{providers.find((p) => p.id === providerId)?.disclosure}
					</p>
				{/if}
			</div>

			{#if error}
				<Alert.Root variant="destructive">
					<Alert.Title>Error</Alert.Title>
					<Alert.Description>{error}</Alert.Description>
				</Alert.Root>
			{/if}

			{#if !quote && !result}
				<Button class="w-full" disabled={loading || enabledProviders.length === 0} onclick={fetchQuote}>
					{loading ? 'Loading...' : 'Get quote'}
				</Button>
			{/if}

			{#if quote}
				<div class="space-y-2 rounded-md border border-border p-3 text-sm">
					<p>
						You send: {formatWalletBalance(quote.from_asset, quote.send_amount_atomic)}
					</p>
					<p>
						You receive: {formatWalletBalance(quote.to_asset, quote.receive_amount_atomic)}
					</p>
					<p>Rate: {quote.rate} {assetLabel(quote.to_asset)} per {assetLabel(quote.from_asset)}</p>
					<p>Network fee estimate: {formatWalletBalance(quote.from_asset, quote.fees.network)}</p>
					<p>Provider fee: {formatWalletBalance(quote.to_asset, quote.fees.provider)}</p>
					<p class="text-xs text-muted-foreground">Expires: {quote.expires_at}</p>
					<p class="text-xs text-muted-foreground">{quote.disclosure}</p>
				</div>

				{#each swapTips(quote) as tip (tip.id)}
					<Alert.Root variant={tip.severity === 'critical' ? 'destructive' : 'default'}>
						<Alert.Title>{tip.title}</Alert.Title>
						<Alert.Description>{tip.detail}</Alert.Description>
					</Alert.Root>
				{/each}

				<div class="space-y-2">
					<Label for="dest">Receive into wallet ({assetLabel(toAsset)})</Label>
					<Select.Root
						type="single"
						value={destinationWalletId}
						onValueChange={(v) => (destinationWalletId = v ?? destinationWalletId)}
					>
						<Select.Trigger id="dest" class="w-full">
							{destinationWallets.find((w) => String(w.id) === destinationWalletId)?.name ??
								'Select wallet'}
						</Select.Trigger>
						<Select.Content>
							{#each destinationWallets as w (w.id)}
								<Select.Item value={String(w.id)}>{w.name}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>

				<WalletLockedGate action="confirm swaps">
					<div class="flex flex-col gap-2 sm:flex-row">
						<Button variant="outline" class="w-full sm:w-auto" onclick={() => (quote = null)}>
							Cancel
						</Button>
						<Button
							class="w-full sm:w-auto"
							disabled={loading || !destinationWalletId}
							onclick={confirmSwap}
						>
							{loading ? 'Confirming...' : 'Confirm swap'}
						</Button>
					</div>
				</WalletLockedGate>
			{/if}

			{#if result}
				<Alert.Root>
					<Alert.Title>Swap initiated</Alert.Title>
					<Alert.Description class="space-y-2">
						<p>Swap #{result.swap_id} — status: <Badge variant="secondary">{result.status}</Badge></p>
						{#if result.instructions}
							<p class="text-sm">{result.instructions}</p>
						{/if}
					</Alert.Description>
				</Alert.Root>
				<Button variant="outline" onclick={() => { result = null; amount = ''; }}>New swap</Button>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root class="lg:col-span-1">
		<Card.Header>
			<Card.Title>Swap history</Card.Title>
			<Card.Description>Attach transaction IDs after sending to enable block explorer links.</Card.Description>
		</Card.Header>
		<Card.Content>
			{#each historyTips as tip (tip.id)}
				<Alert.Root class="mb-4" variant="default">
					<Alert.Title>{tip.title}</Alert.Title>
					<Alert.Description>{tip.detail}</Alert.Description>
				</Alert.Root>
			{/each}
			{#if history.length === 0}
				<p class="text-sm text-muted-foreground">No swaps yet.</p>
			{:else}
				<ScrollTable>
					<Table.Root class="min-w-[40rem]">
						<Table.Header>
							<Table.Row>
								<Table.Head>Date</Table.Head>
								<Table.Head>Pair</Table.Head>
								<Table.Head>Send</Table.Head>
								<Table.Head>Receive</Table.Head>
								<Table.Head>Status</Table.Head>
								<Table.Head>Explorer</Table.Head>
								<Table.Head></Table.Head>
							</Table.Row>
						</Table.Header>
						<Table.Body>
							{#each history as s (s.id)}
								<Table.Row>
									<Table.Cell class="text-xs text-muted-foreground whitespace-nowrap">
										{s.created_at?.slice(0, 10) ?? '—'}
									</Table.Cell>
									<Table.Cell>
										{assetLabel(s.from_asset)}→{assetLabel(s.to_asset)}
									</Table.Cell>
									<Table.Cell>{formatWalletBalance(s.from_asset, s.send_amount_atomic)}</Table.Cell>
									<Table.Cell>{formatWalletBalance(s.to_asset, s.receive_amount_atomic)}</Table.Cell>
									<Table.Cell>
										<Badge variant="outline" class="capitalize">{s.status.replace(/_/g, ' ')}</Badge>
									</Table.Cell>
									<Table.Cell class="space-x-2 text-xs">
										{#if s.explorer_links?.from}
											<a
												href={s.explorer_links.from}
												target="_blank"
												rel="noopener noreferrer"
												class="text-primary underline"
											>
												{assetLabel(s.from_asset)} tx
											</a>
										{/if}
										{#if s.explorer_links?.to}
											<a
												href={s.explorer_links.to}
												target="_blank"
												rel="noopener noreferrer"
												class="text-primary underline"
											>
												{assetLabel(s.to_asset)} tx
											</a>
										{/if}
										{#if !s.explorer_links?.from && !s.explorer_links?.to}
											<span class="text-muted-foreground">—</span>
										{/if}
									</Table.Cell>
									<Table.Cell>
										<Button variant="ghost" size="sm" onclick={() => startAttach(s)}>
											{s.from_txid || s.to_txid ? 'Edit txids' : 'Link tx'}
										</Button>
									</Table.Cell>
								</Table.Row>
								{#if attachSwapId === s.id}
									<Table.Row>
										<Table.Cell colspan={7}>
											<div class="grid gap-2 rounded-md border border-border p-3 sm:grid-cols-2">
												<div class="space-y-1">
													<Label for="from-txid-{s.id}">{assetLabel(s.from_asset)} send txid</Label>
													<Input
														id="from-txid-{s.id}"
														bind:value={attachFromTxid}
														placeholder="64-char hex"
														class="font-mono text-xs"
													/>
												</div>
												<div class="space-y-1">
													<Label for="to-txid-{s.id}">{assetLabel(s.to_asset)} receive txid</Label>
													<Input
														id="to-txid-{s.id}"
														bind:value={attachToTxid}
														placeholder="64-char hex"
														class="font-mono text-xs"
													/>
												</div>
												<div class="flex gap-2 sm:col-span-2">
													<Button size="sm" disabled={loading} onclick={saveAttachTxids}>Save</Button>
													<Button
														size="sm"
														variant="outline"
														onclick={() => (attachSwapId = null)}
													>
														Cancel
													</Button>
												</div>
											</div>
										</Table.Cell>
									</Table.Row>
								{/if}
							{/each}
						</Table.Body>
					</Table.Root>
				</ScrollTable>
			{/if}
		</Card.Content>
	</Card.Root>
</div>

<Dialog.Root
	bind:open={showDepositDialog}
	onOpenChange={(open) => {
		if (!open && !depositAck) showDepositDialog = true;
		else if (!open) closeDepositDialog();
	}}
>
	<Dialog.Content class="sm:max-w-lg" showCloseButton={false}>
		<Dialog.Header>
			<Dialog.Title>Swap deposit address</Dialog.Title>
			<Dialog.Description>
				This address is shown once. Verify the checksum before sending funds.
			</Dialog.Description>
		</Dialog.Header>
		<p class="break-all rounded-md border border-border bg-muted p-4 font-mono text-sm">
			{depositAddress}
		</p>
		<p class="text-sm">
			Checksum:
			{#if depositChecksumValid}
				<Badge variant="outline" class="border-success/40 text-success">Valid</Badge>
			{:else}
				<Badge variant="destructive">Invalid — do not send</Badge>
			{/if}
		</p>
		<p class="text-xs text-muted-foreground">
			Send {assetLabel(depositAsset)} only to this address. CoinWallet will not show it again in
			swap history.
		</p>
		<div class="flex items-start gap-2 pt-2">
			<Checkbox id="deposit-ack" bind:checked={depositAck} disabled={!depositChecksumValid} />
			<Label for="deposit-ack" class="font-normal leading-snug">
				I verified the address checksum and copied it securely.
			</Label>
		</div>
		<Dialog.Footer>
			<Button disabled={!depositAck || !depositChecksumValid} onclick={closeDepositDialog}>
				I have saved the address
			</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
