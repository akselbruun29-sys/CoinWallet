# Stop Wallet Vault Admin services (API on 8001, UI on 5173)
$ErrorActionPreference = "SilentlyContinue"

function Stop-PortProcess($Port, $Label) {
    $pids = Get-NetTCPConnection -LocalPort $Port -State Listen -ErrorAction SilentlyContinue |
        Select-Object -ExpandProperty OwningProcess -Unique

    if (-not $pids) {
        Write-Host "$Label (port $Port): not running"
        return
    }

    foreach ($procId in $pids) {
        $name = (Get-Process -Id $procId -ErrorAction SilentlyContinue).ProcessName
        Stop-Process -Id $procId -Force -ErrorAction SilentlyContinue
        Write-Host "Stopped $Label (port $Port, PID $procId, $name)" -ForegroundColor Green
    }
}

Stop-PortProcess 8001 "API"
Stop-PortProcess 5173 "Admin UI"

Write-Host ""
Write-Host "Done. Run .\start_admin.ps1 to start again."
