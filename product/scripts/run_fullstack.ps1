param(
  [string]$ScriptsDir = "c:\Zhong\Windsurf\data_migration\product\scripts",
  [int]$BackendPort = 8099,
  [int]$FrontendPort = 3133
)

$ErrorActionPreference = "Stop"

Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", "$ScriptsDir\run_backend.ps1", "-Port", "$BackendPort"
Start-Sleep -Seconds 2
Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-NoExit", "-File", "$ScriptsDir\run_frontend.ps1", "-Port", "$FrontendPort"

Write-Host "Started backend on $BackendPort and frontend on $FrontendPort in separate terminals."
