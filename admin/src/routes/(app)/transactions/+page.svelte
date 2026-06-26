<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type WalletTransaction } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { formatBtc, formatSats, explorerTxUrl } from '$lib/utils';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import ScrollTable from '$lib/components/layout/ScrollTable.svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';

	let txs: WalletTransaction[] = $state([]);
	let network = $state('testnet');
	let error = $state('');

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		try {
			const wallets = await api.wallets();
			network = wallets.find((w) => w.id === $activeWalletId)?.network ?? 'testnet';
			txs = await api.walletTransactions($activeWalletId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		}
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>Transactions</Card.Title>
	</Card.Header>
	<Card.Content>
		{#if $activeWalletId == null}
			<p class="text-sm text-muted-foreground">Select a wallet first.</p>
		{:else if error}
			<p class="text-sm text-destructive">{error}</p>
		{:else if txs.length === 0}
			<p class="text-sm text-muted-foreground">No transactions yet. Sync after receiving funds.</p>
		{:else}
			<ScrollTable>
			<Table.Root class="min-w-[32rem]">
				<Table.Header>
					<Table.Row>
						<Table.Head>Time</Table.Head>
						<Table.Head>Direction</Table.Head>
						<Table.Head>Amount</Table.Head>
						<Table.Head>Fee</Table.Head>
						<Table.Head>TxID</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each txs as t}
						<Table.Row>
							<Table.Cell class="text-muted-foreground">{t.timestamp?.slice(0, 19) ?? '—'}</Table.Cell>
							<Table.Cell>
								<Badge variant="secondary" class="capitalize">{t.direction}</Badge>
							</Table.Cell>
							<Table.Cell>{formatBtc(t.amount_sats)}</Table.Cell>
							<Table.Cell>{t.fee_sats ? formatSats(t.fee_sats) : '—'}</Table.Cell>
							<Table.Cell class="max-w-[120px] truncate font-mono text-xs">
								<a
									href={explorerTxUrl(t.txid, network)}
									target="_blank"
									rel="noopener noreferrer"
									class="text-primary underline"
									title={t.txid}
								>
									{t.txid.slice(0, 12)}…
								</a>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
			</ScrollTable>
		{/if}
	</Card.Content>
</Card.Root>
