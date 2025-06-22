#!/usr/bin/env python3
"""
IMD to RAW/DSK Image Converter

Converts ImageDisk (.imd) format disk images to raw (.dsk/.raw) format.
Based on the original imd2raw.c implementation.

IMD format structure:
- ASCII header: "IMD v.v: dd/mm/yyyy hh:mm:ss"
- Comment terminated with 0x1a
- For each track:
  - mode (0-5): encoding type
  - cylinder number
  - head number  
  - sector count
  - sector size code (0-6)
  - sector numbering map
  - sector data records with type codes
"""

import sys
import struct
from typing import BinaryIO, List, Tuple, Optional

# Mode table for different encoding types
MODE_TABLE = [
    "500K FM", "300K FM", "250K FM", 
    "500K MFM", "300K MFM", "250K MFM"
]

# Sector size lookup table
SECTOR_SIZES = {
    0: 128, 1: 256, 2: 512, 3: 1024,
    4: 2048, 5: 4096, 6: 8192
}

class DiskImageValidator:
    """Validates disk image formats"""
    
    @staticmethod
    def is_valid_imd(file_path: str) -> bool:
        """Check if file is a valid IMD image"""
        try:
            with open(file_path, 'rb') as fp:
                # Check for IMD signature
                signature = fp.read(3)
                if signature != b'IMD':
                    return False
                    
                # Read until header terminator
                while True:
                    c = fp.read(1)
                    if not c:
                        return False
                    if c[0] == 0x1a:
                        break
                        
                # Try to read at least one track header
                mode_byte = fp.read(1)
                if not mode_byte or mode_byte[0] > 6:
                    return False
                    
                return True
        except:
            return False
            
    @staticmethod 
    def is_valid_rt11_dsk(file_path: str) -> bool:
        """Check if file is a valid RT-11 DSK image"""
        try:
            with open(file_path, 'rb') as fp:
                # Check minimum size (at least a few blocks)
                fp.seek(0, 2)  # Seek to end
                size = fp.tell()
                if size < 512:  # Too small to be a disk image
                    return False
                    
                # Check if size is multiple of 512 (block size)
                if size % 512 != 0:
                    return False
                    
                # For now, if it's a reasonable size disk image, accept it
                # RT-11 validation can be complex and varies by disk format
                # We'll let rt11extract handle the actual validation
                return True
                
        except:
            return False
            
    @staticmethod
    def get_disk_format(file_path: str) -> str:
        """Detect disk image format"""
        if DiskImageValidator.is_valid_imd(file_path):
            return "IMD"
        elif DiskImageValidator.is_valid_rt11_dsk(file_path):
            return "RT11_DSK"
        else:
            return "UNKNOWN"

class IMDConverter:
    """Converts IMD disk images to raw/DSK format"""
    
    def __init__(self, input_file: str, output_file: str, verbose: bool = False):
        self.input_file = input_file
        self.output_file = output_file
        self.verbose = verbose
        
    def log(self, message: str):
        """Print verbose logging messages"""
        if self.verbose:
            print(message, file=sys.stderr)
            
    def read_header(self, fp: BinaryIO) -> str:
        """Read and validate IMD header"""
        # Check for IMD signature
        signature = fp.read(3)
        if signature != b'IMD':
            raise ValueError("File doesn't start with 'IMD'")
            
        # Read header until 0x1a terminator
        header_chars = []
        while True:
            c = fp.read(1)
            if not c:
                raise ValueError("Unexpected end of file in header")
            if c[0] == 0x1a:
                break
            header_chars.append(chr(c[0]))
            
        header = ''.join(header_chars)
        self.log(f"IMD Header: {header}")
        return header
        
    def read_track(self, fp: BinaryIO) -> Optional[bytes]:
        """Read and process a single track from IMD file"""
        # Read track header
        mode_byte = fp.read(1)
        if not mode_byte:
            return None  # End of file
            
        mode = mode_byte[0]
        if mode > 6:
            raise ValueError(f"Stream out of sync at mode, got 0x{mode:02x}")
            
        cyl = fp.read(1)[0]
        if cyl > 80:
            raise ValueError(f"Stream out of sync at cylinder, got 0x{cyl:02x}")
            
        head = fp.read(1)[0]
        if head > 1:
            raise ValueError(f"Stream out of sync at head, got {head}")
            
        sector_count = fp.read(1)[0]
        sector_size_code = fp.read(1)[0]
        
        if sector_size_code not in SECTOR_SIZES:
            raise ValueError(f"Invalid sector size code: {sector_size_code}")
            
        sector_size = SECTOR_SIZES[sector_size_code]
        
        self.log(f"Cyl:{cyl:02d} Hd:{head} {MODE_TABLE[mode]} {sector_count} sectors size {sector_size}")
        
        # Read sector numbering map
        sector_map = []
        for i in range(sector_count):
            sector_map.append(fp.read(1)[0])
            
        # Initialize sector data storage
        sector_data = {}
        sector_types = []
        
        # Read sector data
        for i in range(sector_count):
            sector_type = fp.read(1)[0]
            sector_num = sector_map[i]
            
            if sector_type in [0, 5, 7]:  # Unavailable/bad sectors
                sector_types.append('X')
                sector_data[sector_num] = bytes([0xE5] * sector_size)
                
            elif sector_type == 1:  # Normal data
                sector_types.append('.')
                data = fp.read(sector_size)
                if len(data) != sector_size:
                    raise ValueError(f"Incomplete sector data: expected {sector_size}, got {len(data)}")
                sector_data[sector_num] = data
                
            elif sector_type == 3:  # Data with deleted data address mark
                sector_types.append('d')
                data = fp.read(sector_size)
                if len(data) != sector_size:
                    raise ValueError(f"Incomplete sector data: expected {sector_size}, got {len(data)}")
                sector_data[sector_num] = data
                
            elif sector_type in [2, 4, 6, 8]:  # Compressed data
                sector_types.append('C')
                fill_value = fp.read(1)[0]
                sector_data[sector_num] = bytes([fill_value] * sector_size)
                
            else:
                raise ValueError(f"Unknown sector type: {sector_type}")
                
        # Build track output showing sector types and numbers
        type_str = ''.join(sector_types)
        sector_nums = ' '.join(f"{s:2d}" for s in sector_map)
        self.log(f"Cyl {cyl:02d} Hd {head} {sector_size:4d} {type_str} {sector_nums}")
        
        # Generate raw track data in sector order
        track_data = bytearray()
        for sector_num in sorted(sector_data.keys()):
            track_data.extend(sector_data[sector_num])
            
        return bytes(track_data)
        
    def convert(self) -> bool:
        """Convert IMD file to raw/DSK format"""
        try:
            with open(self.input_file, 'rb') as input_fp:
                # Read header
                header = self.read_header(input_fp)
                
                # Open output file
                with open(self.output_file, 'wb') as output_fp:
                    track_count = 0
                    
                    # Process all tracks
                    while True:
                        track_data = self.read_track(input_fp)
                        if track_data is None:
                            break
                            
                        output_fp.write(track_data)
                        track_count += 1
                        
                    self.log(f"Conversion complete: {track_count} tracks processed")
                    return True
                    
        except FileNotFoundError:
            print(f"Error: Cannot open input file '{self.input_file}'", file=sys.stderr)
            return False
        except ValueError as e:
            print(f"Error: {e}", file=sys.stderr)
            return False
        except Exception as e:
            print(f"Unexpected error: {e}", file=sys.stderr)
            return False

def main():
    """Command line interface"""
    if len(sys.argv) != 3:
        print(f"Usage: {sys.argv[0]} input.imd output.dsk", file=sys.stderr)
        sys.exit(1)
        
    input_file = sys.argv[1] 
    output_file = sys.argv[2]
    
    converter = IMDConverter(input_file, output_file, verbose=True)
    if converter.convert():
        print(f"Successfully converted '{input_file}' to '{output_file}'")
        sys.exit(0)
    else:
        sys.exit(1)

if __name__ == "__main__":
    main()
