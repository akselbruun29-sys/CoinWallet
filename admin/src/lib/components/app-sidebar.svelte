<script lang="ts">
	import { page } from '$app/stores';
	import LayoutDashboardIcon from '@lucide/svelte/icons/layout-dashboard';
	import WalletIcon from '@lucide/svelte/icons/wallet';
	import ArrowDownToLineIcon from '@lucide/svelte/icons/arrow-down-to-line';
	import ArrowUpFromLineIcon from '@lucide/svelte/icons/arrow-up-from-line';
	import CoinsIcon from '@lucide/svelte/icons/coins';
	import ArrowLeftRightIcon from '@lucide/svelte/icons/arrow-left-right';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import BarChart3Icon from '@lucide/svelte/icons/bar-chart-3';
	import ScrollTextIcon from '@lucide/svelte/icons/scroll-text';
	import Settings2Icon from '@lucide/svelte/icons/settings-2';
	import UsersIcon from '@lucide/svelte/icons/users';
	import * as Sidebar from '$lib/components/ui/sidebar/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import type { StatusResponse } from '$lib/api';
	import type { ComponentProps } from 'svelte';

	interface Props extends ComponentProps<typeof Sidebar.Root> {
		status?: StatusResponse;
	}

	let {
		status,
		ref = $bindable(null),
		collapsible = 'icon',
		...restProps
	}: Props = $props();

	const nav = [
		{ href: '/', label: 'Dashboard', icon: LayoutDashboardIcon },
		{ href: '/wallets', label: 'Wallets', icon: WalletIcon },
		{ href: '/receive', label: 'Receive', icon: ArrowDownToLineIcon },
		{ href: '/send', label: 'Send', icon: ArrowUpFromLineIcon },
		{ href: '/utxos', label: 'Coin Control', icon: CoinsIcon },
		{ href: '/transactions', label: 'Transactions', icon: ArrowLeftRightIcon },
		{ href: '/privacy', label: 'Privacy', icon: ShieldIcon },
		{ href: '/stats', label: 'Stats', icon: BarChart3Icon },
		{ href: '/logs', label: 'Logs', icon: ScrollTextIcon },
		{ href: '/settings', label: 'Settings', icon: Settings2Icon }
	];

	const adminNav = { href: '/admin', label: 'Admin', icon: UsersIcon };
</script>

<Sidebar.Root bind:ref {collapsible} {...restProps}>
	<Sidebar.Header>
		<div class="flex h-12 items-center gap-2 px-2">
			<div
				class="flex size-8 shrink-0 items-center justify-center rounded-md bg-primary text-primary-foreground"
			>
				<ShieldIcon class="size-4" />
			</div>
			<span class="truncate text-base font-bold tracking-tight group-data-[collapsible=icon]:hidden">
				Wallet Vault
			</span>
		</div>
	</Sidebar.Header>
	<Sidebar.Content>
		<Sidebar.Group>
			<Sidebar.GroupLabel>Wallet</Sidebar.GroupLabel>
			<Sidebar.Menu>
				{#each nav as item (item.href)}
					<Sidebar.MenuItem>
						<Sidebar.MenuButton
							isActive={$page.url.pathname === item.href}
							tooltipContent={item.label}
						>
							{#snippet child({ props })}
								<a href={item.href} {...props}>
									<item.icon />
									<span>{item.label}</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
					</Sidebar.MenuItem>
				{/each}
			</Sidebar.Menu>
		</Sidebar.Group>
		{#if status?.user.role === 'admin'}
			<Sidebar.Group>
				<Sidebar.GroupLabel>System</Sidebar.GroupLabel>
				<Sidebar.Menu>
					<Sidebar.MenuItem>
						<Sidebar.MenuButton
							isActive={$page.url.pathname === adminNav.href}
							tooltipContent={adminNav.label}
						>
							{#snippet child({ props })}
								<a href={adminNav.href} {...props}>
									<adminNav.icon />
									<span>{adminNav.label}</span>
								</a>
							{/snippet}
						</Sidebar.MenuButton>
					</Sidebar.MenuItem>
				</Sidebar.Menu>
			</Sidebar.Group>
		{/if}
	</Sidebar.Content>
	<Sidebar.Footer>
		<div class="flex flex-col gap-2 p-2 group-data-[collapsible=icon]:items-center">
			{#if status?.synced}
				<Badge variant="outline" class="border-success/40 bg-success/10 text-success">
					Synced
				</Badge>
			{:else}
				<Badge variant="outline" class="border-warning/40 bg-warning/10 text-warning">
					Not synced
				</Badge>
			{/if}
			{#if status?.network}
				<Badge variant="secondary" class="group-data-[collapsible=icon]:hidden">
					{status.network}
				</Badge>
			{/if}
		</div>
	</Sidebar.Footer>
</Sidebar.Root>
