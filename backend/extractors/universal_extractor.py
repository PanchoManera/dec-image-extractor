#!/usr/bin/env python3
"""
Universal PDP-11 Filesystem Extractor
======================================

Universal extractor that automatically detects and handles:
- RT-11 filesystems (PDP-11)
- Unix v6/v7 filesystems (PDP-11)
- ODS-1/Files-11 filesystems (RSX-11M, RSX-11M+, RSX-11S, IAS, early VMS)

This script serves as a unified interface to all extractors,
automatically detecting the filesystem type and using the appropriate parser.
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

# Add backend/filesystems to Python path for imports
script_dir = Path(__file__).parent
backend_dir = script_dir.parent
filesystems_dir = backend_dir / 'filesystems'
sys.path.insert(0, str(filesystems_dir))
sys.path.insert(0, str(backend_dir))  # Add backend to path

# Import detection functions from each extractor
from utils.bundle_paths import get_rt11extract_path

def detect_rt11_filesystem(path):
    """Detect RT-11 filesystem using CLI extractor"""
    try:
        # Use helper to find path
        rt11extract_path = get_rt11extract_path()
        
        # Convert path to absolute path to avoid working directory issues
        abs_path = os.path.abspath(path)
        cmd = [str(rt11extract_path), abs_path, '-l']
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        # Debug output
        # print(f"DEBUG: RT-11 cmd: {cmd}")
        # print(f"DEBUG: RT-11 returncode: {result.returncode}")
        # print(f"DEBUG: RT-11 stdout: {result.stdout[:200]}...")
        # print(f"DEBUG: RT-11 stderr: {result.stderr}")
        
        if result.returncode == 0 and 'RT-11 Directory Listing' in result.stdout:
            # Count files
            lines = result.stdout.split('\n')
            file_count = 0
            for line in lines:
                if line.startswith('Total files:'):
                    file_count = int(line.split(':')[1].strip())
                    break
            
            if file_count > 0:
                return True, f"RT-11 filesystem ({file_count} files detected)"
            else:
                return True, "RT-11 filesystem detected"
        else:
            return False, f"Not an RT-11 filesystem (returncode: {result.returncode})"
    except FileNotFoundError as e:
        return False, f"RT-11 extractor (rt11extract) not found: {e}"
    except Exception as e:
        return False, f"RT-11 detection failed: {e}"

try:
    # Try to import unix_pdp11_extractor functions
    import unix_pdp11_extractor
    def detect_unix_filesystem(path):
        return unix_pdp11_extractor.detect_unix_filesystem(path)
except ImportError:
    def detect_unix_filesystem(path):
        return False, "Unix extractor not available"

try:
    # Try to import ODS-1 extractor functions
    from ods1_extractor_v2 import ODS1Extractor
    def detect_ods1_filesystem(path):
        try:
            extractor = ODS1Extractor(path)
            # Try to parse home block
            if extractor.parse_home_block():
                # Verify structure level is correct for ODS-1 (0x0101)
                if extractor.volume_structure_level != 0x0101:
                    return False, f"Invalid ODS-1 structure level: 0x{extractor.volume_structure_level:04x} (expected 0x0101)"
                
                # Additional validation: check if max_files is reasonable
                if extractor.max_files == 0 or extractor.max_files > 100000:
                    return False, f"Invalid max_files value: {extractor.max_files}"
                
                # Additional validation: check if index file bitmap LBN is reasonable
                if extractor.index_file_bitmap_lbn > extractor.total_blocks:
                    return False, f"Index file bitmap LBN ({extractor.index_file_bitmap_lbn}) exceeds disk size ({extractor.total_blocks})"
                
                vol_name = extractor.volume_name.strip()
                if vol_name:
                    return True, f"ODS-1/Files-11 filesystem (Volume: {vol_name})"
                else:
                    return True, "ODS-1/Files-11 filesystem (RSX-11 or early VMS) with enhanced TSK support"
            return False, "Not an ODS-1 filesystem"
        except Exception as e:
            return False, f"ODS-1 detection failed: {e}"
except ImportError:
    def detect_ods1_filesystem(path):
        return False, "ODS-1 extractor not available"

def detect_filesystem_type(image_path: str) -> tuple[str, str, str]:
    """
    Detect filesystem type and return (type, description, extractor_command)
    
    Returns:
        tuple: (filesystem_type, description, extractor_script)
        
    filesystem_type can be: 'rt11', 'unix', 'ods1', or 'unknown'
    """
    
    # Try ODS-1/Files-11 detection first (most specific)
    try:
        is_ods1, ods1_desc = detect_ods1_filesystem(image_path)
        if is_ods1:
            return 'ods1', ods1_desc, 'ods1_extractor_v2.py'
    except Exception as e:
        print(f"ODS-1 detection error: {e}")
    
    # Try RT-11 detection
    try:
        is_rt11, rt11_desc = detect_rt11_filesystem(image_path)
        if is_rt11:
            return 'rt11', rt11_desc, 'rt11_extractor_tu58em.py'
    except Exception as e:
        print(f"RT-11 detection error: {e}")
    
    # Try Unix detection
    try:
        is_unix, unix_desc = detect_unix_filesystem(image_path)
        if is_unix:
            return 'unix', unix_desc, 'unix_pdp11_extractor.py'
    except Exception as e:
        print(f"Unix detection error: {e}")
    
    return 'unknown', 'Unknown or unsupported PDP-11 filesystem', None

def run_extractor(extractor_script: str, image_path: str, args: argparse.Namespace) -> int:
    """Run the appropriate extractor with the given arguments"""
    
    if not extractor_script:
        print("❌ No suitable extractor found")
        return 1
    
    # Special handling for RT-11 - use same backend as GUI
    if 'rt11' in extractor_script:
        # Use helper to find path
        rt11extract_path = get_rt11extract_path()
        
        # Convert path to absolute path to avoid working directory issues
        abs_image_path = os.path.abspath(image_path)
        cmd = [str(rt11extract_path), abs_image_path]
        
        # Add RT-11 specific arguments
        if args.list:
            cmd.append('-l')
        if args.detailed:
            cmd.append('-d')
        if args.file:
            cmd.extend(['-f', args.file])
        if args.output and args.output != 'extracted':
            cmd.extend(['-o', args.output])
        if args.verbose:
            cmd.append('-v')
        
        try:
            # Run the RT-11 CLI extractor
            result = subprocess.run(cmd, capture_output=False, text=True)
            return result.returncode
        except FileNotFoundError:
            print(f"❌ RT-11 extractor (rt11extract) not found")
            return 1
        except Exception as e:
            print(f"❌ Error running RT-11 extractor: {e}")
            return 1
    
    # Build command line for other extractors - use correct paths
    script_dir = Path(__file__).parent
    backend_dir = script_dir.parent
    filesystems_dir = backend_dir / 'filesystems'
    extractor_path = filesystems_dir / extractor_script
    
    cmd = [sys.executable, str(extractor_path), image_path]
    
    # Add common arguments
    if args.list:
        cmd.append('-l')
    if args.detailed:
        cmd.append('-d')
    if args.file:
        cmd.extend(['-f', args.file])
    if args.output and args.output != 'extracted':
        cmd.extend(['-o', args.output])
    if args.verbose:
        cmd.append('-v')
    if args.detect_only:
        cmd.append('--detect-only')
    
    # Add filesystem-specific arguments
    if 'unix' in extractor_script and args.recursive:
        cmd.append('-r')
    
    # ODS-1 extractor uses -a for analysis only
    if 'ods1' in extractor_script and args.list:
        cmd.append('-a')  # Analysis mode for ODS-1
    
    try:
        # Run the extractor
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode
    except FileNotFoundError:
        print(f"❌ Extractor script not found: {extractor_script}")
        return 1
    except Exception as e:
        print(f"❌ Error running extractor: {e}")
        return 1

def main():
    parser = argparse.ArgumentParser(
        description="Universal PDP-11 Filesystem Extractor",
        epilog="""
Supported filesystems:
  RT-11      - PDP-11 RT-11 operating system
  Unix v6/v7 - PDP-11 Unix version 6 and 7
  ODS-1      - Files-11 Level 1 (RSX-11M, RSX-11M+, RSX-11S, IAS, early VMS)

Examples:
  %(prog)s disk.dsk -l                 # List files (auto-detect filesystem)
  %(prog)s disk.dsk -l -d              # List files with details
  %(prog)s disk.dsk                    # Extract all files
  %(prog)s disk.dsk -f HELLO.C         # Extract specific file
  %(prog)s disk.dsk --detect-only      # Only detect filesystem type
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("image", help="Disk image file")
    parser.add_argument("-l", "--list", action="store_true",
                       help="List files only, don't extract")
    parser.add_argument("-d", "--detailed", action="store_true",
                       help="Show detailed file information")
    parser.add_argument("-f", "--file", 
                       help="Extract specific file by name")
    parser.add_argument("-o", "--output", default="extracted",
                       help="Output directory (default: extracted)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("-r", "--recursive", action="store_true",
                       help="Recursive listing (Unix only)")
    parser.add_argument("--detect-only", action="store_true",
                       help="Only detect filesystem type")
    parser.add_argument("--force-type", choices=['rt11', 'unix', 'ods1'],
                       help="Force filesystem type (skip detection)")
    
    args = parser.parse_args()
    
    # Check if image file exists
    image_path = Path(args.image)
    if not image_path.exists():
        print(f"❌ Error: Image file not found: {args.image}")
        return 1
    
    # Force filesystem type if specified
    if args.force_type:
        extractor_map = {
            'rt11': 'rt11_extractor_tu58em.py',
            'unix': 'unix_pdp11_extractor.py',
            'ods1': 'ods1_extractor_v2.py'
        }
        fs_type = args.force_type
        description = f"Forced {fs_type.upper()} filesystem"
        extractor_script = extractor_map[fs_type]
        
        if args.verbose or args.detect_only:
            print(f"🔧 {description}")
        
        if args.detect_only:
            return 0
    else:
        # Auto-detect filesystem type
        if args.verbose:
            print(f"🔍 Detecting filesystem type for {args.image}...")
        
        fs_type, description, extractor_script = detect_filesystem_type(args.image)
        
        if args.detect_only:
            if fs_type != 'unknown':
                print(f"✅ {description}")
                return 0
            else:
                print(f"❌ {description}")
                return 1
        
        if fs_type == 'unknown':
            print(f"❌ Error: {description}")
            print("Supported formats: RT-11, Unix v6/v7")
            print("Use --force-type to override detection")
            return 1
        
        if args.verbose:
            print(f"✅ {description}")
    
    # Run the appropriate extractor
    if args.verbose:
        print(f"🚀 Using {fs_type.upper()} extractor...")
    
    return run_extractor(extractor_script, str(image_path), args)

if __name__ == '__main__':
    try:
        sys.exit(main())
    except KeyboardInterrupt:
        print("\n❌ Operation cancelled")
        sys.exit(130)
    except Exception as e:
        print(f"❌ Unexpected error: {e}")
        sys.exit(1)
