# Wonder Linko - Windows の通知設定をリセットするスクリプト
# 通知をオフにしたあと一覧にアプリが出てこない場合、このスクリプトで
# レジストリの通知設定を削除すると、再度通知が表示されることがあります。
# 実行前: Wonder Linko を終了してください。

$basePath = "Registry::HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings"
$possibleNames = @("Wonder Rinko", "WonderLinko", "WonderLinkoDesktop", "WonderLinko.Desktop", "Wonder Rinko")

Write-Host "通知設定のリセットを試行します。" -ForegroundColor Cyan
Write-Host ""

if (-not (Test-Path $basePath)) {
    Write-Host "通知設定のレジストリキーが見つかりません。既にリセット済みの可能性があります。" -ForegroundColor Yellow
    exit 0
}

$removed = 0
foreach ($name in $possibleNames) {
    $fullPath = Join-Path $basePath $name
    if (Test-Path $fullPath) {
        try {
            Remove-Item -Path $fullPath -Recurse -Force -ErrorAction Stop
            Write-Host "削除しました: $name" -ForegroundColor Green
            $removed++
        } catch {
            Write-Host "削除に失敗しました: $name - $_" -ForegroundColor Red
        }
    }
}

if ($removed -eq 0) {
    Write-Host "Wonder Linko 用のキーは見つかりませんでした。" -ForegroundColor Yellow
    Write-Host "現在の通知設定一覧（参考）:" -ForegroundColor Gray
    Get-ChildItem -Path $basePath -ErrorAction SilentlyContinue | ForEach-Object { Write-Host "  - $($_.PSChildName)" }
    Write-Host ""
    Write-Host "上記の一覧で Wonder Linko に該当しそうな名前のキーを、レジストリエディターで手動削除してみてください。" -ForegroundColor Gray
    Write-Host "  regedit で以下のパスを開きます:" -ForegroundColor Gray
    Write-Host "  HKEY_CURRENT_USER\SOFTWARE\Microsoft\Windows\CurrentVersion\Notifications\Settings" -ForegroundColor Gray
} else {
    Write-Host ""
    Write-Host "リセットしました。Wonder Linko を起動し、トレイの「テストお知らせ」で通知を確認してください。" -ForegroundColor Green
}
