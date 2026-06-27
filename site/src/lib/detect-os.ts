export type PlatformId = 'windows' | 'mac';
export type DetectedOS = PlatformId | 'unknown';

export type DetectOsHints = {
  maxTouchPoints?: number;
  platform?: string;
};

/** iPadOS "Request Desktop Website" — UA looks like Mac without "ipad". */
export function isIPadDesktopUserAgent(
  userAgent: string,
  hints: DetectOsHints = {}
): boolean {
  const ua = userAgent.toLowerCase();
  if (/iphone|ipad|ipod|android/.test(ua)) return false;

  const maxTouch = hints.maxTouchPoints ?? 0;
  const platform = hints.platform ?? '';
  return platform === 'MacIntel' && maxTouch > 1;
}

/** Map user agent to the closest download platform. SSR-safe when given an empty UA. */
export function detectOS(userAgent: string, hints: DetectOsHints = {}): DetectedOS {
  const ua = userAgent.toLowerCase();

  // Mobile first — do not highlight a desktop platform card on phones/tablets.
  if (/iphone|ipad|ipod|android/.test(ua)) return 'unknown';

  // iPad desktop mode pretends to be macOS.
  if (isIPadDesktopUserAgent(userAgent, hints)) return 'unknown';

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
