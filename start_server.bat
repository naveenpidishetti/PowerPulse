@echo off
title PowerPulse Server
cd /d "%~dp0\powerpulse"
echo ===================================================================
echo   Starting PowerPulse Energy Intelligence Server
echo   Open in browser: http://127.0.0.1:8000/ or http://localhost:8000/
echo ===================================================================
venv\Scripts\python.exe manage.py runserver 0.0.0.0:8000
pause

