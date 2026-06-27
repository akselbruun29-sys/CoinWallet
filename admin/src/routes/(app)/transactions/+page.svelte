<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type WalletTransaction } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { formatBtc, formatSats, explorerTxUrl } from '$lib/utils';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import ScrollTable from '$lib/components/layout/ScrollTable.svelte';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Button } from '$lib/components/ui/button/index.js';

	let txs: WalletTransaction[] = $state([]);
	let network = $state('testnet');
	let error = $state('');
	let editingTxid = $state('');
	let editLabel = $state('');
	let editEntity = $state('');

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

	function startEdit(t: WalletTransaction) {
		editingTxid = t.txid;
		editLabel = t.label ?? '';
		editEntity = '';
	}

	async function saveLabel(txid: string) {
		if ($activeWalletId == null || !editLabel.trim()) return;
		await api.setWalletLabel($activeWalletId, 'tx', txid, editLabel.trim(), editEntity || undefined);
		editingTxid = '';
		await load();
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>Transactions</Card.Title>
		<Card.Description>Click a row label cell to tag transactions (e.g. exchange deposits).</Card.Description>
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
						<Table.Head>Label</Table.Head>
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
							<Table.Cell>
								{#if editingTxid === t.txid}
									<div class="flex flex-col gap-1">
										<Input class="h-7" bind:value={editLabel} placeholder="Label" />
										<Input class="h-7" bind:value={editEntity} placeholder="Entity (e.g. exchange)" />
										<Button size="sm" variant="secondary" onclick={() => saveLabel(t.txid)}>Save</Button>
									</div>
								{:else}
									<button
										type="button"
										class="text-left text-sm underline-offset-2 hover:underline"
										onclick={() => startEdit(t)}
									>
										{t.label || 'Add label'}
									</button>
								{/if}
							</Table.Cell>
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
