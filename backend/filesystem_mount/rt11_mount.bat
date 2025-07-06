@echo off
setlocal enabledelayedexpansion

REM RT-11 WinFsp Mount Script for Windows
REM ====================================== 
REM Unified script that handles WinFsp installation check and mounting

echo RT-11 WinFsp Mount Script
echo ==========================

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set WINFSP_EXE=%SCRIPT_DIR%rt11_winfsp.exe

REM Check arguments
if "%~2"=="" (
    echo Usage: rt11_mount.bat ^<image.dsk^> ^<mount_point^>
    echo Example: rt11_mount.bat disk.dsk Z:
    echo.
    echo This script will:
    echo 1. Check if WinFsp is installed
    echo 2. Mount the RT-11 image as a filesystem
    echo 3. Display the mounted drive
    echo.
    pause
    exit /b 1
)

set IMAGE_FILE=%~1
set MOUNT_POINT=%~2

echo Image file: %IMAGE_FILE%
echo Mount point: %MOUNT_POINT%
echo.

REM Check if image file exists
if not exist "%IMAGE_FILE%" (
    echo ERROR: Image file not found: %IMAGE_FILE%
    pause
    exit /b 1
)

REM Check if WinFsp is installed
echo Checking WinFsp installation...
set WINFSP_FOUND=0

if exist "C:\Program Files (x86)\WinFsp\bin\winfsp-x64.dll" set WINFSP_FOUND=1
if exist "C:\Program Files\WinFsp\bin\winfsp-x64.dll" set WINFSP_FOUND=1
if exist "C:\Program Files (x86)\WinFsp\bin\winfsp-x86.dll" set WINFSP_FOUND=1

if !WINFSP_FOUND!==0 (
    echo ERROR: WinFsp not installed
    echo.
    echo Please install WinFsp from:
    echo https://winfsp.dev/
    echo.
    echo Direct download:
    echo https://github.com/winfsp/winfsp/releases
    echo.
    echo After installing WinFsp, run this script again.
    pause
    exit /b 1
)

echo ✓ WinFsp is installed

REM Check if standalone executable exists, fallback to Python script
set PYTHON_WINFSP=%SCRIPT_DIR%rt11_winfsp.py
set USE_PYTHON=0

if not exist "%WINFSP_EXE%" (
    echo RT-11 WinFsp executable not found: %WINFSP_EXE%
    echo Looking for Python script fallback...
    
    if exist "%PYTHON_WINFSP%" (
        echo ✓ Found Python WinFsp driver: %PYTHON_WINFSP%
        set USE_PYTHON=1
    ) else (
        echo ERROR: Neither executable nor Python script found
        echo Expected files:
        echo   %WINFSP_EXE%
        echo   %PYTHON_WINFSP%
        echo.
        pause
        exit /b 1
    )
) else (
    echo ✓ RT-11 WinFsp driver found: %WINFSP_EXE%
)

REM Normalize mount point
set NORM_MOUNT=%MOUNT_POINT%
if not "%NORM_MOUNT:~-1%"==":" (
    if "%NORM_MOUNT:~1%"=="" (
        set NORM_MOUNT=%NORM_MOUNT%:
    ) else (
        echo ERROR: Mount point should be a drive letter (e.g., Z:)
        pause
        exit /b 1
    )
)

echo ✓ Mount point: %NORM_MOUNT%
echo.

REM Execute the WinFsp driver
echo Starting RT-11 filesystem mount...

if !USE_PYTHON!==1 (
    echo Command: python "%PYTHON_WINFSP%" "%IMAGE_FILE%" "%NORM_MOUNT%"
    echo.
    python "%PYTHON_WINFSP%" "%IMAGE_FILE%" "%NORM_MOUNT%"
    set MOUNT_RESULT=!ERRORLEVEL!
) else (
    echo Command: "%WINFSP_EXE%" "%IMAGE_FILE%" "%NORM_MOUNT%"
    echo.
    "%WINFSP_EXE%" "%IMAGE_FILE%" "%NORM_MOUNT%"
    set MOUNT_RESULT=!ERRORLEVEL!
)

echo.
if !MOUNT_RESULT!==0 (
    echo ✓ Mount completed successfully!
    echo Drive %NORM_MOUNT% should now contain your RT-11 files.
    echo.
    echo To unmount:
    echo - Right-click on drive %NORM_MOUNT% and select "Eject"
    echo - Or use: net use %NORM_MOUNT% /delete
) else (
    echo ✗ Mount failed with exit code: !MOUNT_RESULT!
    echo.
    echo Possible causes:
    echo - WinFsp service not running
    echo - Drive letter %NORM_MOUNT% already in use
    echo - RT-11 image file is corrupted or invalid
    echo - Insufficient permissions
    echo.
    echo Try:
    echo 1. Choose a different drive letter
    echo 2. Run as Administrator
    echo 3. Restart WinFsp service: sc restart winfsp.launcher
)

echo.
pause
exit /b !MOUNT_RESULT!
