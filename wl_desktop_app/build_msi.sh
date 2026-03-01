#!/usr/bin/env bash
# MSI ビルドは Windows で PowerShell を使って行います。
# Linux では MSI を生成できないため、案内を表示して終了します。

case "$(uname -s)" in
  Windows*|MINGW*|MSYS*|CYGWIN*)
    # Windows の場合は PowerShell で実行を試みる（Git Bash 等）
    if command -v pwsh >/dev/null 2>&1; then
      exec pwsh -NoProfile -File "$(dirname "$0")/build_msi.ps1"
    elif command -v powershell.exe >/dev/null 2>&1; then
      exec powershell.exe -NoProfile -ExecutionPolicy Bypass -File "$(dirname "$0")/build_msi.ps1"
    else
      echo "PowerShell が見つかりません。Windows で PowerShell を開き、以下を実行してください:"
      echo "  cd $(dirname "$0")"
      echo "  .\\build_msi.ps1"
      exit 1
    fi
    ;;
  *)
    echo "MSI ビルドは Windows 上で行ってください。"
    echo "開発環境は Linux、配布用 MSI は Windows PC でビルドする運用です。"
    echo ""
    echo "Windows で PowerShell を開き、以下を実行してください:"
    echo "  cd wl_desktop_app"
    echo "  .\\build_msi.ps1"
    echo ""
    echo "出力: dist\\WonderLinko.msi"
    exit 1
    ;;
esac
