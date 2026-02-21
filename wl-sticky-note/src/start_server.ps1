# Webアプリ（Next.js + Express + Socket.IO）起動スクリプト
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "付箋ボードアプリ サーバー起動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

# 依存関係の確認
if (-not (Test-Path "node_modules")) {
    Write-Host "依存関係をインストールしています..." -ForegroundColor Yellow
    npm install
}

# サーバー起動
Write-Host "`nサーバーを起動しています..." -ForegroundColor Green
Write-Host "ブラウザで http://localhost:3000 を開いてください" -ForegroundColor Yellow
Write-Host "終了するには Ctrl+C を押してください`n" -ForegroundColor Gray

npm run dev
