export type PlatformId = 'windows' | 'mac';
export type DetectedOS = PlatformId | 'unknown';

/** Map user agent to the closest download platform. SSR-safe when given an empty UA. */
export function detectOS(userAgent: string): DetectedOS {
  const ua = userAgent.toLowerCase();

  if (/win/.test(ua)) return 'windows';
  if (/mac/.test(ua)) return 'mac';

  return 'unknown';
}

export function platformLabel(id: PlatformId): string {
  const labels: Record<PlatformId, string> = {
    windows: 'Windows',
    mac: 'macOS',
  };
  return labels[id];
}
