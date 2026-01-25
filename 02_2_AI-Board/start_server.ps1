# AI-Board（Flask）サーバー起動スクリプト
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "AI-Board サーバー起動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 仮想環境の確認とアクティベート
if (Test-Path ".venv\Scripts\Activate.ps1") {
    Write-Host "仮想環境 (.venv) をアクティベートしています..." -ForegroundColor Yellow
    & ".venv\Scripts\Activate.ps1"
    $pythonCmd = ".venv\Scripts\python.exe"
} elseif (Test-Path "venv\Scripts\Activate.ps1") {
    Write-Host "仮想環境 (venv) をアクティベートしています..." -ForegroundColor Yellow
    & "venv\Scripts\Activate.ps1"
    $pythonCmd = "venv\Scripts\python.exe"
} else {
    Write-Host "仮想環境が見つかりません。システムのPythonを使用します。" -ForegroundColor Yellow
    $pythonCmd = "python"
    if (Get-Command python3 -ErrorAction SilentlyContinue) {
        $pythonCmd = "python3"
    }
}

# 依存関係の確認（仮想環境内で実行）
Write-Host "`n依存関係を確認しています..." -ForegroundColor Yellow
& $pythonCmd -m pip install -q -r requirements.txt

# サーバー起動
Write-Host "`nサーバーを起動しています..." -ForegroundColor Green
Write-Host "ブラウザで http://localhost:5000 を開いてください" -ForegroundColor Yellow
Write-Host "終了するには Ctrl+C を押してください`n" -ForegroundColor Gray

Set-Location "src\webapp"
& $pythonCmd app.py
