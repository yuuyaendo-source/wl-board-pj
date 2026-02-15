# AI-Board server background start (PowerShell can be closed)
# Usage: .\start_server_background.ps1
# Stop: stop_server_background.ps1 or kill python in Task Manager

$ErrorActionPreference = "Stop"
$ProjectRoot = (Resolve-Path $PSScriptRoot).Path
$LogDir = Join-Path $ProjectRoot "logs"
if (-not (Test-Path $LogDir)) {
    New-Item -ItemType Directory -Force -Path $LogDir | Out-Null
}

$timestamp = Get-Date -Format "yyyyMMdd_HHmmss"
if (-not $timestamp) { $timestamp = "00000000_000000" }

$LogFileOut = Join-Path $LogDir "server_${timestamp}_stdout.log"
$LogFileErr = Join-Path $LogDir "server_${timestamp}_stderr.log"
$PidFile = Join-Path $LogDir "server.pid"

$existing = Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | Where-Object { $_.State -eq "Listen" }
if ($existing) {
    Write-Host "Port 5000 is already in use." -ForegroundColor Yellow
    $choice = Read-Host "Start anyway? (y/N)"
    if ($choice -ne "y" -and $choice -ne "Y") { exit 0 }
}

$pythonExe = Join-Path $ProjectRoot ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonExe)) { $pythonExe = "python.exe" }
$workDir = Join-Path $ProjectRoot "src\webapp"
$appPy = Join-Path $workDir "app.py"

Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-Board server starting in background" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Stdout: $LogFileOut" -ForegroundColor Gray
Write-Host "Stderr: $LogFileErr" -ForegroundColor Gray
Write-Host "Browser: https://172.16.1.251:5000" -ForegroundColor Green

# Use UTF-8 for Python stdout/stderr so Unicode (e.g. checkmarks) does not cause cp932 error
$env:PYTHONIOENCODING = "utf-8"
$proc = Start-Process -FilePath $pythonExe -ArgumentList "-u", "`"$appPy`"" -WorkingDirectory $workDir `
    -WindowStyle Hidden -PassThru `
    -RedirectStandardOutput $LogFileOut -RedirectStandardError $LogFileErr

$proc.Id | Set-Content -Path $PidFile -Encoding utf8
Write-Host "Started. PID: $($proc.Id)" -ForegroundColor Green

Start-Sleep -Seconds 3
$stillRunning = $false
try {
    $stillRunning = -not $proc.HasExited
} catch { $stillRunning = $false }
if (-not $stillRunning) {
    Write-Host ""
    Write-Host "Server exited shortly after start. Check error below." -ForegroundColor Red
    if (Test-Path $LogFileErr) {
        Write-Host "--- stderr ---" -ForegroundColor Yellow
        Get-Content -Path $LogFileErr -Encoding UTF8 -ErrorAction SilentlyContinue
        Write-Host "---" -ForegroundColor Yellow
    }
    if (Test-Path $LogFileOut) {
        $out = Get-Content -Path $LogFileOut -Encoding UTF8 -ErrorAction SilentlyContinue
        if ($out) {
            Write-Host "--- stdout ---" -ForegroundColor Yellow
            $out
            Write-Host "---" -ForegroundColor Yellow
        }
    }
    Write-Host "Tip: run manually: cd src\webapp; python app.py" -ForegroundColor Gray
    Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
    exit 1
}
Write-Host "Server is running. Logs: see paths above." -ForegroundColor Gray
