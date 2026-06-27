<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type AuthConfig } from '$lib/api';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Card from '$lib/components/ui/card/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import CircleAlertIcon from '@lucide/svelte/icons/circle-alert';

	let mode: 'login' | 'register' = $state('login');
	let username = $state('');
	let password = $state('');
	let regUsername = $state('');
	let regPassword = $state('');
	let regEmail = $state('');
	let error = $state('');
	let regError = $state('');
	let regSuccess = $state('');
	let loading = $state(false);
	let config: AuthConfig | null = $state(null);

	onMount(async () => {
		try {
			config = await api.authConfig();
		} catch {
			config = { open_registration: false, auto_approve_users: true };
		}
	});

	async function submit(e: Event) {
		e.preventDefault();
		loading = true;
		error = '';
		try {
			const user = await api.login(username, password);
			if (user.role === 'pending') {
				goto('/pending');
			} else {
				goto('/');
			}
		} catch (err) {
			error = err instanceof Error ? err.message : 'Login failed';
		} finally {
			loading = false;
		}
	}

	async function register(e: Event) {
		e.preventDefault();
		loading = true;
		regError = '';
		regSuccess = '';
		try {
			const result = await api.register(regUsername, regPassword, regEmail || undefined);
			regSuccess =
				result.role === 'pending'
					? 'Account created — waiting for admin approval.'
					: 'Account created — you can sign in now.';
			regUsername = '';
			regPassword = '';
			regEmail = '';
			mode = 'login';
		} catch (err) {
			regError = err instanceof Error ? err.message : 'Registration failed';
		} finally {
			loading = false;
		}
	}
</script>

<div class="flex min-h-dvh items-center justify-center bg-background p-4 pb-[max(1rem,env(safe-area-inset-bottom))]">
	<Card.Root class="w-full max-w-md border-border">
		<Card.Header class="text-center">
			<div class="mx-auto mb-2 flex size-12 items-center justify-center rounded-xl bg-primary">
				<ShieldIcon class="size-6 text-primary-foreground" />
			</div>
			<Card.Title class="text-xl">Wallet Vault</Card.Title>
			<Card.Description>Privacy-focused Bitcoin wallet</Card.Description>
		</Card.Header>
		<Card.Content>
			{#if mode === 'login'}
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
				{#if config?.open_registration}
					<p class="mt-4 text-center text-sm text-muted-foreground">
						No account?
						<button type="button" class="text-primary underline" onclick={() => (mode = 'register')}>
							Register
						</button>
					</p>
				{/if}
			{:else}
				<form class="space-y-4" onsubmit={register}>
					<div class="space-y-2">
						<Label for="reg-username">Username</Label>
						<Input id="reg-username" bind:value={regUsername} required minlength={3} />
					</div>
					<div class="space-y-2">
						<Label for="reg-password">Password</Label>
						<Input
							id="reg-password"
							type="password"
							bind:value={regPassword}
							required
							minlength={8}
						/>
					</div>
					<div class="space-y-2">
						<Label for="reg-email">Email (optional)</Label>
						<Input id="reg-email" type="email" bind:value={regEmail} />
					</div>
					{#if regError}
						<p class="text-sm text-destructive">{regError}</p>
					{/if}
					{#if regSuccess}
						<p class="text-sm text-success">{regSuccess}</p>
					{/if}
					<Button type="submit" class="w-full" disabled={loading}>
						{loading ? 'Creating...' : 'Create account'}
					</Button>
				</form>
				<p class="mt-4 text-center text-sm text-muted-foreground">
					Already have an account?
					<button type="button" class="text-primary underline" onclick={() => (mode = 'login')}>
						Sign in
					</button>
				</p>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
