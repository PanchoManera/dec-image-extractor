#!/usr/bin/env python3
"""
Windows-compatible wrapper for universal_extractor.py
====================================================

This file serves as a replacement for the symbolic link pdp11_smart_extractor.py
that doesn't work on Windows. It simply imports and executes the universal_extractor.py
module to provide the same functionality.

This allows the FUSE driver to work on Windows without requiring symbolic links.
"""

import sys
import os
from pathlib import Path

# Add the extractors directory to the Python path
current_dir = Path(__file__).parent
extractors_dir = current_dir.parent / "extractors"
sys.path.insert(0, str(extractors_dir))

# Import and run the universal extractor
try:
    from universal_extractor import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Error importing universal_extractor: {e}")
    print(f"Looking for extractors in: {extractors_dir}")
    sys.exit(1)
