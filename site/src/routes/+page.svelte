<script lang="ts">
  const features = [
    {
      title: 'Non-custodial',
      description: 'Your keys stay on your device. Encrypted seed storage — we never hold your Bitcoin.',
    },
    {
      title: 'Direct downloads',
      description: 'Get the app from this site. No App Store, Play Store, or middleman fees.',
    },
    {
      title: 'Every platform',
      description: 'Native desktop apps for Windows and macOS — one wallet, same experience on both.',
    },
    {
      title: 'Testnet first',
      description: 'Practice with testnet before mainnet. Switch networks in settings when you are ready.',
    },
    {
      title: 'Send & receive',
      description: 'Native SegWit addresses, QR codes, fee preview, and broadcast — built in.',
    },
    {
      title: 'Optional leaderboard',
      description: 'Opt in to rank by balance only. No addresses, mnemonics, or transaction history shared.',
    },
  ];
</script>

<svelte:head>
  <title>CoinWallet — Non-custodial Bitcoin wallet</title>
  <meta
    name="description"
    content="CoinWallet is a non-custodial Bitcoin wallet for Windows and macOS. Download directly — no app stores."
  />
</svelte:head>

<main>
  <!-- Hero -->
  <section class="relative overflow-hidden border-b border-border">
    <div
      class="pointer-events-none absolute inset-0 bg-[radial-gradient(ellipse_80%_60%_at_50%_-20%,oklch(0.72_0.17_145/0.15),transparent)]"
      aria-hidden="true"
    ></div>
    <div class="relative mx-auto flex max-w-5xl flex-col items-center px-6 py-20 text-center sm:py-28">
      <p class="mb-4 text-sm font-medium tracking-wide text-muted-foreground uppercase">Non-custodial Bitcoin wallet</p>
      <h1 class="mb-5 max-w-3xl text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
        Your keys. Your coins. <span class="text-success">No app stores.</span>
      </h1>
      <p class="mb-10 max-w-2xl text-lg text-muted-foreground sm:text-xl">
        CoinWallet runs on Windows and macOS. Download the build for your platform — direct from
        us, no store fees.
      </p>
      <div class="flex flex-col items-center gap-4 sm:flex-row">
        <a
          href="/download"
          class="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-8 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
        >
          Download CoinWallet
        </a>
        <a
          href="/leaderboard"
          class="inline-flex h-11 items-center justify-center rounded-lg border border-border bg-card px-8 text-sm font-semibold text-foreground transition-colors hover:bg-accent"
        >
          View leaderboard
        </a>
      </div>
    </div>
  </section>

  <!-- Features -->
  <section class="mx-auto max-w-5xl px-6 py-16 sm:py-20">
    <div class="mb-12 text-center">
      <h2 class="mb-3 text-2xl font-bold tracking-tight sm:text-3xl">Built for privacy and control</h2>
      <p class="mx-auto max-w-2xl text-muted-foreground">
        Bitcoin-first, open distribution, and security defaults that treat your seed like it matters —
        because it does.
      </p>
    </div>
    <ul class="grid gap-6 sm:grid-cols-2 lg:grid-cols-3">
      {#each features as feature}
        <li
          class="rounded-xl border border-border bg-card p-6 transition-colors hover:border-muted-foreground/30 hover:bg-accent/50"
        >
          <h3 class="mb-2 font-semibold text-foreground">{feature.title}</h3>
          <p class="text-sm leading-relaxed text-muted-foreground">{feature.description}</p>
        </li>
      {/each}
    </ul>
  </section>

  <!-- Bottom CTA -->
  <section class="border-t border-border bg-card/50">
    <div class="mx-auto flex max-w-5xl flex-col items-center px-6 py-16 text-center">
      <h2 class="mb-3 text-2xl font-bold tracking-tight">Ready to get started?</h2>
      <p class="mb-8 max-w-xl text-muted-foreground">
        Pick your platform on the download page. Builds are signed with checksums for verification.
      </p>
      <a
        href="/download"
        class="inline-flex h-11 items-center justify-center rounded-lg bg-primary px-8 text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
      >
        Go to downloads
      </a>
    </div>
  </section>
</main>
