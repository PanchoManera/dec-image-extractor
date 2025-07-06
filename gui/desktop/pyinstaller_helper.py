#!/usr/bin/env python3
"""
PyInstaller Helper - Path resolution for RT-11 Extractor GUI
Helps find backend files when running as compiled executable
"""

import sys
import os
from pathlib import Path

def get_resource_path(relative_path):
    """Get absolute path to resource, works for dev and for PyInstaller"""
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")
    
    return os.path.join(base_path, relative_path)

def get_backend_path():
    """Get path to backend directory"""
    if getattr(sys, 'frozen', False):
        # Running as compiled executable
        # Check if backend is included in the executable
        try:
            backend_path = get_resource_path("backend")
            if os.path.exists(backend_path):
                return Path(backend_path)
        except:
            pass
        
        # Fallback: look relative to executable
        exe_dir = Path(sys.executable).parent
        backend_path = exe_dir / "backend"
        if backend_path.exists():
            return backend_path
        
        # Another fallback: look in parent directory 
        backend_path = exe_dir.parent / "backend"
        if backend_path.exists():
            return backend_path
    else:
        # Running as script
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "backend"
    
    return None

def get_rt11extract_cli_path():
    """Get path to RT-11 extract CLI executable.
    Windows: Tries RT11Extract.exe, rt11extract_universal.exe, universal_extractor.exe
    macOS: Tries CLIs in Contents/cli/ inside app bundle
    """
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        
        if sys.platform.startswith('win'):
            # Windows: Try all CLI executables in same directory
            cli_names = [
                "RT11Extract.exe",
                "rt11extract_universal.exe",
                "universal_extractor.exe"
            ]
            for name in cli_names:
                cli_path = exe_dir / name
                if cli_path.exists():
                    return cli_path
                    
        elif sys.platform == 'darwin':
            # macOS: Try CLIs in bundle's cli directory
            if str(exe_dir).endswith('.app/Contents/MacOS'):
                cli_dir = exe_dir.parent.parent / "cli"
                cli_names = [
                    "rt11extract_cli",
                    "rt11extract_universal",
                    "universal_extractor"
                ]
                for name in cli_names:
                    cli_path = cli_dir / name
                    if cli_path.exists():
                        return cli_path
                        
            # Fallback: Try parent directory for standalone executables
            else:
                return exe_dir / "rt11extract_cli"
                
        else:  # Linux
            return exe_dir / "RT11Extract"
            
    else:
        # Running as script - use backend script directly
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "backend" / "extractors" / "rt11extract"
    
    return None

def get_imd2raw_path():
    """Get path to imd2raw executable.
    Windows: Uses imd2raw.exe in same directory
    macOS: Uses imd2raw in Contents/cli/ inside app bundle
    """
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        
        if sys.platform.startswith('win'):
            # Windows: imd2raw.exe in same directory
            return exe_dir / "imd2raw.exe"
            
        elif sys.platform == 'darwin':
            # macOS: imd2raw in bundle's cli directory
            if str(exe_dir).endswith('.app/Contents/MacOS'):
                cli_dir = exe_dir.parent.parent / "cli"
                return cli_dir / "imd2raw"
            # Fallback: same directory for standalone
            else:
                return exe_dir / "imd2raw"
                
        else:  # Linux
            return exe_dir / "imd2raw"
            
    else:
        # Running as script
        script_dir = Path(__file__).parent.parent.parent
        return script_dir / "backend" / "image_converters" / "imd2raw.py"
    
    return None

def find_backend_script(script_relative_path):
    """Find a backend script by relative path"""
    backend_path = get_backend_path()
    if backend_path:
        script_path = backend_path / script_relative_path
        if script_path.exists():
            return script_path
    
    return None

def is_frozen():
    """Check if running as PyInstaller executable"""
    return getattr(sys, 'frozen', False)

def get_script_dir():
    """Get directory containing the main script/executable"""
    if is_frozen():
        return Path(sys.executable).parent
    else:
        return Path(__file__).parent.parent.parent

def setup_backend_path():
    """Setup backend path in sys.path for imports"""
    backend_path = get_backend_path()
    if backend_path and str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    return backend_path
