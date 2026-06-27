import type { BrowserId } from './detect-browser';
import { browserLabel } from './detect-browser';
import type { DetectedOS } from './detect-os';
import { platformLabel } from './detect-os';

export type ClientEnvironment = {
  os: DetectedOS;
  browser: BrowserId;
  mobile: boolean;
};

export function downloadHint(env: ClientEnvironment): string | null {
  const { os, browser, mobile } = env;

  if (mobile) {
    return 'CoinWallet is a desktop app for Windows and macOS. Open this page on your computer to download the installer.';
  }

  if (os === 'unknown') {
    if (browser === 'unknown') return null;
    return `Using ${browserLabel(browser)}? After you download, check your browser's downloads list to open the installer.`;
  }

  const platform = platformLabel(os);

  switch (browser) {
    case 'chrome':
      return `On ${platform} with Chrome, click Download below — then open the file from the bar at the bottom of the window (or press Ctrl+J / ⌘+J).`;
    case 'edge':
      return `On ${platform} with Edge, click Download below — then open Downloads (Ctrl+J) and run the installer when it finishes.`;
    case 'firefox':
      return `On ${platform} with Firefox, click Download below — then use the downloads arrow in the toolbar to open the file.`;
    case 'safari':
      if (os === 'mac') {
        return 'On macOS with Safari, click Download below — then open the file from the Downloads button in the toolbar. If macOS blocks the app, right-click it → Open.';
      }
      return `On ${platform} with Safari, use the Downloads list in the toolbar to open the installer after it finishes.`;
    case 'opera':
      return `On ${platform} with Opera, open the downloads panel (Ctrl+J) after the file finishes downloading.`;
    default:
      return `On ${platform}, download the build below and open the installer from your browser's downloads folder.`;
  }
}

export function detectionSummary(env: ClientEnvironment): string | null {
  const parts: string[] = [];

  if (env.mobile) {
    parts.push('Mobile device');
  } else if (env.os !== 'unknown') {
    parts.push(platformLabel(env.os));
  }

  if (env.browser !== 'unknown') {
    parts.push(browserLabel(env.browser));
  }

  if (parts.length === 0) return null;
  return parts.join(' · ');
}
