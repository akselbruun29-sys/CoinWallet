<script lang="ts">
  import BrandLogo from './BrandLogo.svelte';

  let mobileOpen = $state(false);

  const links = [
    { href: '/', label: 'Home' },
    { href: '/download', label: 'Download' },
    { href: '/install', label: 'Install' },
    { href: '/leaderboard', label: 'Leaderboard' },
    { href: '/privacy', label: 'Privacy' },
  ];

  function closeMobile() {
    mobileOpen = false;
  }
</script>

<header class="sticky top-0 z-50 border-b border-border/80 bg-background/75 backdrop-blur-md">
  <div class="site-container flex items-center justify-between py-3.5">
    <a href="/" class="rounded-md focus-visible:ring-2 focus-visible:ring-ring" onclick={closeMobile}>
      <BrandLogo size="md" />
    </a>

    <nav class="hidden items-center gap-1 md:flex" aria-label="Main">
      {#each links as link}
        <a href={link.href} class="site-nav-link">
          {link.label}
        </a>
      {/each}
      <a href="/download" class="btn-primary ml-2 !px-4 !text-xs">Get app</a>
    </nav>

    <button
      type="button"
      class="inline-flex size-11 items-center justify-center rounded-lg border border-border text-muted-foreground md:hidden"
      aria-expanded={mobileOpen}
      aria-controls="mobile-nav"
      aria-label={mobileOpen ? 'Close menu' : 'Open menu'}
      onclick={() => (mobileOpen = !mobileOpen)}
    >
      {#if mobileOpen}
        <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M18 6 6 18M6 6l12 12" />
        </svg>
      {:else}
        <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
          <path d="M4 6h16M4 12h16M4 18h16" />
        </svg>
      {/if}
    </button>
  </div>

  {#if mobileOpen}
    <nav
      id="mobile-nav"
      class="border-t border-border bg-background/95 px-6 py-4 md:hidden"
      aria-label="Mobile"
    >
      <ul class="flex flex-col gap-1">
        {#each links as link}
          <li>
            <a
              href={link.href}
              class="site-nav-link block w-full font-medium"
              onclick={closeMobile}
            >
              {link.label}
            </a>
          </li>
        {/each}
        <li class="pt-2">
          <a href="/download" class="btn-primary w-full" onclick={closeMobile}>Download CoinWallet</a>
        </li>
      </ul>
    </nav>
  {/if}
</header>
