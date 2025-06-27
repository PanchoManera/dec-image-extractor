#!/usr/bin/env python3
"""
PDP-8 Disk Image Extractor - Improved Version
Based on analysis of PUTR.ASM code

This extractor handles:
- OS/8 and PS/8 file systems
- Multiple interleave patterns (DECtape 2:1, RX01/02 2:1/3:1, RX50 variants)
- Auto-detection of filesystem type and interleave
- Proper 12-bit word handling for PDP-8 systems
"""

import struct
import os
import sys
from typing import List, Tuple, Optional, Dict, Any
from dataclasses import dataclass
from enum import Enum

class FileSystemType(Enum):
    OS8 = "OS/8"
    PS8 = "PS/8"
    PUTR = "TSS/8 PUTR"
    UNKNOWN = "Unknown"

class MediaType(Enum):
    RX01 = "RX01"
    RX02 = "RX02"
    RX50 = "RX50"
    RX52 = "RX52"
    TU56 = "TU56"  # DECtape
    UNKNOWN = "Unknown"

@dataclass
class DeviceGeometry:
    """Device geometry information"""
    cylinders: int
    heads: int
    sectors_per_track: int
    bytes_per_sector: int
    total_sectors: int
    interleave_pattern: str
    word_size: int = 12  # PDP-8 uses 12-bit words

@dataclass
class DirectoryEntry:
    """OS/8 directory entry"""
    filename: str
    extension: str
    start_block: int
    length: int
    is_empty: bool = False

class InterleaveCalculator:
    """Handles different interleave patterns based on PUTR.ASM logic"""
    
    @staticmethod
    def rx01_interleave(logical_sector: int, track: int, is_pdp11: bool = False) -> int:
        """RX01 interleave: 2:1 for PDP-11, 2:1 no skew for PDP-8"""
        # From PUTR: ISEC=(ISEC-1)*2, IF(ISEC.GE.26) ISEC=ISEC-25
        sector = (logical_sector * 2) % 26
        
        if is_pdp11:
            # PDP-11 has 6-sector skew
            skew = (track * 6) % 26
            sector = (sector + skew) % 26
        
        return sector + 1  # 1-based
    
    @staticmethod
    def rx02_interleave(logical_sector: int, track: int, is_pdp11: bool = False) -> int:
        """RX02/03 interleave: 2:1 for PDP-11, 3:1 for PDP-8"""
        if is_pdp11:
            # 2:1 interleave, 6-sector skew
            sector = (logical_sector * 2) % 26
            skew = (track * 6) % 26
            sector = (sector + skew) % 26
        else:
            # 3:1 interleave, no skew for PDP-8
            sector = (logical_sector * 3) % 26
        
        return sector + 1
    
    @staticmethod
    def rx50_interleave(logical_sector: int, track: int, is_pdp11: bool = False) -> int:
        """RX50 interleave: complex pattern based on track number"""
        # From PUTR: ISEC=(ISEC-1)*2, IF(ISEC.GE.10) ISEC=ISEC-9
        sector = (logical_sector * 2) % 10
        if sector >= 10:
            sector = sector - 9
        
        if is_pdp11:
            # PDP-11 has 2-sector skew
            skew = (track * 2) % 10
            sector = (sector + skew) % 10
        
        return sector + 1
    
    @staticmethod
    def ps8_dectape_interleave(logical_block: int) -> Tuple[int, bool]:
        """PS/8 DECtape 2:1 interleave pattern"""
        # From PUTR: PS/8 has 2:1 interleave
        physical_block = logical_block * 2
        if physical_block >= 1024:
            physical_block = physical_block - 1024 + 1
        
        return physical_block, False  # False = forward direction
    
    @staticmethod
    def putr_dectape_interleave(logical_block: int) -> Tuple[int, bool]:
        """TSS/8 PUTR DECtape 11:1 interleave pattern"""
        # Complex 11:1 interleave from PUTR.ASM
        if logical_block < 2:
            adjusted_block = logical_block + 1474
        else:
            adjusted_block = logical_block - 2
        
        blocks_per_pass = 134  # 1474 / 11
        pass_number = adjusted_block // blocks_per_pass
        block_in_pass = adjusted_block % blocks_per_pass
        
        # Odd passes are in reverse
        reverse = (pass_number % 2) == 1
        if reverse:
            block_in_pass = 133 - block_in_pass
        
        # Apply 11:1 interleave
        physical_block = (block_in_pass * 11 + pass_number + 2) % 1474
        
        return physical_block, reverse

class PDP8DiskExtractor:
    """Improved PDP-8 disk extractor based on PUTR.ASM analysis"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image_data = None
        self.filesystem_type = FileSystemType.UNKNOWN
        self.media_type = MediaType.UNKNOWN
        self.geometry = None
        self.directory_entries = []
        self.interleave_detected = False
        
    def load_image(self) -> bool:
        """Load disk image"""
        try:
            with open(self.image_path, 'rb') as f:
                self.image_data = f.read()
            print(f"Loaded image: {len(self.image_data)} bytes")
            return True
        except Exception as e:
            print(f"Error loading image: {e}")
            return False
    
    def detect_media_type(self) -> MediaType:
        """Detect media type based on file size"""
        size = len(self.image_data)
        
        # Based on PUTR.ASM fsztab table
        media_sizes = {
            252928: (MediaType.RX01, True),   # RX01 interleaved
            256256: (MediaType.RX01, False),  # RX01 non-interleaved
            505856: (MediaType.RX02, True),   # RX02 interleaved  
            512512: (MediaType.RX02, False),  # RX02 non-interleaved
            409600: MediaType.RX50,           # RX50 400KB (both interleaved and not)
            819200: MediaType.RX52,           # RX52 800KB
            # DECtape sizes
            184832: MediaType.TU56,           # TU56 128 words * 1474 blocks * 1.5 bytes/word
            380928: MediaType.TU56,           # TU56 129 words * 1474 blocks * 1.5 bytes/word
        }
        
        if size in media_sizes:
            media_info = media_sizes[size]
            if isinstance(media_info, tuple):
                media_type, self.interleave_detected = media_info
                return media_type
            else:
                return media_info
        
        print(f"Unknown media size: {size} bytes")
        return MediaType.UNKNOWN
    
    def setup_geometry(self) -> bool:
        """Setup device geometry based on detected media type"""
        geometries = {
            MediaType.RX01: DeviceGeometry(77, 1, 26, 128, 2002, "2:1"),
            MediaType.RX02: DeviceGeometry(77, 1, 26, 256, 2002, "3:1" if not self.interleave_detected else "2:1"),
            MediaType.RX50: DeviceGeometry(80, 1, 10, 512, 800, "2:1"),
            MediaType.RX52: DeviceGeometry(80, 2, 10, 512, 1600, "2:1"),
            MediaType.TU56: DeviceGeometry(1, 1, 1474, 256, 1474, "varies"),  # DECtape
        }
        
        if self.media_type in geometries:
            self.geometry = geometries[self.media_type]
            print(f"Detected geometry: {self.geometry}")
            return True
        
        return False
    
    def read_block(self, block_number: int, apply_interleave: bool = True) -> Optional[bytes]:
        """Read a logical block, applying interleave if needed"""
        if not self.geometry:
            return None
        
        # Calculate physical position
        if apply_interleave and self.media_type == MediaType.TU56:
            # DECtape handling
            if self.filesystem_type == FileSystemType.PS8:
                physical_block, reverse = InterleaveCalculator.ps8_dectape_interleave(block_number)
            elif self.filesystem_type == FileSystemType.PUTR:
                physical_block, reverse = InterleaveCalculator.putr_dectape_interleave(block_number)
            else:
                physical_block, reverse = block_number, False
        else:
            # Regular disk handling
            if self.media_type in [MediaType.RX01, MediaType.RX02, MediaType.RX50, MediaType.RX52]:
                track = block_number // self.geometry.sectors_per_track
                sector = block_number % self.geometry.sectors_per_track
                
                if apply_interleave:
                    if self.media_type == MediaType.RX01:
                        physical_sector = InterleaveCalculator.rx01_interleave(sector, track, False)
                    elif self.media_type == MediaType.RX02:
                        physical_sector = InterleaveCalculator.rx02_interleave(sector, track, False)
                    elif self.media_type in [MediaType.RX50, MediaType.RX52]:
                        physical_sector = InterleaveCalculator.rx50_interleave(sector, track, False)
                    else:
                        physical_sector = sector + 1
                else:
                    physical_sector = sector + 1
                
                physical_block = track * self.geometry.sectors_per_track + (physical_sector - 1)
            else:
                physical_block = block_number
        
        # Read the physical block
        block_size = self.geometry.bytes_per_sector
        offset = physical_block * block_size
        
        if offset + block_size > len(self.image_data):
            return None
        
        return self.image_data[offset:offset + block_size]
    
    def convert_12bit_to_bytes(self, data: bytes) -> List[int]:
        """Convert byte stream to 12-bit words (PDP-8 format)"""
        words = []
        i = 0
        
        # Convert 8-bit bytes to a list of 12-bit words
        while i + 2 < len(data):
            # Merge three 8-bit bytes into two 12-bit words
            w1 = data[i] | ((data[i+1] & 0x0F) << 8)
            w2 = (data[i+1] >> 4) | (data[i+2] << 4)
            words.extend([w1 & 0xFFF, w2 & 0xFFF])  # Mask to 12 bits
            i += 3
        return words
    
    def detect_filesystem_type(self) -> FileSystemType:
        """Detect filesystem type by examining directory structure"""
        print("Detecting filesystem type...")
        
        # Try to read directory block (block 1 for OS/8)
        for interleave in [True, False]:
            print(f"\nTrying interleave: {interleave}")
            block_data = self.read_block(1, apply_interleave=interleave)
            if not block_data:
                print(f"Could not read block with interleave={interleave}")
                continue
            
            print(f"Block size: {len(block_data)} bytes")
            print(f"First 16 bytes: {' '.join(f'{b:02x}' for b in block_data[:16])}")
            
            # Check for OS/8 directory signature
            if self.check_os8_directory(block_data):
                print(f"Detected OS/8 filesystem (interleave: {interleave})")
                self.interleave_detected = interleave
                return FileSystemType.OS8
            
            # Check for PS/8 patterns
            if self.check_ps8_patterns(block_data):
                print(f"Detected PS/8 filesystem (interleave: {interleave})")
                self.interleave_detected = interleave
                return FileSystemType.PS8
            
            print(f"No filesystem detected with interleave={interleave}")
        
        print("Could not detect filesystem type")
        return FileSystemType.UNKNOWN
    
    def check_os8_directory(self, block_data: bytes) -> bool:
        """Check if block contains valid OS/8 directory"""
        try:
            # Convert to 12-bit words
            words = self.convert_12bit_to_bytes(block_data)
            print(f"Converted {len(block_data)} bytes to {len(words)} words")
            
            if len(words) < 10:
                print(f"Too few words: {len(words)}")
                return False
            
            print(f"First 10 words: {[f'{w:04o}' for w in words[:10]]}")
            
            # Check OS/8 directory header structure
            # Word 0: -(number of entries)
            # Word 1: next directory segment (0 if last)
            # Word 2: starting block number
            # Word 3: -(additional info words)
            
            num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
            next_segment = words[1] & 0xFFF
            start_block = words[2] & 0xFFF
            info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
            
            print(f"Parsed header: entries={num_entries}, next={next_segment}, start={start_block}, info={info_words}")
            
            # Sanity checks
            if num_entries > 200 or next_segment > 6 or start_block > 4096 or info_words > 10:
                print(f"Failed sanity check")
                return False
            
            # Check if we can parse some directory entries
            if len(words) > 5:
                return self.parse_os8_directory_entries(words[5:], num_entries, info_words) > 0
            else:
                print("Not enough words for directory entries")
                return False
            
        except Exception as e:
            print(f"Error checking OS/8 directory: {e}")
            import traceback
            traceback.print_exc()
            return False
    
    def check_ps8_patterns(self, block_data: bytes) -> bool:
        """Check for PS/8 specific patterns"""
        # PS/8 uses similar structure but with different file extension encoding
        # Look for PS/8 specific extension patterns
        try:
            words = self.convert_12bit_to_bytes(block_data)
            
            # Look for PS/8 specific file patterns
            for i in range(0, len(words) - 5, 5):
                if words[i] != 0:  # Not empty entry
                    # Check extension word for PS/8 patterns
                    ext_word = words[i + 4] if i + 4 < len(words) else 0
                    # PS/8 has different extension encoding
                    if (ext_word & 0o7740) != 0o0040:  # Not PUTR encoding
                        # Might be PS/8
                        return True
            
            return False
        except:
            return False
    
    def parse_os8_directory_entries(self, words: List[int], num_entries: int, info_words: int) -> int:
        """Parse OS/8 directory entries"""
        entries_found = 0
        i = 0
        
        for entry_num in range(num_entries):
            if i + 5 + info_words >= len(words):
                break
            
            # OS/8 directory entry format:
            # Words 0-4: filename (6 chars packed)
            # Word 4: extension 
            # Words 5+: info words
            # Last word: -(length in blocks)
            
            if words[i] == 0:
                # Empty entry
                i += 6 + info_words
                continue
            
            # Extract filename (first 5 words)
            filename = self.extract_filename(words[i:i+5])
            
            # Skip info words
            i += 5 + info_words
            
            # Get length
            if i < len(words):
                length_word = words[i]
                length = (0o10000 - length_word) & 0xFFF if length_word != 0 else 0
                i += 1
                
                if filename and length > 0:
                    entries_found += 1
        
        return entries_found
    
    def extract_filename(self, words: List[int]) -> str:
        """Extract filename from OS/8 directory entry"""
        try:
            # OS/8 packs filename in first 4.5 words (6 characters)
            chars = []
            
            for word in words[:4]:
                # Each word contains 2 characters
                char1 = (word >> 6) & 0o77
                char2 = word & 0o77
                
                if char1 >= 0o40:  # Valid character
                    chars.append(chr(char1))
                if char2 >= 0o40:
                    chars.append(chr(char2))
            
            # Handle extension in word 4
            ext_word = words[4] if len(words) > 4 else 0
            ext_chars = []
            char1 = (ext_word >> 6) & 0o77
            char2 = ext_word & 0o77
            
            if char1 >= 0o40:
                ext_chars.append(chr(char1))
            if char2 >= 0o40:
                ext_chars.append(chr(char2))
            
            filename = ''.join(chars).strip()
            extension = ''.join(ext_chars).strip()
            
            return f"{filename}.{extension}" if extension else filename
            
        except:
            return ""
    
    def extract_directory(self) -> bool:
        """Extract complete directory"""
        if self.filesystem_type == FileSystemType.UNKNOWN:
            return False
        
        print("Extracting directory...")
        self.directory_entries = []
        
        # Start with directory segment 1 (block 1)
        segment_num = 1
        current_block = 7  # Running block counter for files
        
        while segment_num > 0 and segment_num <= 6:
            block_data = self.read_block(segment_num, apply_interleave=self.interleave_detected)
            if not block_data:
                break
            
            words = self.convert_12bit_to_bytes(block_data)
            if len(words) < 10:
                break
            
            # Parse directory segment header
            print(f"Raw header words: {words[0]:04o} {words[1]:04o} {words[2]:04o} {words[3]:04o} {words[4]:04o}")
            
            num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
            next_segment = words[1] & 0xFFF
            start_block = words[2] & 0xFFF
            info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
            
            print(f"Parsed: entries={num_entries}, next={next_segment}, start={start_block}, info={info_words}")
            print(f"Directory segment {segment_num}: {num_entries} entries, next={next_segment}")
            
            # Parse entries
            i = 5  # Start after header
            for entry_num in range(num_entries):
                if i + 5 + info_words >= len(words):
                    break
                
                if words[i] == 0:
                    # Empty entry
                    entry = DirectoryEntry(
                        filename="<EMPTY>",
                        extension="",
                        start_block=0,
                        length=0,
                        is_empty=True
                    )
                    i += 6 + info_words
                else:
                    # File entry
                    filename = self.extract_filename(words[i:i+5])
                    i += 5 + info_words
                    
                    length_word = words[i] if i < len(words) else 0
                    length = (0o10000 - length_word) & 0xFFF if length_word != 0 else 0
                    i += 1
                    
                    entry = DirectoryEntry(
                        filename=filename,
                        extension="",
                        start_block=current_block,
                        length=length
                    )
                    current_block += length
                
                self.directory_entries.append(entry)
            
            segment_num = next_segment
        
        print(f"Found {len(self.directory_entries)} directory entries")
        return True
    
    def extract_file(self, entry: DirectoryEntry, output_dir: str) -> bool:
        """Extract a single file"""
        if entry.is_empty or entry.length == 0:
            return False
        
        try:
            filename = entry.filename.replace('/', '_').replace('\\', '_')
            filepath = os.path.join(output_dir, filename)
            
            with open(filepath, 'wb') as f:
                for block_num in range(entry.start_block, entry.start_block + entry.length):
                    block_data = self.read_block(block_num, apply_interleave=self.interleave_detected)
                    if block_data:
                        f.write(block_data)
            
            print(f"Extracted: {filename} ({entry.length} blocks)")
            return True
            
        except Exception as e:
            print(f"Error extracting {entry.filename}: {e}")
            return False
    
    def analyze_and_extract(self, output_dir: str = "extracted_pdp8") -> bool:
        """Main analysis and extraction routine"""
        if not self.load_image():
            return False
        
        # Create output directory
        os.makedirs(output_dir, exist_ok=True)
        
        # Detect media type
        self.media_type = self.detect_media_type()
        if self.media_type == MediaType.UNKNOWN:
            print("Warning: Unknown media type, attempting extraction anyway")
            # Set default geometry
            self.geometry = DeviceGeometry(80, 1, 10, 512, 800, "unknown")
        else:
            self.setup_geometry()
        
        # Detect filesystem
        self.filesystem_type = self.detect_filesystem_type()
        if self.filesystem_type == FileSystemType.UNKNOWN:
            print("Error: Could not detect filesystem type")
            return False
        
        # Extract directory
        if not self.extract_directory():
            print("Error: Could not extract directory")
            return False
        
        # Extract files
        extracted_count = 0
        for entry in self.directory_entries:
            if not entry.is_empty and self.extract_file(entry, output_dir):
                extracted_count += 1
        
        print(f"\nExtraction complete:")
        print(f"  Media: {self.media_type.value}")
        print(f"  Filesystem: {self.filesystem_type.value}")
        print(f"  Interleave: {self.interleave_detected}")
        print(f"  Files extracted: {extracted_count}")
        print(f"  Output directory: {output_dir}")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Usage: python extract_pdp8_improved.py <disk_image_file>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: File {image_path} not found")
        sys.exit(1)
    
    extractor = PDP8DiskExtractor(image_path)
    
    if extractor.analyze_and_extract():
        print("Extraction successful!")
    else:
        print("Extraction failed!")
        sys.exit(1)

if __name__ == "__main__":
    main()
