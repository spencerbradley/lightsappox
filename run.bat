@echo off
cd /d "%~dp0"
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe backend\main.py
) else (
    python backend\main.py
)
pause
