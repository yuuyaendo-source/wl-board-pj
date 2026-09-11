# Wonder Linko Desktop App - MSI ビルド（cx_Freeze）
# 会社ポリシーで exe 直接実行が不可なため、MSI 形式で配布する。
# 実行: .\build_msi.ps1
# 出力: dist\WonderLinko.msi およびインストール用スクリプト

Set-Location $PSScriptRoot

# 環境変数（.env）のロード (CERT_PASSWORD 取得のため)
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*([^#]\w+)\s*=\s*(.*)') {
            $val = $matches[2].Trim().Trim('"').Trim("'")
            [Environment]::SetEnvironmentVariable($matches[1], $val)
        }
    }
}

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

Write-Host "Ensuring pynput is removed from virtual environment..." -ForegroundColor Yellow
& $venvPython -m pip uninstall -y -q pynput 2>$null

Write-Host "Installing cx_Freeze and freeze-core..." -ForegroundColor Yellow
& $venvPython -m pip install -q --upgrade freeze-core cx_Freeze

$pyVer = (& $venvPython -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')" 2>$null)
if ($pyVer -match "3\.(1[3-9]|[2-9][0-9])") {
    & $venvPython -m pip install -q python-msilib 2>$null
}

# 3. キャッシュ・過去ビルドのクリーンアップ
if (Test-Path build) { Remove-Item -Recurse -Force build }
if (Test-Path dist) { Remove-Item -Recurse -Force dist }

# -------------------------------------------------------------
# 4. 証明書の検証と signtool 準備
# -------------------------------------------------------------
$certPfx = Join-Path $PSScriptRoot "cert\WonderLink_CodeSigning.pfx"
$certCer = Join-Path $PSScriptRoot "cert\WonderLink_InternalRoot.cer"
$certPwd = $env:CERT_PASSWORD

if (-not (Test-Path $certPfx)) {
    Write-Error "証明書ファイル ($certPfx) が見つかりません。初回セットアップを行ってください。"
    exit 1
}
if ([string]::IsNullOrWhiteSpace($certPwd)) {
    Write-Error ".env に CERT_PASSWORD が設定されていません。"
    exit 1
}

# 証明書の有効期限チェック (絶対パス化 & 詳細エラー出力)
try {
    # .NET のファイル参照エラーを防ぐため絶対パスで読み込み
    $pfxFullPath = (Get-Item $certPfx).FullName
    $certObj = New-Object System.Security.Cryptography.X509Certificates.X509Certificate2($pfxFullPath, $certPwd)
    $daysLeft = ($certObj.NotAfter - [datetime]::Now).Days
    if ($daysLeft -lt 0) {
        Write-Error "証明書の有効期限が切れています。更新してください。"
        exit 1
    }
    elseif ($daysLeft -lt 60) {
        Write-Warning "証明書の有効期限が残り ${daysLeft} 日です。次回の更新を計画してください。"
    }
    else {
        Write-Host "証明書有効期限: 残り ${daysLeft} 日" -ForegroundColor Green
    }
}
catch {
    Write-Error "証明書の読み込みに失敗しました: $($_.Exception.Message)"
    exit 1
}

# signtool.exe の自動探索
$signtoolPaths = @(
    "C:\Program Files (x86)\Windows Kits\10\bin\*\x64\signtool.exe",
    "C:\Program Files (x86)\Windows Kits\8.1\bin\x64\signtool.exe"
)
$signtool = $null
foreach ($pattern in $signtoolPaths) {
    $found = Get-ChildItem -Path $pattern -ErrorAction SilentlyContinue | Sort-Object -Property LastWriteTime -Descending | Select-Object -First 1
    if ($found) {
        $signtool = $found.FullName
        break
    }
}
if (-not $signtool) {
    Write-Error "signtool.exe が見つかりません。Windows SDK をインストールしてください。"
    exit 1
}
Write-Host "Using signtool: $signtool" -ForegroundColor Cyan

# 署名用ヘルパー関数（タイムスタンプフェールオーバー付き）
function Sign-File {
    param([string]$FilePath)
    $tsServers = @("http://timestamp.digicert.com", "http://timestamp.sectigo.com")
    $success = $false
    foreach ($ts in $tsServers) {
        Write-Host "Signing $FilePath (TS: $ts)..." -ForegroundColor Gray
        $process = Start-Process -FilePath $signtool -ArgumentList "sign /f `"$certPfx`" /p `"$certPwd`" /fd SHA256 /tr $ts /td SHA256 `"$FilePath`"" -Wait -NoNewWindow -PassThru
        if ($process.ExitCode -eq 0) {
            $success = $true
            break
        }
    }
    if (-not $success) {
        Write-Error "Failed to sign $FilePath"
        exit 1
    }
}

# -------------------------------------------------------------
# 5. exe のビルド、事前チェック、バイナリ署名
# -------------------------------------------------------------
Write-Host "Building exe (build_exe)..." -ForegroundColor Yellow
& $venvPython setup.py build_exe
if ($LASTEXITCODE -ne 0) {
    Write-Error "build_exe failed."
    exit 1
}

# バンドル漏れ・不要パッケージの検証をビルド直後に実施（署名前に行う）
$pilPyd = Get-ChildItem -Path "build" -Recurse -Filter "_imaging*.pyd" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $pilPyd) {
    Write-Error "_imaging*.pyd is not in build. Do not distribute this MSI."
    exit 1
}
$sioDir = Get-ChildItem -Path "build" -Recurse -Directory -Filter "socketio" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $sioDir) {
    Write-Error "python-socketio is not bundled. visitor_notify will not work. Aborting."
    exit 1
}
$eioDir = Get-ChildItem -Path "build" -Recurse -Directory -Filter "engineio" -ErrorAction SilentlyContinue | Select-Object -First 1
if (-not $eioDir) {
    Write-Error "python-engineio is not bundled. visitor_notify will not work. Aborting."
    exit 1
}
$pynputFound = Get-ChildItem -Path "build" -Recurse -Filter "*pynput*" -ErrorAction SilentlyContinue | Select-Object -First 1
if ($pynputFound) {
    Write-Error "pynput was found in build output: $($pynputFound.FullName). Aborting."
    exit 1
}
Write-Host "Bundle checks: OK" -ForegroundColor Green

# exe本体、同梱されたdll、pydにすべて署名する（SmartScreenやDefenderの永続化判定回避）
Write-Host "Signing executable and libraries..." -ForegroundColor Yellow
$targets = Get-ChildItem -Path "build" -Recurse -Include "*.exe", "*.dll", "*.pyd" -ErrorAction SilentlyContinue
foreach ($file in $targets) {
    Sign-File $file.FullName
}

# -------------------------------------------------------------
# 6. MSIのビルドと最終署名
# -------------------------------------------------------------
Write-Host "Building MSI (--skip-build)..." -ForegroundColor Yellow
# 上書き再ビルドを防ぐため --skip-build を付与
& $venvPython setup.py bdist_msi --skip-build
if ($LASTEXITCODE -ne 0) {
    Write-Error "bdist_msi failed."
    exit 1
}

$msiPath = Get-ChildItem -Path "dist" -Filter "*.msi" -ErrorAction SilentlyContinue | Sort-Object LastWriteTime -Descending | Select-Object -First 1
if ($msiPath) {
    Sign-File $msiPath.FullName
    Write-Host ""
    Write-Host "Done: $($msiPath.FullName) (Signed)" -ForegroundColor Green
    
    # 7. 配布セットの作成（Cer と install.bat を dist へコピー）
    if (Test-Path $certCer) {
        Copy-Item -Path $certCer -Destination "dist\" -Force
    }
    if (Test-Path "scripts\install.bat") {
        Copy-Item -Path "scripts\install.bat" -Destination "dist\" -Force
    }

    Write-Host "Distribute the contents of 'dist/' directory as a ZIP." -ForegroundColor Cyan
}
else {
    Write-Host "MSI not found in dist. Check build output." -ForegroundColor Yellow
}