# Check port usage script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Port Usage Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# Check Port 3000
Write-Host "Port 3000 (Web App) Status:" -ForegroundColor Yellow
$port3000 = netstat -ano | findstr ":3000"
if ($port3000) {
    Write-Host $port3000 -ForegroundColor Red
    Write-Host "Warning: Port 3000 is already in use." -ForegroundColor Red
} else {
    Write-Host "OK: Port 3000 is free." -ForegroundColor Green
}

Write-Host ""

# Check Port 5000
Write-Host "Port 5000 (AI-Board) Status:" -ForegroundColor Yellow
$port5000 = netstat -ano | findstr ":5000"
if ($port5000) {
    Write-Host $port5000 -ForegroundColor Red
    Write-Host "Warning: Port 5000 is already in use." -ForegroundColor Red
} else {
    Write-Host "OK: Port 5000 is free." -ForegroundColor Green
}

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
