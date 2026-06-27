<script lang="ts">
	import { page } from '$app/stores';
	import { useSidebar } from '$lib/components/ui/sidebar/context.svelte.js';
	import LayoutDashboardIcon from '@lucide/svelte/icons/layout-dashboard';
	import WalletIcon from '@lucide/svelte/icons/wallet';
	import ArrowDownToLineIcon from '@lucide/svelte/icons/arrow-down-to-line';
	import ArrowUpFromLineIcon from '@lucide/svelte/icons/arrow-up-from-line';
	import MenuIcon from '@lucide/svelte/icons/menu';
	import { cn } from '$lib/utils';

	const sidebar = useSidebar();

	const items = [
		{ href: '/', label: 'Home', icon: LayoutDashboardIcon },
		{ href: '/wallets', label: 'Wallets', icon: WalletIcon },
		{ href: '/receive', label: 'Receive', icon: ArrowDownToLineIcon },
		{ href: '/send', label: 'Send', icon: ArrowUpFromLineIcon }
	];
</script>

<nav
	class="fixed inset-x-0 bottom-0 z-40 border-t border-border bg-background/95 backdrop-blur supports-[backdrop-filter]:bg-background/80 md:hidden"
	style="padding-bottom: env(safe-area-inset-bottom, 0px);"
	aria-label="Mobile navigation"
>
	<div class="grid h-14 grid-cols-5">
		{#each items as item (item.href)}
			<a
				href={item.href}
				class={cn(
					'flex min-h-11 flex-col items-center justify-center gap-0.5 px-1 text-[10px] font-medium transition-colors',
					$page.url.pathname === item.href
						? 'text-primary'
						: 'text-muted-foreground hover:text-foreground'
				)}
			>
				<item.icon class="size-5 shrink-0" />
				<span class="truncate">{item.label}</span>
			</a>
		{/each}
		<button
			type="button"
			class="flex min-h-11 flex-col items-center justify-center gap-0.5 px-1 text-[10px] font-medium text-muted-foreground hover:text-foreground"
			onclick={() => sidebar.setOpenMobile(true)}
		>
			<MenuIcon class="size-5 shrink-0" />
			<span>More</span>
		</button>
	</div>
</nav>
