@echo off
REM Build script for creating LightsApp executable
echo ========================================
echo Building LightsApp Executable
echo ========================================
echo.

set "PY="
if exist ".venv\Scripts\python.exe" set "PY=.venv\Scripts\python.exe"
if not defined PY if exist "venv\Scripts\python.exe" set "PY=venv\Scripts\python.exe"
if not defined PY set "PY=py -3.12"

REM Check if PyInstaller is installed
%PY% -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    %PY% -m pip install pyinstaller
    if errorlevel 1 (
        echo Failed to install PyInstaller. Please install manually: pip install pyinstaller
        pause
        exit /b 1
    )
)

echo.
echo Starting build process...
echo.

REM Run the build script
%PY% build_exe.py

if errorlevel 1 (
    echo.
    echo Build failed! Check errors above.
    pause
    exit /b 1
)

echo.
echo ========================================
echo Build Complete!
echo ========================================
echo.
echo Executable location: dist\LightsApp.exe
echo.
echo To test: Navigate to dist folder and run LightsApp.exe
echo To create installer: Open installer.iss in Inno Setup Compiler
echo.
pause
