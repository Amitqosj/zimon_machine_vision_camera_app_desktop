# ZIMON FastAPI — run from repo root. Listen address/port are fixed in backend/api/config.py (8010).

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Creating venv..." -ForegroundColor Yellow
    py -3 -m venv .venv
}
& $venvPython -m pip install -q -r requirements.txt
Write-Host "Starting API — health: http://127.0.0.1:8010/api/health" -ForegroundColor Green
& $venvPython -m backend.api
