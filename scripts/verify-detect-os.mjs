#!/usr/bin/env node
/** Verify download-site OS/browser detection against real UA samples (Phase 14.3). */
import { detectBrowser, isMobileUserAgent } from '../site/src/lib/detect-browser.ts';
import { detectOS, isIPadDesktopUserAgent } from '../site/src/lib/detect-os.ts';

const cases = [
  {
    name: 'Windows 11 Chrome',
    ua: 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
    hints: { maxTouchPoints: 0, platform: 'Win32' },
    expect: { os: 'windows', mobile: false, browser: 'chrome' },
  },
  {
    name: 'macOS Safari',
    ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Safari/605.1.15',
    hints: { maxTouchPoints: 0, platform: 'MacIntel' },
    expect: { os: 'mac', mobile: false, browser: 'safari' },
  },
  {
    name: 'iPhone Safari',
    ua: 'Mozilla/5.0 (iPhone; CPU iPhone OS 17_2 like Mac OS X) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.2 Mobile/15E148 Safari/604.1',
    hints: { maxTouchPoints: 5, platform: 'iPhone' },
    expect: { os: 'unknown', mobile: true, browser: 'safari' },
  },
  {
    name: 'iPad desktop mode (MacIntel + touch)',
    ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/17.0 Safari/605.1.15',
    hints: { maxTouchPoints: 5, platform: 'MacIntel' },
    expect: { os: 'unknown', mobile: true, ipadDesktop: true, browser: 'safari' },
  },
  {
    name: 'Darwin WebView (must not match Windows)',
    ua: 'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Electron/13.1.7 Safari/537.36',
    hints: { maxTouchPoints: 0, platform: 'MacIntel' },
    expect: { os: 'mac', mobile: false, browser: 'chrome' },
  },
  {
    name: 'Linux Firefox',
    ua: 'Mozilla/5.0 (X11; Linux x86_64; rv:121.0) Gecko/20100101 Firefox/121.0',
    hints: { maxTouchPoints: 0, platform: 'Linux x86_64' },
    expect: { os: 'unknown', mobile: false, browser: 'firefox' },
  },
];

let failed = 0;

for (const sample of cases) {
  const { ua, hints, expect, name } = sample;
  const os = detectOS(ua, hints);
  const browser = detectBrowser(ua);
  const mobile = isMobileUserAgent(ua);
  const ipadDesktop = isIPadDesktopUserAgent(ua, hints);
  const mobileLike = mobile || ipadDesktop;

  const checks = [
    ['os', os, expect.os],
    ['browser', browser, expect.browser],
  ];

  if (expect.mobile !== undefined) {
    checks.push(['mobileLike', mobileLike, expect.mobile]);
  }
  if (expect.ipadDesktop !== undefined) {
    checks.push(['ipadDesktop', ipadDesktop, expect.ipadDesktop]);
  }

  for (const [label, got, want] of checks) {
    if (got !== want) {
      console.error(`FAIL ${name}: ${label} expected ${want}, got ${got}`);
      failed++;
    }
  }
}

if (failed > 0) {
  console.error(`\n${failed} assertion(s) failed`);
  process.exit(1);
}

console.log(`OK — ${cases.length} UA samples passed`);
process.exit(0);
