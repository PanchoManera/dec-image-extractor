@echo off
REM RT-11 WinFsp Driver Wrapper for Windows
REM ========================================
REM This script activates the virtual environment and runs the WinFsp driver

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set VENV_DIR=%SCRIPT_DIR%venv
set WINFSP_SCRIPT=%SCRIPT_DIR%rt11_winfsp.py

REM Check if virtual environment exists
if not exist "%VENV_DIR%" (
    echo Error: Virtual environment not found at %VENV_DIR%
    echo Run setup_winfsp.bat first to set up the environment
    pause
    exit /b 1
)

REM Check if WinFsp script exists
if not exist "%WINFSP_SCRIPT%" (
    echo Error: WinFsp script not found at %WINFSP_SCRIPT%
    pause
    exit /b 1
)

REM Activate virtual environment and run script
call "%VENV_DIR%\Scripts\activate.bat"
python "%WINFSP_SCRIPT%" %*

REM Deactivate virtual environment
call "%VENV_DIR%\Scripts\deactivate.bat"
