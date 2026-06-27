<script lang="ts">
  import { onMount } from 'svelte';
  import { detectOS, platformLabel, type DetectedOS, type PlatformId } from '$lib/detect-os';
  import { releases, platformManifestKey } from '$lib/releases';

  let detectedOS = $state<DetectedOS>('unknown');

  onMount(() => {
    detectedOS = detectOS(navigator.userAgent);
  });

  const platforms: {
    id: PlatformId;
    name: string;
    note: string;
    sideload?: boolean;
  }[] = [
    {
      id: 'windows',
      name: 'Windows',
      note: 'Run the installer or portable executable. Requires Windows 10 or later, 64-bit.',
    },
    {
      id: 'mac',
      name: 'macOS',
      note: 'Open the disk image and move CoinWallet to Applications. If macOS blocks the app, use Right-click → Open or allow it under System Settings → Privacy & Security.',
    },
    {
      id: 'iphone',
      name: 'iOS',
      note: 'Install via sideloading (AltStore, Sideloadly, or equivalent). Distributed directly — not available on the App Store.',
      sideload: true,
    },
    {
      id: 'android',
      name: 'Android',
      note: 'Enable installation from unknown sources for your browser or file manager, then open the APK package.',
    },
  ];

  function fileName(url: string): string {
    return url.split('/').pop() ?? url;
  }
</script>

<svelte:head>
  <title>Download — CoinWallet</title>
  <meta
    name="description"
    content="Download CoinWallet for Windows, macOS, iOS, and Android. Direct downloads with checksums — no app stores."
  />
</svelte:head>

<main class="mx-auto max-w-5xl px-6 py-16 sm:py-20">
  <div class="mb-12 text-center">
    <h1 class="mb-3 text-3xl font-bold tracking-tight sm:text-4xl">Download CoinWallet</h1>
    <p class="mx-auto max-w-2xl text-muted-foreground">
      Version {releases.version} · All releases are distributed directly from this site with
      published checksums.
    </p>
    {#if detectedOS !== 'unknown'}
      <p class="mt-4 text-sm text-primary">
        Detected {platformLabel(detectedOS)} — your platform is highlighted below.
      </p>
    {/if}
  </div>

  <ul class="grid gap-6 sm:grid-cols-2">
    {#each platforms as platform}
      {@const manifestKey = platformManifestKey[platform.id]}
      {@const entry = releases.platforms[manifestKey]}
      {@const isDetected = detectedOS === platform.id}
      {@const available = entry.available}
      <li
        class="flex flex-col rounded-xl border bg-card p-6 transition-colors {isDetected
          ? 'border-primary ring-1 ring-primary/30'
          : 'border-border'}"
      >
        <div class="mb-4 flex items-start justify-between gap-3">
          <div class="flex items-center gap-4">
            <div
              class="flex size-11 shrink-0 items-center justify-center rounded-lg border border-border bg-background text-muted-foreground"
              aria-hidden="true"
            >
              {#if platform.id === 'windows'}
                <svg class="size-5" viewBox="0 0 24 24" fill="currentColor">
                  <path d="M3 5.5L10.5 4.2v7.1H3V5.5zm0 13V12.8h7.5v7.1L3 18.5zM11.3 4.1L21 2.5v9.4h-9.7V4.1zm0 17.4V12.8H21V22l-9.7-1.5z" />
                </svg>
              {:else if platform.id === 'mac'}
                <svg class="size-5" viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M18.71 19.5c-.83 1.24-1.71 2.45-3.08 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"
                  />
                </svg>
              {:else if platform.id === 'iphone'}
                <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                  <rect x="7" y="2" width="10" height="20" rx="2" />
                  <path d="M11 5h2" stroke-linecap="round" />
                </svg>
              {:else}
                <svg class="size-5" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.75">
                  <rect x="6" y="3" width="12" height="18" rx="2" />
                  <path d="M10 18h4" stroke-linecap="round" />
                </svg>
              {/if}
            </div>
            <div>
              <h2 class="text-lg font-semibold tracking-tight">{platform.name}</h2>
              <p class="font-mono text-xs text-muted-foreground">{fileName(entry.url)}</p>
            </div>
          </div>
          <div class="flex shrink-0 flex-col items-end gap-1.5">
            {#if isDetected}
              <span
                class="rounded-md border border-primary/40 bg-primary/10 px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-primary"
              >
                Your platform
              </span>
            {/if}
            {#if !available}
              <span
                class="rounded-md border border-border bg-secondary px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-muted-foreground"
              >
                Coming soon
              </span>
            {/if}
          </div>
        </div>

        <p class="mb-4 flex-1 text-sm leading-relaxed text-muted-foreground">{platform.note}</p>

        {#if entry.sha256}
          <p class="mb-4 break-all font-mono text-xs text-muted-foreground">
            SHA-256: {entry.sha256}
          </p>
        {/if}

        <div class="space-y-3">
          {#if available}
            <a
              href={entry.url}
              class="flex h-10 w-full items-center justify-center rounded-lg bg-primary text-sm font-semibold text-primary-foreground transition-opacity hover:opacity-90"
            >
              Download for {platform.name}
            </a>
          {:else}
            <span
              class="flex h-10 w-full cursor-not-allowed items-center justify-center rounded-lg border border-border bg-muted text-sm font-medium text-muted-foreground"
              aria-disabled="true"
            >
              Download for {platform.name}
            </span>
          {/if}
          {#if platform.sideload}
            <p class="text-center text-xs text-muted-foreground">
              Sideload instructions will ship with the first release.
            </p>
          {/if}
        </div>
      </li>
    {/each}
  </ul>

  <p class="mt-10 text-center text-sm text-muted-foreground">
    Verify downloads with the published SHA-256 checksum before installing.
  </p>
</main>
