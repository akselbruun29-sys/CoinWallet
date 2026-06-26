<script lang="ts">
	import { goto } from '$app/navigation';
	import { walletSecurity } from '$lib/stores/security';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import LockIcon from '@lucide/svelte/icons/lock';

	interface Props {
		action?: string;
		children?: import('svelte').Snippet;
	}

	let { action = 'use this page', children }: Props = $props();

	let security = $state($walletSecurity);
	walletSecurity.subscribe((v) => (security = v));

	let blocked = $derived(
		security != null && (!security.has_wallet_passphrase || !security.unlocked)
	);
</script>

{#if blocked}
	<Alert.Root class="border-warning/40">
		<LockIcon class="size-4" />
		<Alert.Title>Wallet locked</Alert.Title>
		<Alert.Description class="space-y-2">
			<p class="text-sm">
				{#if !security?.has_wallet_passphrase}
					Set your wallet passphrase in Security before you can {action}.
				{:else}
					Unlock your wallet to {action}.
				{/if}
			</p>
			<Button variant="outline" size="sm" onclick={() => goto('/security')}>Open Security</Button>
		</Alert.Description>
	</Alert.Root>
{:else if children}
	{@render children()}
{/if}
