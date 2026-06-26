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

	async function toggleActive(user: User) {
		await api.adminUpdateUser(user.id, { is_active: !user.is_active });
		await load();
	}

	onMount(load);
</script>

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
						<Table.Head>Status</Table.Head>
						<Table.Head></Table.Head>
					</Table.Row>
				</Table.Header>
				<Table.Body>
					{#each users as u}
						<Table.Row>
							<Table.Cell class="font-medium">{u.username}</Table.Cell>
							<Table.Cell>
								<Badge variant="secondary">{roleLabels[u.role] ?? u.role}</Badge>
							</Table.Cell>
							<Table.Cell>
								{#if u.is_active}
									<Badge variant="outline" class="border-success/40 text-success">Active</Badge>
								{:else}
									<Badge variant="outline" class="text-destructive">Disabled</Badge>
								{/if}
							</Table.Cell>
							<Table.Cell>
								<Button variant="ghost" size="sm" onclick={() => toggleActive(u)}>
									{u.is_active ? 'Disable' : 'Enable'}
								</Button>
							</Table.Cell>
						</Table.Row>
					{/each}
				</Table.Body>
			</Table.Root>
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
				{#if error}
					<p class="text-sm text-destructive">{error}</p>
				{/if}
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
