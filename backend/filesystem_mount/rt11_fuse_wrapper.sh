#!/bin/bash
# RT-11 FUSE Driver Wrapper for macOS/Linux
# ==========================================
# This script runs the standalone FUSE driver executable

# Get the directory where this script is located
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
FUSE_EXE="$SCRIPT_DIR/rt11_fuse"
FUSE_SCRIPT="$SCRIPT_DIR/rt11_fuse_complete.py"

# Try standalone executable first (preferred for distribution)
if [ -f "$FUSE_EXE" ] && [ -x "$FUSE_EXE" ]; then
    echo "Running standalone FUSE driver: $FUSE_EXE"
    echo "Arguments: $*"
    "$FUSE_EXE" "$@"
    exit $?
fi

# Fallback to Python script (for development)
if [ -f "$FUSE_SCRIPT" ]; then
    echo "Standalone executable not found, trying Python script: $FUSE_SCRIPT"
    echo "Arguments: $*"
    
    # Check if python3 command is available
    if command -v python3 >/dev/null 2>&1; then
        echo "Using 'python3' command"
        python3 "$FUSE_SCRIPT" "$@"
        exit $?
    fi
    
    # Check if python command is available
    if command -v python >/dev/null 2>&1; then
        echo "Using 'python' command"
        python "$FUSE_SCRIPT" "$@"
        exit $?
    fi
    
    echo "Error: No Python interpreter found"
    echo "Please install Python or run ./setup_fuse.sh"
    exit 1
fi

echo "Error: Neither standalone executable nor Python script found"
echo "Expected locations:"
echo "- $FUSE_EXE"
echo "- $FUSE_SCRIPT"
exit 1
