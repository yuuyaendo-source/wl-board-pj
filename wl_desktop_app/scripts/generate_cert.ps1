# 初回セットアップ用: 自己署名コードサイニング証明書の生成
Set-Location $PSScriptRoot\..

if (-not (Test-Path "cert")) {
    New-Item -ItemType Directory -Force -Path "cert" | Out-Null
}

# .env から CERT_PASSWORD を読み込み
$certPwdPlain = $null
if (Test-Path ".env") {
    Get-Content ".env" | ForEach-Object {
        if ($_ -match '^\s*CERT_PASSWORD\s*=\s*(.*)') {
            $certPwdPlain = $matches[1].Trim().Trim('"').Trim("'")
        }
    }
}

if ([string]::IsNullOrWhiteSpace($certPwdPlain)) {
    Write-Host "自己署名証明書（コードサイニング用）を生成します。"
    $pwdPlain = Read-Host "証明書のエクスポート用パスワードを入力してください (半角英数)" -AsSecureString
}
else {
    Write-Host ".env の CERT_PASSWORD を使用して証明書を生成します。" -ForegroundColor Green
    $pwdPlain = ConvertTo-SecureString -String $certPwdPlain -AsPlainText -Force
}

# 3年有効、コード署名限定 (1.3.6.1.5.5.7.3.3) の証明書を作成
$cert = New-SelfSignedCertificate `
    -Type CodeSigningCert `
    -Subject "CN=WonderLink Internal, O=WonderLink, C=JP" `
    -KeyAlgorithm RSA `
    -KeyLength 2048 `
    -HashAlgorithm SHA256 `
    -CertStoreLocation "Cert:\CurrentUser\My" `
    -NotAfter (Get-Date).AddYears(3) `
    -KeyUsage DigitalSignature `
    -TextExtension @("2.5.29.37={text}1.3.6.1.5.5.7.3.3")

# .pfx (秘密鍵付き) と .cer (公開鍵のみ) をエクスポート
Export-PfxCertificate -Cert $cert -FilePath "cert/WonderLink_CodeSigning.pfx" -Password $pwdPlain
Export-Certificate -Cert $cert -FilePath "cert/WonderLink_InternalRoot.cer"

Write-Host ""
Write-Host "証明書の作成が完了しました。cert/ ディレクトリに保存されています。" -ForegroundColor Green
Write-Host "build_msi.ps1 を実行してください。" -ForegroundColor Cyan