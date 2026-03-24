# Quick Start Guide - Building Portable LightsApp

## Fastest Way to Build

1. **Double-click `build.bat`** - This will automatically install PyInstaller if needed and build the executable

2. **Find your executable**: `dist\LightsApp.exe`

3. **Test it**: Double-click `LightsApp.exe` in the `dist` folder

## For Flash Drive (Portable)

Simply copy the entire `dist` folder to your flash drive. The app will run from anywhere!

```
[Flash Drive]\
└── dist\
    ├── LightsApp.exe
    ├── backend\
    │   └── data\
    └── frontend\
```

## Creating an Installer

1. Download **Inno Setup** from: https://jrsoftware.org/isdl.php
2. Install Inno Setup
3. Open `installer.iss` in Inno Setup Compiler
4. Click "Build" → "Compile"
5. Find installer at: `installer_output\LightsApp_Setup.exe`

## What Was Changed

- ✅ Updated `main.py` to detect portable paths (flash drive support)
- ✅ Updated `routes/data.py` for portable paths
- ✅ Updated `dmx/sender.py` for portable paths
- ✅ Created PyInstaller spec file (`lightsapp.spec`)
- ✅ Created build script (`build_exe.py`)
- ✅ Created Windows batch file (`build.bat`)
- ✅ Created Inno Setup installer script (`installer.iss`)

## Troubleshooting

**Executable won't start?**
- Run from command line to see errors: `dist\LightsApp.exe`
- Check that `backend\data\config.json` exists

**Missing files?**
- Rebuild: `python build_exe.py --clean`
- Or just run `build.bat` again

**Need help?**
- See `BUILD_INSTRUCTIONS.md` for detailed information
