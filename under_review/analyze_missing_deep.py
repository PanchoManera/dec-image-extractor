#!/usr/bin/env python3
"""
Deep analysis of missing files to understand the pattern
"""

import struct
from ods1_extractor_v2 import ODS1Extractor

def analyze_all_missing():
    """Analyze all missing files across different images."""
    images = [
        ("test_dsk_files/RSX11M_V3.1_SYSTEM0.dsk", "SYSTEM0"),
        ("test_dsk_files/RSX11M_V3.1_SYSTEM1.dsk", "SYSTEM1"),
        ("test_dsk_files/rsx11mp-30.dsk", "RSX11MPBL24")
    ]
    
    all_missing = []
    
    for img_path, vol_name in images:
        print(f"\n{'='*60}")
        print(f"Analyzing {vol_name}")
        print(f"{'='*60}")
        
        extractor = ODS1Extractor(img_path)
        extractor.parse_home_block()
        headers = extractor.scan_for_file_headers()
        
        missing_in_this_volume = []
        
        for header in headers:
            file_data = extractor.extract_file_data(header)
            if not file_data:
                missing_in_this_volume.append(header)
                all_missing.append((vol_name, header))
                
                # Deep analysis of this missing file
                print(f"\n❌ MISSING: {header.filename}.{header.filetype};{header.version}")
                print(f"   File number: {header.file_number}.{header.file_sequence}")
                print(f"   Map words used: {header.map_words_used}")
                print(f"   Count/LBN size: {header.count_size}/{header.lbn_size}")
                print(f"   EOF block: {header.end_of_file_block}")
                print(f"   First free byte: {header.first_free_byte}")
                print(f"   Characteristics: 0x{header.characteristics:04x}")
                
                # Check for patterns in characteristics
                if header.characteristics & 0x0200:  # UC_CON bit
                    print(f"   🔍 File marked as CONTIGUOUS")
                if header.characteristics & 0x0100:  # UC_DLK bit
                    print(f"   🔍 File marked as DEACCESS LOCKED")
                
                # Try to find the file in different ways
                analyze_missing_file_locations(extractor, header)
        
        print(f"\nVolume {vol_name}: {len(missing_in_this_volume)} missing files")
    
    # Pattern analysis
    print(f"\n{'='*80}")
    print("PATTERN ANALYSIS")
    print(f"{'='*80}")
    
    # Group by file type
    by_type = {}
    by_number_range = {}
    
    for vol_name, header in all_missing:
        ftype = header.filetype
        if ftype not in by_type:
            by_type[ftype] = []
        by_type[ftype].append((vol_name, header))
        
        # Group by file number range
        if header.file_number <= 5:
            range_key = "1-5 (system)"
        elif header.file_number <= 16:
            range_key = "6-16 (early)"
        elif header.file_number <= 30:
            range_key = "17-30 (mid)"
        else:
            range_key = "31+ (high)"
            
        if range_key not in by_number_range:
            by_number_range[range_key] = []
        by_number_range[range_key].append((vol_name, header))
    
    print("Missing files by type:")
    for ftype, files in by_type.items():
        print(f"  {ftype}: {len(files)} files")
        for vol, h in files[:3]:  # Show first 3
            print(f"    {vol}: {h.filename}.{h.filetype} (#{h.file_number})")
    
    print("\nMissing files by number range:")
    for range_key, files in by_number_range.items():
        print(f"  {range_key}: {len(files)} files")

def analyze_missing_file_locations(extractor, header):
    """Try different strategies to locate missing file data."""
    
    # Strategy 1: Check if file has zero size (empty file)
    if header.end_of_file_block == 0 and header.first_free_byte == 0:
        print(f"   💡 Likely EMPTY FILE (EOF=0, FFB=0)")
        return
    
    # Strategy 2: Look for data at predictable locations
    candidates = []
    
    # Try locations based on file number
    base_lbn = extractor.index_file_bitmap_lbn
    
    test_locations = [
        base_lbn + header.file_number,  # Sequential after index
        base_lbn + header.file_number * 2,  # With gaps
        base_lbn + 100 + header.file_number,  # After system area
        header.file_number * 10,  # Early area
        1000 + header.file_number,  # Mid area
    ]
    
    for test_lbn in test_locations:
        if test_lbn >= extractor.total_blocks:
            continue
            
        try:
            data = extractor.read_block(test_lbn)
            non_zero = sum(1 for b in data if b != 0)
            
            if non_zero > 100:  # Significant data
                # Check if it looks like file content vs header
                if not looks_like_file_header(data):
                    candidates.append((test_lbn, non_zero))
                    
        except:
            continue
    
    if candidates:
        print(f"   📍 Possible data locations:")
        for lbn, non_zero in candidates[:3]:  # Top 3
            print(f"      LBN {lbn}: {non_zero} non-zero bytes")
    
    # Strategy 3: Check for extension headers
    if header.extension_file_number > 0:
        print(f"   🔗 Has extension header: file {header.extension_file_number}")
    
    # Strategy 4: Look at the raw map area data
    print_raw_map_area(extractor, header)

def looks_like_file_header(data):
    """Check if data looks like a file header."""
    if len(data) < 10:
        return False
    
    try:
        structure_level = struct.unpack('<H', data[6:8])[0]
        return structure_level == 0x0101
    except:
        return False

def print_raw_map_area(extractor, header):
    """Print raw bytes from the map area to see what's there."""
    try:
        # Get the header block again
        header_lbn = extractor.index_file_bitmap_lbn + header.file_number
        data = extractor.read_block(header_lbn)
        
        map_offset = data[1] * 2  # H.MPOF
        if map_offset > 0 and map_offset + 20 <= len(data):
            map_data = data[map_offset:map_offset + 20]
            print(f"   🔍 Raw map area (20 bytes): {map_data.hex()}")
            
            # Interpret as words
            print(f"   🔍 As words:")
            for i in range(0, min(20, len(map_data)), 2):
                if i + 1 < len(map_data):
                    word = struct.unpack('<H', map_data[i:i+2])[0]
                    print(f"      +{i:2d}: 0x{word:04x} ({word:5d})")
            
    except Exception as e:
        print(f"   ❌ Error reading map area: {e}")

if __name__ == "__main__":
    analyze_all_missing()
