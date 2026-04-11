# Build docs/ZIMON_PROJECT_GUIDE.html then export docs/ZIMON_PROJECT_GUIDE.pdf (Chrome or Edge headless).
# Run from repo root: .\scripts\export_project_guide_pdf.ps1

$ErrorActionPreference = "Stop"
$root = Split-Path -Parent $PSScriptRoot
Set-Location $root

$venvPython = Join-Path $root ".venv\Scripts\python.exe"
if (-not (Test-Path $venvPython)) {
    Write-Host "Virtualenv not found at .venv - create it and install requirements first." -ForegroundColor Red
    exit 1
}

& $venvPython (Join-Path $root "scripts\export_project_guide_html.py")

$html = Join-Path $root "docs\ZIMON_PROJECT_GUIDE.html"
$pdf = Join-Path $root "docs\ZIMON_PROJECT_GUIDE.pdf"
$uri = "file:///" + ($html -replace '\\', '/')

$chrome = "${env:ProgramFiles}\Google\Chrome\Application\chrome.exe"
$edge = "${env:ProgramFiles(x86)}\Microsoft\Edge\Application\msedge.exe"
if (-not (Test-Path $edge)) { $edge = "${env:ProgramFiles}\Microsoft\Edge\Application\msedge.exe" }

$browser = $null
if (Test-Path $chrome) { $browser = $chrome }
elseif (Test-Path $edge) { $browser = $edge }

if (-not $browser) {
    Write-Host "Chrome/Edge not found in default paths. Open docs\ZIMON_PROJECT_GUIDE.html and Print -> Save as PDF." -ForegroundColor Yellow
    exit 0
}

& $browser --headless --disable-gpu "--print-to-pdf=$pdf" $uri
if (Test-Path $pdf) {
    Write-Host "Wrote $pdf" -ForegroundColor Green
} else {
    Write-Host "PDF export failed." -ForegroundColor Red
    exit 1
}
