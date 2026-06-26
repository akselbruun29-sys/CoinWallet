<script lang="ts">
	import { goto } from '$app/navigation';
	import { api } from '$lib/api';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import CircleAlertIcon from '@lucide/svelte/icons/circle-alert';

	let username = $state('admin');
	let password = $state('');
	let error = $state('');
	let loading = $state(false);

	async function submit(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			await api.login(username, password);
			goto('/');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Login failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-screen items-center justify-center bg-background p-4">
	<Card.Root class="w-full max-w-md border-border">
		<Card.Header class="text-center">
			<div class="mx-auto mb-2 flex size-12 items-center justify-center rounded-xl bg-primary">
				<ShieldIcon class="size-6 text-primary-foreground" />
			</div>
			<Card.Title class="text-xl">Wallet Vault</Card.Title>
			<Card.Description>Privacy-focused Bitcoin wallet — sign in to continue</Card.Description>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={submit}>
				<div class="space-y-2">
					<Label for="username">Username</Label>
					<Input id="username" bind:value={username} autocomplete="username" required />
				</div>
				<div class="space-y-2">
					<Label for="password">Password</Label>
					<Input
						id="password"
						type="password"
						bind:value={password}
						autocomplete="current-password"
						required
					/>
				</div>
				{#if error}
					<Alert.Root variant="destructive">
						<CircleAlertIcon />
						<Alert.Title>Login failed</Alert.Title>
						<Alert.Description>{error}</Alert.Description>
					</Alert.Root>
				{/if}
				<Button type="submit" class="w-full" disabled={loading}>
					{loading ? 'Signing in...' : 'Sign in'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>
</div>
