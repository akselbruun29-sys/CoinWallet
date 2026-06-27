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
	import MobileNav from '$lib/components/layout/MobileNav.svelte';
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
		'/swap': 'Swap',
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

		async function lockOnBackground() {
			if (document.visibilityState !== 'hidden') return;
			try {
				await api.lockWallet();
				await refreshWalletSecurity();
			} catch {
				// ignore — session may already be gone
			}
		}

		const onVisibility = () => {
			void lockOnBackground();
		};
		document.addEventListener('visibilitychange', onVisibility);

		const id = setInterval(load, 10000);
		const unsub = appRefreshTick.subscribe(() => load());
		return () => {
			document.removeEventListener('visibilitychange', onVisibility);
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
		<main class="flex-1 overflow-x-hidden overflow-y-auto p-3 pb-20 sm:p-4 sm:pb-4 md:p-6">
			{#if security}
				<WalletUnlockBanner
					hasPassphrase={security.has_wallet_passphrase}
					unlocked={security.unlocked}
				/>
			{/if}
			{@render children()}
		</main>
		<MobileNav />
	</Sidebar.Inset>
</Sidebar.Provider>
