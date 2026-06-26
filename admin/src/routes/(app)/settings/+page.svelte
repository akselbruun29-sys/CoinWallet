<script lang="ts">
	import { onMount } from 'svelte';
	import { api, API_BASE, type User } from '$lib/api';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import { Checkbox } from '$lib/components/ui/checkbox/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import AlertTriangleIcon from '@lucide/svelte/icons/triangle-alert';

	let user: User | null = $state(null);
	let settings: Record<string, string> = $state({});
	let apiOk = $state<boolean | null>(null);
	let saving = $state(false);
	let error = $state('');
	let saved = $state(false);

	let network = $state('testnet');
	let backendType = $state('esplora');
	let backendUri = $state('');
	let coordinatorUri = $state('');
	let torEnabled = $state(false);
	let allowMainnet = $state(false);

	let currentPassword = $state('');
	let newPassword = $state('');
	let confirmPassword = $state('');
	let passwordSaving = $state(false);
	let passwordError = $state('');
	let passwordSaved = $state(false);

	function applySettings(s: Record<string, string>) {
		settings = s;
		network = s.network ?? 'testnet';
		backendType = s.backend_type ?? 'esplora';
		backendUri = s.backend_uri ?? '';
		coordinatorUri = s.coordinator_uri ?? '';
		torEnabled = s.tor_enabled === 'true';
		allowMainnet = s.allow_mainnet === 'true';
	}

	async function load() {
		[user, settings] = await Promise.all([api.me(), api.settings()]);
		applySettings(settings);
		try {
			const res = await fetch(`${API_BASE}/api/health`);
			apiOk = res.ok;
		} catch {
			apiOk = false;
		}
	}

	async function saveSettings(e: Event) {
		e.preventDefault();
		if (user?.role !== 'admin') return;
		saving = true;
		error = '';
		saved = false;
		try {
			applySettings(
				await api.adminUpdateSettings({
					network,
					backend_type: backendType,
					backend_uri: backendUri,
					tor_enabled: torEnabled,
					coordinator_uri: coordinatorUri,
					allow_mainnet: allowMainnet
				})
			);
			saved = true;
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to save settings';
		} finally {
			saving = false;
		}
	}

	async function changePassword(e: Event) {
		e.preventDefault();
		passwordError = '';
		passwordSaved = false;
		if (newPassword.length < 8) {
			passwordError = 'New password must be at least 8 characters';
			return;
		}
		if (newPassword !== confirmPassword) {
			passwordError = 'New passwords do not match';
			return;
		}
		passwordSaving = true;
		try {
			await api.changePassword(currentPassword, newPassword);
			currentPassword = '';
			newPassword = '';
			confirmPassword = '';
			passwordSaved = true;
		} catch (err) {
			passwordError = err instanceof Error ? err.message : 'Failed to change password';
		} finally {
			passwordSaving = false;
		}
	}

	onMount(load);
</script>

<div class="mx-auto max-w-lg space-y-6">
	<Card.Root>
		<Card.Header><Card.Title>Account</Card.Title></Card.Header>
		<Card.Content class="space-y-2 text-sm">
			<p><span class="text-muted-foreground">Username:</span> {user?.username ?? '—'}</p>
			<p>
				<span class="text-muted-foreground">Role:</span>
				<Badge variant="secondary" class="ml-1 capitalize">{user?.role ?? '—'}</Badge>
			</p>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header><Card.Title>Change password</Card.Title></Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={changePassword}>
				<div class="space-y-2">
					<Label for="current-password">Current password</Label>
					<Input id="current-password" type="password" bind:value={currentPassword} required />
				</div>
				<div class="space-y-2">
					<Label for="new-password">New password</Label>
					<Input id="new-password" type="password" bind:value={newPassword} minlength={8} required />
				</div>
				<div class="space-y-2">
					<Label for="confirm-password">Confirm new password</Label>
					<Input id="confirm-password" type="password" bind:value={confirmPassword} minlength={8} required />
				</div>
				{#if passwordError}
					<p class="text-sm text-destructive">{passwordError}</p>
				{/if}
				{#if passwordSaved}
					<p class="text-sm text-success">Password updated.</p>
				{/if}
				<Button type="submit" disabled={passwordSaving}>
					{passwordSaving ? 'Updating...' : 'Update password'}
				</Button>
			</form>
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header><Card.Title>Network</Card.Title></Card.Header>
		<Card.Content class="space-y-4 text-sm">
			{#if settings.allow_mainnet === 'true' || settings.network === 'mainnet'}
				<Alert.Root variant="destructive">
					<AlertTriangleIcon class="size-4" />
					<Alert.Title>Mainnet enabled</Alert.Title>
					<Alert.Description>
						Real funds at risk. Mainnet wallet create/import is allowed on this instance.
					</Alert.Description>
				</Alert.Root>
			{/if}

			{#if user?.role === 'admin'}
				<form class="space-y-4" onsubmit={saveSettings}>
					<div class="space-y-2">
						<Label>Bitcoin network</Label>
						<Select.Root type="single" value={network} onValueChange={(v) => (network = v ?? 'testnet')}>
							<Select.Trigger class="w-full">{network}</Select.Trigger>
							<Select.Content>
								<Select.Item value="testnet">testnet</Select.Item>
								<Select.Item value="signet">signet</Select.Item>
								<Select.Item value="regtest">regtest</Select.Item>
								<Select.Item value="mainnet">mainnet</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-2">
						<Label>Backend type</Label>
						<Select.Root type="single" value={backendType} onValueChange={(v) => (backendType = v ?? 'esplora')}>
							<Select.Trigger class="w-full">{backendType}</Select.Trigger>
							<Select.Content>
								<Select.Item value="esplora">esplora</Select.Item>
								<Select.Item value="core">core (Bitcoin Core RPC)</Select.Item>
							</Select.Content>
						</Select.Root>
					</div>
					<div class="space-y-2">
						<Label for="backend-uri">Backend URI</Label>
						<Input id="backend-uri" bind:value={backendUri} placeholder="https://blockstream.info/testnet/api/" />
					</div>
					<div class="space-y-2">
						<Label for="coordinator-uri">Coordinator URI</Label>
						<Input id="coordinator-uri" bind:value={coordinatorUri} placeholder="Optional" />
					</div>
					<div class="flex items-center gap-2">
						<Checkbox id="tor" bind:checked={torEnabled} />
						<Label for="tor" class="font-normal">Enable Tor proxy</Label>
					</div>
					<div class="flex items-center gap-2">
						<Checkbox id="mainnet" bind:checked={allowMainnet} />
						<Label for="mainnet" class="font-normal">Allow mainnet wallets</Label>
					</div>
					{#if error}
						<p class="text-destructive">{error}</p>
					{/if}
					{#if saved}
						<p class="text-success">Settings saved.</p>
					{/if}
					<Button type="submit" disabled={saving}>{saving ? 'Saving...' : 'Save settings'}</Button>
				</form>
			{:else}
				<p><span class="text-muted-foreground">Bitcoin network:</span> {settings.network ?? 'testnet'}</p>
				<p><span class="text-muted-foreground">Mainnet wallets:</span> {settings.allow_mainnet === 'true' ? 'Allowed' : 'Blocked'}</p>
				<p><span class="text-muted-foreground">Tor:</span> {settings.tor_enabled === 'true' ? 'Enabled' : 'Disabled'}</p>
				<p><span class="text-muted-foreground">Backend type:</span> {settings.backend_type ?? 'esplora'}</p>
				<p><span class="text-muted-foreground">Backend URI:</span> {settings.backend_uri || 'Not configured'}</p>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header><Card.Title>API Connection</Card.Title></Card.Header>
		<Card.Content class="space-y-3">
			{#if apiOk === true}
				<p class="text-sm text-success">API reachable at {API_BASE}</p>
			{:else if apiOk === false}
				<p class="text-sm text-destructive">Cannot reach API. Run: uvicorn api.main:app --reload --port 8001</p>
			{/if}
			<Button variant="outline" size="sm" onclick={() => location.reload()}>Test again</Button>
		</Card.Content>
	</Card.Root>
</div>
