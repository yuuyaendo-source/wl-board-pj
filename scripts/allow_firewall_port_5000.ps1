# Windowsファイアウォール: ポート5000を許可（AI-Board遠隔アクセス用）
# 管理者としてPowerShellで実行してください。
# 例: 右クリック「PowerShellを管理者として実行」→ cd プロジェクトルート → .\scripts\allow_firewall_port_5000.ps1

$ruleName = "AI-Board (Port 5000)"
$port = 5000

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "このスクリプトは管理者権限で実行してください。" -ForegroundColor Red
    Write-Host "PowerShellを右クリック → '管理者として実行' で開き、再度実行してください。" -ForegroundColor Yellow
    exit 1
}

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Write-Host "ルール '$ruleName' は既に存在します。削除して再作成します。" -ForegroundColor Yellow
    Remove-NetFirewallRule -DisplayName $ruleName
}

New-NetFirewallRule -DisplayName $ruleName `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort $port `
    -Action Allow `
    -Profile Any

Write-Host "OK: ポート $port の受信を許可しました。遠隔から https://<このPCのIP>:5000 でアクセスできます。" -ForegroundColor Green
