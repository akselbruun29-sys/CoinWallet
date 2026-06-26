<script lang="ts">
	import { api } from '$lib/api';
	import { goto } from '$app/navigation';
	import WalletSelector from '$lib/components/WalletSelector.svelte';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Separator } from '$lib/components/ui/separator/index.js';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import * as DropdownMenu from '$lib/components/ui/dropdown-menu/index.js';
	import LogOutIcon from '@lucide/svelte/icons/log-out';
	import UserIcon from '@lucide/svelte/icons/user';
	import WifiIcon from '@lucide/svelte/icons/wifi';
	import RefreshCwIcon from '@lucide/svelte/icons/refresh-cw';
	import WifiOffIcon from '@lucide/svelte/icons/wifi-off';
	import { activeWalletId, bumpAppRefresh } from '$lib/stores/wallet';

	interface Props {
		title: string;
		username?: string;
		network?: string;
		synced?: boolean;
		torEnabled?: boolean;
		wallets?: import('$lib/api').Wallet[];
	}

	let {
		title,
		username = '',
		network = 'testnet',
		synced = false,
		torEnabled = false,
		wallets = []
	}: Props = $props();

	let syncing = $state(false);
	let syncProgress = $state<number | null>(null);

	async function syncActive() {
		if ($activeWalletId == null) return;
		const walletId = $activeWalletId;
		syncing = true;
		syncProgress = 0;
		try {
			const result = await api.syncWallet(walletId);
			syncProgress = result.progress;
			if (!result.synced) {
				for (let i = 0; i < 30; i++) {
					await new Promise((r) => setTimeout(r, 500));
					const status = await api.walletSync(walletId);
					syncProgress = status.progress;
					if (status.synced) break;
				}
			}
			bumpAppRefresh();
		} finally {
			syncing = false;
			syncProgress = null;
		}
	}

	async function logout() {
		await api.logout();
		goto('/login');
	}
</script>

<header class="shrink-0 border-b border-border">
	<div class="flex min-h-14 items-center gap-2 px-3 py-2 sm:px-4">
		<Sidebar.Trigger class="-ms-1 size-9 shrink-0" />
		<Separator orientation="vertical" class="hidden h-4 sm:block" />
		<h1 class="min-w-0 flex-1 truncate text-base font-semibold sm:text-lg">{title}</h1>
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button variant="outline" size="icon" class="size-9 shrink-0 sm:hidden" {...props}>
						<UserIcon class="size-4" />
					</Button>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content align="end">
				<DropdownMenu.Label>{username}</DropdownMenu.Label>
				<DropdownMenu.Separator />
				<DropdownMenu.Item onclick={logout}>
					<LogOutIcon class="size-4" />
					Logout
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</div>
	<div
		class="flex flex-wrap items-center gap-2 border-t border-border/60 px-3 py-2 sm:border-t-0 sm:px-4"
	>
		<WalletSelector {wallets} class="min-w-0 flex-1 sm:flex-initial" />
		<Button
			variant="outline"
			size="sm"
			class="shrink-0"
			disabled={syncing || $activeWalletId == null}
			onclick={syncActive}
		>
			<RefreshCwIcon class="size-4 {syncing ? 'animate-spin' : ''}" />
			<span class="hidden sm:inline">
				{syncing && syncProgress != null ? `${syncProgress}%` : 'Sync'}
			</span>
		</Button>
		<Badge variant="secondary" class="hidden capitalize sm:inline-flex">{network}</Badge>
		{#if syncing}
			<Badge variant="outline" class="hidden border-warning/40 bg-warning/10 text-warning sm:inline-flex">
				<RefreshCwIcon class="size-3 animate-spin" />
				<span class="hidden md:inline">Syncing…</span>
			</Badge>
		{:else if synced}
			<Badge variant="outline" class="border-success/40 bg-success/10 text-success">
				<WifiIcon class="size-3" />
				<span class="sr-only sm:not-sr-only sm:ms-1">Synced</span>
			</Badge>
		{:else}
			<Badge variant="outline" class="border-warning/40 bg-warning/10 text-warning">
				<WifiOffIcon class="size-3" />
				<span class="sr-only sm:not-sr-only sm:ms-1">Not synced</span>
			</Badge>
		{/if}
		{#if torEnabled}
			<Badge variant="outline" class="hidden sm:inline-flex">Tor</Badge>
		{/if}
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button variant="outline" size="sm" class="hidden shrink-0 sm:inline-flex" {...props}>
						<UserIcon class="size-4" />
						<span class="max-w-[6rem] truncate">{username}</span>
					</Button>
				{/snippet}
			</DropdownMenu.Trigger>
			<DropdownMenu.Content align="end">
				<DropdownMenu.Label>{username}</DropdownMenu.Label>
				<DropdownMenu.Separator />
				<DropdownMenu.Item onclick={logout}>
					<LogOutIcon class="size-4" />
					Logout
				</DropdownMenu.Item>
			</DropdownMenu.Content>
		</DropdownMenu.Root>
	</div>
</header>
