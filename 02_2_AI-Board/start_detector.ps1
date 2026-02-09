# 付箋検知・キャリブレーション（Sticky Note Detector）起動
# プロジェクトルート（02_2_AI-Board）で実行してください。
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "付箋検知・キャリブレーション起動" -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan

$pythonCmd = ".venv\Scripts\python.exe"
if (-not (Test-Path $pythonCmd)) {
    $pythonCmd = "python"
}
Set-Location "src"
& $pythonCmd sticky_note_detector.py
$exitCode = $LASTEXITCODE
Set-Location ..
if ($exitCode -ne 0) { exit $exitCode }
