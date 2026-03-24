# -*- mode: python ; coding: utf-8 -*-
"""
PyInstaller spec file for LightsApp
"""
import sys
import os
from pathlib import Path

# Get project root (where this spec file is located)
# SPECPATH is set by PyInstaller to the path of this spec file
try:
    project_root = Path(SPECPATH).parent.resolve()
except NameError:
    # Fallback if SPECPATH not available
    project_root = Path(__file__).parent.resolve() if '__file__' in globals() else Path.cwd()

backend_dir = project_root / 'backend'
frontend_dir = project_root / 'frontend'
data_dir = backend_dir / 'data'

# Collect all Python files
a = Analysis(
    [str(backend_dir / 'main.py')],
    pathex=[str(backend_dir)],
    binaries=[],
    datas=[
        (str(data_dir), 'backend/data'),  # Include all data files
        (str(frontend_dir), 'frontend'),  # Include entire frontend directory
    ],
    hiddenimports=[
        'uvicorn.lifespan.on',
        'uvicorn.lifespan.off',
        'uvicorn.protocols.http.auto',
        'uvicorn.protocols.http.h11_impl',
        'uvicorn.protocols.http.httptools_impl',
        'uvicorn.protocols.websockets.auto',
        'uvicorn.protocols.websockets.websockets_impl',
        'uvicorn.loops.auto',
        'uvicorn.loops.asyncio',
        'uvicorn.logging',
        'fastapi.staticfiles',
        'fastapi.middleware.cors',
        'pydantic',
        'sacn',
        'requests',
        'urllib3',
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.datas,
    [],
    name='LightsApp',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=True,  # Keep console for debugging
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon=None,  # Add icon path here if you have one
)
