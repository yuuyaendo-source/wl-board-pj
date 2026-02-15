# バックグラウンドで起動した AI-Board サーバーを停止します
# 使い方: 02_2_AI-Board フォルダで .\stop_server_background.ps1 を実行

$ProjectRoot = $PSScriptRoot
$LogDir = Join-Path $ProjectRoot "logs"
$PidFile = Join-Path $LogDir "server.pid"

if (-not (Test-Path $PidFile)) {
    Write-Host "PID ファイルが見つかりません。手動で停止する場合:" -ForegroundColor Yellow
    Write-Host "  タスクマネージャーで「python」を探して終了するか、以下のコマンドでポート 5000 を使用しているプロセスを終了してください。" -ForegroundColor Gray
    Write-Host '  Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }' -ForegroundColor Gray
    $choice = Read-Host "ポート 5000 のプロセスを今すぐ終了しますか？ (y/N)"
    if ($choice -eq "y" -or $choice -eq "Y") {
        Get-NetTCPConnection -LocalPort 5000 -ErrorAction SilentlyContinue | ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
        Write-Host "終了しました。" -ForegroundColor Green
    }
    exit 0
}

$pidValue = Get-Content -Path $PidFile -Raw
$pidNum = [int]($pidValue -replace "\s+", "")
$proc = Get-Process -Id $pidNum -ErrorAction SilentlyContinue
if ($proc) {
    $proc | Stop-Process -Force
    Write-Host "サーバー (PID: $pidNum) を停止しました。" -ForegroundColor Green
} else {
    Write-Host "PID $pidNum のプロセスは既に存在しません。" -ForegroundColor Gray
}
Remove-Item -Path $PidFile -Force -ErrorAction SilentlyContinue
