<script lang="ts">
  import '../app.css';
  import SiteHeader from '$lib/components/SiteHeader.svelte';
  import SiteFooter from '$lib/components/SiteFooter.svelte';

  let { children } = $props();
</script>

<div class="flex min-h-dvh flex-col">
  <SiteHeader />
  <div class="flex-1">
    {@render children()}
  </div>
  <SiteFooter />
</div>
