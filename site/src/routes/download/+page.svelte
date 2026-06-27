<script lang="ts">
  import { onMount } from 'svelte';
  import { detectBrowser, browserLabel, isMobileUserAgent } from '$lib/detect-browser';
  import { detectionSummary, downloadHint, type ClientEnvironment } from '$lib/download-hints';
  import { detectOS, isIPadDesktopUserAgent, platformLabel, type PlatformId } from '$lib/detect-os';
  import { releases, platformManifestKey } from '$lib/releases';

  let env = $state<ClientEnvironment>({
    os: 'unknown',
    browser: 'unknown',
    mobile: false,
  });

  onMount(() => {
    const ua = navigator.userAgent;
    const hints = { maxTouchPoints: navigator.maxTouchPoints, platform: navigator.platform };
    const ipadDesktop = isIPadDesktopUserAgent(ua, hints);
    env = {
      os: detectOS(ua, hints),
      browser: detectBrowser(ua),
      mobile: isMobileUserAgent(ua) || ipadDesktop,
    };
  });

  const summary = $derived(detectionSummary(env));
  const hint = $derived(downloadHint(env));
  const detectedOS = $derived(env.os);

  const platforms: {
    id: PlatformId;
    name: string;
    note: string;
  }[] = [
    {
      id: 'windows',
      name: 'Windows',
      note: 'Run the Windows installer (setup wizard), not a raw portable binary. Requires Windows 10 or later, 64-bit.',
    },
    {
      id: 'mac',
      name: 'macOS',
      note: 'Open the disk image and move CoinWallet to Applications. If macOS blocks the app, use Right-click → Open or allow it under System Settings → Privacy & Security.',
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
    content="Download CoinWallet for Windows and macOS. Direct downloads with checksums — no app stores."
  />
</svelte:head>

<main class="mx-auto max-w-5xl px-6 py-16 sm:py-20">
  <div class="mb-12 text-center">
    <h1 class="mb-3 text-3xl font-bold tracking-tight sm:text-4xl">Download CoinWallet</h1>
    <p class="mx-auto max-w-2xl text-muted-foreground">
      Version {releases.version} · Desktop builds for Windows and macOS, distributed directly from
      this site with published checksums.
    </p>
    {#if summary}
      <p class="mt-4 text-sm text-success">
        Detected {summary}{#if !env.mobile && detectedOS !== 'unknown'} — your platform is highlighted below{/if}.
      </p>
    {/if}
  </div>

  {#if hint}
    <div
      class="mx-auto mb-10 max-w-3xl rounded-xl border border-border bg-card px-5 py-4 text-sm leading-relaxed text-muted-foreground {env.mobile
        ? 'border-muted-foreground/30 bg-muted/40'
        : ''}"
      role="note"
    >
      {#if env.mobile}
        <p class="mb-1 font-medium text-foreground">Desktop download required</p>
      {:else if env.browser !== 'unknown'}
        <p class="mb-1 font-medium text-foreground">
          Tip for {browserLabel(env.browser)}{#if detectedOS !== 'unknown'} on {platformLabel(detectedOS)}{/if}
        </p>
      {:else}
        <p class="mb-1 font-medium text-foreground">Download tip</p>
      {/if}
      <p>{hint}</p>
    </div>
  {/if}

  <ul class="mx-auto grid max-w-3xl gap-6 sm:grid-cols-2">
    {#each platforms as platform}
      {@const manifestKey = platformManifestKey[platform.id]}
      {@const entry = releases.platforms[manifestKey]}
      {@const isDetected = !env.mobile && detectedOS === platform.id}
      {@const available = entry.available}
      <li
        class="flex flex-col rounded-xl border bg-card p-6 transition-colors {isDetected
          ? 'border-success ring-1 ring-success/30'
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
              {:else}
                <svg class="size-5" viewBox="0 0 24 24" fill="currentColor">
                  <path
                    d="M18.71 19.5c-.83 1.24-1.71 2.45-3.08 2.47-1.34.03-1.77-.79-3.29-.79-1.53 0-2 .77-3.27.82-1.31.05-2.3-1.32-3.14-2.53C4.25 17 2.94 12.45 4.7 9.39c.87-1.52 2.43-2.48 4.12-2.51 1.28-.02 2.5.87 3.29.87.78 0 2.26-1.07 3.8-.91.65.03 2.47.26 3.64 1.98-.09.06-2.17 1.28-2.15 3.81.03 3.02 2.65 4.03 2.68 4.04-.03.07-.42 1.44-1.38 2.83M13 3.5c.73-.83 1.94-1.46 2.94-1.5.13 1.17-.34 2.35-1.04 3.19-.69.85-1.83 1.51-2.95 1.42-.15-1.15.41-2.35 1.05-3.11z"
                  />
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
                class="rounded-md border border-success/40 bg-success/10 px-2 py-1 text-[11px] font-medium uppercase tracking-wide text-success"
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
          <p class="mb-2 break-all font-mono text-xs text-muted-foreground">
            SHA-256: {entry.sha256}
          </p>
        {/if}
        {#if entry.signature_status}
          <p class="mb-4 text-xs text-muted-foreground">
            Signature:
            <span class={entry.signature_status === 'signed' ? 'text-success' : ''}>
              {entry.signature_status}
            </span>
            {#if entry.signer_fingerprint}
              · Fingerprint: <span class="font-mono">{entry.signer_fingerprint}</span>
            {/if}
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
            <a
              href="/install?platform={platform.id}"
              class="flex h-10 w-full items-center justify-center rounded-lg border border-border text-sm font-medium text-muted-foreground transition-colors hover:border-success/40 hover:text-foreground"
            >
              Installation guide
            </a>
          {:else}
            <span
              class="flex h-10 w-full cursor-not-allowed items-center justify-center rounded-lg border border-border bg-muted text-sm font-medium text-muted-foreground"
              aria-disabled="true"
            >
              Download for {platform.name}
            </span>
            <a
              href="/install?platform={platform.id}"
              class="flex h-10 w-full items-center justify-center rounded-lg border border-border text-sm font-medium text-muted-foreground transition-colors hover:border-success/40 hover:text-foreground"
            >
              Installation guide
            </a>
          {/if}
        </div>
      </li>
    {/each}
  </ul>

  <p class="mt-10 text-center text-sm text-muted-foreground">
    Verify downloads with the published SHA-256 checksum before installing. Compare code-signing
    fingerprints for signed builds.
    <a href="/install" class="text-success hover:underline">Full installation guide</a>
  </p>
  {#if releases.signer_fingerprint}
    <p class="mt-3 text-center font-mono text-xs text-muted-foreground">
      Publisher fingerprint: {releases.signer_fingerprint}
    </p>
  {/if}
</main>
