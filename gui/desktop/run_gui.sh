#!/bin/bash
# RT-11 GUI Launch Script with Virtual Environment Support
# This script automatically sets up and activates the virtual environment
# with FUSE dependencies for development use.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"

echo "RT-11 Extract GUI Launcher"
echo "=========================="
echo "Script directory: $SCRIPT_DIR"

# Check if virtual environment exists
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating virtual environment..."
    python3 -m venv "$VENV_DIR" --system-site-packages
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to create virtual environment"
        exit 1
    fi
    echo "✓ Virtual environment created"
fi

# Activate virtual environment
echo "Activating virtual environment..."
source "$VENV_DIR/bin/activate"
if [ $? -ne 0 ]; then
    echo "ERROR: Failed to activate virtual environment"
    exit 1
fi
echo "✓ Virtual environment activated"

# Check and install dependencies
echo "Checking dependencies..."

# Check for fusepy
python -c "import fuse" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing fusepy..."
    pip install fusepy
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install fusepy"
        exit 1
    fi
    echo "✓ fusepy installed"
else
    echo "✓ fusepy available"
fi

# Check for Pillow
python -c "import PIL" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "Installing Pillow..."
    pip install pillow
    if [ $? -ne 0 ]; then
        echo "ERROR: Failed to install Pillow"
        exit 1
    fi
    echo "✓ Pillow installed"
else
    echo "✓ Pillow available"
fi

# Check for macFUSE on macOS
if [[ "$OSTYPE" == "darwin"* ]]; then
    echo "Checking macFUSE installation..."
    if [ -f "/usr/local/lib/libfuse.dylib" ] || [ -f "/usr/local/lib/libfuse.2.dylib" ] || [ -f "/opt/homebrew/lib/libfuse.dylib" ]; then
        echo "✓ macFUSE detected"
    else
        echo "⚠️  WARNING: macFUSE not detected"
        echo "   For filesystem mounting, please install macFUSE from:"
        echo "   https://osxfuse.github.io/"
        echo ""
        echo "   Continuing without FUSE support..."
    fi
fi

echo ""
echo "Starting RT-11 Extract GUI..."
echo "============================="

# Launch the GUI with the virtual environment active
python rt11extract_gui.py "$@"

# Deactivate virtual environment
deactivate
