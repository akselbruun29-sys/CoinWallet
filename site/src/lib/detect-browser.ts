export type BrowserId = 'chrome' | 'edge' | 'firefox' | 'safari' | 'opera' | 'unknown';

/** Map user agent to the closest browser family. Order matters (Edge before Chrome). */
export function detectBrowser(userAgent: string): BrowserId {
  const ua = userAgent.toLowerCase();

  if (/edg\//.test(ua)) return 'edge';
  if (/opr\//.test(ua) || /opios/.test(ua)) return 'opera';
  if (/firefox|fxios/.test(ua)) return 'firefox';
  if (/chrome|crios|chromium/.test(ua)) return 'chrome';
  if (/safari/.test(ua)) return 'safari';

  return 'unknown';
}

export function browserLabel(id: BrowserId): string {
  const labels: Record<BrowserId, string> = {
    chrome: 'Chrome',
    edge: 'Edge',
    firefox: 'Firefox',
    safari: 'Safari',
    opera: 'Opera',
    unknown: 'your browser',
  };
  return labels[id];
}

export function isMobileUserAgent(userAgent: string): boolean {
  return /android|iphone|ipad|ipod|mobile|webos|blackberry/i.test(userAgent);
}
