# Windows Firewall: Allow port 3000 (wl-sticky-note / CATO dev access)
# Run PowerShell as Administrator.
# Example: Right-click PowerShell -> Run as administrator -> cd project root -> .\scripts\allow_firewall_port_3000.ps1

$ruleName = "wl-sticky-note (Port 3000)"
$port = 3000

if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Run this script as Administrator." -ForegroundColor Red
    exit 1
}

$existing = Get-NetFirewallRule -DisplayName $ruleName -ErrorAction SilentlyContinue
if ($existing) {
    Remove-NetFirewallRule -DisplayName $ruleName
}

New-NetFirewallRule -DisplayName $ruleName `
    -Direction Inbound `
    -Protocol TCP `
    -LocalPort $port `
    -Action Allow `
    -Profile Any

Write-Host "OK: Port $port allowed. CATO PCs can access http://172.16.1.251:3000" -ForegroundColor Green
