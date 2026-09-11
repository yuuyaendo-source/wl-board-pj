@echo off
:: 管理者権限の確認と自動昇格
net session >nul 2>&1
if %errorlevel% neq 0 (
    powershell -Command "Start-Process '%~f0' -Verb RunAs"
    exit /b
)

:: カレントディレクトリをバッチファイルの存在する場所へ移動
cd /d "%~dp0"

:: ZIP未解凍実行のチェック
if not exist "WonderLinko.msi" (
    echo [ERROR] 必要なファイルが見つかりません。
    echo ZIPファイルをすべて展開（解凍）してから install.bat を実行してください。
    pause
    exit /b 1
)

:: 常駐プロセスの終了（ファイルロックによるインストール失敗防止）
taskkill /f /im WonderLinko.exe >nul 2>&1

:: 【将来用】古い証明書の削除（Thumbprint等で指定）
:: certutil -delstore "Root" "OLD_CERT_THUMBPRINT" >nul 2>&1

:: 証明書の登録 (Root および TrustedPublisher)
certutil -addstore -f "Root" "WonderLink_InternalRoot.cer" >nul 2>&1
certutil -addstore -f "TrustedPublisher" "WonderLink_InternalRoot.cer" >nul 2>&1

:: MSIインストーラーの起動 (基本UIのみ表示で自動進行)
msiexec /i "WonderLinko.msi" /qb
if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo インストールが正常に完了しました。
    echo ============================================
) else (
    echo.
    echo [ERROR] インストール中にエラーが発生しました (ErrorCode: %errorlevel%)。
    pause
)