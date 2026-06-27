<script lang="ts">
  import '../app.css';
  import { page } from '$app/state';
  import SiteHeader from '$lib/components/SiteHeader.svelte';
  import SiteFooter from '$lib/components/SiteFooter.svelte';

  let { children } = $props();
</script>

<div class="flex min-h-dvh flex-col">
  <a
    href="#main-content"
    class="sr-only focus:not-sr-only focus:absolute focus:left-4 focus:top-4 focus:z-[100] focus:rounded-lg focus:bg-primary focus:px-4 focus:py-2 focus:text-sm focus:font-semibold focus:text-primary-foreground"
  >
    Skip to content
  </a>
  <SiteHeader />
  <div id="main-content" class="flex-1" tabindex="-1">
    {#key page.url.pathname}
      <div class="page-enter">
        {@render children()}
      </div>
    {/key}
  </div>
  <SiteFooter />
</div>
