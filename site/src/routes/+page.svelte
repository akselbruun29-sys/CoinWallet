<script lang="ts">
  import FeatureCard from '$lib/components/FeatureCard.svelte';

  const features = [
    {
      title: 'Non-custodial',
      description: 'Your keys stay on your device. Encrypted seed storage — we never hold your Bitcoin.',
      icon: 'shield' as const,
    },
    {
      title: 'Direct downloads',
      description: 'Get the app from this site. No App Store, Play Store, or middleman fees.',
      icon: 'download' as const,
    },
    {
      title: 'Every platform',
      description: 'Native desktop apps for Windows and macOS — one wallet, same experience on both.',
      icon: 'desktop' as const,
    },
    {
      title: 'Testnet first',
      description: 'Practice with testnet before mainnet. Switch networks in settings when you are ready.',
      icon: 'flask' as const,
    },
    {
      title: 'Send & receive',
      description: 'Native SegWit addresses, QR codes, fee preview, and broadcast — built in.',
      icon: 'send' as const,
    },
    {
      title: 'Optional leaderboard',
      description: 'Opt in to rank by balance only. No addresses, mnemonics, or transaction history shared.',
      icon: 'trophy' as const,
    },
  ];
</script>

<svelte:head>
  <title>CoinWallet — Non-custodial Bitcoin wallet</title>
  <meta
    name="description"
    content="CoinWallet is a non-custodial Bitcoin wallet for Windows and macOS. Download directly — no app stores."
  />
  <meta property="og:title" content="CoinWallet — Non-custodial Bitcoin wallet" />
  <meta
    property="og:description"
    content="Your keys. Your coins. Direct downloads for Windows and macOS — no app stores."
  />
  <meta property="og:type" content="website" />
  <meta name="twitter:card" content="summary" />
  <meta name="twitter:title" content="CoinWallet" />
  <meta
    name="twitter:description"
    content="Non-custodial Bitcoin wallet. Download for Windows and macOS."
  />
</svelte:head>

<main>
  <section class="relative overflow-hidden border-b border-border/80 mesh-hero">
    <div class="site-container grid items-center gap-12 py-16 lg:grid-cols-2 lg:py-24">
      <div class="text-center lg:text-left">
        <p class="mb-4 inline-flex rounded-full border border-success/30 bg-success/10 px-3 py-1 text-xs font-medium uppercase tracking-wide text-success">
          Non-custodial Bitcoin wallet
        </p>
        <h1 class="mb-5 text-4xl font-bold tracking-tight sm:text-5xl lg:text-6xl">
          Your keys. Your coins. <span class="text-success">No app stores.</span>
        </h1>
        <p class="mb-8 max-w-xl text-lg text-muted-foreground sm:text-xl lg:mx-0 mx-auto">
          CoinWallet runs on Windows and macOS. Download the build for your platform — direct from us,
          with published checksums and optional code signing.
        </p>
        <div class="flex flex-col items-center gap-3 sm:flex-row lg:justify-start">
          <a href="/download" class="btn-primary w-full sm:w-auto">Download CoinWallet</a>
          <a href="/install" class="btn-secondary w-full sm:w-auto">Install guide</a>
        </div>
      </div>

      <div class="relative mx-auto w-full max-w-md lg:max-w-none">
        <div
          class="absolute -inset-4 rounded-2xl bg-success/10 blur-3xl"
          aria-hidden="true"
        ></div>
        <div class="glass-card relative overflow-hidden p-1">
          <div class="flex items-center gap-2 border-b border-border/60 px-4 py-3">
            <span class="size-2.5 rounded-full bg-red-500/80"></span>
            <span class="size-2.5 rounded-full bg-amber-400/80"></span>
            <span class="size-2.5 rounded-full bg-success/80"></span>
            <span class="ml-2 text-xs text-muted-foreground">CoinWallet — Dashboard</span>
          </div>
          <div class="space-y-4 p-5">
            <div class="flex items-center justify-between">
              <span class="text-sm text-muted-foreground">Total balance</span>
              <span class="rounded-md border border-success/30 bg-success/10 px-2 py-0.5 text-xs text-success">testnet</span>
            </div>
            <p class="text-3xl font-bold text-success">0.04200000 BTC</p>
            <div class="grid grid-cols-3 gap-2">
              {#each ['Receive', 'Send', 'Sync'] as action}
                <div class="rounded-lg border border-border/60 bg-background/50 py-2 text-center text-xs text-muted-foreground">
                  {action}
                </div>
              {/each}
            </div>
            <div class="rounded-lg border border-border/60 bg-background/40 p-3">
              <p class="mb-2 text-xs font-medium text-muted-foreground">Recent activity</p>
              <div class="space-y-2">
                <div class="skeleton h-2 w-full"></div>
                <div class="skeleton h-2 w-[80%]"></div>
                <div class="skeleton h-2 w-[60%]"></div>
              </div>
            </div>
          </div>
        </div>
      </div>
    </div>
  </section>

  <section class="site-section site-container">
    <div class="mb-12 text-center">
      <h2 class="page-heading mb-3">Built for privacy and control</h2>
      <p class="page-lead mx-auto max-w-2xl">
        Bitcoin-first, open distribution, and security defaults that treat your seed like it matters —
        because it does.
      </p>
    </div>
    <ul class="grid gap-5 sm:grid-cols-2 lg:grid-cols-3">
      {#each features as feature}
        <FeatureCard title={feature.title} description={feature.description} icon={feature.icon} />
      {/each}
    </ul>
  </section>

  <section class="border-t border-border/80 bg-card/40 site-section">
    <div class="site-container flex flex-col items-center text-center">
      <h2 class="page-heading mb-3">Ready to get started?</h2>
      <p class="page-lead mb-8 max-w-xl">
        Pick your platform on the download page. Verify SHA-256 checksums before you install.
      </p>
      <div class="flex flex-col gap-3 sm:flex-row">
        <a href="/download" class="btn-primary">Go to downloads</a>
        <a href="/leaderboard" class="btn-secondary">View leaderboard</a>
      </div>
    </div>
  </section>
</main>
