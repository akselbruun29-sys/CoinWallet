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

<header
	class="flex h-14 shrink-0 items-center gap-2 border-b border-border transition-[width,height] ease-linear group-has-data-[collapsible=icon]/sidebar-wrapper:h-12"
>
	<div class="flex flex-1 items-center gap-2 px-4">
		<Sidebar.Trigger class="-ms-1" />
		<Separator orientation="vertical" class="me-2 data-[orientation=vertical]:h-4" />
		<h1 class="text-lg font-semibold">{title}</h1>
	</div>
	<div class="flex items-center gap-2 px-4">
		<WalletSelector {wallets} />
		<Button variant="outline" size="sm" disabled={syncing || $activeWalletId == null} onclick={syncActive}>
			<RefreshCwIcon class="size-4 {syncing ? 'animate-spin' : ''}" />
			{syncing && syncProgress != null ? `${syncProgress}%` : 'Sync'}
		</Button>
		<Badge variant="secondary" class="capitalize">{network}</Badge>
		{#if syncing}
			<Badge variant="outline" class="border-warning/40 bg-warning/10 text-warning">
				<RefreshCwIcon class="size-3 animate-spin" />
				Syncing…
			</Badge>
		{:else if synced}
			<Badge variant="outline" class="border-success/40 bg-success/10 text-success">
				<WifiIcon class="size-3" />
				Synced
			</Badge>
		{:else}
			<Badge variant="outline" class="border-warning/40 bg-warning/10 text-warning">
				<WifiOffIcon class="size-3" />
				Syncing
			</Badge>
		{/if}
		{#if torEnabled}
			<Badge variant="outline">Tor</Badge>
		{/if}
		<DropdownMenu.Root>
			<DropdownMenu.Trigger>
				{#snippet child({ props })}
					<Button variant="outline" size="sm" {...props}>
						<UserIcon class="size-4" />
						{username}
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
