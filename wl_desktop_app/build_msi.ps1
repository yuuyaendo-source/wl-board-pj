# Wonder Rinko Desktop App - MSI ビルド（cx_Freeze）
# 会社ポリシーで exe 直接実行が不可なため、MSI 形式で配布する。
# 実行: .\build_msi.ps1
# 出力: dist\WonderRinko.msi

Set-Location $PSScriptRoot

if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python not found."
    exit 1
}

Write-Host "Installing cx_Freeze and freeze-core..." -ForegroundColor Yellow
# freeze-core は cx_Freeze の Windows 用依存。Python バージョンに合った wheel を入れるため明示的にアップグレード
pip install -q --upgrade freeze-core cx_Freeze

# Python 3.13+ では python-msilib が cx_Freeze の依存で入る
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
    $pilPyd = Get-ChildItem -Path "build" -Recurse -Filter "_imaging*.pyd" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pilPyd) {
        Write-Host "PIL _imaging: bundled ($($pilPyd.Name))" -ForegroundColor Gray
    } else {
        Write-Error "_imaging*.pyd is not in build. Do not distribute this MSI."
        exit 1
    }
    Write-Host "Distribute the MSI for installation." -ForegroundColor Cyan
    Write-Host "Note: Put production config.json before building to bundle it." -ForegroundColor Gray
} else {
    Write-Host "MSI not found in dist. Check build output." -ForegroundColor Yellow
}
