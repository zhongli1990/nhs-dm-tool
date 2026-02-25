param(
  [string]$FrontendDir = "c:\Zhong\Windsurf\data_migration\product\frontend"
)

$ErrorActionPreference = "Stop"
Set-Location $FrontendDir

npm.cmd install
npm.cmd run build

Write-Host "Frontend setup complete."
