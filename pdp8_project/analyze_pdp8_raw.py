#!/usr/bin/env python3
"""
Análisis en bruto de imagen PDP-8
Examina los primeros sectores sin aplicar interleave para entender la estructura
"""

import struct
import sys
from typing import List

def bytes_to_12bit_words(data: bytes) -> List[int]:
    """Convert 8-bit bytes to 12-bit words (3 bytes -> 2 words)"""
    words = []
    i = 0
    while i + 2 < len(data):
        # Merge three 8-bit bytes into two 12-bit words
        w1 = data[i] | ((data[i+1] & 0x0F) << 8)
        w2 = (data[i+1] >> 4) | (data[i+2] << 4)
        words.extend([w1 & 0xFFF, w2 & 0xFFF])
        i += 3
    return words

def bytes_to_16bit_words_le(data: bytes) -> List[int]:
    """Convert bytes to 16-bit words (little endian)"""
    words = []
    i = 0
    while i + 1 < len(data):
        word = data[i] | (data[i+1] << 8)
        words.append(word & 0xFFFF)
        i += 2
    return words

def bytes_to_16bit_words_be(data: bytes) -> List[int]:
    """Convert bytes to 16-bit words (big endian)"""
    words = []
    i = 0
    while i + 1 < len(data):
        word = (data[i] << 8) | data[i+1]
        words.append(word & 0xFFFF)
        i += 2
    return words

def print_hex_dump(data: bytes, offset: int = 0, max_bytes: int = 256):
    """Print hex dump of data"""
    for i in range(0, min(len(data), max_bytes), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f"{offset + i:04x}: {hex_part:<48} |{ascii_part}|")

def analyze_os8_directory_structure(words: List[int], word_format: str):
    """Analyze potential OS/8 directory structure"""
    print(f"\n=== Analyzing as {word_format} ===")
    
    if len(words) < 10:
        print("Not enough words for OS/8 directory")
        return False
    
    print(f"First 10 words: {[f'{w:04o}' for w in words[:10]]}")
    print(f"First 10 words (hex): {[f'{w:03x}' for w in words[:10]]}")
    print(f"First 10 words (dec): {words[:10]}")
    
    # Try OS/8 directory interpretation
    # Word 0: -(number of entries)
    # Word 1: next directory segment (0 if last)  
    # Word 2: starting block number
    # Word 3: -(additional info words)
    
    num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
    next_segment = words[1] & 0xFFF
    start_block = words[2] & 0xFFF
    info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
    
    print(f"OS/8 interpretation:")
    print(f"  Number of entries: {num_entries}")
    print(f"  Next segment: {next_segment}")
    print(f"  Starting block: {start_block}")
    print(f"  Info words: {info_words}")
    
    # Sanity checks
    valid = True
    if num_entries > 200:
        print(f"  WARNING: Too many entries ({num_entries})")
        valid = False
    if next_segment > 6:
        print(f"  WARNING: Invalid next segment ({next_segment})")
        valid = False
    if start_block > 4096:
        print(f"  WARNING: Invalid start block ({start_block})")
        valid = False
    if info_words > 10:
        print(f"  WARNING: Too many info words ({info_words})")
        valid = False
    
    if valid:
        print("  Structure looks valid!")
        
        # Try to parse first few directory entries
        print("\n  First few directory entries:")
        i = 5  # Start after header
        for entry_num in range(min(num_entries, 5)):
            if i + 5 + info_words >= len(words):
                break
            
            if words[i] == 0:
                print(f"    Entry {entry_num}: <EMPTY>")
                i += 6 + info_words
            else:
                # Try to extract filename
                filename_words = words[i:i+5]
                print(f"    Entry {entry_num}: words={[f'{w:04o}' for w in filename_words]}")
                
                # Extract characters
                chars = []
                for word in filename_words[:4]:
                    char1 = (word >> 6) & 0o77
                    char2 = word & 0o77
                    if char1 >= 0o40:
                        chars.append(chr(char1))
                    if char2 >= 0o40:
                        chars.append(chr(char2))
                
                filename = ''.join(chars).strip()
                print(f"    Entry {entry_num}: filename='{filename}'")
                
                i += 5 + info_words
                
                # Get length
                if i < len(words):
                    length_word = words[i]
                    length = (0o10000 - length_word) & 0xFFF if length_word != 0 else 0
                    print(f"    Entry {entry_num}: length={length} blocks")
                    i += 1
    else:
        print("  Structure doesn't look like valid OS/8 directory")
    
    return valid

def analyze_sector(data: bytes, sector_num):
    """Analyze a single sector"""
    print(f"\n{'='*60}")
    print(f"ANALYZING SECTOR {sector_num} ({len(data)} bytes)")
    print(f"{'='*60}")
    
    # Show raw hex dump
    print("\nRAW HEX DUMP:")
    if isinstance(sector_num, int):
        offset = sector_num * len(data)
    else:
        offset = 0
    print_hex_dump(data, offset, 128)
    
    # Check if it's all the same byte
    if len(set(data)) == 1:
        print(f"\nSector is filled with repeated byte: 0x{data[0]:02x} ('{chr(data[0]) if 32 <= data[0] <= 126 else '.'}')")
        return
    
    # Try different word interpretations
    words_12bit = bytes_to_12bit_words(data)
    words_16le = bytes_to_16bit_words_le(data)
    words_16be = bytes_to_16bit_words_be(data)
    
    # Analyze as potential OS/8 directory with different word formats
    analyze_os8_directory_structure(words_12bit, "12-bit words")
    analyze_os8_directory_structure(words_16le, "16-bit LE words") 
    analyze_os8_directory_structure(words_16be, "16-bit BE words")

def main():
    if len(sys.argv) != 2:
        print("Usage: python analyze_pdp8_raw.py <disk_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)
    
    print(f"Loaded image: {len(image_data)} bytes")
    
    # Analyze file size to determine likely geometry
    size = len(image_data)
    print(f"File size: {size} bytes")
    
    if size == 256256:
        print("Size matches RX01 non-interleaved (256256 bytes)")
        sector_size = 128
        sectors_per_track = 26
        tracks = 77
    elif size == 252928:
        print("Size matches RX01 interleaved (252928 bytes)")
        sector_size = 128
        sectors_per_track = 26
        tracks = 77
    else:
        print("Unknown size, assuming 128-byte sectors")
        sector_size = 128
        sectors_per_track = 26
        tracks = size // (sector_size * sectors_per_track)
    
    print(f"Assumed geometry: {tracks} tracks, {sectors_per_track} sectors/track, {sector_size} bytes/sector")
    
    # Analyze first few sectors directly (no interleave)
    print(f"\n{'='*80}")
    print("ANALYZING FIRST FEW SECTORS (NO INTERLEAVE)")
    print(f"{'='*80}")
    
    for sector in range(min(6, len(image_data) // sector_size)):
        offset = sector * sector_size
        sector_data = image_data[offset:offset + sector_size]
        analyze_sector(sector_data, sector)
    
    # Also try some sectors with simple 2:1 interleave pattern
    print(f"\n{'='*80}")
    print("TRYING SIMPLE 2:1 INTERLEAVE PATTERN")
    print(f"{'='*80}")
    
    # Simple 2:1: logical sector N -> physical sector (N*2) % sectors_per_track
    for logical_sector in range(min(3, sectors_per_track)):
        physical_sector = (logical_sector * 2) % sectors_per_track
        offset = physical_sector * sector_size
        if offset + sector_size <= len(image_data):
            sector_data = image_data[offset:offset + sector_size]
            print(f"\nLogical sector {logical_sector} -> Physical sector {physical_sector}")
            analyze_sector(sector_data, f"L{logical_sector}->P{physical_sector}")

if __name__ == "__main__":
    main()
