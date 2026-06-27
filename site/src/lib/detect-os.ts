export type PlatformId = 'windows' | 'mac';
export type DetectedOS = PlatformId | 'unknown';

/** Map user agent to the closest download platform. SSR-safe when given an empty UA. */
export function detectOS(userAgent: string): DetectedOS {
  const ua = userAgent.toLowerCase();

  // Mobile first — do not highlight a desktop platform card on phones/tablets.
  if (/iphone|ipad|ipod|android/.test(ua)) return 'unknown';

  if (/windows nt/.test(ua)) return 'windows';
  if (/\bmac os\b/.test(ua)) return 'mac';

  return 'unknown';
}

export function platformLabel(id: PlatformId): string {
  const labels: Record<PlatformId, string> = {
    windows: 'Windows',
    mac: 'macOS',
  };
  return labels[id];
}
