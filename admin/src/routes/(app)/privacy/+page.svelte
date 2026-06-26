<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type PrivacySummary } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Alert, AlertDescription, AlertTitle } from '$lib/components/ui/alert/index.js';
	import ShieldIcon from '@lucide/svelte/icons/shield';

	let summary: PrivacySummary | null = $state(null);
	let error = $state('');

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		try {
			summary = await api.walletPrivacy($activeWalletId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		}
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

{#if $activeWalletId == null}
	<p class="text-sm text-muted-foreground">Select a wallet first.</p>
{:else if error}
	<p class="text-sm text-destructive">{error}</p>
{:else if summary}
	<div class="space-y-6">
		{#if summary.message}
			<Alert>
				<ShieldIcon class="size-4" />
				<AlertTitle>Privacy analysis</AlertTitle>
				<AlertDescription>{summary.message}</AlertDescription>
			</Alert>
		{/if}

		<div class="grid gap-4 sm:grid-cols-2 lg:grid-cols-3">
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm text-muted-foreground">Privacy score</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="text-2xl font-bold">{summary.privacy_score}<span class="text-base font-normal text-muted-foreground">/100</span></p>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm text-muted-foreground">Private UTXOs</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="text-2xl font-bold text-success">{summary.private_utxos}</p>
				</Card.Content>
			</Card.Root>
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm text-muted-foreground">Non-private UTXOs</Card.Title>
				</Card.Header>
				<Card.Content>
					<p class="text-2xl font-bold">{summary.non_private_utxos}</p>
				</Card.Content>
			</Card.Root>
		</div>

		<Card.Root>
			<Card.Header>
				<Card.Title>Known entities</Card.Title>
				<Card.Description>Address labels and exchange exposure (Phase 3)</Card.Description>
			</Card.Header>
			<Card.Content>
				{#if summary.entities.length === 0}
					<p class="text-sm text-muted-foreground">No labeled entities yet.</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each summary.entities as entity (entity)}
							<Badge variant="secondary">{entity}</Badge>
						{/each}
					</div>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
{:else}
	<p class="text-sm text-muted-foreground">Loading...</p>
{/if}
