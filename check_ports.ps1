# ポート使用状況を確認するスクリプト
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "ポート使用状況確認" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# ポート3000の確認
Write-Host "ポート3000 (Webアプリ) の使用状況:" -ForegroundColor Yellow
$port3000 = netstat -ano | findstr ":3000"
if ($port3000) {
    Write-Host $port3000 -ForegroundColor Red
    Write-Host "⚠️  ポート3000は既に使用されています" -ForegroundColor Red
} else {
    Write-Host "✅ ポート3000は使用されていません" -ForegroundColor Green
}

Write-Host ""

# ポート5000の確認
Write-Host "ポート5000 (AI-Board) の使用状況:" -ForegroundColor Yellow
$port5000 = netstat -ano | findstr ":5000"
if ($port5000) {
    Write-Host $port5000 -ForegroundColor Red
    Write-Host "⚠️  ポート5000は既に使用されています" -ForegroundColor Red
} else {
    Write-Host "✅ ポート5000は使用されていません" -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
