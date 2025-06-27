#!/usr/bin/env python3
"""
Buscar directorio OS/8 en imagen RX01
Probando diferentes patrones de interleave basados en PUTR.ASM
"""

import sys
from typing import List, Tuple

def bytes_to_12bit_words(data: bytes) -> List[int]:
    """Convert 8-bit bytes to 12-bit words"""
    words = []
    i = 0
    while i + 2 < len(data):
        w1 = data[i] | ((data[i+1] & 0x0F) << 8)
        w2 = (data[i+1] >> 4) | (data[i+2] << 4)
        words.extend([w1 & 0xFFF, w2 & 0xFFF])
        i += 3
    return words

def print_hex_dump(data: bytes, max_bytes: int = 64):
    """Print hex dump of first bytes"""
    for i in range(0, min(len(data), max_bytes), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f"{i:04x}: {hex_part:<48} |{ascii_part}|")

def rx01_interleave_2to1(logical_sector: int, track: int = 0) -> int:
    """RX01 2:1 interleave pattern for PDP-8 (no skew)"""
    physical_sector = (logical_sector * 2) % 26
    return physical_sector

def check_os8_directory(words: List[int]) -> Tuple[bool, dict]:
    """Check if words represent valid OS/8 directory"""
    if len(words) < 10:
        return False, {}
    
    # OS/8 directory header
    num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
    next_segment = words[1] & 0xFFF
    start_block = words[2] & 0xFFF
    info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
    
    info = {
        'entries': num_entries,
        'next': next_segment,
        'start': start_block,
        'info_words': info_words,
        'raw_words': words[:10]
    }
    
    # Reasonable bounds for OS/8
    valid = (
        0 <= num_entries <= 100 and
        0 <= next_segment <= 6 and
        0 <= start_block <= 2000 and
        0 <= info_words <= 5
    )
    
    return valid, info

def analyze_sector_as_directory(data: bytes, sector_desc: str):
    """Analyze sector as potential OS/8 directory"""
    print(f"\n=== {sector_desc} ===")
    print_hex_dump(data)
    
    # Skip if mostly empty/spaces
    if len(set(data[:64])) <= 2:
        print("Sector appears to be mostly empty/padding")
        return False
    
    words = bytes_to_12bit_words(data)
    if not words:
        print("Could not convert to words")
        return False
    
    valid, info = check_os8_directory(words)
    
    print(f"OS/8 directory check: {'VALID' if valid else 'INVALID'}")
    print(f"  Entries: {info['entries']}")
    print(f"  Next segment: {info['next']}")
    print(f"  Start block: {info['start']}")
    print(f"  Info words: {info['info_words']}")
    print(f"  Raw header: {[f'{w:04o}' for w in info['raw_words']]}")
    
    if valid:
        print("*** FOUND VALID OS/8 DIRECTORY! ***")
        
        # Try to parse first few entries
        i = 5  # Skip header
        for entry_num in range(min(info['entries'], 3)):
            if i + 5 + info['info_words'] >= len(words):
                break
                
            if words[i] == 0:
                print(f"  Entry {entry_num}: <EMPTY>")
                i += 6 + info['info_words']
            else:
                # Extract filename
                filename_words = words[i:i+5]
                chars = []
                for word in filename_words[:4]:
                    char1 = (word >> 6) & 0o77
                    char2 = word & 0o77
                    if char1 >= 0o40:
                        chars.append(chr(char1))
                    if char2 >= 0o40:
                        chars.append(chr(char2))
                
                filename = ''.join(chars).strip()
                
                i += 5 + info['info_words']
                
                # Get length
                if i < len(words):
                    length_word = words[i]
                    length = (0o10000 - length_word) & 0xFFF if length_word != 0 else 0
                    print(f"  Entry {entry_num}: '{filename}' ({length} blocks)")
                    i += 1
    
    return valid

def main():
    if len(sys.argv) != 2:
        print("Usage: python find_os8_directory.py <disk_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)
    
    print(f"Loaded image: {len(image_data)} bytes")
    
    # RX01 geometry
    sector_size = 128
    sectors_per_track = 26
    
    print("\n" + "="*80)
    print("SEARCHING FOR OS/8 DIRECTORY")
    print("="*80)
    
    found_directories = []
    
    # Check first track sectors (where OS/8 directory should be)
    for logical_sector in range(min(10, sectors_per_track)):
        # Try no interleave first
        physical_sector = logical_sector
        offset = physical_sector * sector_size
        
        if offset + sector_size <= len(image_data):
            sector_data = image_data[offset:offset + sector_size]
            desc = f"Logical {logical_sector} -> Physical {physical_sector} (no interleave)"
            
            if analyze_sector_as_directory(sector_data, desc):
                found_directories.append((logical_sector, physical_sector, "no interleave"))
        
        # Try 2:1 interleave
        physical_sector = rx01_interleave_2to1(logical_sector)
        offset = physical_sector * sector_size
        
        if offset + sector_size <= len(image_data):
            sector_data = image_data[offset:offset + sector_size]
            desc = f"Logical {logical_sector} -> Physical {physical_sector} (2:1 interleave)"
            
            if analyze_sector_as_directory(sector_data, desc):
                found_directories.append((logical_sector, physical_sector, "2:1 interleave"))
    
    # Also check some random sectors that showed interesting data
    interesting_sectors = [4, 8, 12, 16, 20]
    for sector in interesting_sectors:
        offset = sector * sector_size
        if offset + sector_size <= len(image_data):
            sector_data = image_data[offset:offset + sector_size]
            desc = f"Direct sector {sector}"
            
            if analyze_sector_as_directory(sector_data, desc):
                found_directories.append((sector, sector, "direct"))
    
    print(f"\n" + "="*80)
    print("SUMMARY")
    print("="*80)
    
    if found_directories:
        print(f"Found {len(found_directories)} potential OS/8 directories:")
        for logical, physical, method in found_directories:
            print(f"  Logical {logical} -> Physical {physical} ({method})")
    else:
        print("No valid OS/8 directories found")
        print("\nPossible causes:")
        print("- Wrong interleave pattern")
        print("- Different filesystem (PS/8, PUTR, etc.)")
        print("- Corrupted image")
        print("- Need to check other tracks")

if __name__ == "__main__":
    main()
