export type InstallPlatform = 'windows' | 'mac';

export type InstallGuide = {
  id: InstallPlatform;
  title: string;
  artifact: string;
  requirements: string[];
  steps: { title: string; body: string }[];
  verifyChecksum: { label: string; command: string };
  verifySignature?: { label: string; command: string; note: string };
  troubleshooting: { title: string; body: string }[];
};

export const installGuides: InstallGuide[] = [
  {
    id: 'windows',
    title: 'Windows',
    artifact: 'coinwallet-windows-x64-setup.exe',
    requirements: [
      'Windows 10 or later (64-bit)',
      'About 200 MB free disk space',
      'Local network access to 127.0.0.1 (desktop API sidecar)'
    ],
    steps: [
      {
        title: 'Download the installer',
        body: 'Get coinwallet-windows-x64-setup.exe from the Download page. This is the NSIS setup wizard — not a portable app binary.'
      },
      {
        title: 'Verify SHA-256',
        body: 'Run the checksum command below in PowerShell from the folder containing the file. The hash must match the value on the Download page before you run the installer.'
      },
      {
        title: 'Verify Authenticode signature (signed builds)',
        body: 'For signed releases, confirm the certificate thumbprint matches the publisher fingerprint published on the Download page before running the installer.'
      },
      {
        title: 'Run the installer',
        body: 'Double-click the setup .exe and follow the wizard. CoinWallet is added to the Start Menu and an optional desktop shortcut. If Windows SmartScreen shows a warning for an unsigned build, choose “More info” → “Run anyway”.'
      },
      {
        title: 'First launch',
        body: 'CoinWallet starts a local API on http://127.0.0.1:8002. Create your login, set a wallet passphrase under Security, then create or import a wallet. Testnet is the default until an admin enables mainnet. Production builds should use STRICT_SECRETS and WALLET_DB_KEY (see `.env.production.desktop.example`) to seal the local database on exit.'
      },
      {
        title: 'Updates',
        body: 'Download the new setup .exe from this site, verify the checksum, run the installer, and choose to upgrade the existing install. Export your recovery phrase offline before major upgrades.'
      }
    ],
    verifyChecksum: {
      label: 'PowerShell',
      command:
        'Get-FileHash .\\coinwallet-windows-x64-setup.exe -Algorithm SHA256 | Select-Object -ExpandProperty Hash'
    },
    verifySignature: {
      label: 'PowerShell (signed builds)',
      command:
        '(Get-AuthenticodeSignature .\\coinwallet-windows-x64-setup.exe).SignerCertificate.Thumbprint',
      note: 'Compare the thumbprint to the signer fingerprint on the Download page. Status should be Valid.'
    },
    troubleshooting: [
      {
        title: 'SmartScreen blocked the app',
        body: 'Unsigned desktop builds trigger SmartScreen. Verify the SHA-256 hash matches this site, then use “More info” → “Run anyway”. Do not bypass warnings for files from unknown sources.'
      },
      {
        title: 'Cannot connect to wallet API',
        body: 'Ensure CoinWallet is running and nothing else is using port 8002. Restart the app. Corporate firewalls should allow localhost traffic.'
      },
      {
        title: 'Antivirus quarantined the file',
        body: 'Add an exception only after verifying the published SHA-256. Report false positives with the checksum so others can validate the same binary.'
      }
    ]
  },
  {
    id: 'mac',
    title: 'macOS',
    artifact: 'coinwallet-macos.dmg',
    requirements: [
      'macOS 12 Monterey or later (Apple Silicon or Intel)',
      'About 200 MB free disk space',
      'Local network access to 127.0.0.1 (desktop API sidecar)'
    ],
    steps: [
      {
        title: 'Download the disk image',
        body: 'Get coinwallet-macos.dmg from the Download page. Safari may quarantine the file — that is expected for direct downloads.'
      },
      {
        title: 'Verify SHA-256',
        body: 'Run the checksum command below in Terminal. The output must match the hash published on the Download page.'
      },
      {
        title: 'Verify code signature (signed builds)',
        body: 'For signed and notarized releases, verify the Developer ID matches the fingerprint on the Download page.'
      },
      {
        title: 'Install from the DMG',
        body: 'Open the .dmg and drag CoinWallet into Applications. Eject the disk image when finished.'
      },
      {
        title: 'Open the first time',
        body: 'If macOS says the app is from an unidentified developer, Control-click (or right-click) CoinWallet in Applications → Open, then confirm. Alternatively allow it under System Settings → Privacy & Security.'
      },
      {
        title: 'First launch',
        body: 'The app runs a local API on http://127.0.0.1:8002. Log in, set your wallet passphrase in Security, then create or import a wallet. Testnet is default until mainnet is enabled. Enable FileVault (disk encryption) on Mac for additional at-rest protection.'
      }
    ],
    verifyChecksum: {
      label: 'Terminal',
      command: 'shasum -a 256 ~/Downloads/coinwallet-macos.dmg'
    },
    verifySignature: {
      label: 'Terminal (after install)',
      command: 'codesign -dv --verbose=4 /Applications/CoinWallet.app 2>&1 | grep Authority',
      note: 'For notarized builds also run: spctl -a -vv -t install /Applications/CoinWallet.app'
    },
    troubleshooting: [
      {
        title: '“App is damaged” or Gatekeeper block',
        body: 'Ensure the SHA-256 matches this site. Remove the quarantine flag only for verified downloads: xattr -dr com.apple.quarantine /Applications/CoinWallet.app'
      },
      {
        title: 'App cannot be opened',
        body: 'Use Control-click → Open once, or System Settings → Privacy & Security → Open Anyway. Notarized builds will reduce these prompts in future releases.'
      },
      {
        title: 'Local API unreachable',
        body: 'Quit and reopen CoinWallet. Confirm nothing else listens on port 8002. macOS firewall prompts should allow incoming connections for the local sidecar.'
      }
    ]
  }
];

export function guideForPlatform(id: InstallPlatform): InstallGuide | undefined {
  return installGuides.find((g) => g.id === id);
}
