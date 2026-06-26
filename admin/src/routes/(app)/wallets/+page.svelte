<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Wallet, type Balance } from '$lib/api';
	import { formatBtc } from '$lib/utils';
	import { setActiveWalletId, activeWalletId, validateActiveWallet, isWalletSynced } from '$lib/stores/wallet';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import DownloadIcon from '@lucide/svelte/icons/download';

	let wallets: Wallet[] = $state([]);
	let balances: Record<number, Balance> = $state({});
	let name = $state('');
	let importName = $state('');
	let importMnemonic = $state('');
	let creating = $state(false);
	let importing = $state(false);
	let error = $state('');
	let mnemonic = $state('');
	let showMnemonic = $state(false);

	async function load() {
		wallets = await api.wallets();
		const entries = await Promise.all(
			wallets.map(async (w) => {
				try {
					const b = await api.walletBalance(w.id);
					return [w.id, b] as const;
				} catch {
					return [w.id, { confirmed_sats: 0, unconfirmed_sats: 0, total_sats: 0 }] as const;
				}
			})
		);
		balances = Object.fromEntries(entries);
		validateActiveWallet(wallets);
	}

	async function createWallet(e: Event) {
		e.preventDefault();
		if (!name.trim()) return;
		creating = true;
		error = '';
		try {
			const created = await api.createWallet(name.trim());
			if (created.mnemonic) {
				mnemonic = created.mnemonic;
				showMnemonic = true;
			}
			setActiveWalletId(created.id);
			name = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create wallet';
		} finally {
			creating = false;
		}
	}

	async function importWallet(e: Event) {
		e.preventDefault();
		if (!importName.trim() || !importMnemonic.trim()) return;
		importing = true;
		error = '';
		try {
			const imported = await api.importWallet(importName.trim(), importMnemonic.trim());
			setActiveWalletId(imported.id);
			importName = '';
			importMnemonic = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to import wallet';
		} finally {
			importing = false;
		}
	}

	onMount(load);
</script>

<div class="grid gap-6 lg:grid-cols-3">
	<div class="space-y-6 lg:col-span-1">
	<Card.Root>
		<Card.Header>
			<Card.Title>Create Wallet</Card.Title>
			<Card.Description>Generates a BIP84 testnet wallet with encrypted seed storage</Card.Description>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={createWallet}>
				<div class="space-y-2">
					<Label for="name">Wallet name</Label>
					<Input id="name" bind:value={name} placeholder="My Wallet" required />
				</div>
				<Button type="submit" class="w-full" disabled={creating || importing}>
					<PlusIcon class="size-4" />
					{creating ? 'Creating...' : 'Create Wallet'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Import Wallet</Card.Title>
			<Card.Description>Restore from an existing 12-word recovery phrase</Card.Description>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={importWallet}>
				<div class="space-y-2">
					<Label for="import-name">Wallet name</Label>
					<Input id="import-name" bind:value={importName} placeholder="Imported Wallet" required />
				</div>
				<div class="space-y-2">
					<Label for="mnemonic">Recovery phrase</Label>
					<textarea
						id="mnemonic"
						bind:value={importMnemonic}
						placeholder="word1 word2 word3 ..."
						required
						rows="3"
						class="border-input bg-background ring-offset-background placeholder:text-muted-foreground focus-visible:ring-ring flex min-h-[80px] w-full rounded-md border px-3 py-2 text-sm focus-visible:ring-2 focus-visible:ring-offset-2 focus-visible:outline-none"
					></textarea>
				</div>
				<Button type="submit" variant="secondary" class="w-full" disabled={importing || creating}>
					<DownloadIcon class="size-4" />
					{importing ? 'Importing...' : 'Import Wallet'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
	</div>

	<Card.Root class="lg:col-span-2">
		<Card.Header>
			<Card.Title>All Wallets</Card.Title>
		</Card.Header>
		<Card.Content>
			{#if error}
				<p class="mb-4 text-sm text-destructive">{error}</p>
			{/if}
			{#if wallets.length === 0}
				<p class="text-sm text-muted-foreground">No wallets yet.</p>
			{:else}
				<Table.Root>
					<Table.Header>
						<Table.Row>
							<Table.Head>Name</Table.Head>
							<Table.Head>Balance</Table.Head>
							<Table.Head>Sync</Table.Head>
							<Table.Head>Network</Table.Head>
							<Table.Head>XPub</Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each wallets as w (w.id)}
							<Table.Row
								class="cursor-pointer {$activeWalletId === w.id ? 'bg-primary/5' : ''}"
								onclick={() => setActiveWalletId(w.id)}
							>
								<Table.Cell class="font-medium">{w.name}</Table.Cell>
								<Table.Cell>{formatBtc(balances[w.id]?.total_sats ?? 0)}</Table.Cell>
								<Table.Cell>
									{#if isWalletSynced(w)}
										<Badge variant="outline" class="border-success/40 text-success">Synced</Badge>
									{:else}
										<Badge variant="outline" class="border-warning/40 text-warning">Not synced</Badge>
									{/if}
								</Table.Cell>
								<Table.Cell>
									<Badge variant="secondary" class="capitalize">{w.network}</Badge>
								</Table.Cell>
								<Table.Cell class="max-w-[200px] truncate font-mono text-xs text-muted-foreground">
									{w.xpub ?? '—'}
								</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			{/if}
		</Card.Content>
	</Card.Root>
</div>

<Dialog.Root bind:open={showMnemonic}>
	<Dialog.Content class="sm:max-w-lg">
		<Dialog.Header>
			<Dialog.Title>Backup your recovery phrase</Dialog.Title>
			<Dialog.Description>
				Write these 12 words down and store them securely. This is shown only once.
			</Dialog.Description>
		</Dialog.Header>
		<p class="rounded-md border border-border bg-muted p-4 font-mono text-sm leading-relaxed">{mnemonic}</p>
		<Dialog.Footer>
			<Button onclick={() => (showMnemonic = false)}>I have saved my phrase</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
