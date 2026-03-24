@echo off
REM Build script for creating LightsApp executable
echo ========================================
echo Building LightsApp Executable
echo ========================================
echo.

REM Check if PyInstaller is installed
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller not found. Installing...
    pip install pyinstaller
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
python build_exe.py

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
