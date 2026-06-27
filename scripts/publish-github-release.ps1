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

function Resolve-GhCli {
    $gh = Get-Command gh -ErrorAction SilentlyContinue
    if ($gh) { return $gh.Source }

    foreach ($candidate in @(
        (Join-Path $env:ProgramFiles "GitHub CLI\gh.exe"),
        (Join-Path ${env:ProgramFiles(x86)} "GitHub CLI\gh.exe"),
        (Join-Path $env:LOCALAPPDATA "Programs\GitHub CLI\gh.exe")
    )) {
        if ($candidate -and (Test-Path $candidate)) { return $candidate }
    }
    return $null
}

$GhExe = Resolve-GhCli
if (-not $GhExe) {
    Write-Error @"
GitHub CLI (gh) is required. Install: winget install GitHub.cli
Then log in: & `"`$env:ProgramFiles\GitHub CLI\gh.exe`" auth login
"@
}

function Invoke-Gh {
    param([Parameter(ValueFromRemainingArguments = $true)][string[]]$GhArgs)
    & $GhExe @GhArgs
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
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
$releaseExists = $false
$prevEap = $ErrorActionPreference
$ErrorActionPreference = "Continue"
& $GhExe release view $tag --repo $repo 2>$null | Out-Null
if ($LASTEXITCODE -eq 0) { $releaseExists = $true }
$ErrorActionPreference = $prevEap

if (-not $releaseExists) {
    Invoke-Gh release create $tag --repo $repo --title "CoinWallet $tag" --notes $notes
} else {
    Write-Host "Release $tag already exists - uploading assets" -ForegroundColor Yellow
}

$releasesDir = Join-Path $Root "releases"
foreach ($key in @("windows", "macos")) {
    $platform = $meta.$key
    if (-not $platform) { continue }
    $file = Join-Path $releasesDir $platform.filename
    if (-not (Test-Path $file)) {
        $optional = $SkipIfMissing -or ($platform.host_on_github_releases -eq $false)
        if ($optional) {
            Write-Host "Skip $key - not found: $file" -ForegroundColor Yellow
            continue
        }
        Write-Error "Missing artifact: $file"
    }
    Write-Host "Uploading $($platform.filename)..." -ForegroundColor Cyan
    Invoke-Gh release upload $tag $file --repo $repo --clobber
}

Write-Host "GitHub release ready: https://github.com/$repo/releases/tag/$tag" -ForegroundColor Green

& (Join-Path $PSScriptRoot "..\venv\Scripts\python.exe") (Join-Path $PSScriptRoot "update_releases_manifest.py") --version $Version --mark-available
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

Write-Host "Updated releases.json with GitHub download URLs." -ForegroundColor Green
