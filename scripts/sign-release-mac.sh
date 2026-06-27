#!/usr/bin/env bash
# Optional codesign + notarization for macOS release artifacts.
# Set APPLE_SIGNING_IDENTITY (e.g. "Developer ID Application: ...") to enable.
set -euo pipefail

ARTIFACT="${1:-}"
if [[ -z "$ARTIFACT" || ! -f "$ARTIFACT" ]]; then
  echo "Usage: sign-release-mac.sh <path-to.dmg-or.app>" >&2
  exit 1
fi

IDENTITY="${APPLE_SIGNING_IDENTITY:-}"
if [[ -z "$IDENTITY" ]]; then
  echo "Skip codesign — APPLE_SIGNING_IDENTITY not set."
  exit 0
fi

echo "Signing $ARTIFACT as '$IDENTITY'..."
if [[ "$ARTIFACT" == *.app ]]; then
  codesign --force --options runtime --sign "$IDENTITY" --timestamp "$ARTIFACT"
  codesign -dv --verbose=4 "$ARTIFACT"
elif [[ "$ARTIFACT" == *.dmg ]]; then
  codesign --force --sign "$IDENTITY" --timestamp "$ARTIFACT"
  codesign -dv --verbose=4 "$ARTIFACT"
else
  echo "Unsupported artifact type (expected .app or .dmg): $ARTIFACT" >&2
  exit 1
fi

if [[ -n "${APPLE_NOTARY_KEY_PATH:-}" && -n "${APPLE_NOTARY_KEY_ID:-}" && -n "${APPLE_NOTARY_ISSUER:-}" ]]; then
  echo "Submitting for notarization..."
  xcrun notarytool submit "$ARTIFACT" \
    --key "$APPLE_NOTARY_KEY_PATH" \
    --key-id "$APPLE_NOTARY_KEY_ID" \
    --issuer "$APPLE_NOTARY_ISSUER" \
    --wait
  echo "Stapling notarization ticket..."
  xcrun stapler staple "$ARTIFACT"
fi

echo "Verify locally: codesign -dv --verbose=4 '$ARTIFACT'"
