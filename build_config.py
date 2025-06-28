#!/usr/bin/env python3
"""
Build configuration helper for PyInstaller.
This script helps PyInstaller find all dependencies across different platforms.
"""

import sys
import os
from pathlib import Path

# Add all backend paths to Python path
current_dir = Path(__file__).parent
backend_path = current_dir / "backend"
gui_path = current_dir / "gui" / "desktop"

# Add to sys.path so PyInstaller can find modules
sys.path.insert(0, str(backend_path))
sys.path.insert(0, str(gui_path))
sys.path.insert(0, str(current_dir))

# Import all modules to help PyInstaller discover dependencies
try:
    from backend.image_converters.imd2raw import IMDConverter, DiskImageValidator
    print("✓ Successfully imported IMDConverter")
except ImportError as e:
    print(f"✗ Could not import IMDConverter: {e}")

try:
    from backend.filesystem_mount.rt11_winfsp import RT11WinFspDriver
    print("✓ Successfully imported RT11WinFspDriver")
except ImportError as e:
    print(f"✗ Could not import RT11WinFspDriver: {e}")

try:
    from backend.filesystem_mount.rt11_fuse_complete import RT11FuseDriver
    print("✓ Successfully imported RT11FuseDriver")
except ImportError as e:
    print(f"✗ Could not import RT11FuseDriver: {e}")

try:
    import tkinter as tk
    from tkinter import ttk, filedialog, messagebox, scrolledtext
    print("✓ Successfully imported tkinter")
except ImportError as e:
    print(f"✗ Could not import tkinter: {e}")

try:
    from PIL import Image, ImageTk
    print("✓ Successfully imported PIL")
except ImportError as e:
    print(f"✗ Could not import PIL (optional): {e}")

try:
    import refuse
    print("✓ Successfully imported refuse")
except ImportError as e:
    print(f"✗ Could not import refuse (optional): {e}")

try:
    import fuse
    print("✓ Successfully imported fuse")
except ImportError as e:
    print(f"✗ Could not import fuse (optional): {e}")

if __name__ == "__main__":
    print("Build configuration check completed")
    print(f"Current directory: {current_dir}")
    print(f"Backend path: {backend_path}")
    print(f"GUI path: {gui_path}")
    print(f"Python path: {sys.path[:3]}")
