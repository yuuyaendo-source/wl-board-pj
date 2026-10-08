# Script to start all local servers simultaneously
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Wonder Linko Local Servers Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$scriptPath = $PSScriptRoot
if (-not $scriptPath) { $scriptPath = Get-Location }

# パスの定義
$stickyDir   = Join-Path $scriptPath "wl-sticky-note\src"
$backendDir  = Join-Path $scriptPath "board-system\backend"
$frontendDir = Join-Path $scriptPath "board-system\frontend"

# 1. wl-sticky-note (Port 3000)
if (Test-Path $stickyDir) {
    Write-Host "1. Starting wl-sticky-note (Port 3000)..." -ForegroundColor Green
    $script = Join-Path $env:TEMP "start_sticky_$(Get-Random).ps1"
    @("Write-Host 'wl-sticky-note (Port 3000)' -ForegroundColor Cyan", "Set-Location '$stickyDir'", "npm run dev") | Out-File -FilePath $script -Encoding UTF8
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $script)
} else {
    Write-Host "Warning: wl-sticky-note directory not found at $stickyDir" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 2. board-system backend (Port 8000)
if (Test-Path $backendDir) {
    Write-Host "2. Starting board-system backend (Port 8000)..." -ForegroundColor Green
    $script = Join-Path $env:TEMP "start_backend_$(Get-Random).ps1"
    $lines = @(
        "Write-Host 'board-system backend (Port 8000)' -ForegroundColor Cyan",
        "Set-Location '$backendDir'",
        "if (Test-Path '.venv\Scripts\Activate.ps1') { & '.venv\Scripts\Activate.ps1' }",
        "uvicorn app.main:app --reload --host 0.0.0.0 --port 8000"
    )
    $lines | Out-File -FilePath $script -Encoding UTF8
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $script)
} else {
    Write-Host "Warning: board-system backend directory not found at $backendDir" -ForegroundColor Yellow
}

Start-Sleep -Seconds 2

# 3. board-system frontend (Port 3001)
if (Test-Path $frontendDir) {
    Write-Host "3. Starting board-system frontend (Port 3001)..." -ForegroundColor Green
    $script = Join-Path $env:TEMP "start_frontend_$(Get-Random).ps1"
    @("Write-Host 'board-system frontend (Port 3001)' -ForegroundColor Cyan", "Set-Location '$frontendDir'", "npm run dev -- -p 3001") | Out-File -FilePath $script -Encoding UTF8
    Start-Process powershell -ArgumentList @("-NoExit", "-File", $script)
} else {
    Write-Host "Warning: board-system frontend directory not found at $frontendDir" -ForegroundColor Yellow
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Startup Commands Sent" -ForegroundColor Green
Write-Host "Sticky Note: http://localhost:3000/board/wl" -ForegroundColor Yellow
Write-Host "BS Frontend: http://localhost:3001" -ForegroundColor Yellow
Write-Host "BS Backend:  http://localhost:8000/health" -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan