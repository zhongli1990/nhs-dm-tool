param(
  [string]$BackendDir = "c:\Zhong\Windsurf\data_migration\product\backend"
)

$ErrorActionPreference = "Stop"
Set-Location $BackendDir

if (!(Test-Path ".venv")) {
  python -m venv .venv
}

.\.venv\Scripts\python -m pip install --upgrade pip setuptools wheel
.\.venv\Scripts\pip install -r requirements.txt

Write-Host "Backend setup complete."
