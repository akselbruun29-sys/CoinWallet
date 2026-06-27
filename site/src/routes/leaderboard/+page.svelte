<script lang="ts">
  import { onMount } from 'svelte';
  import { fetchLeaderboard, formatBtc, type LeaderboardEntry } from '$lib/api';

  const networks = ['testnet', 'mainnet'] as const;

  let network = $state<(typeof networks)[number]>('testnet');
  let entries = $state<LeaderboardEntry[]>([]);
  let loading = $state(true);
  let error = $state('');

  async function load() {
    loading = true;
    error = '';
    try {
      const data = await fetchLeaderboard(network);
      entries = data.entries;
    } catch {
      error = 'Leaderboard unavailable. Make sure the API is running.';
      entries = [];
    } finally {
      loading = false;
    }
  }

  function setNetwork(value: (typeof networks)[number]) {
    network = value;
    load();
  }

  function rankClass(rank: number): string {
    if (rank === 1) return 'rank-gold font-semibold';
    if (rank === 2) return 'rank-silver font-semibold';
    if (rank === 3) return 'rank-bronze font-semibold';
    return 'text-muted-foreground';
  }

  function rankLabel(rank: number): string {
    return `#${rank}`;
  }

  onMount(load);
</script>

<svelte:head>
  <title>Leaderboard — CoinWallet</title>
  <meta
    name="description"
    content="CoinWallet opt-in public leaderboard ranked by wallet balance."
  />
</svelte:head>

<main class="site-section site-container">
  <div class="mb-10 text-center">
    <h1 class="page-heading mb-3">Leaderboard</h1>
    <p class="page-lead mx-auto max-w-2xl">
      Opt-in ranking by total balance. No addresses or transaction history — display name and balance
      only.
    </p>
  </div>

  <div class="mb-8 flex justify-center gap-2">
    {#each networks as n}
      <button
        type="button"
        class="min-h-11 rounded-lg border px-4 py-2 text-sm font-medium transition-colors {network === n
          ? 'border-success bg-success/10 text-success'
          : 'border-border text-muted-foreground hover:text-foreground'}"
        onclick={() => setNetwork(n)}
      >
        {n.charAt(0).toUpperCase() + n.slice(1)}
      </button>
    {/each}
  </div>

  <div class="glass-card overflow-hidden">
    <table class="w-full text-left text-sm">
      <thead class="border-b border-border bg-card/80">
        <tr>
          <th class="px-4 py-3 font-medium text-muted-foreground">Rank</th>
          <th class="px-4 py-3 font-medium text-muted-foreground">Display name</th>
          <th class="px-4 py-3 text-right font-medium text-muted-foreground">Balance</th>
        </tr>
      </thead>
      <tbody>
        {#if loading}
          {#each Array(5) as _, i}
            <tr class="border-b border-border/60">
              <td class="px-4 py-4"><div class="skeleton h-4 w-8"></div></td>
              <td class="px-4 py-4"><div class="skeleton h-4 w-32"></div></td>
              <td class="px-4 py-4"><div class="skeleton ml-auto h-4 w-20"></div></td>
            </tr>
          {/each}
        {:else if error}
          <tr>
            <td colspan="3" class="px-4 py-12 text-center text-muted-foreground">{error}</td>
          </tr>
        {:else if entries.length === 0}
          <tr>
            <td colspan="3" class="px-4 py-12 text-center text-muted-foreground">
              No entries on {network} yet.
            </td>
          </tr>
        {:else}
          {#each entries as entry (entry.rank)}
            <tr
              class="border-b border-border/60 last:border-0 even:bg-muted/20 {entry.rank <= 3
                ? 'bg-success/5'
                : ''}"
            >
              <td class="px-4 py-3 font-mono {rankClass(entry.rank)}">{rankLabel(entry.rank)}</td>
              <td class="px-4 py-3 font-medium">{entry.display_name}</td>
              <td class="px-4 py-3 text-right font-mono text-success">{formatBtc(entry.balance_sats)}</td>
            </tr>
          {/each}
        {/if}
      </tbody>
    </table>
  </div>

  <p class="mt-8 text-center text-xs text-muted-foreground">
    Opt in from CoinWallet Settings. Opt out removes your entry immediately.
  </p>
</main>
