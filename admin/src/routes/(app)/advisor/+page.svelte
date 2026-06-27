<script lang="ts">
	import { onMount } from 'svelte';
	import { api } from '$lib/api';
	import { activeWalletId } from '$lib/stores/wallet';
	import { runAdvisorWithOptionalCloud, type AdvisorReport } from '$lib/advisor';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Badge } from '$lib/components/ui/badge/index.js';
	import { Alert, AlertDescription, AlertTitle } from '$lib/components/ui/alert/index.js';
	import BotIcon from '@lucide/svelte/icons/bot';
	import AlertTriangleIcon from '@lucide/svelte/icons/triangle-alert';
	import InfoIcon from '@lucide/svelte/icons/info';
	import CircleHelpIcon from '@lucide/svelte/icons/circle-help';
	import CircleCheckIcon from '@lucide/svelte/icons/circle-check';
	import CircleXIcon from '@lucide/svelte/icons/circle-x';

	let report: AdvisorReport | null = $state(null);
	let error = $state('');
	let loading = $state(false);

	function severityVariant(severity: string) {
		if (severity === 'critical') return 'destructive' as const;
		if (severity === 'warning') return 'secondary' as const;
		return 'outline' as const;
	}

	function tipIcon(severity: string) {
		if (severity === 'critical' || severity === 'warning') return AlertTriangleIcon;
		return InfoIcon;
	}

	async function load() {
		loading = true;
		error = '';
		try {
			const [status, security, settings, swapHist] = await Promise.all([
				api.status(),
				api.walletSecurity(),
				api.settings(),
				api.swapHistory().catch(() => ({ swaps: [] }))
			]);

			let balance = null;
			let transactions: Awaited<ReturnType<typeof api.walletTransactions>> = [];
			let privacy = null;
			let walletName: string | undefined;
			let network: string | undefined;

			if ($activeWalletId != null) {
				const wallet = status.wallets.find((w) => w.id === $activeWalletId);
				walletName = wallet?.name;
				network = wallet?.network;
				const [b, txs, p] = await Promise.all([
					api.walletBalance($activeWalletId),
					api.walletTransactions($activeWalletId),
					api.walletPrivacy($activeWalletId)
				]);
				balance = b;
				transactions = txs.slice(0, 10);
				privacy = p;
			}

			report = await runAdvisorWithOptionalCloud({
				walletId: $activeWalletId,
				walletName,
				network,
				balance,
				transactions,
				privacy,
				security,
				status,
				settings,
				swapHistory: swapHist.swaps
			});
		} catch (e) {
			error = e instanceof Error ? e.message : 'Failed to load advisor';
			report = null;
		} finally {
			loading = false;
		}
	}

	onMount(load);
	$effect(() => {
		if ($activeWalletId != null) load();
	});
</script>

<div class="space-y-6">
	<Alert>
		<BotIcon class="size-4" />
		<AlertTitle>Advisor AI</AlertTitle>
		<AlertDescription>
			{report?.intro ??
				'Rule-based guidance from your wallet data. No cloud LLM. No trading or market signals.'}
		</AlertDescription>
	</Alert>

	{#if error}
		<p class="text-sm text-destructive">{error}</p>
	{:else if loading && !report}
		<p class="text-sm text-muted-foreground">Loading guidance...</p>
	{:else if report}
		{#each report.sections as section (section.id)}
			<Card.Root>
				<Card.Header>
					<Card.Title>{section.title}</Card.Title>
					<Card.Description>{section.summary}</Card.Description>
				</Card.Header>
				{#if section.checklist?.length}
					<Card.Content class="space-y-2 border-b pb-4">
						<ul class="space-y-2 text-sm">
							{#each section.checklist as item (item.id)}
								<li class="flex items-start gap-2">
									{#if item.passed}
										<CircleCheckIcon class="mt-0.5 size-4 shrink-0 text-success" />
									{:else}
										<CircleXIcon class="mt-0.5 size-4 shrink-0 text-destructive" />
									{/if}
									<div>
										<p class="font-medium">{item.label}</p>
										{#if item.detail}
											<p class="text-muted-foreground">{item.detail}</p>
										{/if}
									</div>
								</li>
							{/each}
						</ul>
					</Card.Content>
				{/if}
				{#if section.tips.length > 0}
					<Card.Content class="space-y-3">
						{#each section.tips as tip (tip.id)}
							{@const Icon = tipIcon(tip.severity)}
							<Alert variant={tip.severity === 'critical' ? 'destructive' : 'default'}>
								<Icon class="size-4" />
								<AlertTitle class="flex flex-wrap items-center gap-2">
									{tip.title}
									<Badge variant={severityVariant(tip.severity)}>{tip.severity}</Badge>
								</AlertTitle>
								<AlertDescription>{tip.detail}</AlertDescription>
							</Alert>
						{/each}
					</Card.Content>
				{/if}
			</Card.Root>
		{/each}

		<Card.Root>
			<Card.Header>
				<Card.Title class="flex items-center gap-2">
					<CircleHelpIcon class="size-5" />
					Bitcoin FAQ
				</Card.Title>
				<Card.Description>Static help content — not financial advice</Card.Description>
			</Card.Header>
			<Card.Content class="space-y-4">
				{#each report.faq as item (item.id)}
					<details class="group rounded-lg border px-4 py-3">
						<summary class="cursor-pointer font-medium marker:content-none group-open:mb-2">
							{item.question}
						</summary>
						<p class="text-sm text-muted-foreground">{item.answer}</p>
					</details>
				{/each}
			</Card.Content>
		</Card.Root>
	{/if}
</div>
