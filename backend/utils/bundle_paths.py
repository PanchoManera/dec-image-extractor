#!/usr/bin/env python3
"""
Bundle Path Helper for RT11 Extractor
====================================

This module provides utilities for finding bundled executables when running
in PyInstaller frozen mode, especially on macOS where CLI tools are in
Contents/Frameworks/cli/
"""

import sys
import os
from pathlib import Path

def get_bundled_executable_path(exe_name: str) -> Path:
    """
    Get path to bundled executable, handling frozen mode correctly
    
    Args:
        exe_name: Name of executable (e.g., 'rt11extract_cli', 'imd2raw', 'universal_extractor')
        
    Returns:
        Path to executable
    """
    if getattr(sys, 'frozen', False):
        # We're running in PyInstaller frozen mode
        exe_dir = Path(sys.executable).parent
        
        if sys.platform == 'darwin':
            # macOS: Look in Contents/Frameworks/cli/
            bundle_cli_dir = exe_dir.parent / "Frameworks" / "cli"
            exe_path = bundle_cli_dir / exe_name
            if exe_path.exists():
                # Make sure it's executable
                exe_path.chmod(exe_path.stat().st_mode | 0o755)
                return exe_path
        elif sys.platform.startswith('win'):
            # Windows: Same directory as main executable
            exe_path = exe_dir / f"{exe_name}.exe"
            if exe_path.exists():
                return exe_path
        else:
            # Linux: Same directory as main executable
            exe_path = exe_dir / exe_name
            if exe_path.exists():
                exe_path.chmod(exe_path.stat().st_mode | 0o755)
                return exe_path
    
    # Not frozen or not found in bundle - try relative paths
    script_dir = Path(__file__).parent.parent  # backend/
    
    # Common locations to search
    search_paths = [
        script_dir / "extractors" / exe_name,  # backend/extractors/
        script_dir / "image_converters" / f"{exe_name}.py",  # backend/image_converters/
        Path.cwd() / exe_name,  # Current directory
        Path.cwd() / f"{exe_name}.py",  # Current directory with .py
    ]
    
    for path in search_paths:
        if path.exists():
            return path
    
    # Last resort: assume it's in PATH
    return Path(exe_name)

def get_rt11extract_path() -> Path:
    """Get path to RT11Extract CLI tool"""
    # Try different names in order of preference
    for name in ['rt11extract_cli', 'rt11extract', 'RT11Extract']:
        path = get_bundled_executable_path(name)
        if path.exists():
            return path
    
    # Return first preference even if not found
    return get_bundled_executable_path('rt11extract_cli')

def get_imd2raw_path() -> Path:
    """Get path to imd2raw converter tool"""
    return get_bundled_executable_path('imd2raw')

def get_universal_extractor_path() -> Path:
    """Get path to universal extractor tool"""
    return get_bundled_executable_path('universal_extractor')
