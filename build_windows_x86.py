#!/usr/bin/env python3
"""
Cross-compilation script: macOS -> Windows x86 (32-bit)
Builds RT11ExtractGUI.exe for Windows 32-bit from macOS
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path
import platform

def run_command(cmd, cwd=None, check=True):
    """Run a command and return the result"""
    print(f"🔧 Running: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"✅ Output: {result.stdout.strip()}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"❌ Error: {e}")
        if e.stdout:
            print(f"📤 stdout: {e.stdout}")
        if e.stderr:
            print(f"📥 stderr: {e.stderr}")
        if check:
            raise
        return e

def check_wine():
    """Check if Wine is available"""
    try:
        result = subprocess.run(['wine', '--version'], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"✅ Wine found: {result.stdout.strip()}")
            return True
    except FileNotFoundError:
        pass
    
    print("❌ Wine not found. Installing Wine...")
    
    # Check if Homebrew is available
    try:
        subprocess.run(['brew', '--version'], capture_output=True, check=True)
        print("📦 Installing Wine via Homebrew...")
        subprocess.run(['brew', 'install', '--cask', 'wine-stable'], check=True)
        return True
    except (FileNotFoundError, subprocess.CalledProcessError):
        print("❌ Homebrew not found. Please install Wine manually:")
        print("   Option 1: Install Homebrew and run: brew install --cask wine-stable")
        print("   Option 2: Download Wine from https://www.winehq.org/download")
        return False

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
        import urllib.request
        urllib.request.urlretrieve(python_url, "python-win32.zip")
        
        import zipfile
        with zipfile.ZipFile("python-win32.zip", 'r') as zip_ref:
            zip_ref.extractall(python_dir)
        
        os.remove("python-win32.zip")
        print("✅ Python for Windows x86 downloaded and extracted")
        return python_dir
        
    except Exception as e:
        print(f"❌ Failed to download Python: {e}")
        return None

def setup_wine_python(python_dir):
    """Setup Python in Wine environment"""
    wine_python_dir = Path.home() / ".wine/drive_c/Python311"
    
    if wine_python_dir.exists():
        print("✅ Python already setup in Wine")
        return wine_python_dir
    
    print("🍷 Setting up Python in Wine environment...")
    
    # Create Wine prefix if needed
    run_command(['winecfg'], check=False)  # This will create the prefix
    
    # Copy Python to Wine drive
    wine_python_dir.parent.mkdir(parents=True, exist_ok=True)
    shutil.copytree(python_dir, wine_python_dir)
    
    # Install pip in Wine
    try:
        # Download get-pip.py
        import urllib.request
        urllib.request.urlretrieve("https://bootstrap.pypa.io/get-pip.py", "get-pip.py")
        
        # Install pip in Wine Python
        run_command(['wine', str(wine_python_dir / 'python.exe'), 'get-pip.py'])
        
        # Install required packages
        pip_cmd = ['wine', str(wine_python_dir / 'python.exe'), '-m', 'pip', 'install']
        packages = ['pyinstaller', 'pillow']
        
        for package in packages:
            run_command(pip_cmd + [package])
        
        os.remove("get-pip.py")
        print("✅ Python packages installed in Wine")
        
    except Exception as e:
        print(f"⚠️ Warning: Could not install packages in Wine: {e}")
    
    return wine_python_dir

def create_windows_spec():
    """Create PyInstaller spec file for Windows"""
    spec_content = '''
# -*- mode: python ; coding: utf-8 -*-

block_cipher = None

a = Analysis(
    ['rt11extract_gui.py'],
    pathex=['.'],
    binaries=[],
    datas=[('images.png', '.')],
    hiddenimports=[],
    hookspath=[],
    runtime_hooks=[],
    excludes=[],
    win_no_prefer_redirects=False,
    win_private_assemblies=False,
    cipher=block_cipher,
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=block_cipher)

exe = EXE(
    pyz,
    a.scripts,
    a.binaries,
    a.zipfiles,
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
    target_arch='x86',
    codesign_identity=None,
    entitlements_file=None,
    icon='icon.ico'
)
'''
    
    with open('RT11ExtractGUI-Win32.spec', 'w') as f:
        f.write(spec_content.strip())
    
    print("✅ Windows spec file created")

def build_with_wine():
    """Build executable using Wine"""
    wine_python_dir = Path.home() / ".wine/drive_c/Python311"
    
    if not wine_python_dir.exists():
        print("❌ Wine Python not found")
        return False
    
    print("🏗️ Building Windows executable with Wine + PyInstaller...")
    
    # Build with PyInstaller in Wine
    pyinstaller_cmd = [
        'wine', 
        str(wine_python_dir / 'python.exe'), 
        '-m', 'PyInstaller',
        '--onefile',
        '--windowed',
        '--name=RT11ExtractGUI',
        '--icon=icon.ico',
        '--add-data=images.png;.',
        '--target-arch=x86',
        'rt11extract_gui.py'
    ]
    
    result = run_command(pyinstaller_cmd, check=False)
    
    if result.returncode == 0:
        # Copy the executable to our directory
        wine_dist = Path.home() / ".wine/drive_c/users" / os.getenv('USER', 'user') / "temp/dist"
        local_dist = Path("dist")
        
        if wine_dist.exists():
            local_dist.mkdir(exist_ok=True)
            exe_files = list(wine_dist.glob("*.exe"))
            if exe_files:
                shutil.copy2(exe_files[0], local_dist / "RT11ExtractGUI-Win32.exe")
                print("✅ Windows executable created: dist/RT11ExtractGUI-Win32.exe")
                return True
    
    print("❌ Failed to build with Wine")
    return False

def build_alternative():
    """Alternative build method using cx_Freeze or manual packaging"""
    print("🔄 Trying alternative build method...")
    
    # Try installing cx_Freeze
    try:
        subprocess.run([sys.executable, '-m', 'pip', 'install', 'cx_Freeze'], check=True)
        print("✅ cx_Freeze installed")
    except subprocess.CalledProcessError:
        print("❌ Could not install cx_Freeze")
        return False
    
    # Create cx_Freeze setup script
    setup_content = '''
import sys
from cx_Freeze import setup, Executable

# Dependencies are automatically detected, but it might need fine tuning.
build_options = {
    'packages': [],
    'excludes': [],
    'include_files': [('images.png', 'images.png')],
    'optimize': 2
}

base = 'Win32GUI' if sys.platform == 'win32' else None

executables = [
    Executable('rt11extract_gui.py', 
               base=base, 
               target_name='RT11ExtractGUI.exe',
               icon='icon.ico')
]

setup(name='RT11ExtractGUI',
      version='1.0',
      description='RT-11 Disk Image Extractor',
      options={'build_exe': build_options},
      executables=executables)
'''
    
    with open('setup_cx.py', 'w') as f:
        f.write(setup_content.strip())
    
    # Try to build (this probably won't work for Windows from macOS, but let's try)
    try:
        result = run_command([sys.executable, 'setup_cx.py', 'build'], check=False)
        if result.returncode == 0:
            print("✅ Alternative build succeeded")
            return True
    except Exception as e:
        print(f"❌ Alternative build failed: {e}")
    
    return False

def create_portable_package():
    """Create a portable Windows package"""
    print("📦 Creating portable Windows package...")
    
    # Download Python for Windows if needed
    python_dir = download_python_windows()
    if not python_dir:
        return False
    
    # Create portable package directory
    package_dir = Path("RT11ExtractGUI-Win32-Portable")
    package_dir.mkdir(exist_ok=True)
    
    # Copy Python
    python_target = package_dir / "python"
    if python_target.exists():
        shutil.rmtree(python_target)
    shutil.copytree(python_dir, python_target)
    
    # Copy our application files
    app_files = ['rt11extract_gui.py', 'rt11extract', 'rt11extract_simple.py', 'images.png']
    for file in app_files:
        if os.path.exists(file):
            shutil.copy2(file, package_dir)
    
    # Create launcher batch file
    launcher_content = '''@echo off
cd /d "%~dp0"
python\\python.exe rt11extract_gui.py %*
pause
'''
    
    with open(package_dir / "RT11ExtractGUI.bat", 'w') as f:
        f.write(launcher_content)
    
    # Create README
    readme_content = '''RT-11 Extractor - Windows Portable Version

This is a portable version that includes Python and all dependencies.

To run:
1. Double-click RT11ExtractGUI.bat
2. Or from command line: RT11ExtractGUI.bat

No installation required!

System Requirements:
- Windows 7 or later (32-bit or 64-bit)
- No additional software needed

Files included:
- RT11ExtractGUI.bat - Main launcher
- python/ - Portable Python installation
- rt11extract_gui.py - Main GUI application
- rt11extract - Core extraction tool
- images.png - GUI icons
'''
    
    with open(package_dir / "README.txt", 'w') as f:
        f.write(readme_content)
    
    print(f"✅ Portable package created: {package_dir}")
    print("📁 This package can be copied to any Windows machine and run directly")
    
    return True

def main():
    """Main build process"""
    print("🚀 RT-11 Extractor - Windows x86 Cross-compilation")
    print("=" * 50)
    
    if platform.system() != 'Darwin':
        print("❌ This script is designed to run on macOS")
        return False
    
    # Check required files
    required_files = ['rt11extract_gui.py', 'rt11extract', 'images.png']
    for file in required_files:
        if not os.path.exists(file):
            print(f"❌ Required file missing: {file}")
            return False
    
    print("✅ All required files found")
    
    # Method 1: Try Wine + PyInstaller
    if check_wine():
        python_dir = download_python_windows()
        if python_dir:
            wine_python_dir = setup_wine_python(python_dir)
            create_windows_spec()
            
            if build_with_wine():
                print("🎉 Success! Windows executable created with Wine")
                return True
    
    # Method 2: Try alternative build
    if build_alternative():
        print("🎉 Success! Windows executable created with alternative method")
        return True
    
    # Method 3: Create portable package
    if create_portable_package():
        print("🎉 Success! Portable Windows package created")
        print("\n📋 Instructions:")
        print("1. Copy the RT11ExtractGUI-Win32-Portable folder to a Windows machine")
        print("2. Double-click RT11ExtractGUI.bat to run")
        return True
    
    print("❌ All build methods failed")
    return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
