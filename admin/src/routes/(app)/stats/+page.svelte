<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type WalletStats } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { formatBtc, formatSats } from '$lib/utils';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	let stats: WalletStats | null = $state(null);
	let error = $state('');

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		try {
			stats = await api.walletStats($activeWalletId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		}
	}

	let maxHistorySats = $derived(
		stats?.balance_history.length
			? Math.max(...stats.balance_history.map((p) => p.sats), 1)
			: 1
	);

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

{#if $activeWalletId == null}
	<p class="text-sm text-muted-foreground">Select a wallet first.</p>
{:else if error}
	<p class="text-sm text-destructive">{error}</p>
{:else if stats}
	<div class="space-y-6">
		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3 xl:grid-cols-6">
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">Transactions</Card.Title></Card.Header>
				<Card.Content><p class="text-2xl font-bold">{stats.tx_count}</p></Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">Total Received</Card.Title></Card.Header>
				<Card.Content><p class="text-2xl font-bold">{formatBtc(stats.total_received_sats)}</p></Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">Total Sent</Card.Title></Card.Header>
				<Card.Content><p class="text-2xl font-bold">{formatBtc(stats.total_sent_sats)}</p></Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">Fees Paid</Card.Title></Card.Header>
				<Card.Content><p class="text-2xl font-bold">{formatSats(stats.fees_paid_sats)} sats</p></Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">UTXOs</Card.Title></Card.Header>
				<Card.Content><p class="text-2xl font-bold">{stats.utxo_count}</p></Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2"><Card.Title class="text-sm text-muted-foreground">Privacy score</Card.Title></Card.Header>
				<Card.Content>
					<p class="text-2xl font-bold">{stats.privacy_score}<span class="text-base font-normal text-muted-foreground">/100</span></p>
					<Button href="/privacy" variant="link" class="h-auto p-0 text-xs">View privacy →</Button>
				</Card.Content>
			</Card.Root>
		</div>

		<Card.Root>
			<Card.Header>
				<Card.Title>Balance history</Card.Title>
				<Card.Description>Balance after each synced transaction</Card.Description>
			</Card.Header>
			<Card.Content>
				{#if stats.balance_history.length === 0}
					<p class="text-sm text-muted-foreground">No history yet. Sync after receiving funds.</p>
				{:else}
					<div class="flex h-40 items-end gap-1">
						{#each stats.balance_history as point (point.date + point.sats)}
							<div class="flex min-w-0 flex-1 flex-col items-center gap-1">
								<div
									class="w-full rounded-t bg-primary/80"
									style="height: {Math.max(4, (point.sats / maxHistorySats) * 100)}%"
									title="{point.date}: {formatBtc(point.sats)}"
								></div>
								<span class="truncate text-[10px] text-muted-foreground">{point.date.slice(5)}</span>
							</div>
						{/each}
					</div>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
{:else}
	<p class="text-sm text-muted-foreground">Loading...</p>
{/if}
