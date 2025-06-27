#!/usr/bin/env python3
"""
Decodificador de caracteres PDP-8
Examina los datos encontrados para determinar la codificación correcta
"""

import sys

def analyze_char_encoding(data: bytes):
    """Analyze character encoding in the data"""
    print("=== CHARACTER ENCODING ANALYSIS ===")
    
    # Get first few non-space bytes
    interesting_bytes = []
    for b in data:
        if b != 0x40 and b != 0x00:  # Skip spaces and nulls
            interesting_bytes.append(b)
        if len(interesting_bytes) >= 20:
            break
    
    print(f"Interesting bytes: {[f'{b:02x}' for b in interesting_bytes]}")
    
    # Try different interpretations
    print("\n=== ASCII INTERPRETATION ===")
    ascii_chars = ''.join(chr(b) if 32 <= b <= 126 else f'\\x{b:02x}' for b in interesting_bytes)
    print(f"ASCII: {ascii_chars}")
    
    print("\n=== PDP-8 SIXBIT INTERPRETATION ===")
    # PDP-8 SIXBIT: add 0x40 to get ASCII
    sixbit_chars = ''.join(chr((b & 0x3F) + 0x40) if 0x40 <= (b & 0x3F) + 0x40 <= 0x7F else f'\\x{b:02x}' for b in interesting_bytes)
    print(f"SIXBIT: {sixbit_chars}")
    
    print("\n=== PDP-8 7-BIT ASCII ===")
    # Mask to 7 bits
    ascii7_chars = ''.join(chr(b & 0x7F) if 32 <= (b & 0x7F) <= 126 else f'\\x{b:02x}' for b in interesting_bytes)
    print(f"7-bit ASCII: {ascii7_chars}")
    
    print("\n=== RADIX-50 ANALYSIS ===")
    # Check if it could be RADIX-50 encoded
    for i in range(0, len(interesting_bytes)-1, 2):
        if i+1 < len(interesting_bytes):
            word = interesting_bytes[i] | (interesting_bytes[i+1] << 8)
            print(f"Word {i//2}: 0x{word:04x} = {word:05o} octal")
    
    print("\n=== OS/8 FILENAME ENCODING ===")
    # OS/8 packs 2 chars per word, 6 bits each
    # Try to decode assuming this is a filename
    words = []
    for i in range(0, len(interesting_bytes)-1, 2):
        if i+1 < len(interesting_bytes):
            word = interesting_bytes[i] | (interesting_bytes[i+1] << 8)
            words.append(word)
    
    print("Trying OS/8 filename decoding:")
    for i, word in enumerate(words[:4]):  # First 4 words usually filename
        char1 = (word >> 6) & 0o77
        char2 = word & 0o77
        
        c1 = chr(char1) if 0x20 <= char1 <= 0x7F else f'\\x{char1:02x}'
        c2 = chr(char2) if 0x20 <= char2 <= 0x7F else f'\\x{char2:02x}'
        
        print(f"  Word {i}: 0x{word:04x} -> chars: {c1}{c2} (0x{char1:02x}, 0x{char2:02x})")

def main():
    if len(sys.argv) != 2:
        print("Usage: python decode_pdp8_chars.py <disk_image>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    
    try:
        with open(image_path, 'rb') as f:
            image_data = f.read()
    except Exception as e:
        print(f"Error reading image: {e}")
        sys.exit(1)
    
    print(f"Loaded image: {len(image_data)} bytes")
    
    # Look at the sectors we found interesting data in
    sector_size = 128
    interesting_sectors = [4, 6, 8]
    
    for sector in interesting_sectors:
        offset = sector * sector_size
        sector_data = image_data[offset:offset + sector_size]
        
        print(f"\n{'='*60}")
        print(f"SECTOR {sector}")
        print(f"{'='*60}")
        
        # Show hex dump of first part
        print("First 32 bytes:")
        for i in range(0, min(32, len(sector_data)), 16):
            hex_part = ' '.join(f'{b:02x}' for b in sector_data[i:i+16])
            ascii_part = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in sector_data[i:i+16])
            print(f"{i:04x}: {hex_part:<48} |{ascii_part}|")
        
        analyze_char_encoding(sector_data)

if __name__ == "__main__":
    main()
