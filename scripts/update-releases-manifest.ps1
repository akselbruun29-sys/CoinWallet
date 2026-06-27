# Update releases/releases.json with SHA-256 hashes for built artifacts.
param(
    [string]$Version = "0.1.0",
    [switch]$MarkAvailable
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

function Set-PlatformArtifact($platformKey, $filePath, $urlPath) {
    if (-not (Test-Path $filePath)) {
        Write-Host "Skip $platformKey — not found: $filePath" -ForegroundColor Yellow
        return
    }
    $hash = (Get-FileHash -Path $filePath -Algorithm SHA256).Hash.ToLower()
    $manifest.platforms.$platformKey.url = $urlPath
    $manifest.platforms.$platformKey.sha256 = $hash
    if ($MarkAvailable) {
        $manifest.platforms.$platformKey.available = $true
    }
    Write-Host "Updated $platformKey — SHA-256 $hash"
}

$releasesDir = Join-Path $Root "releases"
Set-PlatformArtifact "windows" (Join-Path $releasesDir "coinwallet-windows-x64.exe") "/releases/coinwallet-windows-x64.exe"
Set-PlatformArtifact "macos" (Join-Path $releasesDir "coinwallet-macos.dmg") "/releases/coinwallet-macos.dmg"

$json = $manifest | ConvertTo-Json -Depth 6
Set-Content -Path $ManifestPath -Value $json -Encoding UTF8
Set-Content -Path $SiteManifestPath -Value $json -Encoding UTF8
Write-Host "Manifest written to releases/ and site/static/releases/"
