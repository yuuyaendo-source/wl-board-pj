# Wonder Rinko Desktop App - MSI ビルド（cx_Freeze）
# 会社ポリシーで exe 直接実行が不可なため、MSI 形式で配布する。
# 実行: .\build_msi.ps1
# 出力: dist\WonderRinko.msi

Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found."
    exit 1
}

Write-Host "Installing cx_Freeze..." -ForegroundColor Yellow
pip install -q cx_Freeze

# Python 3.13+ では python-msilib が必要な場合あり
$pyVer = (python -c "import sys; print(sys.version_info.major, sys.version_info.minor)" 2>$null)
if ($pyVer -match "3\.(1[3-9]|[2-9][0-9])") {
    pip install -q python-msilib 2>$null
}

Write-Host "Building MSI..." -ForegroundColor Yellow
python setup.py bdist_msi

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

$msiPath = Get-ChildItem -Path "dist" -Filter "*.msi" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($msiPath) {
    Write-Host ""
    Write-Host "Done: $($msiPath.FullName)" -ForegroundColor Green
    Write-Host "Distribute: MSI を配布し、メンバーはインストーラーでインストール。" -ForegroundColor Cyan
    Write-Host "Note: ビルド前に本番用 config.json を置いておくと、同梱された状態でインストールされます。" -ForegroundColor Gray
} else {
    Write-Host "MSI not found in dist. Check build output." -ForegroundColor Yellow
}
