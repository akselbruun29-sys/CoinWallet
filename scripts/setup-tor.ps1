# Fetch Tor Expert Bundle for Windows and stage files for the Tauri installer.
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")

$torVersion = "14.5.8"
$arch = "x86_64"
$archiveName = "tor-expert-bundle-windows-$arch-$torVersion.tar.gz"
$url = "https://archive.torproject.org/tor-package-archive/torbrowser/$torVersion/$archiveName"

$stageRoot = Join-Path $PWD "src-tauri\resources\tor"
$marker = Join-Path $stageRoot ".version"

if ((Test-Path (Join-Path $stageRoot "tor.exe")) -and (Test-Path $marker)) {
    $existing = Get-Content $marker -Raw
    if ($existing.Trim() -eq $torVersion) {
        Write-Host "Tor $torVersion already staged - skipping download" -ForegroundColor Green
        exit 0
    }
}

$work = Join-Path $env:TEMP "coinwallet-tor-$torVersion"
if (Test-Path $work) { Remove-Item $work -Recurse -Force }
New-Item -ItemType Directory -Force -Path $work | Out-Null

$archivePath = Join-Path $work $archiveName
Write-Host "Downloading Tor Expert Bundle $torVersion..." -ForegroundColor Cyan
Invoke-WebRequest -Uri $url -OutFile $archivePath -UseBasicParsing

Write-Host "Extracting..." -ForegroundColor Cyan
tar -xzf $archivePath -C $work

$extractedTor = Get-ChildItem -Path $work -Recurse -Filter "tor.exe" | Select-Object -First 1
if (-not $extractedTor) {
    Write-Error "tor.exe not found in downloaded archive"
}

$torFolder = $extractedTor.Directory.FullName
if (Test-Path $stageRoot) { Remove-Item $stageRoot -Recurse -Force }
New-Item -ItemType Directory -Force -Path $stageRoot | Out-Null
Copy-Item -Path (Join-Path $torFolder "*") -Destination $stageRoot -Recurse -Force

Copy-Item $extractedTor.FullName (Join-Path $stageRoot "tor.exe") -Force
Set-Content -Path $marker -Value $torVersion -NoNewline

Write-Host "Staged Tor to $stageRoot" -ForegroundColor Green
