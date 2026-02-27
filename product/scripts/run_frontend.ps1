param(
  [string]$FrontendDir = "c:\Zhong\Windsurf\data_migration\product\frontend",
  [int]$Port = 9133
)

$ErrorActionPreference = "Stop"
Set-Location $FrontendDir

$env:PORT = "$Port"
npm.cmd run dev

