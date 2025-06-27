#!/usr/bin/env python3
"""
Surgical analysis of the remaining missing files to reach 100%
"""

import struct
from ods1_extractor_v2 import ODS1Extractor

def analyze_specific_missing():
    """Analyze exactly which files are still missing and why."""
    
    # Test the best performing image first
    print("=== ANALYZING RSX11M_V3.1_SYSTEM1.dsk (96.8% success) ===")
    analyze_missing_in_image("test_dsk_files/RSX11M_V3.1_SYSTEM1.dsk", "SYSTEM1")
    
    print("\n=== ANALYZING RSX11M_V3.1_SYSTEM0.dsk (81.6% success) ===")
    analyze_missing_in_image("test_dsk_files/RSX11M_V3.1_SYSTEM0.dsk", "SYSTEM0")

def analyze_missing_in_image(img_path, vol_name):
    """Analyze missing files in a specific image."""
    extractor = ODS1Extractor(img_path)
    extractor.parse_home_block()
    headers = extractor.scan_for_file_headers()
    
    missing_files = []
    
    for header in headers:
        file_data = extractor.extract_file_data(header)
        if file_data is None:  # None means real error, b"" means empty file
            missing_files.append(header)
    
    print(f"\nVolume {vol_name}: {len(missing_files)} files still missing")
    
    if not missing_files:
        print("🎉 ALL FILES EXTRACTED!")
        return
    
    # Analyze each missing file in detail
    for i, header in enumerate(missing_files):
        print(f"\n--- Missing File #{i+1}: {header.filename}.{header.filetype};{header.version} ---")
        print(f"File number: {header.file_number}.{header.file_sequence}")
        print(f"Map words used: {header.map_words_used}")
        print(f"Count/LBN size: {header.count_size}/{header.lbn_size}")
        print(f"EOF block: {header.end_of_file_block}")
        print(f"First free byte: {header.first_free_byte}")
        print(f"Characteristics: 0x{header.characteristics:04x}")
        print(f"Retrieval pointers: {len(header.retrieval_pointers)}")
        
        # Check if it has valid retrieval pointers that we're not reading correctly
        if header.map_words_used > 0:
            print("🔍 HAS MAP WORDS - should have retrieval pointers!")
            examine_raw_map_data(extractor, header)
        
        # Check if it has non-zero EOF/FFB but we're not finding data
        if header.end_of_file_block > 0 or header.first_free_byte > 0:
            print(f"🔍 HAS SIZE INFO - EOF:{header.end_of_file_block}, FFB:{header.first_free_byte}")
            examine_possible_locations(extractor, header)

def examine_raw_map_data(extractor, header):
    """Examine the raw map data to see what we're missing."""
    try:
        # Get the header block again
        header_lbn = extractor.index_file_bitmap_lbn + header.file_number
        data = extractor.read_block(header_lbn)
        
        map_offset = data[1] * 2  # H.MPOF
        if map_offset > 0 and map_offset + 20 <= len(data):
            map_start = map_offset
            
            print(f"Map area at offset {map_start}:")
            
            # Show key map fields
            m_use = struct.unpack('<H', data[map_start + 10:map_start + 12])[0]
            print(f"  M.USE (words used): {m_use}")
            
            # Show the actual retrieval pointer area
            retr_start = map_start + 10
            retr_end = retr_start + (m_use * 2)
            
            print(f"Retrieval pointer area (bytes {retr_start}-{retr_end}):")
            if retr_end <= len(data):
                retr_data = data[retr_start:retr_end]
                print(f"  Raw bytes: {retr_data.hex()}")
                
                # Try to interpret as words
                for i in range(0, len(retr_data), 2):
                    if i + 1 < len(retr_data):
                        word = struct.unpack('<H', retr_data[i:i+2])[0]
                        print(f"    +{i:2d}: 0x{word:04x} ({word:5d})")
                
                # Try manual parsing with different interpretations
                print("\nTrying different parsing approaches:")
                try_alternative_parsing(retr_data, header.count_size, header.lbn_size)
            
    except Exception as e:
        print(f"Error examining raw map data: {e}")

def try_alternative_parsing(retr_data, count_size, lbn_size):
    """Try alternative ways to parse retrieval pointers."""
    
    # Method 1: Standard format 1,3 but different byte order
    if len(retr_data) >= 4:
        print("Method 1 - Standard 1,3:")
        try:
            lbn_high = retr_data[0]
            count = retr_data[1]
            lbn_low = struct.unpack('<H', retr_data[2:4])[0]
            lbn = (lbn_high << 16) | lbn_low
            print(f"  LBN: {lbn}, Count: {count}")
            if lbn > 0 and count > 0:
                print("  ✅ Valid pointer found!")
        except:
            pass
    
    # Method 2: Try swapped count/lbn order
    if len(retr_data) >= 4:
        print("Method 2 - Swapped order:")
        try:
            count = retr_data[0]
            lbn_high = retr_data[1]
            lbn_low = struct.unpack('<H', retr_data[2:4])[0]
            lbn = (lbn_high << 16) | lbn_low
            print(f"  LBN: {lbn}, Count: {count}")
            if lbn > 0 and count > 0:
                print("  ✅ Valid pointer found!")
        except:
            pass
    
    # Method 3: Try as all little-endian words
    if len(retr_data) >= 4:
        print("Method 3 - All little-endian words:")
        try:
            word1 = struct.unpack('<H', retr_data[0:2])[0]
            word2 = struct.unpack('<H', retr_data[2:4])[0]
            print(f"  Word1: {word1}, Word2: {word2}")
            # Try word1 as count, word2 as LBN
            if word1 > 0 and word2 > 0:
                print(f"  Interpretation 1: Count={word1}, LBN={word2}")
            # Try word2 as count, word1 as LBN
            if word1 > 0 and word2 > 0:
                print(f"  Interpretation 2: Count={word2}, LBN={word1}")
        except:
            pass

def examine_possible_locations(extractor, header):
    """Look for the file data in various possible locations."""
    print("Searching for file data in various locations...")
    
    # Calculate expected file size
    if header.end_of_file_block > 0:
        expected_size = (header.end_of_file_block - 1) * 512
        if header.first_free_byte > 0:
            expected_size += header.first_free_byte
        else:
            expected_size += 512
        print(f"Expected file size: {expected_size} bytes ({expected_size // 512} blocks)")
        
        # Look for blocks that match this size pattern
        search_locations = [
            header.file_number,  # Simple file number
            header.file_number * 2,  # Double spacing
            header.file_number + 100,  # Offset base
            header.file_number + 1000,  # Different offset
            header.file_number + extractor.index_file_bitmap_lbn,  # After index
        ]
        
        for base_lbn in search_locations:
            if base_lbn >= extractor.total_blocks:
                continue
                
            try:
                # Try reading the expected number of blocks
                expected_blocks = (expected_size + 511) // 512
                found_data = b""
                
                for i in range(expected_blocks):
                    test_lbn = base_lbn + i
                    if test_lbn >= extractor.total_blocks:
                        break
                    
                    block_data = extractor.read_block(test_lbn)
                    found_data += block_data
                
                # Check if this looks like real file data
                non_zero = sum(1 for b in found_data if b != 0)
                if non_zero > expected_size * 0.1:  # At least 10% non-zero
                    print(f"  📍 Possible location at LBN {base_lbn}: {non_zero} non-zero bytes")
                    
                    # Show first few bytes
                    preview = found_data[:32]
                    print(f"      Preview: {preview.hex()}")
                    
            except:
                continue

if __name__ == "__main__":
    analyze_specific_missing()
