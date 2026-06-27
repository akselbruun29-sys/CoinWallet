<script lang="ts">
  import { onMount } from 'svelte';
  import { api, type LeaderboardEntry, type LeaderboardMe } from '$lib/api';
  import { formatBtc } from '$lib/utils';
  import * as Card from '$lib/components/ui/card/index.js';
  import { Button } from '$lib/components/ui/button/index.js';
  import { Badge } from '$lib/components/ui/badge/index.js';

  const networks = ['testnet', 'mainnet'] as const;

  let network = $state<(typeof networks)[number]>('testnet');
  let entries = $state<LeaderboardEntry[]>([]);
  let me = $state<LeaderboardMe | null>(null);
  let loading = $state(false);
  let error = $state('');

  async function load() {
    loading = true;
    error = '';
    try {
      const [board, status] = await Promise.all([
        api.leaderboard(network),
        api.leaderboardMe(network),
      ]);
      entries = board.entries;
      me = status;
    } catch (e) {
      error = e instanceof Error ? e.message : 'Failed to load leaderboard';
    } finally {
      loading = false;
    }
  }

  function setNetwork(value: (typeof networks)[number]) {
    network = value;
    load();
  }

  onMount(load);
</script>

<div class="space-y-6">
  <div class="flex flex-col gap-4 sm:flex-row sm:items-center sm:justify-between">
    <div>
      <h1 class="text-2xl font-bold tracking-tight">Leaderboard</h1>
      <p class="text-sm text-muted-foreground">
        Opt-in rankings by total balance. Display name and balance only.
      </p>
    </div>
    <div class="flex gap-2">
      {#each networks as n}
        <Button
          variant={network === n ? 'default' : 'outline'}
          size="sm"
          onclick={() => setNetwork(n)}
        >
          {n}
        </Button>
      {/each}
    </div>
  </div>

  {#if me?.opted_in}
    <Card.Root>
      <Card.Header class="pb-2">
        <Card.Title class="text-sm text-muted-foreground">Your rank</Card.Title>
      </Card.Header>
      <Card.Content class="flex flex-wrap items-center gap-3">
        <Badge variant="outline" class="border-primary/40 text-primary">
          #{me.rank ?? '—'}
        </Badge>
        <span class="font-medium">{me.display_name}</span>
        <span class="text-muted-foreground">{formatBtc(me.balance_sats)}</span>
      </Card.Content>
    </Card.Root>
  {:else}
    <Card.Root>
      <Card.Content class="py-4 text-sm text-muted-foreground">
        You are not on the {network} leaderboard. Opt in from Settings.
      </Card.Content>
    </Card.Root>
  {/if}

  {#if error}
    <p class="text-sm text-destructive">{error}</p>
  {:else if loading}
    <p class="text-sm text-muted-foreground">Loading…</p>
  {:else}
    <Card.Root>
      <Card.Content class="p-0">
        <div class="overflow-x-auto">
          <table class="w-full text-sm">
            <thead class="border-b border-border bg-muted/30">
              <tr>
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">Rank</th>
                <th class="px-4 py-3 text-left font-medium text-muted-foreground">Name</th>
                <th class="px-4 py-3 text-right font-medium text-muted-foreground">Balance</th>
              </tr>
            </thead>
            <tbody>
              {#if entries.length === 0}
                <tr>
                  <td colspan="3" class="px-4 py-10 text-center text-muted-foreground">
                    No entries yet on {network}.
                  </td>
                </tr>
              {:else}
                {#each entries as entry (entry.rank)}
                  <tr class="border-b border-border last:border-0">
                    <td class="px-4 py-3 font-mono text-muted-foreground">{entry.rank}</td>
                    <td class="px-4 py-3 font-medium">{entry.display_name}</td>
                    <td class="px-4 py-3 text-right font-mono">{formatBtc(entry.balance_sats)}</td>
                  </tr>
                {/each}
              {/if}
            </tbody>
          </table>
        </div>
      </Card.Content>
    </Card.Root>
  {/if}
</div>
