@echo off
setlocal enabledelayedexpansion
REM RT-11 WinFsp Driver Wrapper for Windows
REM ========================================
REM This script runs the standalone WinFsp driver executable

REM Get the directory where this script is located
set SCRIPT_DIR=%~dp0
set WINFSP_EXE=%SCRIPT_DIR%rt11_winfsp.exe
set WINFSP_SCRIPT=%SCRIPT_DIR%rt11_winfsp.py

REM Debug: Show what we're looking for
echo DEBUG: Looking for executable at: %WINFSP_EXE%
echo DEBUG: Current directory: %CD%
echo DEBUG: Script directory: %SCRIPT_DIR%

REM Try standalone executable first (preferred for distribution)
if exist "%WINFSP_EXE%" (
    echo SUCCESS: Found standalone WinFsp driver: %WINFSP_EXE%
    echo Arguments: %*
    echo DEBUG: About to execute: "%WINFSP_EXE%" %*
    "%WINFSP_EXE%" %* 2>&1
    set EXEC_RESULT=!ERRORLEVEL!
    echo DEBUG: Executable returned with exit code: !EXEC_RESULT!
    if !EXEC_RESULT! neq 0 (
        echo ERROR: WinFsp driver failed with exit code !EXEC_RESULT!
    )
    goto :end
) else (
    echo WARNING: Standalone executable not found at: %WINFSP_EXE%
)

REM Fallback to Python script (for development)
if exist "%WINFSP_SCRIPT%" (
    echo Standalone executable not found, trying Python script: %WINFSP_SCRIPT%
    echo Arguments: %*
    
    REM Check if python command is available
    python --version >nul 2>&1
    if not errorlevel 1 (
        echo Using 'python' command
        python "%WINFSP_SCRIPT%" %*
        goto :end
    )
    
    REM Check if py command is available
    py --version >nul 2>&1
    if not errorlevel 1 (
        echo Using 'py' command
        py "%WINFSP_SCRIPT%" %*
        goto :end
    )
    
    echo Error: No Python interpreter found
    echo Please install Python or run setup_winfsp.bat
    pause
    exit /b 1
)

echo Error: Neither standalone executable nor Python script found
echo Expected locations:
echo - %WINFSP_EXE%
echo - %WINFSP_SCRIPT%
pause
exit /b 1

:end
