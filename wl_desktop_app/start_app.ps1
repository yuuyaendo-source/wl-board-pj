# Wonder Rinko Desktop App 起動
Set-Location $PSScriptRoot
if (-not (Get-Command python -ErrorAction SilentlyContinue)) {
    Write-Error "Python が見つかりません。"
    exit 1
}
python -m venv .venv 2>$null
.\.venv\Scripts\Activate.ps1
pip install -q -r requirements.txt
python app.py
