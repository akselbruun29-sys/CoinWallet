<script lang="ts">
  let { class: className = '', size = 'md' }: { class?: string; size?: 'sm' | 'md' | 'lg' } = $props();

  const sizes = {
    sm: { box: 'size-7', text: 'text-base', icon: 'size-3.5' },
    md: { box: 'size-9', text: 'text-lg', icon: 'size-4' },
    lg: { box: 'size-11', text: 'text-xl', icon: 'size-5' },
  } as const;
  const s = $derived(sizes[size]);
</script>

<span class="inline-flex items-center gap-2.5 {className}">
  <span
    class="flex {s.box} shrink-0 items-center justify-center rounded-lg border border-success/30 bg-success/10 shadow-[0_0_20px_var(--glow-success)]"
    aria-hidden="true"
  >
    <svg class="{s.icon} text-success" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2">
      <path d="M12 2v4M12 18v4M4.93 4.93l2.83 2.83M16.24 16.24l2.83 2.83M2 12h4M18 12h4M4.93 19.07l2.83-2.83M16.24 7.76l2.83-2.83" />
      <circle cx="12" cy="12" r="4" fill="currentColor" fill-opacity="0.15" />
    </svg>
  </span>
  <span class="{s.text} font-semibold tracking-tight text-foreground">
    Coin<span class="text-success">Wallet</span>
  </span>
</span>
