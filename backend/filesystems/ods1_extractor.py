import struct
import binascii
import datetime
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

def parse_radix50(word):
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
            chars.append('?')
    
    return ''.join(reversed(chars))

def parse_ods1_date(date_bytes):
    """Parse ODS-1 date format (7 bytes: DD-MMM-YY HH:MM:SS)."""
    try:
        if len(date_bytes) >= 12:
            date_str = safe_decode(date_bytes[:12])
            return date_str
        return "Unknown"
    except:
        return "Invalid"

def parse_home_block(data):
    """Extract key information from the home block, sector 1."""
    print("=== HOME BLOCK ANALYSIS ===")
    print("Raw home block data (first 128 bytes):")
    for i in range(0, min(128, len(data)), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f'{i:04x}: {hex_part:<48} |{ascii_part}|')
    
    # Parse ODS-1 Home Block structure (based on Files-11 spec)
    # Offset 4: Cluster factor (words 2-3)
    cluster_factor = struct.unpack('<H', data[4:6])[0] if len(data) >= 6 else 0
    
    # Offset 12: Volume name (10 characters, space-padded)
    volume_name = safe_decode(data[12:22])
    
    # Offset 22: Structure level
    structure_level = struct.unpack('<H', data[22:24])[0] if len(data) >= 24 else 0
    
    # Offset 46: Creation date (appears to be around offset 48-60 based on hex)
    creation_date = parse_ods1_date(data[48:60])
    
    # Look for file structure identifier around offset 488-511
    if len(data) >= 500:
        fs_id = safe_decode(data[488:500])
    else:
        fs_id = "Unknown"
    
    return {
        'cluster_factor': cluster_factor,
        'structure_level': structure_level,
        'volume_name': volume_name,
        'creation_date': creation_date,
        'file_structure_id': fs_id,
        'total_sectors': len(data) // 512
    }

def analyze_index_file_header(data):
    """Analyze the Index File Header (INDEXF.SYS)."""
    print("\n=== INDEX FILE HEADER ANALYSIS ===")
    
    # Look for file entries in what appears to be a directory structure
    # Based on our hex dump, we see entries that look like user accounts
    entries = []
    
    for offset in range(0, min(512, len(data)), 128):  # 128-byte entries
        entry_data = data[offset:offset+128]
        if len(entry_data) < 128:
            break
            
        # Check if this looks like a valid entry
        if entry_data[0] != 0 and any(32 <= b <= 126 for b in entry_data[:20]):
            # Try to extract what looks like UIC and username
            uic_str = safe_decode(entry_data[0:6])
            username = safe_decode(entry_data[6:16]).strip()
            group = safe_decode(entry_data[16:26]).strip()
            
            if username and len(username) > 0:
                entries.append({
                    'uic': uic_str,
                    'username': username,
                    'group': group,
                    'raw_offset': offset
                })
    
    return entries


def extract_ods1_info(file_path):
    """Extract and display information from an ODS-1 disk image."""
    print(f"Analyzing ODS-1 disk image: {file_path}")
    print("=" * 50)
    
    # Read and parse the home block (sector 1)
    home_block_data = read_sector(file_path, 1)
    home_info = parse_home_block(home_block_data)
    
    # Output the extracted information
    print(f"\nParsed Information:")
    print(f"Structure Level: {home_info['structure_level']}")
    print(f"Volume Name: {home_info['volume_name']}")
    print(f"Creation Date: {home_info['creation_date']}")
    print(f"Cluster Factor: {home_info['cluster_factor']}")
    print(f"File Structure ID: {home_info['file_structure_id']}")
    print(f"Total Sectors: {home_info['total_sectors']}")
    
    # Analyze sector 2 which seems to contain user directory information
    print("\n" + "=" * 50)
    sector2_data = read_sector(file_path, 2)
    user_entries = analyze_index_file_header(sector2_data)
    
    if user_entries:
        print(f"\nFound {len(user_entries)} user entries:")
        for entry in user_entries:
            print(f"  UIC: {entry['uic']} | Username: {entry['username']} | Group: {entry['group']}")
    else:
        print("\nNo recognizable user entries found in sector 2")
    
    # Try to analyze more sectors to find actual file directory
    print("\n" + "=" * 50)
    print("=== SCANNING FOR FILE DIRECTORIES ===")
    
    scan_file_directories(file_path)
    
    # Try to analyze index file (typically starts around sector 20-30 based on our findings)
    print("\n" + "=" * 50)
    print("=== INDEX FILE ANALYSIS ===")
    analyze_index_file(file_path)


def has_file_entries(data):
    """Check if sector contains potential file entries."""
    # Look for patterns that suggest file entries:
    # - Multiple null-terminated strings
    # - Patterns that look like filenames with extensions
    # - UIC patterns [xxx,yyy]
    
    text_blocks = 0
    for i in range(0, len(data), 32):
        block = data[i:i+32]
        if any(32 <= b <= 126 for b in block[:16]) and block.count(0) > 4:
            text_blocks += 1
    
    return text_blocks >= 2

def parse_file_directory(data, sector_num):
    """Parse what appears to be a file directory sector."""
    
    print(f"Raw data from sector {sector_num}:")
    for i in range(0, min(256, len(data)), 16):
        hex_part = ' '.join(f'{b:02x}' for b in data[i:i+16])
        ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data[i:i+16])
        print(f'{i:04x}: {hex_part:<48} |{ascii_part}|')
    
    # Try to find file entries
    files_found = []
    
    # Improved logic to look for filename patterns
    for offset in range(0, len(data) - 16, 2):
        # Look for potential filename + extension patterns
        chunk = data[offset:offset+16]
        if any(32 <= b <= 126 for b in chunk[:11]) or b'.' in chunk[:11]:
            filename_candidate = safe_decode(chunk[:11]).strip()
            if len(filename_candidate) > 2 and '.' in filename_candidate:
                files_found.append({
                    'filename': filename_candidate,
                    'offset': offset,
                    'sector': sector_num
                })
    
    if files_found:
        print(f"\nPotential files found in sector {sector_num}:")
        for file_info in files_found[:10]:  # Limit to first 10
            print(f"  - {file_info['filename']} (offset {file_info['offset']})")
    else:
        print(f"\nNo clear file entries found in sector {sector_num}")

def process_file_header(data):
    """Process a potential file header sector."""
    print("=== FILE HEADER ANALYSIS ===")
    header_info = {}
    # Assuming file header follows the structure detailed in the PDF
    file_number = struct.unpack('<H', data[0:2])[0]
    file_sequence_number = struct.unpack('<H', data[2:4])[0]
    relative_volume_number = struct.unpack('<H', data[4:6])[0]
    header_info['file_number'] = file_number
    header_info['file_sequence_number'] = file_sequence_number
    header_info['relative_volume_number'] = relative_volume_number

    # Parse additional header details
    # placeholder offsets and lengths - these should be extracted from the actual specification details
    name_start = 14
    name_length = 20
    header_info['name'] = safe_decode(data[name_start:name_start + name_length])

    print(f"File Number: {header_info['file_number']}")
    print(f"Sequence Number: {header_info['file_sequence_number']}")
    print(f"Relative Volume Number: {header_info['relative_volume_number']}")
    print(f"File Name: {header_info['name']}")

    return header_info

# Adjusting the range of sectors to scan based on findings
def scan_file_directories(file_path):
    """Scan multiple sectors looking for file directory structures."""
    
    # Read several sectors to look for file directory information
    print("Checking sectors for file directories...")
    for sector_num in range(20, 100):  # Expanded range
        try:
            sector_data = read_sector(file_path, sector_num)
            
            # Look for what appears to be file entries
            if has_file_entries(sector_data):
                print(f"\nAnalyzing sector {sector_num} (potential file directory):")
                parse_file_directory(sector_data, sector_num)
        except:
            continue

def analyze_index_file(file_path):
    """Analyze the index file which contains file headers."""
    print("Searching for index file structure...")
    
    # Based on the PDF, the index file contains file headers
    # Let's look at sectors that might contain file headers
    potential_headers = []
    
    for sector_num in range(20, 60):  # Focus on area where we found content
        try:
            sector_data = read_sector(file_path, sector_num)
            
            # Check if this sector looks like a file header
            if is_potential_file_header(sector_data):
                print(f"\nPotential file header found in sector {sector_num}:")
                header_info = process_file_header(sector_data)
                potential_headers.append({
                    'sector': sector_num,
                    'header': header_info
                })
        except:
            continue
    
    if potential_headers:
        print(f"\nFound {len(potential_headers)} potential file headers:")
        for i, header in enumerate(potential_headers[:5]):  # Show first 5
            print(f"  Header {i+1}: Sector {header['sector']}, File #{header['header']['file_number']}")
    else:
        print("\nNo clear file headers found in expected range")

def is_potential_file_header(data):
    """Check if a sector contains what looks like a file header."""
    if len(data) < 512:
        return False
    
    # Basic checks for file header structure
    # File headers should have specific patterns at the beginning
    try:
        file_number = struct.unpack('<H', data[0:2])[0]
        file_seq = struct.unpack('<H', data[2:4])[0]
        rel_vol = struct.unpack('<H', data[4:6])[0]
        
        # Reasonable ranges for these values
        if (0 < file_number < 65536 and 
            0 <= file_seq < 65536 and 
            rel_vol == 0):  # relative volume should be 0 for single volumes
            return True
    except:
        pass
    
    return False

# Example usage
if __name__ == "__main__":
    test_disk = "test_dsk_files/RSX11M_V3.1_SYSTEM0.dsk"
    extract_ods1_info(test_disk)

