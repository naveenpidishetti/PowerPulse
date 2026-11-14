# PowerPulse Root PowerShell Server Launcher
Write-Host "===================================================================" -ForegroundColor Cyan
Write-Host "  Starting PowerPulse Energy Intelligence Server" -ForegroundColor Yellow
Write-Host "  Open in browser: http://127.0.0.1:8000/ or http://localhost:8000/" -ForegroundColor Green
Write-Host "===================================================================" -ForegroundColor Cyan

Set-Location "$PSScriptRoot\powerpulse"
& ".\venv\Scripts\python.exe" manage.py runserver 0.0.0.0:8000
