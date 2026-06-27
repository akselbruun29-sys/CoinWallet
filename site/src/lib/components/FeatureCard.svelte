<script lang="ts">
  let {
    title,
    description,
    icon,
  }: {
    title: string;
    description: string;
    icon: 'shield' | 'download' | 'desktop' | 'flask' | 'send' | 'trophy';
  } = $props();
</script>

<li class="glass-card-hover p-6">
  <div
    class="mb-4 flex size-10 items-center justify-center rounded-lg border border-success/25 bg-success/10 text-success"
    aria-hidden="true"
  >
    {#if icon === 'shield'}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M12 22s8-4 8-10V5l-8-3-8 3v7c0 6 8 10 8 10z" />
      </svg>
    {:else if icon === 'download'}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M21 15v4a2 2 0 0 1-2 2H5a2 2 0 0 1-2-2v-4M7 10l5 5 5-5M12 15V3" />
      </svg>
    {:else if icon === 'desktop'}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <rect x="2" y="3" width="20" height="14" rx="2" /><path d="M8 21h8M12 17v4" />
      </svg>
    {:else if icon === 'flask'}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M10 2v6l-4 9a2 2 0 0 0 1.8 2.9h8.4a2 2 0 0 0 1.8-2.9l-4-9V2" /><path d="M8.5 2h7" />
      </svg>
    {:else if icon === 'send'}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M22 2 11 13M22 2l-7 20-4-9-9-4 20-7z" />
      </svg>
    {:else}
      <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
        <path d="M6 9H4.5a2.2 2.2 0 0 1 0-4H6M18 9h1.5a2.2 2.2 0 0 0 0-4H18M4 22h16M10 14.66V17c0 .55-.47.98-.97 1.21C7.85 18.75 7 20 7 22M14 14.66V17c0 .55.47.98.97 1.21C16.15 18.75 17 20 17 22M12 14h.01M7 2h10v7a5 5 0 0 1-10 0V2z" />
      </svg>
    {/if}
  </div>
  <h3 class="mb-2 font-semibold text-foreground">{title}</h3>
  <p class="text-sm leading-relaxed text-muted-foreground">{description}</p>
</li>
