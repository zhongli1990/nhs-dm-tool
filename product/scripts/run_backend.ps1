param(
  [string]$BackendDir = "c:\Zhong\Windsurf\data_migration\product\backend",
  [string]$BindHost = "127.0.0.1",
  [int]$Port = 8099
)

$ErrorActionPreference = "Stop"
Set-Location $BackendDir

.\.venv\Scripts\uvicorn app.main:app --host $BindHost --port $Port --reload
