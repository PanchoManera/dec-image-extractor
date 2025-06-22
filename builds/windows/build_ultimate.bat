@echo off
echo ============================================
echo RT-11 Extractor Ultimate Windows Builder
echo ============================================
echo Installing requirements...
pip install pyinstaller pillow nuitka auto-py-to-exe cx_freeze

echo.
echo Trying PyInstaller builds...
echo Building Win32...
pyinstaller --onefile --windowed --icon=icon.ico --name=RT11ExtractGUI-Win32 rt11extract_gui.py --add-data="rt11extract;." --noconfirm
echo Building Win64...
pyinstaller --onefile --windowed --icon=icon.ico --name=RT11ExtractGUI-Win64 rt11extract_gui.py --add-data="rt11extract;." --noconfirm
echo Building ARM64...
pyinstaller --onefile --windowed --icon=icon.ico --name=RT11ExtractGUI-ARM64 rt11extract_gui.py --add-data="rt11extract;." --noconfirm

echo.
echo Trying Nuitka build...
python -m nuitka --onefile --enable-plugin=tk-inter --windows-disable-console --output-filename=RT11ExtractGUI-Nuitka.exe rt11extract_gui.py

echo.
echo Trying cx_Freeze build...
python setup_cx.py build

echo.
echo ============================================
echo BUILD COMPLETE! Check dist/ directory
echo ============================================
pause
