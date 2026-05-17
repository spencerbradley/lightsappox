@echo off
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
    .venv\Scripts\python.exe backend\main.py
    goto :done
)
if exist "venv\Scripts\python.exe" (
    venv\Scripts\python.exe backend\main.py
    goto :done
)

REM py launcher works when Store "python" alias blocks plain python
py -3.12 backend\main.py 2>nul
if not errorlevel 1 goto :done

py backend\main.py
if errorlevel 1 (
    echo Python not found. Run setup.bat or install from https://www.python.org/downloads/
    echo Also disable Store aliases: Settings ^> Apps ^> App execution aliases ^> python.exe off
)

:done
pause
