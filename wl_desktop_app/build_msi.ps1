# Wonder Linko Desktop App - MSI ビルド（cx_Freeze）
# 会社ポリシーで exe 直接実行が不可なため、MSI 形式で配布する。
# 実行: .\build_msi.ps1
# 出力: dist\WonderLinko.msi

Set-Location $PSScriptRoot

# 1. 仮想環境（.venv）の存在確認および自動作成
$venvPath = Join-Path $PSScriptRoot ".venv"
$venvPython = Join-Path $venvPath "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    Write-Host "Creating virtual environment (.venv)..." -ForegroundColor Yellow
    if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
        Write-Error "System Python not found. Please install Python."
        exit 1
    }
    python -m venv .venv
    if ($LASTEXITCODE -ne 0) {
        Write-Error "Failed to create virtual environment."
        exit 1
    }
}

Write-Host "Using virtual environment: $venvPython" -ForegroundColor Cyan

# 2. 仮想環境内への依存パッケージインストール
Write-Host "Installing runtime dependencies (requirements.txt)..." -ForegroundColor Yellow
& $venvPython -m pip install -q -r requirements.txt
if ($LASTEXITCODE -ne 0) {
    Write-Error "requirements.txt install failed."
    exit 1
}

Write-Host "Installing cx_Freeze and freeze-core..." -ForegroundColor Yellow
& $venvPython -m pip install -q --upgrade freeze-core cx_Freeze

# Python 3.13+ 用のパッケージ処理
$pyVer = (& $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
if ($pyVer -match "3\.(1[3-9]|[2-9][0-9])") {
    & $venvPython -m pip install -q python-msilib 2>$null
}

# 3. キャッシュ・過去ビルドのクリーンアップ
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# 4. MSI ビルド実行
Write-Host "Building MSI..." -ForegroundColor Yellow
& $venvPython setup.py bdist_msi

if ($LASTEXITCODE -ne 0) {
    Write-Error "Build failed."
    exit 1
}

# 5. 生成物および各種バンドル確認
$msiPath = Get-ChildItem -Path "dist" -Filter "*.msi" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($msiPath) {
    Write-Host ""
    Write-Host "Done: $($msiPath.FullName)" -ForegroundColor Green
    
    $pilPyd = Get-ChildItem -Path "build" -Recurse -Filter "_imaging*.pyd" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($pilPyd) {
        Write-Host "PIL _imaging: bundled ($($pilPyd.Name))" -ForegroundColor Gray
    }
    else {
        Write-Error "_imaging*.pyd is not in build. Do not distribute this MSI."
        exit 1
    }

    # Phase 3 (来客通知) で socketio が必須。バンドル漏れチェック
    $sioDir = Get-ChildItem -Path "build" -Recurse -Directory -Filter "socketio" -ErrorAction SilentlyContinue | Select-Object -First 1
    if ($sioDir) {
        Write-Host "python-socketio: bundled ($($sioDir.FullName))" -ForegroundColor Gray
    }
    else {
        Write-Error "python-socketio is not bundled. visitor_notify will not work. Aborting."
        exit 1
    }

    $eioDir = Get-ChildItem -Path "build" -Recurse -Directory -Filter "engineio" -ErrorAction SilentlyContinue | Select-Object -First 1
    if (-not $eioDir) {
        Write-Error "python-engineio is not bundled. visitor_notify will not work. Aborting."
        exit 1
    }

    Write-Host "Distribute the MSI for installation." -ForegroundColor Cyan
    Write-Host "Note: Put production config.json before building to bundle it." -ForegroundColor Gray
}
else {
    Write-Host "MSI not found in dist. Check build output." -ForegroundColor Yellow
}