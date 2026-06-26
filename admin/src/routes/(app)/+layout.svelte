<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { page } from '$app/stores';
	import { api, getToken, type User, type StatusResponse } from '$lib/api';
	import { appRefreshTick } from '$lib/stores/wallet';
	import { connectWalletEvents, disconnectWalletEvents } from '$lib/events';
	import { refreshWalletSecurity, walletSecurity } from '$lib/stores/security';
	import WalletUnlockBanner from '$lib/components/WalletUnlockBanner.svelte';
	import AppSidebar from '$lib/components/app-sidebar.svelte';
	import Header from '$lib/components/layout/Header.svelte';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';

	let { children } = $props();

	let user: User | null = $state(null);
	let status: StatusResponse | null = $state(null);
	let security = $state($walletSecurity);

	walletSecurity.subscribe((v) => (security = v));

	const titles: Record<string, string> = {
		'/': 'Dashboard',
		'/wallets': 'Wallets',
		'/receive': 'Receive',
		'/send': 'Send',
		'/utxos': 'Coin Control',
		'/transactions': 'Transactions',
		'/privacy': 'Privacy',
		'/stats': 'Stats',
		'/security': 'Security',
		'/logs': 'Logs',
		'/settings': 'Settings',
		'/admin': 'Admin'
	};

	async function load() {
		try {
			user = await api.me();
			if (user.role === 'pending') {
				goto('/pending');
				return;
			}
			[status] = await Promise.all([api.status(), refreshWalletSecurity()]);
		} catch {
			goto('/login');
		}
	}

	onMount(() => {
		if (!getToken()) {
			goto('/login');
			return;
		}
		load();
		connectWalletEvents();
		const id = setInterval(load, 10000);
		const unsub = appRefreshTick.subscribe(() => load());
		return () => {
			clearInterval(id);
			unsub();
			disconnectWalletEvents();
		};
	});

	let title = $derived(titles[$page.url.pathname] ?? 'Wallet Vault');
</script>

<Sidebar.Provider>
	<AppSidebar {status} />
	<Sidebar.Inset>
		<Header
			{title}
			username={user?.username}
			network={status?.network}
			synced={status?.synced}
			torEnabled={status?.tor_enabled}
			wallets={status?.wallets ?? []}
		/>
		<main class="flex-1 overflow-y-auto p-6">
			{#if security}
				<WalletUnlockBanner
					hasPassphrase={security.has_wallet_passphrase}
					unlocked={security.unlocked}
				/>
			{/if}
			{@render children()}
		</main>
	</Sidebar.Inset>
</Sidebar.Provider>
