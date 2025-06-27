#!/usr/bin/env python3
"""
RT-11 File System Extractor
Based on structures found in tu58em project and RT-11 documentation
"""

import struct
import os
import argparse
from typing import Dict, List, Tuple, Optional

class RT11Extractor:
    """RT-11 file system extractor based on tu58em structures."""
    
    def __init__(self, disk_image_path):
        self.disk_path = disk_image_path
        self.block_size = 512
        self.total_blocks = 0
        self.volume_name = ""
        self.files = []
        
    def read_block(self, block_number):
        """Read a 512-byte block from the disk image."""
        with open(self.disk_path, 'rb') as f:
            f.seek(block_number * self.block_size)
            return f.read(self.block_size)
    
    def analyze_volume(self):
        """Analyze RT-11 volume structure."""
        print(f"Analyzing RT-11 disk image: {self.disk_path}")
        
        # Calculate total blocks
        with open(self.disk_path, 'rb') as f:
            f.seek(0, 2)
            file_size = f.tell()
            self.total_blocks = file_size // self.block_size
        
        print(f"Total blocks: {self.total_blocks}")
        
        # Read boot block (block 0)
        boot_block = self.read_block(0)
        print(f"Boot block signature: {boot_block[:4].hex()}")
        
        # According to tu58em, bitmap starts at block 1 (offset 01000 octal = 512 decimal)
        bitmap_block = self.read_block(1)
        print(f"Bitmap block first words: {struct.unpack('<4H', bitmap_block[:8])}")
        
        # Directory area starts around block 6 (based on tu58em structures)
        self.analyze_directory()
    
    def analyze_directory(self):
        """Analyze RT-11 directory structure."""
        print("\nAnalyzing RT-11 directory...")
        
        # Based on tu58em, directory starts around offset 06000 octal
        # This is block 6 in decimal (06000 octal = 3072 decimal / 512 = 6)
        dir_block = self.read_block(6)
        
        # RT-11 directory entry format (from various sources):
        # Each entry is typically 14 bytes:
        # - Status word (2 bytes)
        # - Filename in RADIX-50 (6 bytes, 3 words)
        # - Length in blocks (2 bytes)
        # - Job/Date (4 bytes)
        
        print(f"Directory block 6 first 32 bytes:")
        print(" ".join(f"{b:02x}" for b in dir_block[:32]))
        
        # Try to parse directory entries
        offset = 0
        entry_num = 0
        
        while offset < len(dir_block) - 14:
            # Read directory entry
            entry_data = dir_block[offset:offset + 14]
            if len(entry_data) < 14:
                break
                
            # Parse entry - RT-11 directory entry format:
            # Status (2 bytes) + Name (6 bytes = 3 words) + Length (2 bytes) + Date (4 bytes)
            if len(entry_data) >= 14:
                status, name1, name2, name3, length = struct.unpack('<H3HH', entry_data[:10])
                job_date = struct.unpack('<H', entry_data[12:14])[0] if len(entry_data) >= 14 else 0
            else:
                continue
            
            # Check for end of directory
            if status == 0:
                break
                
            # Decode RADIX-50 filename
            filename = self.decode_radix50_name(name1, name2, name3)
            
            # Check for valid entry
            if filename.strip() and length > 0 and length < 1000:
                file_info = {
                    'entry': entry_num,
                    'status': status,
                    'filename': filename,
                    'length_blocks': length,
                    'length_bytes': length * self.block_size,
                    'job_date': job_date,
                    'offset': offset
                }
                self.files.append(file_info)
                print(f"  Entry {entry_num}: {filename} ({length} blocks, {length * self.block_size} bytes)")
            
            offset += 14
            entry_num += 1
            
            # Safety check
            if entry_num > 50:
                break
        
        # Also check additional directory blocks
        for block_num in [7, 8, 9]:
            if block_num < self.total_blocks:
                self.analyze_directory_block(block_num)
    
    def analyze_directory_block(self, block_num):
        """Analyze additional directory blocks."""
        dir_block = self.read_block(block_num)
        
        # Check if this looks like a directory block
        # Look for RADIX-50 patterns and reasonable structure
        for offset in range(0, len(dir_block) - 14, 14):
            entry_data = dir_block[offset:offset + 14]
            if len(entry_data) >= 14:
                status, name1, name2, name3, length = struct.unpack('<H3HH', entry_data[:10])
                job_date = struct.unpack('<H', entry_data[12:14])[0] if len(entry_data) >= 14 else 0
            else:
                continue
            
            if status == 0:
                continue
                
            filename = self.decode_radix50_name(name1, name2, name3)
            
            if filename.strip() and length > 0 and length < 1000:
                file_info = {
                    'entry': len(self.files),
                    'status': status,
                    'filename': filename,
                    'length_blocks': length,
                    'length_bytes': length * self.block_size,
                    'job_date': job_date,
                    'block': block_num,
                    'offset': offset
                }
                
                # Check if we already have this file
                existing = any(f['filename'] == filename for f in self.files)
                if not existing:
                    self.files.append(file_info)
                    print(f"  Block {block_num}: {filename} ({length} blocks)")
    
    def decode_radix50_name(self, word1, word2, word3):
        """Decode RT-11 RADIX-50 filename (3 words = 9 characters)."""
        # RT-11 RADIX-50 character set
        radix50_chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$._0123456789"
        
        result = ""
        for word in [word1, word2, word3]:
            if word > 40*40*40:  # Invalid RADIX-50 value
                result += "???"
                continue
                
            # Extract 3 characters from each word
            c1 = word // (40 * 40)
            c2 = (word // 40) % 40
            c3 = word % 40
            
            for c in [c1, c2, c3]:
                if c < len(radix50_chars):
                    result += radix50_chars[c]
                else:
                    result += "?"
        
        # Format as filename.ext
        result = result.rstrip()
        if len(result) > 6:
            # Split into name (6 chars) and extension (3 chars)
            name = result[:6].rstrip()
            ext = result[6:].rstrip()
            if ext:
                return f"{name}.{ext}"
            else:
                return name
        else:
            return result
    
    def list_files(self):
        """Display found files."""
        print(f"\nRT-11 Files Found ({len(self.files)} total):")
        print("=" * 80)
        
        for i, file_info in enumerate(self.files, 1):
            filename = file_info['filename']
            blocks = file_info['length_blocks']
            bytes_size = file_info['length_bytes']
            status = file_info['status']
            
            print(f"{i:3d}. {filename:<12} {blocks:4d} blocks ({bytes_size:6d} bytes) status=0x{status:04x}")
    
    def extract_file(self, file_info, output_dir):
        """Extract a single file (basic implementation)."""
        filename = file_info['filename']
        blocks = file_info['length_blocks']
        
        # This is a simplified extraction - RT-11 has a more complex allocation system
        # For a complete implementation, we'd need to parse the complete directory
        # structure and follow the file allocation chain
        
        print(f"Note: Extraction for {filename} is simplified")
        print(f"      RT-11 requires parsing allocation maps for complete extraction")
        
        # Create placeholder file with file info
        clean_filename = "".join(c for c in filename if c.isalnum() or c in '._-')
        if not clean_filename:
            clean_filename = f"file_{file_info['entry']}.dat"
        
        output_path = os.path.join(output_dir, clean_filename + ".info")
        
        with open(output_path, 'w') as f:
            f.write(f"RT-11 File Information\n")
            f.write(f"=====================\n")
            f.write(f"Filename: {filename}\n")
            f.write(f"Length: {blocks} blocks ({file_info['length_bytes']} bytes)\n")
            f.write(f"Status: 0x{file_info['status']:04x}\n")
            f.write(f"Job/Date: 0x{file_info['job_date']:04x}\n")
            f.write(f"\nNote: Complete extraction requires parsing RT-11 allocation maps\n")
        
        return True
    
    def extract_all_files(self, output_dir):
        """Extract all found files."""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\nExtracting RT-11 files to: {output_dir}")
        print("-" * 50)
        
        extracted_count = 0
        for file_info in self.files:
            if self.extract_file(file_info, output_dir):
                extracted_count += 1
        
        print(f"\nExtraction complete: {extracted_count}/{len(self.files)} files extracted")

def main():
    parser = argparse.ArgumentParser(
        description='RT-11 File System Extractor (based on tu58em structures)',
        epilog='Analyzes RT-11 disk images and extracts file information'
    )
    parser.add_argument('disk_image', help='Path to RT-11 disk image file')
    parser.add_argument('-o', '--output', default='extracted_rt11', 
                       help='Output directory for extracted files (default: extracted_rt11)')
    parser.add_argument('-l', '--list', action='store_true', 
                       help='List files only, don\'t extract')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.disk_image):
        print(f"Error: Disk image '{args.disk_image}' not found")
        return 1
    
    print("RT-11 File System Extractor")
    print("Based on tu58em project structures")
    print("=" * 60)
    
    extractor = RT11Extractor(args.disk_image)
    
    # Analyze the volume
    extractor.analyze_volume()
    
    # List files
    extractor.list_files()
    
    # Extract files if requested
    if not args.list and extractor.files:
        extractor.extract_all_files(args.output)
    elif not extractor.files:
        print("\nNo RT-11 files found to extract.")
    
    return 0

if __name__ == "__main__":
    exit(main())
