# Update releases/releases.json with SHA-256 hashes for built artifacts.
param(
    [string]$Version = "0.1.0",
    [switch]$MarkAvailable,
    [string]$SignatureStatus = "",
    [string]$ReleaseNotes = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
$ManifestPath = Join-Path $Root "releases\releases.json"
$SiteManifestPath = Join-Path $Root "site\static\releases\releases.json"

if (-not (Test-Path $ManifestPath)) {
    Write-Error "Manifest not found: $ManifestPath"
}

$manifest = Get-Content $ManifestPath -Raw | ConvertFrom-Json
$manifest.version = $Version
$manifest.released_at = (Get-Date).ToUniversalTime().ToString("yyyy-MM-ddTHH:mm:ssZ")
if ($ReleaseNotes) {
    $manifest.release_notes = $ReleaseNotes
}

$globalFingerprint = $env:RELEASE_SIGNER_FINGERPRINT
if ($globalFingerprint) {
    $manifest.signer_fingerprint = $globalFingerprint
}

function Set-PlatformArtifact($platformKey, $filePath, $urlPath) {
    if (-not (Test-Path $filePath)) {
        Write-Host "Skip $platformKey - not found: $filePath" -ForegroundColor Yellow
        return
    }
    $hash = (Get-FileHash -Path $filePath -Algorithm SHA256).Hash.ToLower()
    $manifest.platforms.$platformKey.url = $urlPath
    $manifest.platforms.$platformKey.sha256 = $hash
    if ($MarkAvailable) {
        $manifest.platforms.$platformKey.available = $true
    }

    $sig = Get-AuthenticodeSignature -FilePath $filePath -ErrorAction SilentlyContinue
    if ($sig -and $sig.SignerCertificate) {
        $manifest.platforms.$platformKey.signature_status = "signed"
        $manifest.platforms.$platformKey.signer_fingerprint = $sig.SignerCertificate.Thumbprint
        if (-not $manifest.signer_fingerprint) {
            $manifest.signer_fingerprint = $sig.SignerCertificate.Thumbprint
        }
    } elseif ($SignatureStatus) {
        $manifest.platforms.$platformKey.signature_status = $SignatureStatus
    } elseif (-not $manifest.platforms.$platformKey.signature_status) {
        $manifest.platforms.$platformKey.signature_status = "unsigned"
    }

    $envFp = (Get-Item "env:RELEASE_SIGNER_FINGERPRINT_$($platformKey.ToUpper())" -ErrorAction SilentlyContinue).Value
    if ($envFp) {
        $manifest.platforms.$platformKey.signer_fingerprint = $envFp
    }

    Write-Host "Updated $platformKey - SHA-256 $hash status=$($manifest.platforms.$platformKey.signature_status)"
}

$releasesDir = Join-Path $Root "releases"
$artifacts = Get-Content (Join-Path $PSScriptRoot "release-artifacts.json") -Raw | ConvertFrom-Json
Set-PlatformArtifact "windows" (Join-Path $releasesDir $artifacts.windows.filename) $artifacts.windows.url
Set-PlatformArtifact "macos" (Join-Path $releasesDir $artifacts.macos.filename) $artifacts.macos.url

$json = $manifest | ConvertTo-Json -Depth 8
$utf8NoBom = New-Object System.Text.UTF8Encoding $false
[System.IO.File]::WriteAllText($ManifestPath, $json + "`n", $utf8NoBom)
[System.IO.File]::WriteAllText($SiteManifestPath, $json + "`n", $utf8NoBom)
Write-Host "Manifest written to releases/ and site/static/releases/"
