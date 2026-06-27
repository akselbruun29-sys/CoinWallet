<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Wallet, type Balance, type AssetType } from '$lib/api';
	import { formatWalletBalance, assetLabel } from '$lib/utils';
	import { setActiveWalletId, activeWalletId, validateActiveWallet, isWalletSynced } from '$lib/stores/wallet';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import ScrollTable from '$lib/components/layout/ScrollTable.svelte';
	import * as Dialog from '$lib/components/ui/dialog/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import PlusIcon from '@lucide/svelte/icons/plus';
	import DownloadIcon from '@lucide/svelte/icons/download';

	type AssetFilter = 'all' | AssetType;

	let wallets: Wallet[] = $state([]);
	let balances: Record<number, Balance> = $state({});
	let assetFilter: AssetFilter = $state('all');
	let createAsset: AssetType = $state('btc');
	let createNetwork = $state('testnet');
	let importAsset: AssetType = $state('btc');
	let importNetwork = $state('testnet');
	let name = $state('');
	let importName = $state('');
	let importMnemonic = $state('');
	let creating = $state(false);
	let importing = $state(false);
	let error = $state('');
	let mnemonic = $state('');
	let createdAsset: AssetType = $state('btc');
	let showMnemonic = $state(false);
	let backupConfirmed = $state(false);

	const btcNetworks = [
		{ value: 'testnet', label: 'Testnet' },
		{ value: 'signet', label: 'Signet' },
		{ value: 'regtest', label: 'Regtest' },
		{ value: 'mainnet', label: 'Mainnet' }
	];
	const xmrNetworks = [
		{ value: 'stagenet', label: 'Stagenet' },
		{ value: 'testnet', label: 'Testnet' },
		{ value: 'mainnet', label: 'Mainnet' }
	];

	function networkOptions(asset: AssetType) {
		return asset === 'xmr' ? xmrNetworks : btcNetworks;
	}

	function onCreateAssetChange(value: string | undefined) {
		createAsset = (value as AssetType) ?? 'btc';
		createNetwork = createAsset === 'xmr' ? 'stagenet' : 'testnet';
	}

	function onImportAssetChange(value: string | undefined) {
		importAsset = (value as AssetType) ?? 'btc';
		importNetwork = importAsset === 'xmr' ? 'stagenet' : 'testnet';
	}

	function closeMnemonicDialog() {
		showMnemonic = false;
		mnemonic = '';
		backupConfirmed = false;
	}

	async function load() {
		const filter = assetFilter === 'all' ? undefined : assetFilter;
		wallets = await api.wallets(filter);
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
			const created = await api.createWallet(name.trim(), {
				asset_type: createAsset,
				network: createNetwork
			});
			if (created.mnemonic) {
				mnemonic = created.mnemonic;
				createdAsset = created.asset_type ?? createAsset;
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
			const imported = await api.importWallet(importName.trim(), importMnemonic.trim(), {
				asset_type: importAsset,
				network: importNetwork
			});
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

	async function exportWallet(w: Wallet, e: Event) {
		e.stopPropagation();
		try {
			const data = await api.exportWallet(w.id);
			const text =
				w.asset_type === 'xmr'
					? (data as { primary_address?: string }).primary_address ?? ''
					: data.xpub ?? '';
			await navigator.clipboard.writeText(text);
		} catch (err) {
			error = err instanceof Error ? err.message : 'Export failed';
		}
	}

	async function removeWallet(id: number, e: Event) {
		e.stopPropagation();
		if (!confirm('Delete this wallet from the server? This cannot be undone.')) return;
		try {
			await api.deleteWallet(id);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Delete failed';
		}
	}

	onMount(load);
</script>

<div class="grid gap-6 lg:grid-cols-3">
	<div class="space-y-6 lg:col-span-1">
	<Card.Root>
		<Card.Header>
			<Card.Title>Create Wallet</Card.Title>
			<Card.Description>Generate a new BTC or XMR wallet with encrypted seed storage</Card.Description>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={createWallet}>
				<div class="space-y-2">
					<Label for="create-asset">Asset</Label>
					<Select.Root type="single" value={createAsset} onValueChange={onCreateAssetChange}>
						<Select.Trigger id="create-asset" class="w-full">
							{assetLabel(createAsset)}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="btc">Bitcoin (BTC)</Select.Item>
							<Select.Item value="xmr">Monero (XMR)</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
				<div class="space-y-2">
					<Label for="create-network">Network</Label>
					<Select.Root
						type="single"
						value={createNetwork}
						onValueChange={(v) => (createNetwork = v ?? createNetwork)}
					>
						<Select.Trigger id="create-network" class="w-full">
							{networkOptions(createAsset).find((n) => n.value === createNetwork)?.label ?? createNetwork}
						</Select.Trigger>
						<Select.Content>
							{#each networkOptions(createAsset) as opt (opt.value)}
								<Select.Item value={opt.value}>{opt.label}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
				<div class="space-y-2">
					<Label for="name">Wallet name</Label>
					<Input id="name" bind:value={name} placeholder="My Wallet" required />
				</div>
				<Button type="submit" class="w-full" disabled={creating || importing}>
					<PlusIcon class="size-4" />
					{creating ? 'Creating...' : `Create ${assetLabel(createAsset)} Wallet`}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Import Wallet</Card.Title>
			<Card.Description>Restore from a BTC (12-word) or XMR (25-word) recovery phrase</Card.Description>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={importWallet}>
				<div class="space-y-2">
					<Label for="import-asset">Asset</Label>
					<Select.Root type="single" value={importAsset} onValueChange={onImportAssetChange}>
						<Select.Trigger id="import-asset" class="w-full">
							{assetLabel(importAsset)}
						</Select.Trigger>
						<Select.Content>
							<Select.Item value="btc">Bitcoin (BTC)</Select.Item>
							<Select.Item value="xmr">Monero (XMR)</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
				<div class="space-y-2">
					<Label for="import-network">Network</Label>
					<Select.Root
						type="single"
						value={importNetwork}
						onValueChange={(v) => (importNetwork = v ?? importNetwork)}
					>
						<Select.Trigger id="import-network" class="w-full">
							{networkOptions(importAsset).find((n) => n.value === importNetwork)?.label ?? importNetwork}
						</Select.Trigger>
						<Select.Content>
							{#each networkOptions(importAsset) as opt (opt.value)}
								<Select.Item value={opt.value}>{opt.label}</Select.Item>
							{/each}
						</Select.Content>
					</Select.Root>
				</div>
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
					{importing ? 'Importing...' : `Import ${assetLabel(importAsset)} Wallet`}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
	</div>

	<Card.Root class="lg:col-span-2">
		<Card.Header class="flex flex-row flex-wrap items-center justify-between gap-3">
			<Card.Title>All Wallets</Card.Title>
			<Select.Root
				type="single"
				value={assetFilter}
				onValueChange={(v) => {
					assetFilter = (v as AssetFilter) ?? 'all';
					load();
				}}
			>
				<Select.Trigger class="w-[140px]">
					{assetFilter === 'all' ? 'All assets' : assetLabel(assetFilter)}
				</Select.Trigger>
				<Select.Content>
					<Select.Item value="all">All assets</Select.Item>
					<Select.Item value="btc">BTC only</Select.Item>
					<Select.Item value="xmr">XMR only</Select.Item>
				</Select.Content>
			</Select.Root>
		</Card.Header>
		<Card.Content>
			{#if error}
				<p class="mb-4 text-sm text-destructive">{error}</p>
			{/if}
			{#if wallets.length === 0}
				<p class="text-sm text-muted-foreground">No wallets yet.</p>
			{:else}
			<ScrollTable>
				<Table.Root class="min-w-[40rem]">
					<Table.Header>
						<Table.Row>
							<Table.Head>Name</Table.Head>
							<Table.Head>Asset</Table.Head>
							<Table.Head>Balance</Table.Head>
							<Table.Head>Sync</Table.Head>
							<Table.Head>Network</Table.Head>
							<Table.Head>Identifier</Table.Head>
							<Table.Head></Table.Head>
						</Table.Row>
					</Table.Header>
					<Table.Body>
						{#each wallets as w (w.id)}
							<Table.Row
								class="cursor-pointer {$activeWalletId === w.id ? 'bg-primary/5' : ''}"
								onclick={() => setActiveWalletId(w.id)}
							>
								<Table.Cell class="font-medium">{w.name}</Table.Cell>
								<Table.Cell>
									<Badge variant={w.asset_type === 'xmr' ? 'default' : 'secondary'}>
										{assetLabel(w.asset_type)}
									</Badge>
								</Table.Cell>
								<Table.Cell>{formatWalletBalance(w.asset_type, balances[w.id]?.total_sats ?? 0)}</Table.Cell>
								<Table.Cell>
									{#if isWalletSynced(w)}
										<Badge variant="outline" class="border-success/40 text-success">Synced</Badge>
									{:else}
										<Badge variant="outline" class="border-warning/40 text-warning">Not synced</Badge>
									{/if}
								</Table.Cell>
								<Table.Cell>
									<Badge variant="outline" class="capitalize">{w.network}</Badge>
								</Table.Cell>
								<Table.Cell class="max-w-[200px] truncate font-mono text-xs text-muted-foreground">
									{w.asset_type === 'xmr' ? (w.xmr_primary_address ?? '—') : (w.xpub ?? '—')}
								</Table.Cell>
								<Table.Cell class="space-x-1">
									<Button variant="ghost" size="sm" onclick={(e) => exportWallet(w, e)}>
										{w.asset_type === 'xmr' ? 'Copy address' : 'Copy xpub'}
									</Button>
									<Button variant="ghost" size="sm" onclick={(e) => removeWallet(w.id, e)}>Delete</Button>
								</Table.Cell>
							</Table.Row>
						{/each}
					</Table.Body>
				</Table.Root>
			</ScrollTable>
			{/if}
		</Card.Content>
	</Card.Root>
</div>

<Dialog.Root bind:open={showMnemonic} onOpenChange={(open) => { if (!open && !backupConfirmed) showMnemonic = true; else if (!open) closeMnemonicDialog(); }}>
	<Dialog.Content class="sm:max-w-lg" showCloseButton={false}>
		<Dialog.Header>
			<Dialog.Title>Backup your recovery phrase</Dialog.Title>
			<Dialog.Description>
				Write these words down offline. This phrase is shown only once and cannot be retrieved later.
			</Dialog.Description>
		</Dialog.Header>
		<p class="rounded-md border border-border bg-muted p-4 font-mono text-sm leading-relaxed">{mnemonic}</p>
		<p class="text-xs text-muted-foreground">
			{createdAsset === 'xmr' ? '25-word Monero seed' : '12-word BIP39 seed'} — store securely offline.
		</p>
		<div class="flex items-start gap-2 pt-2">
			<Checkbox id="backup-confirm" bind:checked={backupConfirmed} />
			<Label for="backup-confirm" class="font-normal leading-snug">
				I have written down my recovery phrase and stored it securely offline.
			</Label>
		</div>
		<Dialog.Footer>
			<Button disabled={!backupConfirmed} onclick={closeMnemonicDialog}>I have saved my phrase</Button>
		</Dialog.Footer>
	</Dialog.Content>
</Dialog.Root>
