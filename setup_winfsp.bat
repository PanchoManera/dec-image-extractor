@echo off
REM RT-11 WinFsp Setup Script for Windows
REM ====================================
REM This script sets up the environment for using RT-11 with WinFsp on Windows

echo RT-11 WinFsp Setup Script
echo =========================
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    py --version >nul 2>&1
    if errorlevel 1 (
        echo Error: Python is not installed or not in PATH
        echo Please install Python from https://python.org/
        pause
        exit /b 1
    ) else (
        echo Found Python via 'py' command
        set PYTHON_CMD=py
    )
) else (
    echo Found Python via 'python' command
    set PYTHON_CMD=python
)

echo Installing Python dependencies globally...

REM Install required packages
echo Installing refuse (WinFsp Python bindings)...
%PYTHON_CMD% -m pip install refuse

if errorlevel 1 (
    echo Error: Failed to install refuse
    echo.
    echo Trying fallback: fusepy
    %PYTHON_CMD% -m pip install fusepy
    if errorlevel 1 (
        echo Error: Failed to install FUSE libraries
        echo Try running as administrator
        pause
        exit /b 1
    )
)

REM Check if WinFsp is installed
echo.
echo Checking for WinFsp installation...

set WINFSP_FOUND=0
if exist "C:\Program Files (x86)\WinFsp\bin\winfsp-x64.dll" set WINFSP_FOUND=1
if exist "C:\Program Files\WinFsp\bin\winfsp-x64.dll" set WINFSP_FOUND=1
if exist "C:\Program Files (x86)\WinFsp\bin\winfsp-x86.dll" set WINFSP_FOUND=1

if %WINFSP_FOUND%==1 (
    echo ✓ WinFsp is installed
) else (
    echo ✗ WinFsp is NOT installed
    echo.
    echo WinFsp is required for filesystem mounting on Windows.
    echo.
    echo Please download and install WinFsp from:
    echo   https://winfsp.dev/
    echo   https://github.com/winfsp/winfsp/releases
    echo.
    echo After installing WinFsp, run this script again.
    pause
    exit /b 1
)

REM Test the installation
echo.
echo Testing installation...
%PYTHON_CMD% -c "import refuse; print('✓ refuse module available')" 2>nul
if errorlevel 1 (
    %PYTHON_CMD% -c "import fuse; print('✓ fusepy module available as fallback')" 2>nul
    if errorlevel 1 (
        echo ✗ No FUSE modules available
        pause
        exit /b 1
    )
)

echo.
echo ✓ Setup completed successfully!
echo.
echo You can now use rt11_winfsp.bat to mount RT-11 disk images
echo.
echo Example usage:
echo   rt11_winfsp.bat disk.dsk Z:
echo.
pause
