# Start CloudForge FastAPI Backend Server
Write-Host "Starting CloudForge Backend on http://127.0.0.1:8000..." -ForegroundColor Cyan
Set-Location -Path "$PSScriptRoot\backend"
$env:PYTHONPATH = "."
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
