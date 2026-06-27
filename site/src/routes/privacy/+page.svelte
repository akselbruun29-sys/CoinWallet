<svelte:head>
  <title>Privacy — CoinWallet</title>
</svelte:head>

<main class="mx-auto max-w-3xl px-6 py-16 sm:py-20">
  <h1 class="mb-8 text-3xl font-bold tracking-tight">Privacy Policy</h1>

  <div class="prose prose-invert max-w-none space-y-8 text-muted-foreground">
    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">Non-custodial by design</h2>
      <p class="text-sm leading-relaxed">
        CoinWallet is a non-custodial wallet. Your seed phrase and private keys are generated and
        stored on your device, encrypted at rest. We do not have access to your funds, mnemonics, or
        signing keys.
      </p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">What stays on your device</h2>
      <ul class="list-inside list-disc space-y-2 text-sm leading-relaxed">
        <li>Seed phrases and encrypted wallet data</li>
        <li>Transaction history synced from public block explorers</li>
        <li>Settings, labels, and UTXO metadata</li>
      </ul>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">Leaderboard (opt-in only)</h2>
      <p class="mb-4 text-sm leading-relaxed">
        The public leaderboard is disabled by default. If you opt in, only your chosen display name
        and total balance (in satoshis) are sent to the server. We never upload addresses,
        mnemonics, UTXOs, or transaction history for leaderboard purposes. You can opt out at any
        time; your entry is removed immediately.
      </p>
      <div class="rounded-lg border border-border bg-muted/40 p-4 text-sm">
        <p class="mb-3 font-medium text-foreground">Leaderboard data flow</p>
        <pre class="overflow-x-auto whitespace-pre text-xs leading-relaxed text-muted-foreground"><code>Your device                         CoinWallet server              Public site
───────────                         ─────────────────              ───────────
Wallet sync (local)
      │
      ▼
Total balance computed ──opt-in──►  display_name + balance_sats ──►  /leaderboard page
      │                               (no addresses / seeds)
      │
      ✕ opt-out ───────────────────►  entry deleted immediately</code></pre>
        <ul class="mt-3 list-inside list-disc space-y-1 text-xs text-muted-foreground">
          <li>Display names are validated (length, charset, no impersonation).</li>
          <li>Balance updates are rate-limited and matched to your synced wallet total.</li>
          <li>Leaderboard GET responses are cached briefly; no authentication required to read ranks.</li>
        </ul>
      </div>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">Swaps (Phase 10)</h2>
      <p class="text-sm leading-relaxed">
        If you use BTC↔XMR swap features, you will see full fee and provider disclosure before
        confirming each swap. Swaps are user-initiated only — nothing runs in the background. Third-party
        swap providers may have their own privacy policies; custodial risk will be clearly labeled.
      </p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">Direct downloads & sideloading</h2>
      <p class="text-sm leading-relaxed">
        CoinWallet is distributed outside app stores as signed desktop builds. Verify SHA-256
        checksums and code signature metadata published in
        <code class="rounded bg-muted px-1 py-0.5 text-xs text-foreground">releases.json</code>
        before installing.
      </p>
    </section>

    <section>
      <h2 class="mb-3 text-lg font-semibold text-foreground">Block explorer data</h2>
      <p class="text-sm leading-relaxed">
        Wallet sync uses public Esplora APIs to read balances and transactions. This exposes your
        wallet addresses to the explorer operator — standard for light clients. Use your own node or
        Tor if you require stronger network privacy.
      </p>
    </section>
  </div>
</main>
