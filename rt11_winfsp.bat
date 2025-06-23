@echo off
REM RT-11 WinFsp Driver Wrapper for Windows
REM ========================================
REM This script runs the WinFsp driver with Python

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set WINFSP_SCRIPT=%SCRIPT_DIR%rt11_winfsp.py

REM Check if WinFsp script exists
if not exist "%WINFSP_SCRIPT%" (
    echo Error: WinFsp script not found at %WINFSP_SCRIPT%
    echo Expected location: %WINFSP_SCRIPT%
    pause
    exit /b 1
)

REM Try to run with python, fallback to py
echo Running WinFsp driver: %WINFSP_SCRIPT%
echo Arguments: %*
python "%WINFSP_SCRIPT%" %* 2>nul
if errorlevel 1 (
    echo Python command failed, trying 'py' command...
    py "%WINFSP_SCRIPT%" %*
    if errorlevel 1 (
        echo Error: Could not run Python script
        echo Make sure Python is installed and WinFsp dependencies are available
        pause
        exit /b 1
    )
)
