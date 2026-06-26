<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type User, type AuditEntry, type SystemInfo } from '$lib/api';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import { Input } from '$lib/components/ui/input/index.js';
	import { Label } from '$lib/components/ui/label/index.js';
	import * as Table from '$lib/components/ui/table/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import * as Select from '$lib/components/ui/select/index.js';
	import * as Alert from '$lib/components/ui/alert/index.js';
	import ShieldCheckIcon from '@lucide/svelte/icons/shield-check';

	let users: User[] = $state([]);
	let audit: AuditEntry[] = $state([]);
	let system: SystemInfo | null = $state(null);
	let newUsername = $state('');
	let newPassword = $state('');
	let newRole = $state('user');
	let error = $state('');

	const roleLabels: Record<string, string> = {
		admin: 'Admin',
		user: 'User',
		pending: 'Pending'
	};

	const pendingCount = $derived(users.filter((u) => u.role === 'pending').length);

	async function load() {
		const me = await api.me();
		if (me.role !== 'admin') {
			goto('/');
			return;
		}
		[users, audit, system] = await Promise.all([
			api.adminUsers(),
			api.adminAuditLog(),
			api.adminSystem()
		]);
	}

	async function createUser(e: Event) {
		e.preventDefault();
		error = '';
		try {
			await api.adminCreateUser(newUsername, newPassword, newRole);
			newUsername = '';
			newPassword = '';
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Failed to create user';
		}
	}

	async function updateUser(user: User, patch: { role?: string; is_active?: boolean }) {
		try {
			await api.adminUpdateUser(user.id, patch);
			await load();
		} catch (err) {
			error = err instanceof Error ? err.message : 'Update failed';
		}
	}

	onMount(load);
</script>

<div class="mb-6">
	<Alert.Root class="border-primary/30">
		<ShieldCheckIcon class="size-4" />
		<Alert.Title>User isolation</Alert.Title>
		<Alert.Description>
			Admins manage accounts and instance settings only. Wallet mnemonics are encrypted per-user
			with each user's wallet passphrase — admins cannot decrypt or spend from other users' wallets.
		</Alert.Description>
	</Alert.Root>
</div>

{#if pendingCount > 0}
	<Card.Root class="mb-6 border-warning/40">
		<Card.Header>
			<Card.Title>{pendingCount} pending approval</Card.Title>
			<Card.Description>Approve registrations by setting role to User.</Card.Description>
		</Card.Header>
	</Card.Root>
{/if}

<div class="grid gap-6 lg:grid-cols-2">
	<Card.Root>
		<Card.Header>
			<Card.Title>Users</Card.Title>
			<Card.Description>Multi-user management — Open WebUI style</Card.Description>
		</Card.Header>
		<Card.Content>
			<Table.Root>
				<Table.Header>
					<Table.Row>
						<Table.Head>Username</Table.Head>
						<Table.Head>Role</Table.Head>
						<Table.Head>Wallets</Table.Head>
						<Table.Head>Status</Table.Head>
						<Table.Head></Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each users as u}
						<Table.Row>
							<Table.Cell class="font-medium">{u.username}</Table.Cell>
							<Table.Cell>
								<Select.Root
									type="single"
									value={u.role}
									onValueChange={(v) => v && updateUser(u, { role: v })}
								>
									<Select.Trigger class="h-8 w-[110px]">
										{roleLabels[u.role] ?? u.role}
									</Select.Trigger>
									<Select.Content>
										<Select.Item value="user">User</Select.Item>
										<Select.Item value="admin">Admin</Select.Item>
										<Select.Item value="pending">Pending</Select.Item>
									</Select.Content>
								</Select.Root>
							</Table.Cell>
							<Table.Cell>{u.wallet_count ?? 0}</Table.Cell>
							<Table.Cell>
								{#if u.is_active}
									<Badge variant="outline" class="border-success/40 text-success">Active</Badge>
								{:else}
									<Badge variant="outline" class="text-destructive">Disabled</Badge>
								{/if}
							</Table.Cell>
							<Table.Cell class="space-x-1">
								{#if u.role === 'pending'}
									<Button
										variant="secondary"
										size="sm"
										onclick={() => updateUser(u, { role: 'user' })}
									>
										Approve
									</Button>
								{/if}
								<Button
									variant="ghost"
									size="sm"
									onclick={() => updateUser(u, { is_active: !u.is_active })}
								>
									{u.is_active ? 'Disable' : 'Enable'}
								</Button>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
			{#if error}
				<p class="mt-3 text-sm text-destructive">{error}</p>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Create User</Card.Title>
		</Card.Header>
		<Card.Content>
			<form class="space-y-4" onsubmit={createUser}>
				<div class="space-y-2">
					<Label for="username">Username</Label>
					<Input id="username" bind:value={newUsername} required />
				</div>
				<div class="space-y-2">
					<Label for="password">Password</Label>
					<Input id="password" type="password" bind:value={newPassword} required minlength={8} />
				</div>
				<div class="space-y-2">
					<Label>Role</Label>
					<Select.Root type="single" bind:value={newRole}>
						<Select.Trigger>{roleLabels[newRole]}</Select.Trigger>
						<Select.Content>
							<Select.Item value="user">User</Select.Item>
							<Select.Item value="admin">Admin</Select.Item>
							<Select.Item value="pending">Pending</Select.Item>
						</Select.Content>
					</Select.Root>
				</div>
				<Button type="submit">Create User</Button>
			</form>
		</Card.Content>
	</Card.Root>
</div>

<div class="mt-6 grid gap-6 lg:grid-cols-2">
	<Card.Root>
		<Card.Header>
			<Card.Title>System</Card.Title>
		</Card.Header>
		<Card.Content class="space-y-2 text-sm">
			{#if system}
				<p><span class="text-muted-foreground">Version:</span> {system.version}</p>
				<p><span class="text-muted-foreground">Network:</span> {system.settings.network}</p>
				<p><span class="text-muted-foreground">Node height:</span> {system.node_height}</p>
				<p class="text-muted-foreground">{system.message}</p>
			{/if}
		</Card.Content>
	</Card.Root>

	<Card.Root>
		<Card.Header>
			<Card.Title>Audit Log</Card.Title>
		</Card.Header>
		<Card.Content>
			{#if audit.length === 0}
				<p class="text-sm text-muted-foreground">No audit entries yet.</p>
			{:else}
				<ul class="max-h-64 space-y-2 overflow-y-auto text-sm">
					{#each audit as entry}
						<li class="rounded border border-border px-3 py-2">
							<div class="flex justify-between gap-2">
								<span class="font-medium">{entry.action}</span>
								<span class="shrink-0 text-muted-foreground">{entry.timestamp?.slice(0, 19)}</span>
							</div>
							<p class="text-muted-foreground">
								{entry.username ?? 'system'}{entry.details ? ` — ${entry.details}` : ''}
							</p>
						</li>
					{/each}
				</ul>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
