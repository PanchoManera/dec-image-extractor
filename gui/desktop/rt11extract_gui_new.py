#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox
import subprocess
import os
import sys
from pathlib import Path

def get_rt11extract_cli_path():
    """Get path to rt11extract CLI tool"""
    exe_dir = Path(sys.executable).parent if getattr(sys, 'frozen', False) else Path(__file__).parent
    
    if getattr(sys, 'frozen', False):
        # Running from frozen/bundled mode
        if sys.platform.startswith('win'):
            # Windows: Try all possible CLI executables
            cli_options = [
                "RT11Extract.exe",           # Main CLI name
                "rt11extract_universal.exe", # Universal extractor
                "rt11extract_cli.exe",      # Alternative name
                "rt11extract.exe"           # Basic name with .exe
            ]
            
            for cli in cli_options:
                cli_path = exe_dir / cli
                if cli_path.exists():
                    return cli_path
                    
        elif sys.platform == 'darwin':
            # macOS: Check bundled CLI tools directory
            bundle_cli_dir = exe_dir.parent / "cli"
            if bundle_cli_dir.exists():
                cli_options = [
                    "rt11extract_cli",    # Main CLI
                    "rt11extract",           # Alternative name
                    "RT11Extract"           # Alternative name
                ]
                
                for cli in cli_options:
                    cli_path = bundle_cli_dir / cli
                    if cli_path.exists():
                        # Make it executable
                        cli_path.chmod(cli_path.stat().st_mode | 0o755)
                        return cli_path
                        
            # If not found in bundle, error in frozen mode
            print(f"ERROR: CLI not found in bundle at {bundle_cli_dir}")
            return None
            
    # Default development mode paths
    dev_paths = [
        Path(__file__).parent.parent.parent / "backend" / "extractors" / "rt11extract",
        Path.cwd() / "backend" / "extractors" / "rt11extract"
    ]
    
    for path in dev_paths:
        if path.exists():
            return path
            
    # Last resort: Try current directory
    return Path.cwd() / "rt11extract"
