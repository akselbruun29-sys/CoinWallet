<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type StatusResponse, type Wallet, type Balance } from '$lib/api';
	import { activeWalletId, setActiveWalletId, validateActiveWallet, isWalletSynced } from '$lib/stores/wallet';
	import { formatBtc, formatSats } from '$lib/utils';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import WalletIcon from '@lucide/svelte/icons/wallet';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import ArrowDownToLineIcon from '@lucide/svelte/icons/arrow-down-to-line';
	import ArrowUpFromLineIcon from '@lucide/svelte/icons/arrow-up-from-line';

	let status: StatusResponse | null = $state(null);
	let wallets: Wallet[] = $state([]);
	let balances: Record<number, Balance> = $state({});
	let totalSats = $state(0);

	async function load() {
		status = await api.status();
		wallets = status.wallets;
		let sum = 0;
		const entries = await Promise.all(
			wallets.map(async (w) => {
				try {
					const b = await api.walletBalance(w.id);
					sum += b.total_sats;
					return [w.id, b] as const;
				} catch {
					return [w.id, { confirmed_sats: 0, unconfirmed_sats: 0, total_sats: 0 }] as const;
				}
			})
		);
		balances = Object.fromEntries(entries);
		totalSats = sum;
		validateActiveWallet(wallets);
	}

	onMount(() => {
		load();
	});
</script>

<div class="mb-6 grid grid-cols-2 gap-3 sm:gap-4 lg:grid-cols-4">
	<Card.Root>
		<Card.Header class="pb-2">
			<Card.Title class="text-sm font-medium text-muted-foreground">Total Balance</Card.Title>
		</Card.Header>
		<Card.Content>
			<p class="text-xl font-bold text-primary sm:text-2xl">{formatBtc(totalSats)}</p>
			{#if totalSats > 0}
				<p class="text-sm text-muted-foreground">{formatSats(totalSats)} sats</p>
			{/if}
		</Card.Content>
	</Card.Root>
	<Card.Root>
		<Card.Header class="pb-2">
			<Card.Title class="text-sm font-medium text-muted-foreground">Wallets</Card.Title>
		</Card.Header>
		<Card.Content>
			<p class="text-2xl font-bold">{status?.wallet_count ?? 0}</p>
		</Card.Content>
	</Card.Root>
	<Card.Root>
		<Card.Header class="pb-2">
			<Card.Title class="text-sm font-medium text-muted-foreground">Sync</Card.Title>
		</Card.Header>
		<Card.Content>
			{#if status?.synced}
				<Badge variant="outline" class="border-success/40 bg-success/10 text-success">Synced</Badge>
			{:else}
				<Badge variant="outline" class="border-warning/40 bg-warning/10 text-warning">Not synced</Badge>
			{/if}
		</Card.Content>
	</Card.Root>
	<Card.Root>
		<Card.Header class="pb-2">
			<Card.Title class="text-sm font-medium text-muted-foreground">Network</Card.Title>
		</Card.Header>
		<Card.Content>
			<p class="text-2xl font-bold capitalize">{status?.network ?? 'testnet'}</p>
		</Card.Content>
	</Card.Root>
</div>

<div class="mb-6 grid gap-4 sm:grid-cols-3">
	<Button href="/receive" variant="outline" class="h-auto flex-col gap-2 py-4">
		<ArrowDownToLineIcon class="size-5 text-primary" />
		Receive
	</Button>
	<Button href="/send" variant="outline" class="h-auto flex-col gap-2 py-4">
		<ArrowUpFromLineIcon class="size-5 text-primary" />
		Send
	</Button>
	<Button href="/wallets" variant="outline" class="h-auto flex-col gap-2 py-4">
		<WalletIcon class="size-5 text-primary" />
		Manage Wallets
	</Button>
</div>

<Card.Root>
	<Card.Header>
		<Card.Title>Your Wallets</Card.Title>
		<Card.Description>Non-custodial wallets — keys encrypted at rest</Card.Description>
	</Card.Header>
	<Card.Content>
		{#if wallets.length === 0}
			<div class="flex flex-col items-center gap-3 py-8 text-center">
				<ShieldIcon class="size-10 text-muted-foreground" />
				<p class="text-sm text-muted-foreground">No wallets yet. Create one to get started.</p>
				<Button href="/wallets">Create Wallet</Button>
			</div>
		{:else}
			<ul class="space-y-2">
				{#each wallets as wallet (wallet.id)}
					<li>
						<button
							type="button"
							class="flex w-full items-center justify-between rounded-md border px-4 py-3 text-left transition-colors hover:bg-muted/50 {$activeWalletId === wallet.id ? 'border-primary bg-primary/5' : 'border-border'}"
							onclick={() => setActiveWalletId(wallet.id)}
						>
							<div>
								<p class="font-medium">{wallet.name}</p>
								<div class="mt-1 flex items-center gap-2">
									<p class="text-sm capitalize text-muted-foreground">{wallet.network}</p>
									{#if isWalletSynced(wallet)}
										<Badge variant="outline" class="border-success/40 text-success text-xs">Synced</Badge>
									{:else}
										<Badge variant="outline" class="border-warning/40 text-warning text-xs">Not synced</Badge>
									{/if}
								</div>
							</div>
							<p class="font-mono text-sm">{formatBtc(balances[wallet.id]?.total_sats ?? 0)}</p>
						</button>
					</li>
				{/each}
			</ul>
		{/if}
	</Card.Content>
</Card.Root>
