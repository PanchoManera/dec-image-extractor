#!/usr/bin/env python3
"""
RT-11 WinFsp Driver for Windows
===============================

Windows-compatible FUSE driver for mounting RT-11 disk images using WinFsp.
This is the Windows equivalent of the FUSE driver for macOS/Linux.

WinFsp: https://winfsp.dev/
Install WinFsp from: https://github.com/winfsp/winfsp/releases

Usage:
    python rt11_winfsp.py <image.dsk> <mount_point>

Example:
    python rt11_winfsp.py disk.dsk Z:

Requirements:
    pip install refuse
    WinFsp installed from https://winfsp.dev/
"""

import os
import sys
import errno
import stat
import time
import logging
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional

# Check if running on Windows
if sys.platform != "win32":
    print("Error: This driver is only for Windows systems.")
    print("Use rt11_fuse_complete.py on macOS/Linux instead.")
    sys.exit(1)

# Import WinFsp-compatible FUSE library
try:
    from refuse.high import FUSE, FuseOSError, Operations, LoggingMixIn
    WINFSP_AVAILABLE = True
except ImportError:
    try:
        # Fallback to regular fusepy (might work with WinFsp)
        from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
        WINFSP_AVAILABLE = True
    except ImportError:
        WINFSP_AVAILABLE = False

class RT11FileEntry:
    """Representation of an RT-11 file"""
    def __init__(self, filename, file_type, size_blocks, start_block, status=0):
        self.filename = filename.strip()
        self.file_type = file_type.strip()
        self.size_blocks = size_blocks
        self.start_block = start_block
        self.status = status
        self.creation_date = None
        
    @property
    def full_filename(self):
        if self.file_type:
            return f"{self.filename}.{self.file_type}"
        return self.filename
    
    @property
    def size_bytes(self):
        return self.size_blocks * 512
    
    @property
    def is_protected(self):
        return (self.status & 0x0100) != 0
    
    @property
    def is_valid(self):
        return len(self.filename.strip()) > 0

class RT11ExtractorWrapper:
    """Wrapper for RT-11 extractor on Windows"""
    
    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        # Look for RT11Extract.exe in various locations
        script_dir = Path(__file__).parent
        cwd = Path.cwd()
        
        search_paths = [
            script_dir / "RT11Extract.exe",
            script_dir / "rt11extract.exe", 
            script_dir / "rt11extract",
            cwd / "RT11Extract.exe",
            cwd / "rt11extract.exe",
            cwd / "rt11extract",
            Path(sys.executable).parent / "RT11Extract.exe",  # When running from packaged exe
            Path(sys.executable).parent / "rt11extract.exe",
            Path(sys.executable).parent / "rt11extract"
        ]
        
        self.rt11extract_path = None
        for path in search_paths:
            if path.exists():
                self.rt11extract_path = path
                break
        
        self.logger = logging.getLogger('RT11-Extractor')
        self._file_data_cache = {}
        
        if not self.rt11extract_path:
            error_msg = f"RT11Extract not found. Searched in: {[str(p) for p in search_paths]}"
            print(error_msg)
            raise Exception(error_msg)
        
    def list_files(self) -> List[RT11FileEntry]:
        """Get list of files by extracting to temporary directory"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Run RT11Extract to extract all files
                cmd = [str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60, 
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode != 0:
                    self.logger.error(f"RT11Extract failed: {result.stderr}")
                    return []
                
                # Scan extracted files
                files = []
                for file_path in temp_path.iterdir():
                    if file_path.is_file() and not file_path.name.endswith('.rt11info'):
                        filename = file_path.name
                        size_bytes = file_path.stat().st_size
                        size_blocks = (size_bytes + 511) // 512
                        
                        # Separate name and extension
                        if '.' in filename:
                            name, ext = filename.rsplit('.', 1)
                        else:
                            name, ext = filename, ""
                        
                        entry = RT11FileEntry(name, ext, size_blocks, 0)
                        files.append(entry)
                        
                        # Cache file data
                        self._file_data_cache[filename] = file_path.read_bytes()
                
                self.logger.info(f"Found {len(files)} files")
                return files
                
        except subprocess.TimeoutExpired:
            self.logger.error("RT11Extract timeout")
            return []
        except Exception as e:
            self.logger.error(f"Error running RT11Extract: {e}")
            return []
    
    def extract_file_data(self, filename: str) -> bytes:
        """Extract data for a specific file"""
        # Try cache first
        if filename in self._file_data_cache:
            return self._file_data_cache[filename]
            
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Extract all files (RT11Extract doesn't support single file extraction easily)
                cmd = [str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30,
                                      creationflags=subprocess.CREATE_NO_WINDOW)
                
                if result.returncode != 0:
                    self.logger.error(f"Error extracting {filename}: {result.stderr}")
                    return b''
                
                # Find the requested file
                extracted_file = temp_path / filename
                if extracted_file.exists():
                    data = extracted_file.read_bytes()
                    self._file_data_cache[filename] = data
                    return data
                
                # Try case-insensitive search
                for file in temp_path.glob("*"):
                    if file.name.upper() == filename.upper():
                        data = file.read_bytes()
                        self._file_data_cache[filename] = data
                        return data
                
                self.logger.error(f"File {filename} not found after extraction")
                return b''
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout extracting {filename}")
            return b''
        except Exception as e:
            self.logger.error(f"Error extracting {filename}: {e}")
            return b''

class RT11FileSystemWinFsp(LoggingMixIn, Operations):
    """RT-11 filesystem for WinFsp on Windows"""
    
    def __init__(self, disk_image_path: str):
        self.disk_image_path = disk_image_path
        self.extractor = RT11ExtractorWrapper(disk_image_path)
        self.files_cache: Dict[str, RT11FileEntry] = {}
        self.file_data_cache: Dict[str, bytes] = {}
        self.last_scan_time = 0
        self.cache_timeout = 30
        
        # Configure logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RT11-WinFsp')
        
        # Initial scan
        self._scan_files()
    
    def _scan_files(self):
        """Scan files from RT-11 image"""
        try:
            current_time = time.time()
            if current_time - self.last_scan_time < self.cache_timeout:
                return
                
            self.logger.info("Scanning RT-11 files...")
            self.files_cache.clear()
            self.file_data_cache.clear()
            
            files = self.extractor.list_files()
            
            for file_entry in files:
                if file_entry.is_valid:
                    filename = file_entry.full_filename
                    # Make filename Windows-safe
                    safe_filename = self._make_windows_safe_filename(filename)
                    self.files_cache[safe_filename] = file_entry
                    
                    # Copy data from extractor cache
                    if filename in self.extractor._file_data_cache:
                        self.file_data_cache[safe_filename] = self.extractor._file_data_cache[filename]
                    
            self.last_scan_time = current_time
            self.logger.info(f"Scanned {len(self.files_cache)} files")
            
        except Exception as e:
            self.logger.error(f"Error scanning files: {e}")
    
    def _make_windows_safe_filename(self, filename: str) -> str:
        """Make filename safe for Windows"""
        # Replace characters not allowed in Windows filenames
        unsafe_chars = '<>:"|?*'
        safe_name = filename
        for char in unsafe_chars:
            safe_name = safe_name.replace(char, '_')
        
        # Handle reserved names
        reserved_names = ['CON', 'PRN', 'AUX', 'NUL', 'COM1', 'COM2', 'COM3', 'COM4', 
                         'COM5', 'COM6', 'COM7', 'COM8', 'COM9', 'LPT1', 'LPT2', 
                         'LPT3', 'LPT4', 'LPT5', 'LPT6', 'LPT7', 'LPT8', 'LPT9']
        
        name_part = safe_name.split('.')[0].upper()
        if name_part in reserved_names:
            safe_name = f"_{safe_name}"
        
        return safe_name.upper()  # RT-11 traditionally uses uppercase
    
    def _get_file_data(self, filename: str) -> bytes:
        """Get file data with caching"""
        if filename in self.file_data_cache:
            return self.file_data_cache[filename]
            
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        try:
            # Convert back to original name
            original_name = filename.replace('_', '')  # Simple reverse conversion
            data = self.extractor.extract_file_data(original_name)
            
            if len(data) < 1024 * 1024:  # Cache files smaller than 1MB
                self.file_data_cache[filename] = data
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error getting file data for {filename}: {e}")
            raise FuseOSError(errno.EIO)

    # FUSE Operations
    
    def getattr(self, path, fh=None):
        """Get file/directory attributes"""
        self._scan_files()
        
        if path == '/':
            # Root directory
            st = dict(
                st_mode=(stat.S_IFDIR | 0o755),
                st_ctime=time.time(),
                st_mtime=time.time(),
                st_atime=time.time(),
                st_nlink=2,
                st_size=0,
                st_uid=0,  # Windows doesn't use Unix UIDs
                st_gid=0
            )
            return st
        
        filename = path[1:]  # Remove leading '/'
        
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        file_entry = self.files_cache[filename]
        size_bytes = file_entry.size_bytes
        mtime = time.time()
        
        st = dict(
            st_mode=(stat.S_IFREG | 0o644),
            st_ctime=mtime,
            st_mtime=mtime,
            st_atime=mtime,
            st_nlink=1,
            st_size=size_bytes,
            st_uid=0,
            st_gid=0
        )
        
        # Protected files are read-only
        if file_entry.is_protected:
            st['st_mode'] = stat.S_IFREG | 0o444
            
        return st
    
    def readdir(self, path, fh):
        """List directory contents"""
        if path != '/':
            raise FuseOSError(errno.ENOTDIR)
            
        self._scan_files()
        
        entries = ['.', '..']
        entries.extend(self.files_cache.keys())
        
        for entry in entries:
            yield entry
    
    def open(self, path, flags):
        """Open file"""
        filename = path[1:]
        
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        # Read-only filesystem
        if flags & (os.O_WRONLY | os.O_RDWR):
            raise FuseOSError(errno.EACCES)
            
        return 0
    
    def read(self, path, size, offset, fh):
        """Read file data"""
        filename = path[1:]
        
        try:
            data = self._get_file_data(filename)
            end = offset + size
            return data[offset:end]
            
        except Exception as e:
            self.logger.error(f"Error reading {filename}: {e}")
            raise FuseOSError(errno.EIO)
    
    def statfs(self, path):
        """Get filesystem statistics"""
        try:
            total_blocks = 0
            used_blocks = 0
            
            for file_entry in self.files_cache.values():
                total_blocks += file_entry.size_blocks
                used_blocks += file_entry.size_blocks
            
            if total_blocks == 0:
                total_blocks = 1000
                
            free_blocks = max(0, total_blocks - used_blocks)
            
            return dict(
                f_bsize=512,
                f_frsize=512,
                f_blocks=total_blocks,
                f_bfree=free_blocks,
                f_bavail=free_blocks,
                f_files=len(self.files_cache),
                f_ffree=0,
                f_favail=0,
                f_namemax=255
            )
        except:
            return dict(
                f_bsize=512,
                f_frsize=512,
                f_blocks=1000,
                f_bfree=100,
                f_bavail=100,
                f_files=len(self.files_cache),
                f_ffree=0,
                f_favail=0,
                f_namemax=255
            )

def check_winfsp_requirements():
    """Check if WinFsp is available on Windows"""
    if sys.platform != "win32":
        print("Error: This driver is only for Windows systems.")
        return False
    
    if not WINFSP_AVAILABLE:
        print("Error: refuse library not installed.")
        print("Install with: pip install refuse")
        return False
    
    # Check if WinFsp is installed
    winfsp_paths = [
        "C:\\Program Files (x86)\\WinFsp\\bin\\winfsp-x64.dll",
        "C:\\Program Files\\WinFsp\\bin\\winfsp-x64.dll",
        "C:\\Program Files (x86)\\WinFsp\\bin\\winfsp-x86.dll"
    ]
    
    winfsp_found = any(os.path.exists(path) for path in winfsp_paths)
    
    if not winfsp_found:
        print("Error: WinFsp not found.")
        print("Download and install WinFsp from: https://winfsp.dev/")
        print("Direct download: https://github.com/winfsp/winfsp/releases")
        return False
    
    return True

def main():
    """Main function"""
    if len(sys.argv) != 3:
        print("RT-11 WinFsp Driver for Windows")
        print("===============================")
        print()
        print("Usage: python rt11_winfsp.py <image.dsk> <mount_point>")
        print()
        print("Examples:")
        print("  python rt11_winfsp.py disk.dsk Z:")
        print("  python rt11_winfsp.py image.imd R:")
        print()
        print("To unmount:")
        print("  Right-click on the mounted drive and select 'Eject'")
        print("  Or use: net use Z: /delete")
        print()
        print("Requirements:")
        print("  - refuse: pip install refuse")
        print("  - WinFsp: https://winfsp.dev/")
        sys.exit(1)
    
    if not check_winfsp_requirements():
        sys.exit(1)
    
    disk_image = sys.argv[1]
    mount_point = sys.argv[2]
    
    # Verify image exists
    if not os.path.exists(disk_image):
        print(f"Error: Image file {disk_image} not found")
        sys.exit(1)
    
    # Normalize mount point for Windows
    if not mount_point.endswith(':'):
        if len(mount_point) == 1:
            mount_point += ':'
        else:
            print("Error: Mount point should be a drive letter (e.g., Z:)")
            sys.exit(1)
    
    print(f"Mounting RT-11 image: {disk_image}")
    print(f"Mount point: {mount_point}")
    print("Press Ctrl+C to unmount")
    print()
    
    # Create and run filesystem
    try:
        fs = RT11FileSystemWinFsp(disk_image)
        
        # WinFsp-specific options
        mount_options = {
            'foreground': True,
            'debug': False,
            'nothreads': True,
            'volname': f"RT11-{Path(disk_image).stem}"
        }
        
        FUSE(fs, mount_point, **mount_options)
        
    except KeyboardInterrupt:
        print("\nUnmounting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
