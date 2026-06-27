<script lang="ts">
  import { githubReleasesUrl, githubRepoUrl, releases } from '$lib/releases';

  const githubRepo = releases.github_repo ?? null;
  const githubReleasePage = githubRepo ? githubReleasesUrl(githubRepo, releases.version) : null;
</script>

<footer class="mt-auto border-t border-border/80 bg-card/30">
  <div class="site-container grid gap-10 py-12 sm:grid-cols-2 lg:grid-cols-4">
    <div class="sm:col-span-2 lg:col-span-1">
      <p class="mb-2 font-semibold text-foreground">CoinWallet</p>
      <p class="max-w-xs text-sm leading-relaxed text-muted-foreground">
        Non-custodial Bitcoin wallet for Windows and macOS. Direct downloads — no app stores.
      </p>
    </div>
    <div>
      <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Product</p>
      <ul class="space-y-2 text-sm">
        <li><a href="/download" class="text-muted-foreground hover:text-success">Download</a></li>
        <li><a href="/install" class="text-muted-foreground hover:text-success">Install guide</a></li>
        <li><a href="/leaderboard" class="text-muted-foreground hover:text-success">Leaderboard</a></li>
        {#if githubReleasePage}
          <li>
            <a
              href={githubReleasePage}
              class="text-muted-foreground hover:text-success"
              rel="noopener noreferrer"
              target="_blank"
            >
              GitHub Releases
            </a>
          </li>
        {/if}
        {#if githubRepo}
          <li>
            <a
              href={githubRepoUrl(githubRepo)}
              class="text-muted-foreground hover:text-success"
              rel="noopener noreferrer"
              target="_blank"
            >
              Source code
            </a>
          </li>
        {/if}
      </ul>
    </div>
    <div>
      <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Legal</p>
      <ul class="space-y-2 text-sm">
        <li><a href="/privacy" class="text-muted-foreground hover:text-success">Privacy</a></li>
        <li><a href="/terms" class="text-muted-foreground hover:text-success">Terms</a></li>
      </ul>
    </div>
    <div>
      <p class="mb-3 text-xs font-semibold uppercase tracking-wider text-muted-foreground">Security</p>
      <ul class="space-y-2 text-sm text-muted-foreground">
        <li>Keys stay on your device</li>
        <li>Signed builds + SHA-256</li>
        <li>Testnet default</li>
      </ul>
    </div>
  </div>
  <div class="border-t border-border/60 py-6 text-center text-xs text-muted-foreground">
    © {new Date().getFullYear()} CoinWallet · Non-custodial · Not financial advice
  </div>
</footer>
