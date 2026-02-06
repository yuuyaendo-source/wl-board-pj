# Script to start both servers simultaneously
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-Board System Startup" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Project root directory
$scriptPath = $PSScriptRoot
if (-not $scriptPath) {
    $scriptPath = Get-Location
}
$webAppDir = Join-Path $scriptPath "02_1_sticky-note\src"
$aiBoardDir = Join-Path $scriptPath "02_2_AI-Board"

# Check paths
if (-not (Test-Path $webAppDir)) {
    Write-Host "Error: Web App directory not found: $webAppDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $aiBoardDir)) {
    Write-Host "Error: AI-Board directory not found: $aiBoardDir" -ForegroundColor Red
    exit 1
}

# Create temp script to start Web App
Write-Host "1. Starting Web App (Port 3000)..." -ForegroundColor Green
$webAppScript = Join-Path $env:TEMP "start_webapp_$(Get-Random).ps1"
$webAppLines = @(
    "Write-Host 'Web App Server (Port 3000)' -ForegroundColor Cyan",
    "Set-Location '$webAppDir'",
    "npm run dev"
)
$webAppLines | Out-File -FilePath $webAppScript -Encoding UTF8
Start-Process powershell -ArgumentList @("-NoExit", "-File", $webAppScript)

# Wait a bit
Start-Sleep -Seconds 3

# Create temp script to start AI-Board
Write-Host "2. Starting AI-Board (Port 5000)..." -ForegroundColor Green
$aiBoardScript = Join-Path $env:TEMP "start_aiboard_$(Get-Random).ps1"
$aiBoardLines = @(
    "Write-Host 'AI-Board Server (Port 5000)' -ForegroundColor Cyan",
    "Set-Location '$aiBoardDir'",
    "# Check and activate virtual environment",
    "`$pythonCmd = 'python'",
    "if (Test-Path '.venv\Scripts\Activate.ps1') {",
    "    & '.venv\Scripts\Activate.ps1'",
    "    if (Test-Path '.venv\Scripts\python.exe') {",
    "        `$pythonCmd = (Resolve-Path '.venv\Scripts\python.exe').Path",
    "    }",
    "} elseif (Test-Path 'venv\Scripts\Activate.ps1') {",
    "    & 'venv\Scripts\Activate.ps1'",
    "    if (Test-Path 'venv\Scripts\python.exe') {",
    "        `$pythonCmd = (Resolve-Path 'venv\Scripts\python.exe').Path",
    "    }",
    "}",
    "Set-Location 'src\webapp'",
    "Write-Host 'Starting python server with: ' `$pythonCmd -ForegroundColor Yellow",
    "& `$pythonCmd app.py"
)
$aiBoardLines | Out-File -FilePath $aiBoardScript -Encoding UTF8
Start-Process powershell -ArgumentList @("-NoExit", "-File", $aiBoardScript)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Servers Startup Complete" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Local:  Web App http://localhost:3000  |  AI-Board http://localhost:5000" -ForegroundColor Yellow
Write-Host "CATO:   Web App http://172.16.1.251:3000  |  AI-Board http://172.16.1.251:5000" -ForegroundColor Cyan
Write-Host "  (from CATO-connected PCs, use 172.16.1.251 instead of localhost)" -ForegroundColor Gray
Write-Host ""
Write-Host "Each server is running in a separate window. Press Ctrl+C in each to stop." -ForegroundColor Gray
