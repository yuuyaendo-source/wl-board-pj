# Wonder Linko Desktop App - exe build (PyInstaller)
# Run: .\build_exe.ps1
# Output: dist\WonderLinko\WonderLinko.exe
#
# Note: 改善計画16により、--onefile による単一ファイル化はマルウェア誤検知
#       (Bearfoos.A!ml等) を招くため廃止し、ディレクトリ配置型に変更しました。
#       exe配布が許可されない・または誤検知が続く環境では、代わりに 
#       .\build_msi.ps1 で MSI をビルドして配布することを強く推奨します。

Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found."
    exit 1
}

Write-Host "Installing PyInstaller..." -ForegroundColor Yellow
pip install -q pyinstaller

Write-Host "Building exe..." -ForegroundColor Yellow
# WonderLinko.spec で PIL を同梱（_imaging.pyd 必須）。spec が無ければ CLI でビルド
if (Test-Path "WonderLinko.spec") {
    pyinstaller --noconsole --clean WonderLinko.spec
}
else {
    # 改善計画16: --onefile オプションを削除し、デフォルトのディレクトリ出力 (--onedir) とする
    pyinstaller --noconsole --onedir --name WonderLinko app.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

# Ensure dist\WonderLinko exists, then copy config for distribution
# --onedir の場合、成果物は dist\WonderLinko フォルダに出力されるためパスを変更
$distPath = Join-Path $PSScriptRoot "dist\WonderLinko"
if (-not (Test-Path $distPath)) {
    New-Item -ItemType Directory -Force -Path $distPath | Out-Null
}
if (Test-Path "config.json") {
    Copy-Item -Path "config.json" -Destination (Join-Path $distPath "config.json") -Force
}
if (Test-Path ".env.example") {
    Copy-Item -Path ".env.example" -Destination (Join-Path $distPath ".env.example") -Force
}

Write-Host ""
Write-Host "Done: dist\WonderLinko\WonderLinko.exe" -ForegroundColor Green
Write-Host "Distribute: Distribute the entire 'dist\WonderLinko' folder." -ForegroundColor Cyan