#!/bin/bash
echo "============================================"
echo "RT-11 Extractor Ultimate Linux Builder"
echo "============================================"
echo "Installing requirements..."
pip3 install pyinstaller pillow nuitka cx_freeze

echo ""
echo "Trying PyInstaller build..."
pyinstaller --onefile --windowed --name=RT11ExtractGUI-Linux64 rt11extract_gui.py --add-data="rt11extract:." --noconfirm

echo ""
echo "Trying Nuitka build..."
python3 -m nuitka --onefile --enable-plugin=tk-inter --output-filename=RT11ExtractGUI-Nuitka-Linux rt11extract_gui.py

echo ""
echo "Trying cx_Freeze build..."
python3 setup_cx.py build

echo ""
echo "============================================"
echo "BUILD COMPLETE! Check dist/ directory"
echo "============================================"
