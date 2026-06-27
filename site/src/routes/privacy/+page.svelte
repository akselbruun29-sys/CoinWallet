<script lang="ts">
  const sections = [
    { id: 'non-custodial', title: 'Non-custodial' },
    { id: 'on-device', title: 'On your device' },
    { id: 'leaderboard', title: 'Leaderboard' },
    { id: 'swaps', title: 'Swaps' },
    { id: 'network', title: 'Network sync' },
    { id: 'advisor', title: 'Advisor AI' },
    { id: 'downloads', title: 'Downloads' },
    { id: 'changes', title: 'Updates' },
  ] as const;
</script>

<svelte:head>
  <title>Privacy — CoinWallet</title>
  <meta
    name="description"
    content="How CoinWallet handles your keys, leaderboard opt-in, swaps, and network sync. Non-custodial Bitcoin and Monero wallet."
  />
</svelte:head>

<main class="site-section site-container">
  <div class="lg:grid lg:grid-cols-[12rem_1fr] lg:gap-10">
    <aside class="mb-8 lg:mb-0">
      <p class="mb-4 text-sm text-muted-foreground">
        <a href="/" class="text-success hover:underline">← Home</a>
      </p>
      <nav class="glass-card sticky top-20 p-4" aria-label="On this page">
        <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">
          On this page
        </p>
        <ul class="space-y-1">
          {#each sections as section (section.id)}
            <li>
              <a
                href="#{section.id}"
                class="block rounded-md px-2 py-2 text-sm text-muted-foreground transition-colors hover:bg-success/5 hover:text-success"
              >
                {section.title}
              </a>
            </li>
          {/each}
        </ul>
      </nav>
    </aside>

    <div class="max-w-3xl">
      <h1 class="page-heading mb-3">Privacy Policy</h1>
      <p class="page-lead mb-8">
        CoinWallet is built to keep signing keys on your device. This page explains what stays local,
        what you can opt into, and what third parties may see when you sync or swap.
      </p>

      <div class="prose-page">
        <section id="non-custodial">
          <h2>Non-custodial by design</h2>
          <p>
            CoinWallet is a non-custodial wallet. Your seed phrase and private keys are generated and
            stored on your device, encrypted at rest when <code class="rounded bg-muted px-1 py-0.5 text-xs text-foreground">WALLET_DB_KEY</code>
            is configured. We do not have access to your funds, mnemonics, or signing keys.
          </p>
        </section>

        <section id="on-device">
          <h2>What stays on your device</h2>
          <ul class="list-inside list-disc space-y-2">
            <li>Seed phrases, passphrases, and encrypted wallet databases</li>
            <li>Bitcoin UTXO metadata, labels, coin-control flags, and privacy scores</li>
            <li>Monero view keys (encrypted) and subaddress labels for XMR wallets</li>
            <li>Settings, session tokens, and swap history you confirm locally</li>
          </ul>
          <p class="mt-4">
            The desktop app binds its API to localhost only. Unlocking the wallet clears sensitive
            material from memory when you lock the app or after an idle timeout.
          </p>
        </section>

        <section id="leaderboard">
          <h2>Leaderboard (opt-in only)</h2>
          <p>
            The public leaderboard is <strong class="font-medium text-foreground">disabled by default</strong>.
            If you opt in from Settings, only your chosen display name and total balance (in satoshis)
            are sent to the server. We never upload addresses, mnemonics, UTXOs, or transaction history
            for leaderboard purposes. Opt out at any time — your entry is removed immediately.
          </p>
          <div class="glass-card p-4">
            <p class="mb-3 font-medium text-foreground">Leaderboard data flow</p>
            <pre
              class="overflow-x-auto whitespace-pre text-xs leading-relaxed text-muted-foreground"
            ><code>Your device                         CoinWallet server              Public site
───────────                         ─────────────────              ───────────
Wallet sync (local)
      │
      ▼
Total balance computed ──opt-in──►  display_name + balance_sats ──►  /leaderboard page
      │                               (no addresses / seeds)
      │
      ✕ opt-out ───────────────────►  entry deleted immediately</code></pre>
            <ul class="mt-3 list-inside list-disc space-y-1 text-xs">
              <li>Display names are validated (length, charset, no impersonation).</li>
              <li>Balance updates are rate-limited and matched to your synced wallet total.</li>
              <li>Leaderboard reads are cached briefly; no authentication required to view ranks.</li>
            </ul>
          </div>
        </section>

        <section id="swaps">
          <h2>BTC ↔ XMR swaps</h2>
          <p>
            Swaps are user-initiated only — nothing runs in the background. Before you confirm, the app
            shows fees, provider name, and custodial risk labels. Only providers on the built-in
            allowlist can be used; the client cannot point swaps at arbitrary URLs.
          </p>
          <p>
            Third-party swap providers operate under their own privacy policies. Using a swap temporarily
            involves those providers and may link on-chain activity across assets.
          </p>
        </section>

        <section id="network">
          <h2>Network sync &amp; block explorers</h2>
          <p>
            Bitcoin sync uses public Esplora APIs to read balances and transactions. That exposes your
            wallet addresses to the explorer operator — standard for light clients. Monero sync talks to
            a local or configured <code class="rounded bg-muted px-1 py-0.5 text-xs text-foreground">monero-wallet-rpc</code>
            instance; your spend key never leaves the wallet process.
          </p>
          <p>
            For stronger network privacy, run your own node, point Esplora to it, or route traffic over
            Tor from Settings.
          </p>
        </section>

        <section id="advisor">
          <h2>Advisor AI</h2>
          <p>
            Advisor tips are generated locally from your wallet state using rule-based templates — no
            cloud LLM by default. Optional cloud hints require an explicit server URL in your build
            config; keys and seeds are never sent. Privacy scores on the in-app Privacy tab use the same
            local UTXO analysis.
          </p>
        </section>

        <section id="downloads">
          <h2>Direct downloads &amp; sideloading</h2>
          <p>
            CoinWallet is distributed outside app stores as signed desktop builds. Verify SHA-256
            checksums and signature metadata published in
            <code class="rounded bg-muted px-1 py-0.5 text-xs text-foreground">releases.json</code>
            on the <a href="/download" class="text-success hover:underline">Download page</a> before
            installing. Large Windows installers may be hosted on GitHub Releases instead of this site.
          </p>
        </section>

        <section id="changes">
          <h2>Policy updates</h2>
          <p>
            This policy may change when the software is updated. Continued use after an update constitutes
            acceptance of the revised policy published here. Last updated June 2026.
          </p>
          <p>
            Questions? See also our <a href="/terms" class="text-success hover:underline">Terms of Use</a>.
          </p>
        </section>
      </div>
    </div>
  </div>
</main>
