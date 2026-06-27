# Optional Authenticode signing for Windows release artifacts.
# Set WIN_SIGN_CERT_PATH (PFX) and WIN_SIGN_CERT_PASSWORD before running.
param(
    [Parameter(Mandatory = $true)]
    [string]$FilePath
)

$ErrorActionPreference = "Stop"

if (-not (Test-Path $FilePath)) {
    Write-Error "File not found: $FilePath"
}

$pfx = $env:WIN_SIGN_CERT_PATH
if (-not $pfx) {
    Write-Host "Skip Authenticode signing - WIN_SIGN_CERT_PATH not set." -ForegroundColor Yellow
    exit 0
}

$signtool = $env:SIGNTOOL_PATH
if (-not $signtool) {
    $signtool = "signtool.exe"
}

$tsUrl = if ($env:WIN_SIGN_TIMESTAMP_URL) { $env:WIN_SIGN_TIMESTAMP_URL } else { "http://timestamp.digicert.com" }
$args = @("sign", "/fd", "SHA256", "/tr", $tsUrl, "/f", $pfx, "/d", "CoinWallet", $FilePath)
if ($env:WIN_SIGN_CERT_PASSWORD) {
    $args = @("sign", "/fd", "SHA256", "/tr", $tsUrl, "/f", $pfx, "/p", $env:WIN_SIGN_CERT_PASSWORD, "/d", "CoinWallet", $FilePath)
}

Write-Host "Signing $FilePath with Authenticode..." -ForegroundColor Cyan
& $signtool @args
if ($LASTEXITCODE -ne 0) {
    Write-Error "signtool failed with exit code $LASTEXITCODE"
}

$sig = Get-AuthenticodeSignature -FilePath $FilePath
if ($sig.SignerCertificate) {
    $thumb = $sig.SignerCertificate.Thumbprint
    Write-Host "Signed. Certificate thumbprint: $thumb" -ForegroundColor Green
    if ($env:RELEASE_SIGNER_FINGERPRINT_WINDOWS) {
        if ($env:RELEASE_SIGNER_FINGERPRINT_WINDOWS -ne $thumb) {
            Write-Warning "Thumbprint differs from RELEASE_SIGNER_FINGERPRINT_WINDOWS env var."
        }
    }
} else {
    Write-Warning "Signed file has no SignerCertificate in Get-AuthenticodeSignature output."
}

Write-Host ('Verify locally: Get-AuthenticodeSignature ' + $FilePath) -ForegroundColor DarkGray
