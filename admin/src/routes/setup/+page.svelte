<script lang="ts">
	import { onMount } from 'svelte';
	import { goto } from '$app/navigation';
	import { api, type NetworkStatus } from '$lib/api';
	import { IS_DESKTOP_BUILD } from '$lib/desktop';
	import * as Card from '$lib/components/ui/card/index.js';
	import { Button } from '$lib/components/ui/button/index.js';
	import ShieldIcon from '@lucide/svelte/icons/shield';
	import LoaderCircleIcon from '@lucide/svelte/icons/loader-circle';
	import CheckCircleIcon from '@lucide/svelte/icons/circle-check';

	let status: NetworkStatus | null = $state(null);
	let error = $state('');
	let loading = $state(false);
	let pollError = $state('');

	const ready = $derived(
		status &&
			(!status.tor_managed || !status.tor_enabled || status.tor_bootstrap_complete)
	);

	async function refresh() {
		try {
			status = await api.networkStatus();
			pollError = '';
			if (status.network_wizard_complete) {
				goto('/login');
			}
		} catch (err) {
			pollError = err instanceof Error ? err.message : 'Waiting for local API…';
		}
	}

	async function continueSetup() {
		loading = true;
		error = '';
		try {
			await api.completeNetworkSetup(false);
			goto('/login');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not finish setup';
		} finally {
			loading = false;
		}
	}

	async function skipDevSetup() {
		loading = true;
		error = '';
		try {
			await api.completeNetworkSetup(true);
			goto('/login');
		} catch (err) {
			error = err instanceof Error ? err.message : 'Could not finish setup';
		} finally {
			loading = false;
		}
	}

	onMount(() => {
		if (!IS_DESKTOP_BUILD) {
			goto('/login');
			return;
		}
		void refresh();
		const id = setInterval(refresh, 2000);
		return () => clearInterval(id);
	});
</script>

<div class="flex min-h-dvh items-center justify-center bg-background p-4">
	<Card.Root class="w-full max-w-lg border-border">
		<Card.Header class="text-center">
			<div class="mx-auto mb-2 flex size-12 items-center justify-center rounded-xl bg-primary">
				<ShieldIcon class="size-6 text-primary-foreground" />
			</div>
			<Card.Title class="text-xl">Private network setup</Card.Title>
			<Card.Description>
				CoinWallet routes Bitcoin sync through Tor by default. No full blockchain download — balances
				sync via Esplora over Tor (light client).
			</Card.Description>
		</Card.Header>
		<Card.Content class="space-y-4">
			{#if pollError && !status}
				<div class="flex items-center gap-2 text-sm text-muted-foreground">
					<LoaderCircleIcon class="size-4 animate-spin" />
					{pollError}
				</div>
			{:else if status}
				<ul class="space-y-3 text-sm">
					<li class="flex items-start gap-2">
						{#if status.tor_managed}
							<CheckCircleIcon class="mt-0.5 size-4 shrink-0 text-success" />
						{:else}
							<LoaderCircleIcon class="mt-0.5 size-4 shrink-0 text-muted-foreground" />
						{/if}
						<span>
							<strong>Tor sidecar</strong> —
							{status.tor_managed ? 'running on this device' : 'not bundled (dev mode)'}
						</span>
					</li>
					<li class="flex items-start gap-2">
						{#if status.tor_bootstrap_complete}
							<CheckCircleIcon class="mt-0.5 size-4 shrink-0 text-success" />
						{:else if status.tor_enabled}
							<LoaderCircleIcon class="mt-0.5 size-4 shrink-0 animate-spin text-primary" />
						{:else}
							<LoaderCircleIcon class="mt-0.5 size-4 shrink-0 text-muted-foreground" />
						{/if}
						<span>
							<strong>Tor connection</strong> —
							{status.tor_bootstrap_complete
								? 'connected — wallet traffic is anonymized'
								: status.tor_enabled
									? 'connecting to the Tor network…'
									: 'disabled'}
						</span>
					</li>
					<li class="flex items-start gap-2">
						<CheckCircleIcon class="mt-0.5 size-4 shrink-0 text-success" />
						<span>
							<strong>Light sync</strong> — no local blockchain download; Esplora queries go through
							Tor when enabled.
						</span>
					</li>
				</ul>

				{#if error}
					<p class="text-sm text-destructive">{error}</p>
				{/if}

				<div class="flex flex-col gap-2 sm:flex-row">
					<Button class="flex-1" disabled={!ready || loading} onclick={continueSetup}>
						{loading ? 'Finishing…' : 'Continue to sign in'}
					</Button>
					{#if status && !status.tor_managed}
						<Button variant="outline" class="flex-1" disabled={loading} onclick={skipDevSetup}>
							Skip (dev)
						</Button>
					{/if}
				</div>
			{/if}
		</Card.Content>
	</Card.Root>
</div>
