"""
Build script to create standalone executable using PyInstaller.
Run: python build_exe.py
"""
import PyInstaller.__main__
import sys
import os
from pathlib import Path

# Get the project root directory
project_root = Path(__file__).parent.resolve()

# PyInstaller arguments
args = [
    'lightsapp.spec',
    '--clean',
    '--noconfirm',
]

print("Building executable...")
print(f"Project root: {project_root}")
print(f"PyInstaller args: {args}")

# Run PyInstaller
PyInstaller.__main__.run(args)

print("\nBuild complete! Check the 'dist' folder for LightsApp.exe")
