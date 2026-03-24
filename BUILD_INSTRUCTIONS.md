# Building LightsApp as Standalone Executable and Installer

This guide explains how to create a portable `.exe` file and installer for LightsApp that can run from a flash drive.

## Prerequisites

1. **Python 3.10+** installed on your build machine
2. **PyInstaller** - Install with: `pip install pyinstaller`
3. **Inno Setup** (for creating installer) - Download from [jrsoftware.org](https://jrsoftware.org/isdl.php)

## Step 1: Install Dependencies

```bash
pip install -r requirements.txt
pip install pyinstaller
```

## Step 2: Build the Executable

Run the build script:

```bash
python build_exe.py
```

This will:
- Create a `dist` folder containing `LightsApp.exe`
- Bundle all Python dependencies
- Include the `backend/data` directory with all JSON files
- Include the entire `frontend` directory

The executable will be located at: `dist\LightsApp.exe`

## Step 3: Test the Executable

Before creating the installer, test the executable:

1. Navigate to the `dist` folder
2. Double-click `LightsApp.exe`
3. Verify it starts correctly and opens the web interface
4. Check that DMX and LedFx functionality works

## Step 4: Create the Installer (Optional)

If you want to create an installer:

1. **Install Inno Setup** from [jrsoftware.org](https://jrsoftware.org/isdl.php)

2. **Open Inno Setup Compiler**

3. **Open the script**: File → Open → Select `installer.iss`

4. **Build the installer**: Build → Compile

5. The installer will be created in `installer_output\LightsApp_Setup.exe`

## Step 5: Portable Flash Drive Setup

For a portable version that runs directly from a flash drive (no installer needed):

1. Copy the entire `dist` folder to your flash drive
2. The folder structure should be:
   ```
   [Flash Drive]\
   ├── LightsApp.exe
   ├── backend\
   │   └── data\
   │       ├── config.json
   │       ├── devices.json
   │       ├── device_presets.json
   │       ├── presets.json
   │       └── scenes.json
   └── frontend\
       ├── index.html
       ├── css\
       ├── js\
       └── html\
   ```

3. Double-click `LightsApp.exe` from the flash drive to run

## Important Notes

- **Configuration**: The `backend/data/config.json` file must exist and be properly configured before running
- **Network Access**: If you want to access from other devices on the network, set `server_host` to `"0.0.0.0"` in `config.json`
- **Firewall**: Windows Firewall may prompt for network access - allow it for DMX functionality
- **Portable Paths**: The application automatically detects if it's running from a portable location and adjusts paths accordingly

## Troubleshooting

### Executable won't start
- Check that all files are present in the `dist` folder
- Run from command line to see error messages: `dist\LightsApp.exe`
- Ensure `backend/data/config.json` exists and is valid

### Missing dependencies
- Rebuild with `--clean` flag: `pyinstaller lightsapp.spec --clean`
- Check that all imports in `lightsapp.spec` are correct

### Frontend not loading
- Verify `frontend` folder is included in `dist`
- Check that paths in `main.py` are correct for portable mode

### DMX not working
- Verify network configuration in `config.json`
- Check Windows Firewall settings
- Ensure ethernet cable is connected

## File Structure After Build

```
dist/
├── LightsApp.exe          # Main executable
├── backend/
│   ├── data/              # All JSON config files
│   └── [Python modules]  # Bundled Python code
└── frontend/              # All HTML/CSS/JS files
```

## Updating the Build

To rebuild after making changes:

1. Make your code changes
2. Run `python build_exe.py` again
3. Test the new executable
4. Rebuild installer if needed
