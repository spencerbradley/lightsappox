@echo off
cd /d "%~dp0"
echo Setting up LightsApp Python environment...
echo.

where py >nul 2>&1
if errorlevel 1 (
    echo Python launcher ^(py^) not found.
    echo Install Python 3.12+ from https://www.python.org/downloads/
    echo Check "Add python.exe to PATH" during install.
    pause
    exit /b 1
)

if not exist ".venv\Scripts\python.exe" (
    echo Creating virtual environment in .venv ...
    py -3.12 -m venv .venv
    if errorlevel 1 (
        py -m venv .venv
        if errorlevel 1 (
            echo Failed to create virtual environment.
            pause
            exit /b 1
        )
    )
)

echo Installing dependencies...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 (
    echo pip install failed.
    pause
    exit /b 1
)

echo Seeding app data directory...
.venv\Scripts\python.exe -c "import sys; from pathlib import Path; sys.path.insert(0, 'backend'); from paths import ensure_data_initialized; ensure_data_initialized(Path('backend/data'))"

echo.
echo Setup complete. Run the app with: run.bat
pause
