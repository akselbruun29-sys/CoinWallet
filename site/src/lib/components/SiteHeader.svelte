<script lang="ts">
  const links = [
    { href: '/', label: 'Home' },
    { href: '/download', label: 'Download' },
    { href: '/leaderboard', label: 'Leaderboard' },
    { href: '/privacy', label: 'Privacy' },
    { href: '/terms', label: 'Terms' },
  ];
</script>

<header class="border-b border-border bg-background/80 backdrop-blur-sm">
  <div class="mx-auto flex max-w-5xl items-center justify-between px-6 py-4">
    <a href="/" class="text-lg font-semibold tracking-tight text-foreground">
      Coin<span class="text-success">Wallet</span>
    </a>
    <nav class="hidden items-center gap-6 sm:flex" aria-label="Main">
      {#each links as link}
        <a
          href={link.href}
          class="text-sm text-muted-foreground transition-colors hover:text-foreground"
        >
          {link.label}
        </a>
      {/each}
    </nav>
  </div>
</header>
