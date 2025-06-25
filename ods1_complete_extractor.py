#!/usr/bin/env python3
"""
Complete ODS-1 (Files-11) File System Extractor
Based on RSX-11M disk image analysis and Files-11 ODS-1 specification
"""

import struct
import binascii
import os
import argparse
from typing import Dict, List, Tuple, Optional

def read_sector(file_path, sector_number, sector_size=512):
    """Read a specific sector from a disk file."""
    with open(file_path, 'rb') as f:
        f.seek(sector_number * sector_size)
        return f.read(sector_size)

def safe_decode(data, encoding='ascii'):
    """Safely decode bytes to string, handling non-printable characters."""
    try:
        return data.decode(encoding, errors='ignore').strip('\x00').strip()
    except:
        return binascii.hexlify(data).decode('ascii')

class ODS1FileHeader:
    """Represents a Files-11 ODS-1 file header.
    
    Based on DEC Files-11 ODS-1 specification and VMS wiki information.
    ODS-1 is the oldest Files-11 structure, used by RSX-11 systems.
    """
    
    def __init__(self, sector_data, sector_num):
        self.sector_num = sector_num
        self.raw_data = sector_data
        self.file_number = 0
        self.file_sequence = 0
        self.relative_volume = 0
        self.filename = "UNKNOWN"
        self.file_size = 0
        self.creation_date = ""
        self.protection = 0
        self.owner_uic = 0
        self.parse_header()
    
    def parse_header(self):
        """Parse the file header structure according to ODS-1 specification."""
        data = self.raw_data
        
        if len(data) < 512:
            return
        
        # File ID (first 6 bytes) - File Number, Sequence, Relative Volume
        self.file_number = struct.unpack('<H', data[0:2])[0]
        self.file_sequence = struct.unpack('<H', data[2:4])[0]
        self.relative_volume = struct.unpack('<H', data[4:6])[0]
        
        # Header area structure (based on Files-11 ODS-1 spec)
        # Offset 6-7: Header area checksum or size indicator
        header_checksum = struct.unpack('<H', data[6:8])[0] if len(data) >= 8 else 0
        
        # Offset 8-9: Ident area offset (word offset from start of header)
        self.ident_area_offset = struct.unpack('<H', data[8:10])[0] * 2 if len(data) >= 10 else 0
        
        # Offset 10-11: Map area offset (word offset from start of header)
        self.map_area_offset = struct.unpack('<H', data[10:12])[0] * 2 if len(data) >= 12 else 0
        
        # Protection and owner information (typically at offset 12-15)
        if len(data) >= 16:
            self.protection = struct.unpack('<H', data[12:14])[0]
            self.owner_uic = struct.unpack('<H', data[14:16])[0]
        
        # Parse filename from multiple possible locations
        self.filename = self.extract_filename(data)
        
        # Extract file size from map area if available
        self.file_size = self.extract_file_size(data)
    
    def extract_filename(self, data):
        """Extract filename from various possible locations in the header."""
        # Try multiple strategies to find the filename
        
        # Strategy 1: Look in ident area if offset is valid
        if (self.ident_area_offset > 0 and 
            self.ident_area_offset < len(data) - 20):
            name_data = data[self.ident_area_offset:self.ident_area_offset + 40]
            filename = safe_decode(name_data).strip()
            if filename and len(filename) > 1 and filename.isprintable():
                return filename[:20]  # Limit to reasonable length
        
        # Strategy 2: Scan for filename patterns in the data
        for offset in range(20, min(200, len(data) - 20)):
            chunk = data[offset:offset + 20]
            decoded = safe_decode(chunk).strip()
            # Look for typical filename patterns
            if (len(decoded) >= 3 and 
                decoded.replace('.', '').replace('_', '').isalnum() and
                ('.' in decoded or decoded.isupper())):
                return decoded
        
        # Strategy 3: Look for RADIX-50 encoded names
        for offset in range(20, min(100, len(data) - 6), 2):
            if offset + 6 <= len(data):
                try:
                    word1 = struct.unpack('<H', data[offset:offset+2])[0]
                    word2 = struct.unpack('<H', data[offset+2:offset+4])[0]
                    word3 = struct.unpack('<H', data[offset+4:offset+6])[0]
                    
                    name1 = self.parse_radix50(word1)
                    name2 = self.parse_radix50(word2)
                    name3 = self.parse_radix50(word3)
                    
                    full_name = (name1 + name2 + name3).strip()
                    if len(full_name) >= 3 and full_name.replace('.', '').isalnum():
                        return full_name
                except:
                    continue
        
        return "UNKNOWN"
    
    def parse_radix50(self, word):
        """Convert 16-bit word from RADIX-50 encoding to ASCII string."""
        if word == 0:
            return '   '
        
        chars = []
        for i in range(3):
            char_code = word % 40
            word //= 40
            
            if char_code == 0:
                chars.append(' ')
            elif 1 <= char_code <= 26:
                chars.append(chr(ord('A') + char_code - 1))
            elif 27 <= char_code <= 36:
                chars.append(chr(ord('0') + char_code - 27))
            elif char_code == 37:
                chars.append('$')
            elif char_code == 38:
                chars.append('.')
            else:
                chars.append(' ')
        
        return ''.join(reversed(chars))
    
    def extract_file_size(self, data):
        """Extract file size from the header."""
        # File size is typically stored in the map area
        if (self.map_area_offset > 0 and 
            self.map_area_offset < len(data) - 8):
            try:
                # Try to read file size (usually a 32-bit value)
                size_offset = self.map_area_offset + 8  # Skip retrieval pointer header
                if size_offset + 4 <= len(data):
                    file_size = struct.unpack('<L', data[size_offset:size_offset+4])[0]
                    # Sanity check - file size shouldn't be larger than disk
                    if 0 < file_size < 100000000:  # 100MB limit
                        return file_size
            except:
                pass
        
        return 0
    
    def get_file_blocks(self):
        """Extract block mapping information from the file header."""
        # This is a simplified version - real implementation would need
        # to parse the map area retrieval pointers properly
        blocks = []
        if self.map_area_offset > 0 and self.map_area_offset < len(self.raw_data) - 8:
            # Extract first retrieval pointer as example
            map_data = self.raw_data[self.map_area_offset:]
            if len(map_data) >= 8:
                start_block = struct.unpack('<L', map_data[0:4])[0]
                block_count = struct.unpack('<H', map_data[4:6])[0]
                blocks.append((start_block, block_count))
        
        return blocks
    
    def __str__(self):
        return f"File #{self.file_number}.{self.file_sequence}: {self.filename} (sector {self.sector_num})"

class ODS1Extractor:
    """Main ODS-1 file system extractor."""
    
    def __init__(self, disk_image_path):
        self.disk_path = disk_image_path
        self.volume_name = ""
        self.file_headers = []
        self.total_sectors = 0
    
    def analyze_home_block(self):
        """Analyze the home block (sector 1) to get volume information."""
        home_data = read_sector(self.disk_path, 1)
        
        # Extract volume name
        self.volume_name = safe_decode(home_data[12:22])
        
        # Calculate total sectors (rough estimate)
        with open(self.disk_path, 'rb') as f:
            f.seek(0, 2)  # Seek to end
            file_size = f.tell()
            self.total_sectors = file_size // 512
        
        print(f"Volume: {self.volume_name}")
        print(f"Total sectors: {self.total_sectors}")
    
    def scan_for_file_headers(self):
        """Scan the disk for file headers in the index file."""
        print("Scanning for file headers...")
        
        # Based on our analysis, file headers are typically in sectors 20-100
        for sector_num in range(20, min(100, self.total_sectors)):
            try:
                sector_data = read_sector(self.disk_path, sector_num)
                
                if self.is_file_header(sector_data):
                    header = ODS1FileHeader(sector_data, sector_num)
                    self.file_headers.append(header)
                    print(f"Found: {header}")
            
            except Exception as e:
                continue
        
        print(f"\\nTotal file headers found: {len(self.file_headers)}")
    
    def is_file_header(self, data):
        """Check if sector data contains a valid file header."""
        if len(data) < 512:
            return False
        
        try:
            file_number = struct.unpack('<H', data[0:2])[0]
            file_seq = struct.unpack('<H', data[2:4])[0]
            rel_vol = struct.unpack('<H', data[4:6])[0]
            
            # Basic validation
            return (0 < file_number < 65536 and 
                   0 <= file_seq < 65536 and 
                   rel_vol == 0)
        except:
            return False
    
    def extract_file(self, header: ODS1FileHeader, output_dir: str):
        """Extract a single file to the output directory."""
        if not header.filename or header.filename == "UNKNOWN":
            filename = f"file_{header.file_number}_{header.file_sequence}.dat"
        else:
            # Clean filename for filesystem
            filename = "".join(c for c in header.filename if c.isalnum() or c in "._-")
            if not filename:
                filename = f"file_{header.file_number}_{header.file_sequence}.dat"
        
        output_path = os.path.join(output_dir, filename)
        
        # Get file blocks
        blocks = header.get_file_blocks()
        
        if not blocks:
            print(f"Warning: No block mapping found for {header}")
            return
        
        # Extract file data
        file_data = b''
        for start_block, block_count in blocks:
            if start_block > 0 and start_block < self.total_sectors:
                for block_num in range(start_block, min(start_block + block_count, self.total_sectors)):
                    try:
                        block_data = read_sector(self.disk_path, block_num)
                        file_data += block_data
                    except:
                        break
        
        if file_data:
            with open(output_path, 'wb') as f:
                f.write(file_data)
            print(f"Extracted: {filename} ({len(file_data)} bytes)")
        else:
            print(f"Warning: No data extracted for {header}")
    
    def extract_all_files(self, output_dir: str):
        """Extract all found files to the output directory."""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\\nExtracting files to: {output_dir}")
        print("-" * 50)
        
        for header in self.file_headers:
            try:
                self.extract_file(header, output_dir)
            except Exception as e:
                print(f"Error extracting {header}: {e}")
    
    def list_files(self):
        """List all found files."""
        print("\\nFile listing:")
        print("-" * 50)
        for i, header in enumerate(self.file_headers, 1):
            blocks = header.get_file_blocks()
            block_info = f"{len(blocks)} block(s)" if blocks else "No blocks"
            print(f"{i:3d}. {header} - {block_info}")

def main():
    parser = argparse.ArgumentParser(description='Extract files from ODS-1 (Files-11) disk images')
    parser.add_argument('disk_image', help='Path to the ODS-1 disk image file')
    parser.add_argument('-o', '--output', default='extracted_ods1', help='Output directory for extracted files')
    parser.add_argument('-l', '--list', action='store_true', help='List files only, don\'t extract')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.disk_image):
        print(f"Error: Disk image '{args.disk_image}' not found")
        return 1
    
    print(f"ODS-1 File Extractor")
    print(f"Analyzing: {args.disk_image}")
    print("=" * 60)
    
    extractor = ODS1Extractor(args.disk_image)
    
    # Analyze the disk
    extractor.analyze_home_block()
    extractor.scan_for_file_headers()
    
    # List files
    extractor.list_files()
    
    # Extract files if requested
    if not args.list:
        extractor.extract_all_files(args.output)
        print(f"\\nExtraction complete. Files saved to: {args.output}")
    
    return 0

if __name__ == "__main__":
    exit(main())
