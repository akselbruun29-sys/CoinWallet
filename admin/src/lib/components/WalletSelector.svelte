<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type Wallet } from '$lib/api';
	import { activeWalletId, setActiveWalletId, validateActiveWallet } from '$lib/stores/wallet';
	import { cn } from '$lib/utils';
	import * as Select from '$lib/components/ui/select/index.js';

	interface Props {
		wallets?: Wallet[];
		class?: string;
	}

	let { wallets = [], class: className }: Props = $props();
	let fetched = $state<Wallet[] | null>(null);
	let list = $derived(fetched ?? wallets);

	onMount(async () => {
		if (wallets.length === 0) {
			fetched = await api.wallets();
		}
		validateActiveWallet(list);
	});

	$effect(() => {
		if (list.length > 0) validateActiveWallet(list);
	});

	let label = $derived(
		list.find((w) => w.id === $activeWalletId)?.name ?? 'Select wallet'
	);

	function onChange(value: string) {
		setActiveWalletId(value ? Number(value) : null);
	}
</script>

{#if list.length > 0}
	<Select.Root type="single" value={$activeWalletId ? String($activeWalletId) : ''} onValueChange={onChange}>
		<Select.Trigger class={cn('w-full max-w-[11rem] sm:w-[180px]', className)}>
			{label}
		</Select.Trigger>
		<Select.Content>
			{#each list as w (w.id)}
				<Select.Item value={String(w.id)}>{w.name}</Select.Item>
			{/each}
		</Select.Content>
	</Select.Root>
{/if}
