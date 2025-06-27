#!/usr/bin/env python3
"""
Specific analysis of rsx11mp-30.dsk to find the missing 13 files
"""

import struct
from ods1_extractor_v2 import ODS1Extractor

def analyze_rsx11mp30():
    """Analyze specifically what's happening with rsx11mp-30.dsk."""
    
    print("=== DEEP ANALYSIS OF rsx11mp-30.dsk ===")
    
    extractor = ODS1Extractor("test_dsk_files/rsx11mp-30.dsk")
    extractor.parse_home_block()
    headers = extractor.scan_for_file_headers()
    
    missing_files = []
    extracted_files = []
    
    print(f"\nVolume: RSX11MPBL24")
    print(f"Total blocks: {extractor.total_blocks}")
    print(f"Index bitmap LBN: {extractor.index_file_bitmap_lbn}")
    
    for header in headers:
        file_data = extractor.extract_file_data(header)
        if file_data is None:  # None means real error, b"" means empty file
            missing_files.append(header)
        else:
            extracted_files.append(header)
    
    print(f"\nExtracted: {len(extracted_files)} files")
    print(f"Missing: {len(missing_files)} files")
    
    if not missing_files:
        print("🎉 ALL FILES EXTRACTED!")
        return
    
    print(f"\n=== ANALYZING {len(missing_files)} MISSING FILES ===")
    
    # Group missing files by patterns
    by_map_words = {"zero": [], "nonzero": []}
    by_eof_info = {"has_eof": [], "no_eof": []}
    by_file_range = {"low": [], "mid": [], "high": []}
    
    for header in missing_files:
        # Group by map words
        if header.map_words_used == 0:
            by_map_words["zero"].append(header)
        else:
            by_map_words["nonzero"].append(header)
        
        # Group by EOF info
        if header.end_of_file_block > 0:
            by_eof_info["has_eof"].append(header)
        else:
            by_eof_info["no_eof"].append(header)
        
        # Group by file number range
        if header.file_number <= 16:
            by_file_range["low"].append(header)
        elif header.file_number <= 32:
            by_file_range["mid"].append(header)
        else:
            by_file_range["high"].append(header)
    
    print(f"\nPattern Analysis:")
    print(f"  Map words = 0: {len(by_map_words['zero'])} files")
    print(f"  Map words > 0: {len(by_map_words['nonzero'])} files")
    print(f"  Has EOF info: {len(by_eof_info['has_eof'])} files")
    print(f"  No EOF info: {len(by_eof_info['no_eof'])} files")
    print(f"  File# 1-16: {len(by_file_range['low'])} files")
    print(f"  File# 17-32: {len(by_file_range['mid'])} files")
    print(f"  File# 33+: {len(by_file_range['high'])} files")
    
    # Analyze each missing file in detail
    for i, header in enumerate(missing_files):
        print(f"\n--- Missing File #{i+1}: {header.filename}.{header.filetype};{header.version} ---")
        print(f"File number: {header.file_number}.{header.file_sequence}")
        print(f"Map words used: {header.map_words_used}")
        print(f"Count/LBN size: {header.count_size}/{header.lbn_size}")
        print(f"EOF block: {header.end_of_file_block}")
        print(f"First free byte: {header.first_free_byte}")
        print(f"Characteristics: 0x{header.characteristics:04x}")
        print(f"Extension file: {header.extension_file_number}")
        
        # Check if this file has retrieval pointers that we're not parsing correctly
        if header.map_words_used > 0:
            print("🔍 HAS MAP WORDS - should have retrieval pointers!")
            examine_detailed_map_area(extractor, header)
        elif header.end_of_file_block > 0:
            print(f"🔍 HAS SIZE INFO - trying advanced location strategies")
            try_advanced_location_strategies(extractor, header)
        else:
            print("🔍 NO SIZE INFO - probably empty file or special case")
    
    # Check if there are extension files or special RSX-11M+ features
    print(f"\n=== CHECKING FOR RSX-11M+ SPECIFIC FEATURES ===")
    check_extension_files(extractor, missing_files)
    check_large_disk_layout(extractor, missing_files)

def examine_detailed_map_area(extractor, header):
    """Examine map area in extreme detail."""
    try:
        header_lbn = extractor.index_file_bitmap_lbn + header.file_number
        data = extractor.read_block(header_lbn)
        
        map_offset = data[1] * 2
        if map_offset > 0 and map_offset + 20 <= len(data):
            map_start = map_offset
            
            print(f"  Map area at offset {map_start}:")
            
            # Parse all map fields in detail
            m_esqn = struct.unpack('<H', data[map_start:map_start + 2])[0]
            m_ervn = struct.unpack('<H', data[map_start + 2:map_start + 4])[0]
            m_efnu = struct.unpack('<H', data[map_start + 4:map_start + 6])[0]
            m_efsq = struct.unpack('<H', data[map_start + 6:map_start + 8])[0]
            
            format_word = struct.unpack('<H', data[map_start + 6:map_start + 8])[0]
            m_ctsz = format_word & 0xFF
            m_lbsz = (format_word >> 8) & 0xFF
            
            m_use = struct.unpack('<H', data[map_start + 10:map_start + 12])[0]
            m_max = data[map_start + 12]
            
            print(f"    M.ESQN: {m_esqn}")
            print(f"    M.ERVN: {m_ervn}")
            print(f"    M.EFNU: {m_efnu}")
            print(f"    M.EFSQ: {m_efsq}")
            print(f"    M.CTSZ: {m_ctsz}")
            print(f"    M.LBSZ: {m_lbsz}")
            print(f"    M.USE: {m_use}")
            print(f"    M.MAX: {m_max}")
            
            # Show raw retrieval pointer area
            if m_use > 0:
                retr_start = map_start + 16  # Start after the 16-byte map header
                retr_end = retr_start + min(32, m_use * 2)  # Show first 32 bytes max
                
                print(f"  Raw retrieval data ({m_use} words):")
                if retr_start < len(data):
                    # Make sure we don't read beyond data
                    actual_end = min(retr_end, len(data))
                    retr_data = data[retr_start:actual_end]
                    
                    # Always show hex data
                    hex_preview = retr_data.hex()
                    print(f"    HEX DATA: {hex_preview}")
                    
                    # Check if it's all zeros
                    all_zeros = all(b == 0 for b in retr_data)
                    if all_zeros:
                        print(f"    ⚠️  ALL ZEROS - empty/unused file")
                    else:
                        print(f"    ✓ Non-zero data found")
                        # Try multiple parsing strategies only if we have data
                        try_all_parsing_strategies(retr_data, m_ctsz, m_lbsz)
                else:
                    print(f"    ❌ Cannot read retrieval data at offset {retr_start}")
            
            # Check if there's an extension file reference
            if m_efnu > 0:
                print(f"  📋 EXTENSION FILE REFERENCE: {m_efnu}.{m_efsq}")
                
    except Exception as e:
        print(f"  Error examining map area: {e}")

def try_all_parsing_strategies(retr_data, count_size, lbn_size):
    """Try every possible way to parse retrieval pointers."""
    print(f"  Trying all parsing strategies:")
    
    strategies = [
        ("Standard 1,3", parse_format_1_3),
        ("Standard 2,2", parse_format_2_2),
        ("Standard 2,4", parse_format_2_4),
        ("Byte-swapped 1,3", parse_format_1_3_swapped),
        ("Word-based parsing", parse_word_based),
        ("LSB format", parse_lsb_format),
    ]
    
    for name, parser in strategies:
        try:
            result = parser(retr_data)
            if result:
                lbn, count = result
                if lbn > 0 and count > 0:
                    print(f"    ✅ {name}: LBN={lbn}, Count={count}")
        except:
            pass

def parse_format_1_3(data):
    """Standard 1,3 format."""
    if len(data) >= 4:
        lbn_high = data[0]
        count = data[1]
        lbn_low = struct.unpack('<H', data[2:4])[0]
        lbn = (lbn_high << 16) | lbn_low
        return lbn, count
    return None

def parse_format_1_3_swapped(data):
    """1,3 format with count/lbn swapped."""
    if len(data) >= 4:
        count = data[0]
        lbn_high = data[1]
        lbn_low = struct.unpack('<H', data[2:4])[0]
        lbn = (lbn_high << 16) | lbn_low
        return lbn, count
    return None

def parse_format_2_2(data):
    """Standard 2,2 format."""
    if len(data) >= 4:
        count = struct.unpack('<H', data[0:2])[0]
        lbn = struct.unpack('<H', data[2:4])[0]
        return lbn, count
    return None

def parse_format_2_4(data):
    """Standard 2,4 format."""
    if len(data) >= 6:
        count = struct.unpack('<H', data[0:2])[0]
        lbn_low = struct.unpack('<H', data[2:4])[0]
        lbn_high = struct.unpack('<H', data[4:6])[0]
        lbn = (lbn_high << 16) | lbn_low
        return lbn, count
    return None

def parse_word_based(data):
    """Parse as all little-endian words."""
    if len(data) >= 4:
        word1 = struct.unpack('<H', data[0:2])[0]
        word2 = struct.unpack('<H', data[2:4])[0]
        # Try both interpretations
        if word1 > 0 and word2 > 0:
            return word2, word1  # word2 as LBN, word1 as count
    return None

def parse_lsb_format(data):
    """Parse with LSB first for LBN."""
    if len(data) >= 4:
        lbn_low = struct.unpack('<H', data[0:2])[0]
        word2 = struct.unpack('<H', data[2:4])[0]
        count = word2 & 0xFF
        lbn_high = (word2 >> 8) & 0xFF
        lbn = (lbn_high << 16) | lbn_low
        return lbn, count
    return None

def try_advanced_location_strategies(extractor, header):
    """Try advanced strategies to find file data."""
    print(f"  Trying advanced location strategies:")
    
    # Strategy 1: Check multiple offsets from file number
    base_locations = [
        header.file_number,
        header.file_number * 2,
        header.file_number + 100,
        header.file_number + 1000,
        header.file_number + 10000,
        header.file_number + extractor.index_file_bitmap_lbn,
        extractor.index_file_bitmap_lbn - header.file_number,
    ]
    
    expected_blocks = header.end_of_file_block if header.end_of_file_block > 0 else 1
    
    for base_lbn in base_locations:
        if base_lbn < 0 or base_lbn >= extractor.total_blocks:
            continue
            
        try:
            # Check if this location has data
            test_data = b""
            blocks_read = 0
            
            for i in range(min(expected_blocks, 10)):  # Check first 10 blocks
                try:
                    block_data = extractor.read_block(base_lbn + i)
                    test_data += block_data
                    blocks_read += 1
                except:
                    break
            
            if test_data:
                non_zero = sum(1 for b in test_data if b != 0)
                if non_zero > len(test_data) * 0.1:  # At least 10% non-zero
                    print(f"    📍 Found data at LBN {base_lbn}: {non_zero} non-zero bytes in {blocks_read} blocks")
                    print(f"       Preview: {test_data[:32].hex()}")
                    
        except:
            continue

def check_extension_files(extractor, missing_files):
    """Check for extension file patterns."""
    print("Checking extension file patterns...")
    
    # Look for files that reference other files as extensions
    extension_refs = {}
    
    for header in missing_files:
        if header.extension_file_number > 0:
            extension_refs[header.file_number] = header.extension_file_number
            print(f"  File {header.file_number} -> Extension {header.extension_file_number}")

def check_large_disk_layout(extractor, missing_files):
    """Check if large disk (166MB) has different layout."""
    print(f"Checking large disk layout patterns...")
    print(f"  Disk size: {extractor.disk_size / (1024*1024):.1f} MB")
    print(f"  Total blocks: {extractor.total_blocks}")
    print(f"  Index bitmap at: {extractor.index_file_bitmap_lbn}")
    
    # For very large disks, files might be allocated differently
    # Check if files are in different sections of the disk
    
    file_numbers = [h.file_number for h in missing_files]
    print(f"  Missing file numbers: {sorted(file_numbers)}")
    
    # Check different disk regions
    regions = [
        ("Start", 0, 1000),
        ("Early", 1000, 10000),
        ("Index area", extractor.index_file_bitmap_lbn - 100, extractor.index_file_bitmap_lbn + 100),
        ("Mid", extractor.total_blocks // 4, extractor.total_blocks // 4 + 1000),
        ("End", extractor.total_blocks - 1000, extractor.total_blocks),
    ]
    
    for region_name, start, end in regions:
        end = min(end, extractor.total_blocks)
        if start >= end:
            continue
            
        print(f"  Checking {region_name} region (blocks {start}-{end})...")
        
        # Sample some blocks in this region
        sample_blocks = min(10, end - start)
        non_zero_blocks = 0
        
        for i in range(sample_blocks):
            try:
                sample_lbn = start + (i * (end - start) // sample_blocks)
                data = extractor.read_block(sample_lbn)
                if sum(1 for b in data if b != 0) > 100:
                    non_zero_blocks += 1
            except:
                pass
        
        print(f"    {non_zero_blocks}/{sample_blocks} sampled blocks have data")

if __name__ == "__main__":
    analyze_rsx11mp30()
