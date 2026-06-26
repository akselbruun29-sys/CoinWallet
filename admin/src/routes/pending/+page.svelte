<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, getToken } from '$lib/api';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import ClockIcon from '@lucide/svelte/icons/clock';

	onMount(async () => {
		if (!getToken()) {
			goto('/login');
			return;
		}
		try {
			const user = await api.me();
			if (user.role !== 'pending') {
				goto('/');
			}
		} catch {
			goto('/login');
		}
	});

	async function logout() {
		await api.logout();
		goto('/login');
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-background p-4">
	<Card.Root class="w-full max-w-md">
		<Card.Header class="text-center">
			<ClockIcon class="mx-auto mb-2 size-10 text-warning" />
			<Card.Title>Account pending approval</Card.Title>
			<Card.Description>
				Your registration is waiting for an administrator to approve your account.
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4 text-center text-sm text-muted-foreground">
			<p>You will be able to access wallets once an admin sets your role to User.</p>
			<Button variant="outline" onclick={() => location.reload()}>Check again</Button>
			<Button variant="ghost" onclick={logout}>Sign out</Button>
		</Card.Content>
	</Card.Root>
</div>
