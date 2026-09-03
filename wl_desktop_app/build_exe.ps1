# Wonder Linko Desktop App - exe build (PyInstaller)
# Run: .\build_exe.ps1
# Output: dist\WonderLinko.exe
#
# Note: exe 単体の配布が許可されない環境では、代わりに .\build_msi.ps1 で MSI をビルドして配布すること。

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
    pyinstaller --noconsole --onefile --name WonderLinko app.py
}

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

# Ensure dist exists, then copy config for distribution
$distPath = Join-Path $PSScriptRoot "dist"
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
Write-Host "Done: dist\WonderLinko.exe" -ForegroundColor Green
Write-Host "Distribute: WonderLinko.exe + config.json in the same folder." -ForegroundColor Cyan
