<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Utxo } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { formatBtc, formatSats } from '$lib/utils';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import { Input } from '$lib/components/ui/input/index.js';

	let utxos: Utxo[] = $state([]);
	let error = $state('');
	let saving = $state<string | null>(null);

	function utxoKey(u: Utxo) {
		return `${u.txid}:${u.vout}`;
	}

	function isFrozen(u: Utxo) {
		return Boolean(u.frozen);
	}

	function replaceUtxo(updated: Utxo) {
		utxos = utxos.map((u) =>
			u.txid === updated.txid && u.vout === updated.vout ? updated : u
		);
	}

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		try {
			utxos = await api.walletUtxos($activeWalletId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		}
	}

	async function toggleFrozen(u: Utxo, frozen: boolean) {
		if ($activeWalletId == null) return;
		const key = utxoKey(u);
		saving = key;
		error = '';
		try {
			replaceUtxo(await api.updateUtxo($activeWalletId, u.txid, u.vout, { frozen }));
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to update UTXO';
		} finally {
			saving = null;
		}
	}

	async function saveLabel(u: Utxo, label: string) {
		if ($activeWalletId == null) return;
		const trimmed = label.trim();
		if ((u.label ?? '') === trimmed) return;
		const key = utxoKey(u);
		saving = key;
		error = '';
		try {
			replaceUtxo(await api.updateUtxo($activeWalletId, u.txid, u.vout, { label: trimmed }));
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to save label';
		} finally {
			saving = null;
		}
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

<Card.Root>
	<Card.Header>
		<Card.Title>Coin Control</Card.Title>
		<Card.Description>Freeze UTXOs to exclude them from sends; add labels for tracking</Card.Description>
	</Card.Header>
	<Card.Content>
		{#if $activeWalletId == null}
			<p class="text-sm text-muted-foreground">Select a wallet first.</p>
		{:else if error}
			<p class="text-sm text-destructive">{error}</p>
		{:else if utxos.length === 0}
			<p class="text-sm text-muted-foreground">No UTXOs. Sync after receiving funds.</p>
		{:else}
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head>Frozen</Table.Head>
						<Table.Head>Amount</Table.Head>
						<Table.Head>Status</Table.Head>
						<Table.Head>Label</Table.Head>
						<Table.Head>Address</Table.Head>
						<Table.Head>Outpoint</Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each utxos as u (utxoKey(u))}
						<Table.Row class={isFrozen(u) ? 'opacity-60' : ''}>
							<Table.Cell>
								<Checkbox
									checked={isFrozen(u)}
									disabled={saving === utxoKey(u)}
									onCheckedChange={(v) => toggleFrozen(u, v === true)}
								/>
							</Table.Cell>
							<Table.Cell>{formatBtc(u.amount_sats)} ({formatSats(u.amount_sats)})</Table.Cell>
							<Table.Cell>
								<div class="flex flex-wrap gap-1">
									{#if isFrozen(u)}
										<Badge variant="secondary">Frozen</Badge>
									{:else}
										<Badge variant="outline" class="border-success/40 text-success">Spendable</Badge>
									{/if}
									<Badge variant={u.confirmations >= 1 ? 'outline' : 'secondary'}>
										{u.confirmations} conf
									</Badge>
									{#if u.is_change}
										<Badge variant="secondary">Change</Badge>
									{/if}
								</div>
							</Table.Cell>
							<Table.Cell>
								<Input
									class="h-8 min-w-[120px]"
									value={u.label ?? ''}
									placeholder="Label"
									disabled={saving === utxoKey(u)}
									onchange={(e) => saveLabel(u, e.currentTarget.value)}
								/>
							</Table.Cell>
							<Table.Cell class="max-w-[140px] truncate font-mono text-xs">{u.address ?? '—'}</Table.Cell>
							<Table.Cell class="font-mono text-xs">{u.txid.slice(0, 8)}:{u.vout}</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
		{/if}
	</Card.Content>
</Card.Root>
