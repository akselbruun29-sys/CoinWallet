import manifest from '../../../releases/releases.json';

export type ReleasePlatform = {
  url: string;
  sha256: string | null;
  signature: string | null;
  signature_status?: 'signed' | 'unsigned' | string;
  signer_fingerprint: string | null;
  available: boolean;
};

export type ReleaseManifest = {
  version: string;
  released_at: string;
  min_supported_version: string;
  github_repo?: string | null;
  signer_fingerprint: string | null;
  signing_keys_url?: string | null;
  release_notes?: string;
  platforms: {
    windows: ReleasePlatform;
    macos: ReleasePlatform;
  };
};

export const releases = manifest as ReleaseManifest;

export const platformManifestKey: Record<
  'windows' | 'mac',
  keyof ReleaseManifest['platforms']
> = {
  windows: 'windows',
  mac: 'macos',
};

/** Public GitHub Releases index — safe to share with users. */
export function githubReleasesUrl(repo: string, version?: string): string {
  const base = `https://github.com/${repo}/releases`;
  if (!version) {
    return `${base}/latest`;
  }
  const tag = version.startsWith('v') ? version : `v${version}`;
  return `${base}/tag/${tag}`;
}

export function githubRepoUrl(repo: string): string {
  return `https://github.com/${repo}`;
}
