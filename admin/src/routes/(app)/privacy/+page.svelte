<script lang="ts">
	import { onMount } from 'svelte';
	import { api, type PrivacySummary } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { privacyTips } from '$lib/advisor';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Alert, AlertDescription, AlertTitle } from '$lib/components/ui/alert/index.js';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import AlertTriangleIcon from '@lucide/svelte/icons/triangle-alert';
	import InfoIcon from '@lucide/svelte/icons/info';

	let summary: PrivacySummary | null = $state(null);
	let error = $state('');

	const FLAG_LABELS: Record<string, string> = {
		address_reuse: 'Address reuse',
		round_amount: 'Round amount',
		labeled: 'Labeled',
		frozen: 'Frozen'
	};

	function severityVariant(severity: string) {
		if (severity === 'critical') return 'destructive' as const;
		if (severity === 'warning') return 'secondary' as const;
		return 'outline' as const;
	}

	function tipIcon(severity: string) {
		if (severity === 'critical') return AlertTriangleIcon;
		if (severity === 'warning') return AlertTriangleIcon;
		return InfoIcon;
	}

	async function load() {
		if ($activeWalletId == null) return;
		error = '';
		try {
			summary = await api.walletPrivacy($activeWalletId);
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load';
		}
	}

	const tips = $derived(summary ? privacyTips(summary) : []);

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

		{#if tips.length > 0}
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title>Recommendations</Card.Title>
					<Card.Description>Rule-based tips from your UTXO graph — same engine as Advisor AI</Card.Description>
				</Card.Header>
				<Card.Content class="space-y-3">
					{#each tips as tip (tip.id)}
						{@const Icon = tipIcon(tip.severity)}
						<Alert variant={tip.severity === 'critical' ? 'destructive' : 'default'}>
							<Icon class="size-4" />
							<AlertTitle class="flex items-center gap-2">
								{tip.title}
								<Badge variant={severityVariant(tip.severity)}>{tip.severity}</Badge>
							</AlertTitle>
							<AlertDescription>{tip.detail}</AlertDescription>
						</Alert>
					{/each}
				</Card.Content>
			</Card.Root>
		{/if}

		{#if summary.flag_counts && Object.keys(summary.flag_counts).length > 0}
			<Card.Root>
				<Card.Header class="pb-2">
					<Card.Title class="text-sm text-muted-foreground">Privacy flags</Card.Title>
					<Card.Description>Detected after each wallet sync</Card.Description>
				</Card.Header>
				<Card.Content>
					<div class="flex flex-wrap gap-2">
						{#each Object.entries(summary.flag_counts) as [flag, count] (flag)}
							<Badge variant="outline">{FLAG_LABELS[flag] ?? flag}: {count}</Badge>
						{/each}
					</div>
				</Card.Content>
			</Card.Root>
		{/if}

		<Card.Root>
			<Card.Header class="pb-2">
				<Card.Title class="text-sm text-muted-foreground">Known entities</Card.Title>
				<Card.Description>Labels from transactions, addresses, and UTXOs</Card.Description>
			</Card.Header>
			<Card.Content>
				{#if summary.entities.length === 0}
					<p class="text-sm text-muted-foreground">No labeled entities yet. Tag transactions on the Transactions page.</p>
				{:else}
					<div class="flex flex-wrap gap-2">
						{#each summary.entities as entity (entity)}
							<Badge variant="secondary">{entity}</Badge>
						{/each}
					</div>
				{/if}
				{#if summary.exchange_exposure != null && summary.exchange_exposure > 0}
					<p class="mt-3 text-sm text-warning">
						{summary.exchange_exposure} address(es) tagged as exchange exposure.
					</p>
				{/if}
			</Card.Content>
		</Card.Root>
	</div>
{:else}
	<p class="text-sm text-muted-foreground">Loading...</p>
{/if}
