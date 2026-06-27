<script lang="ts">
  import { onMount } from 'svelte';
  import { detectOS, platformLabel, type PlatformId } from '$lib/detect-os';
  import { installGuides, type InstallPlatform } from '$lib/install-guides';

  let detectedOS = $state<PlatformId | 'unknown'>('unknown');
  let active = $state<InstallPlatform>('windows');

  onMount(() => {
    const os = detectOS(navigator.userAgent);
    detectedOS = os === 'unknown' ? 'unknown' : os;
    if (os === 'windows' || os === 'mac') active = os;

    const param = new URLSearchParams(window.location.search).get('platform');
    if (param === 'windows' || param === 'mac') active = param;
  });

  function selectPlatform(id: InstallPlatform) {
    active = id;
    history.replaceState({}, '', `/install?platform=${id}`);
  }
</script>

<svelte:head>
  <title>Install — CoinWallet</title>
  <meta
    name="description"
    content="Step-by-step install guides for CoinWallet on Windows and macOS, including checksum verification."
  />
</svelte:head>

<main class="mx-auto max-w-3xl px-6 py-16 sm:py-20">
  <div class="mb-10">
    <p class="mb-2 text-sm text-muted-foreground">
      <a href="/download" class="text-success hover:underline">← Download</a>
    </p>
    <h1 class="mb-3 text-3xl font-bold tracking-tight sm:text-4xl">Installation guide</h1>
    <p class="text-muted-foreground">
      Direct desktop installs for Windows and macOS — no app stores. Always verify SHA-256 checksums
      from the <a href="/download" class="text-success hover:underline">Download page</a> before
      running a build.
    </p>
    {#if detectedOS !== 'unknown'}
      <p class="mt-3 text-sm text-success">Detected {platformLabel(detectedOS)}.</p>
    {/if}
  </div>

  <div class="mb-8 flex flex-wrap gap-2" role="tablist" aria-label="Platform">
    {#each installGuides as guide (guide.id)}
      <button
        type="button"
        role="tab"
        aria-selected={active === guide.id}
        class="rounded-lg border px-4 py-2 text-sm font-medium transition-colors {active === guide.id
          ? 'border-success bg-success/10 text-success'
          : 'border-border text-muted-foreground hover:text-foreground'}"
        onclick={() => selectPlatform(guide.id)}
      >
        {guide.title}
      </button>
    {/each}
  </div>

  {#each installGuides as guide (guide.id)}
    {#if active === guide.id}
      <article id={guide.id} class="space-y-8">
        <section class="rounded-xl border border-border bg-card p-6">
          <h2 class="mb-1 text-xl font-semibold">{guide.title}</h2>
          <p class="font-mono text-xs text-muted-foreground">{guide.artifact}</p>
          <h3 class="mb-2 mt-4 text-sm font-medium text-foreground">Requirements</h3>
          <ul class="list-inside list-disc space-y-1 text-sm text-muted-foreground">
            {#each guide.requirements as req}
              <li>{req}</li>
            {/each}
          </ul>
        </section>

        <section>
          <h3 class="mb-4 text-lg font-semibold">Steps</h3>
          <ol class="space-y-4">
            {#each guide.steps as step, i}
              <li class="rounded-xl border border-border bg-card p-5">
                <p class="mb-1 text-xs font-medium uppercase tracking-wide text-success">
                  Step {i + 1}
                </p>
                <h4 class="mb-2 font-medium">{step.title}</h4>
                <p class="text-sm leading-relaxed text-muted-foreground">{step.body}</p>
              </li>
            {/each}
          </ol>
        </section>

        <section class="rounded-xl border border-border bg-card p-6">
          <h3 class="mb-2 text-lg font-semibold">Verify checksum</h3>
          <p class="mb-3 text-sm text-muted-foreground">
            Compare output with SHA-256 on the
            <a href="/download" class="text-success hover:underline">Download page</a>.
          </p>
          <p class="mb-2 text-xs font-medium text-muted-foreground">{guide.verifyChecksum.label}</p>
          <pre
            class="overflow-x-auto rounded-lg border border-border bg-background p-4 font-mono text-xs text-foreground"
          ><code>{guide.verifyChecksum.command}</code></pre>
        </section>

        {#if guide.verifySignature}
          <section class="rounded-xl border border-border bg-card p-6">
            <h3 class="mb-2 text-lg font-semibold">Verify signature</h3>
            <p class="mb-3 text-sm text-muted-foreground">{guide.verifySignature.note}</p>
            <p class="mb-2 text-xs font-medium text-muted-foreground">{guide.verifySignature.label}</p>
            <pre
              class="overflow-x-auto rounded-lg border border-border bg-background p-4 font-mono text-xs text-foreground"
            ><code>{guide.verifySignature.command}</code></pre>
          </section>
        {/if}

        <section>
          <h3 class="mb-4 text-lg font-semibold">Troubleshooting</h3>
          <div class="space-y-3">
            {#each guide.troubleshooting as item}
              <details class="group rounded-xl border border-border bg-card px-5 py-4">
                <summary class="cursor-pointer font-medium marker:content-none group-open:mb-2">
                  {item.title}
                </summary>
                <p class="text-sm leading-relaxed text-muted-foreground">{item.body}</p>
              </details>
            {/each}
          </div>
        </section>
      </article>
    {/if}
  {/each}

  <p class="mt-12 text-center text-sm text-muted-foreground">
    Need the binary?
    <a href="/download" class="text-success hover:underline">Go to Download</a>
  </p>
</main>
