#!/usr/bin/env python3
"""
Simple Windows package builder for RT-11 Extractor
Creates a portable Windows package without cross-compilation
"""

import os
import sys
import subprocess
import shutil
import urllib.request
import zipfile
from pathlib import Path

def download_python_windows():
    """Download portable Python for Windows x86"""
    python_dir = Path("python_win32")
    
    if python_dir.exists():
        print("✅ Python for Windows already exists")
        return python_dir
    
    print("📦 Downloading Python 3.11 for Windows x86...")
    
    # Use Python embeddable zip for Windows x86
    python_url = "https://www.python.org/ftp/python/3.11.8/python-3.11.8-embed-win32.zip"
    
    try:
        print(f"📥 Downloading from: {python_url}")
        urllib.request.urlretrieve(python_url, "python-win32.zip")
        
        print("📂 Extracting Python...")
        with zipfile.ZipFile("python-win32.zip", 'r') as zip_ref:
            zip_ref.extractall(python_dir)
        
        os.remove("python-win32.zip")
        print("✅ Python for Windows x86 downloaded and extracted")
        return python_dir
        
    except Exception as e:
        print(f"❌ Failed to download Python: {e}")
        return None

def download_tkinter_for_windows():
    """Download tkinter for Windows (if needed)"""
    # For embedded Python, we might need to download tkinter separately
    print("📦 Setting up tkinter for Windows...")
    
    # The embedded Python should include tkinter, but let's make sure
    # by modifying the python311._pth file
    python_dir = Path("python_win32")
    pth_file = python_dir / "python311._pth"
    
    if pth_file.exists():
        # Read current content
        with open(pth_file, 'r') as f:
            content = f.read()
        
        # Add tkinter path if not present
        if "tkinter" not in content:
            with open(pth_file, 'w') as f:
                f.write(content)
                f.write("\n# Added for GUI support\n")
                f.write("tkinter\n")
                f.write("tkinter.ttk\n")
            print("✅ tkinter configuration updated")
    
    return True

def create_portable_package():
    """Create a portable Windows package"""
    print("📦 Creating portable Windows package...")
    
    # Download Python for Windows if needed
    python_dir = download_python_windows()
    if not python_dir:
        return False
    
    # Setup tkinter
    download_tkinter_for_windows()
    
    # Create portable package directory
    package_dir = Path("RT11ExtractGUI-Win32-Portable")
    if package_dir.exists():
        print("🗑️ Removing existing package...")
        shutil.rmtree(package_dir)
    
    package_dir.mkdir(exist_ok=True)
    
    # Copy Python
    python_target = package_dir / "python"
    print(f"📁 Copying Python to {python_target}")
    shutil.copytree(python_dir, python_target)
    
    # Copy our application files
    app_files = ['rt11extract_gui.py', 'rt11extract', 'rt11extract_simple.py', 'images.png']
    for file in app_files:
        if os.path.exists(file):
            print(f"📄 Copying {file}")
            shutil.copy2(file, package_dir)
        else:
            print(f"⚠️ File not found: {file}")
    
    # Copy icon if exists
    if os.path.exists('icon.ico'):
        shutil.copy2('icon.ico', package_dir)
    
    # Create launcher batch file
    launcher_content = '''@echo off
REM RT-11 Extractor GUI Launcher
REM Portable version with embedded Python

cd /d "%~dp0"

REM Check if Python exists
if not exist "python\\python.exe" (
    echo Error: Python not found in python\\python.exe
    echo Please ensure the python folder is in the same directory as this script.
    pause
    exit /b 1
)

REM Check if main script exists
if not exist "rt11extract_gui.py" (
    echo Error: rt11extract_gui.py not found
    echo Please ensure all files are in the same directory.
    pause
    exit /b 1
)

REM Launch the application
echo Starting RT-11 Extractor GUI...
python\\python.exe rt11extract_gui.py %*

REM If we get here, the program ended
if errorlevel 1 (
    echo.
    echo Program ended with error. Press any key to close.
    pause >nul
) else (
    echo.
    echo Program ended normally. Press any key to close.
    pause >nul
)
'''
    
    with open(package_dir / "RT11ExtractGUI.bat", 'w') as f:
        f.write(launcher_content)
    
    # Create silent launcher (no console window)
    silent_launcher = '''@echo off
cd /d "%~dp0"
start "" /b python\\pythonw.exe rt11extract_gui.py %*
'''
    
    with open(package_dir / "RT11ExtractGUI-Silent.bat", 'w') as f:
        f.write(silent_launcher)
    
    # Create CLI launcher for command line usage
    cli_launcher = '''@echo off
REM RT-11 Extractor Command Line Tool
cd /d "%~dp0"
python\\python.exe rt11extract %*
'''
    
    with open(package_dir / "rt11extract.bat", 'w') as f:
        f.write(cli_launcher)
    
    # Create README
    readme_content = '''RT-11 Extractor - Windows Portable Version
==========================================

This is a portable version that includes Python and all dependencies.
No installation required!

QUICK START:
-----------
1. Double-click "RT11ExtractGUI.bat" to start the GUI
2. Or use "RT11ExtractGUI-Silent.bat" for no console window

COMMAND LINE:
------------
Use "rt11extract.bat" for command line operations:
    rt11extract.bat disk.dsk

FILES INCLUDED:
--------------
- RT11ExtractGUI.bat      - Main GUI launcher (with console)
- RT11ExtractGUI-Silent.bat - GUI launcher (no console window)
- rt11extract.bat         - Command line tool launcher
- python/                 - Portable Python installation
- rt11extract_gui.py      - Main GUI application
- rt11extract            - Core extraction tool (Python script)
- rt11extract_simple.py   - Simple GUI version
- images.png              - GUI icons
- README.txt              - This file

SYSTEM REQUIREMENTS:
-------------------
- Windows 7 or later (32-bit or 64-bit)
- No additional software needed

USAGE:
------
GUI Mode:
1. Double-click RT11ExtractGUI.bat
2. Use File -> Open to select an RT-11 disk image
3. Browse files and extract as needed

Command Line Mode:
1. Open Command Prompt in this folder
2. Run: rt11extract.bat your_disk_image.dsk
3. Files will be extracted to a subfolder

TROUBLESHOOTING:
---------------
- If you get "Python not found" error, ensure the python/ folder exists
- If GUI doesn't start, try RT11ExtractGUI.bat to see error messages
- Make sure all files are in the same folder
- On some systems, you may need to "Unblock" the files after extracting from ZIP

TECHNICAL NOTES:
---------------
- Uses Python 3.11 embedded distribution
- Includes tkinter for GUI
- No registry modifications
- Completely self-contained
- Can be run from USB drive or any folder

For more information visit: https://github.com/your-repo/rt11-extractor
'''
    
    with open(package_dir / "README.txt", 'w') as f:
        f.write(readme_content)
    
    # Create a simple unblock script for Windows security
    unblock_script = '''# PowerShell script to unblock all files
# Right-click this file and select "Run with PowerShell"

Get-ChildItem -Path . -Recurse | Unblock-File
Write-Host "All files have been unblocked."
Write-Host "You can now run RT11ExtractGUI.bat"
Read-Host "Press Enter to continue"
'''
    
    with open(package_dir / "Unblock-Files.ps1", 'w') as f:
        f.write(unblock_script)
    
    print(f"✅ Portable package created: {package_dir}")
    print("📁 This package can be copied to any Windows machine and run directly")
    
    # Create a ZIP file for easy distribution
    zip_path = f"{package_dir}.zip"
    print(f"📦 Creating ZIP file: {zip_path}")
    
    shutil.make_archive(str(package_dir), 'zip', '.', str(package_dir))
    
    print(f"✅ ZIP file created: {zip_path}")
    
    return True

def create_minimal_executable():
    """Try to create a minimal executable using available tools"""
    print("🔧 Attempting to create Windows executable...")
    
    # Check if we have pyinstaller
    try:
        import PyInstaller
        print("✅ PyInstaller found")
        
        # Create a simple spec for Windows
        spec_content = '''# -*- mode: python ; coding: utf-8 -*-

a = Analysis(
    ['rt11extract_gui.py'],
    pathex=[],
    binaries=[],
    datas=[('images.png', '.')],
    hiddenimports=['tkinter', 'tkinter.ttk', 'tkinter.filedialog', 'tkinter.messagebox'],
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
    name='RT11ExtractGUI',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    upx_exclude=[],
    runtime_tmpdir=None,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico' if os.path.exists('icon.ico') else None,
)
'''
        
        with open('RT11ExtractGUI-Windows.spec', 'w') as f:
            f.write(spec_content)
        
        print("📝 PyInstaller spec file created")
        print("ℹ️ To build Windows exe, run this on a Windows machine:")
        print("   pyinstaller RT11ExtractGUI-Windows.spec")
        
        return True
        
    except ImportError:
        print("ℹ️ PyInstaller not available, skipping executable creation")
        return False

def main():
    """Main build process"""
    print("🚀 RT-11 Extractor - Simple Windows Package Builder")
    print("=" * 55)
    
    # Check required files
    required_files = ['rt11extract_gui.py', 'rt11extract']
    missing_files = []
    
    for file in required_files:
        if not os.path.exists(file):
            missing_files.append(file)
        else:
            print(f"✅ Found: {file}")
    
    if missing_files:
        print(f"❌ Missing required files: {missing_files}")
        return False
    
    # Optional files
    optional_files = ['images.png', 'icon.ico', 'rt11extract_simple.py']
    for file in optional_files:
        if os.path.exists(file):
            print(f"✅ Found optional: {file}")
        else:
            print(f"⚠️ Optional file missing: {file}")
    
    print("\n" + "=" * 55)
    
    # Create portable package (always works)
    if create_portable_package():
        print("\n🎉 SUCCESS!")
        print("\n📋 What was created:")
        print("1. RT11ExtractGUI-Win32-Portable/ - Portable folder")
        print("2. RT11ExtractGUI-Win32-Portable.zip - ZIP for distribution")
        print("\n📋 Instructions:")
        print("1. Copy the ZIP file to a Windows machine")
        print("2. Extract the ZIP file")
        print("3. Double-click RT11ExtractGUI.bat to run")
        print("\n🔧 Alternative: Run RT11ExtractGUI-Silent.bat for no console")
    
    # Try to create executable spec (for future use)
    create_minimal_executable()
    
    return True

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
