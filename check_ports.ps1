# Check port usage script
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "Wonder Linko Port Usage Check" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

$ports = @(
    @{ Port = 3000; Name = "wl-sticky-note (Local)" },
    @{ Port = 3001; Name = "board-system Frontend (Local)" },
    @{ Port = 8000; Name = "board-system Backend (Local)" },
    @{ Port = 3010; Name = "board-system Frontend (Docker)" },
    @{ Port = 8010; Name = "board-system Backend (Docker)" }
)

foreach ($item in $ports) {
    $p = $item.Port
    $name = $item.Name
    Write-Host "Port $p ($name) Status:" -ForegroundColor Yellow
    $check = netstat -ano | findstr ":$p "
    if ($check) {
        Write-Host $check -ForegroundColor Red
        Write-Host "IN USE: Port $p is currently used." -ForegroundColor Red
    }
    else {
        Write-Host "FREE: Port $p is available." -ForegroundColor Green
    }
    Write-Host ""
}

Write-Host "========================================" -ForegroundColor Cyan