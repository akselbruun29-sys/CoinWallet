# Publish desktop installers to GitHub Releases (for binaries over Cloudflare Pages 25 MiB).
param(
    [string]$Version = "0.1.0",
    [string]$ReleaseNotes = "",
    [switch]$SkipIfMissing
)

$ErrorActionPreference = "Stop"
$Root = Split-Path $PSScriptRoot -Parent
Set-Location $Root

$meta = Get-Content (Join-Path $PSScriptRoot "release-artifacts.json") -Raw | ConvertFrom-Json
$repo = $meta.github_repo
$tag = if ($Version -match '^v') { $Version } else { "v$Version" }

function Test-GhCli {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    return [bool]$gh
}

if (-not (Test-GhCli)) {
    Write-Error @"
GitHub CLI (gh) is required. Install: winget install GitHub.cli
Then: gh auth login
"@
}

$notes = $ReleaseNotes
if (-not $notes) {
    $manifestPath = Join-Path $Root "releases\releases.json"
    if (Test-Path $manifestPath) {
        $manifest = Get-Content $manifestPath -Raw | ConvertFrom-Json
        $notes = $manifest.release_notes
    }
}
if (-not $notes) {
    $notes = "CoinWallet desktop release $tag"
}

Write-Host "Creating GitHub release $tag on $repo..." -ForegroundColor Cyan
gh release view $tag --repo $repo 2>$null
if ($LASTEXITCODE -ne 0) {
    gh release create $tag --repo $repo --title "CoinWallet $tag" --notes $notes
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
} else {
    Write-Host "Release $tag already exists - uploading assets" -ForegroundColor Yellow
}

$releasesDir = Join-Path $Root "releases"
foreach ($key in @("windows", "macos")) {
    $platform = $meta.$key
    if (-not $platform) { continue }
    $file = Join-Path $releasesDir $platform.filename
    if (-not (Test-Path $file)) {
        if ($SkipIfMissing) {
            Write-Host "Skip $key - not found: $file" -ForegroundColor Yellow
            continue
        }
        Write-Error "Missing artifact: $file"
    }
    Write-Host "Uploading $($platform.filename)..." -ForegroundColor Cyan
    gh release upload $tag $file --repo $repo --clobber
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

Write-Host "GitHub release ready: https://github.com/$repo/releases/tag/$tag" -ForegroundColor Green

& (Join-Path $PSScriptRoot "..\venv\Scripts\python.exe") (Join-Path $PSScriptRoot "update_releases_manifest.py") --version $Version --mark-available
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Updated releases.json with GitHub download URLs." -ForegroundColor Green
