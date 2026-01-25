# 両方のサーバーを同時に起動するスクリプト
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-Board システム 起動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# プロジェクトのルートディレクトリ
$scriptPath = $PSScriptRoot
if (-not $scriptPath) {
    $scriptPath = Get-Location
}
$webAppDir = Join-Path $scriptPath "02_1_App_postit_board\src"
$aiBoardDir = Join-Path $scriptPath "02_2_AI-Board"

# パスの存在確認
if (-not (Test-Path $webAppDir)) {
    Write-Host "エラー: Webアプリのディレクトリが見つかりません: $webAppDir" -ForegroundColor Red
    exit 1
}

if (-not (Test-Path $aiBoardDir)) {
    Write-Host "エラー: AI-Boardのディレクトリが見つかりません: $aiBoardDir" -ForegroundColor Red
    exit 1
}

# 一時スクリプトファイルを作成してWebアプリを起動
Write-Host "1. Webアプリ（ポート3000）を起動しています..." -ForegroundColor Green
$webAppScript = Join-Path $env:TEMP "start_webapp_$(Get-Random).ps1"
$webAppLines = @(
    "Write-Host 'Webアプリサーバー (ポート3000)' -ForegroundColor Cyan",
    "Set-Location '$webAppDir'",
    "npm run dev"
)
$webAppLines | Out-File -FilePath $webAppScript -Encoding UTF8
Start-Process powershell -ArgumentList @("-NoExit", "-File", $webAppScript)

# 少し待機
Start-Sleep -Seconds 3

# 一時スクリプトファイルを作成してAI-Boardを起動
Write-Host "2. AI-Board（ポート5000）を起動しています..." -ForegroundColor Green
$aiBoardScript = Join-Path $env:TEMP "start_aiboard_$(Get-Random).ps1"
$aiBoardLines = @(
    "Write-Host 'AI-Boardサーバー (ポート5000)' -ForegroundColor Cyan",
    "Set-Location '$aiBoardDir'",
    "# 仮想環境の確認とアクティベート",
    "if (Test-Path '.venv\Scripts\Activate.ps1') {",
    "    & '.venv\Scripts\Activate.ps1'",
    "    `$pythonCmd = '.venv\Scripts\python.exe'",
    "} elseif (Test-Path 'venv\Scripts\Activate.ps1') {",
    "    & 'venv\Scripts\Activate.ps1'",
    "    `$pythonCmd = 'venv\Scripts\python.exe'",
    "} else {",
    "    `$pythonCmd = 'python'",
    "}",
    "Set-Location 'src\webapp'",
    "& `$pythonCmd app.py"
)
$aiBoardLines | Out-File -FilePath $aiBoardScript -Encoding UTF8
Start-Process powershell -ArgumentList @("-NoExit", "-File", $aiBoardScript)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "サーバー起動完了" -ForegroundColor Green
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Webアプリ: http://localhost:3000" -ForegroundColor Yellow
Write-Host "AI-Board:  http://localhost:5000" -ForegroundColor Yellow
Write-Host ""
Write-Host "各サーバーは別ウィンドウで起動しています。" -ForegroundColor Gray
Write-Host "終了するには各ウィンドウで Ctrl+C を押してください。" -ForegroundColor Gray
