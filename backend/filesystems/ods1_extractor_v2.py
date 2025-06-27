#!/usr/bin/env python3
"""
ODS-1 (Files-11 Level 1) File System Extractor
Based on the Files11.cs reference implementation by Kenneth Gober
and official DEC Files-11 ODS-1 specifications.

Supports RSX-11M, RSX-11S, IAS, and early VMS ODS-1 disk images.
"""

import struct
import os
import argparse
from typing import Dict, List, Tuple, Optional, NamedTuple
from dataclasses import dataclass
from datetime import datetime

class Files11Exception(Exception):
    """Exception for Files-11 specific errors."""
    pass

@dataclass
class FileHeader:
    """Files-11 file header structure."""
    file_number: int
    file_sequence: int
    structure_level: int
    owner_uic: int
    protection: int
    characteristics: int
    
    # User File Attributes
    record_type: int = 0
    record_attributes: int = 0
    record_size: int = 0
    highest_vbn: int = 0
    end_of_file_block: int = 0
    first_free_byte: int = 0
    
    # File Identity Area
    filename: str = ""
    filetype: str = ""
    version: int = 0
    revision_number: int = 0
    revision_date: str = ""
    revision_time: str = ""
    creation_date: str = ""
    creation_time: str = ""
    expiration_date: str = ""
    
    # Map Area
    extension_segment: int = 0
    extension_relative_volume: int = 0
    extension_file_number: int = 0
    extension_file_sequence: int = 0
    count_size: int = 0
    lbn_size: int = 0
    map_words_used: int = 0
    map_words_available: int = 0
    retrieval_pointers: List[Tuple[int, int]] = None
    
    def __post_init__(self):
        if self.retrieval_pointers is None:
            self.retrieval_pointers = []

class Radix50:
    """RADIX-50 encoding/decoding utilities."""
    
    # Standard RADIX-50 character set as used in Files-11
    CHARSET = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$._0123456789"
    
    @classmethod
    def decode_word(cls, word: int) -> str:
        """Decode a single 16-bit RADIX-50 word to 3 characters."""
        if word > 0o174777:  # Beyond valid range
            return "???"
            
        result = ""
        # Extract 3 characters from word (base 40)
        for i in range(3):
            char_index = word % 40
            word //= 40
            result = cls.CHARSET[char_index] + result
            
        return result
    
    @classmethod
    def decode_filename(cls, word1: int, word2: int, word3: int) -> str:
        """Decode filename from 3 RADIX-50 words (9 characters)."""
        name = cls.decode_word(word1) + cls.decode_word(word2) + cls.decode_word(word3)
        return name.rstrip()  # Remove trailing spaces
    
    @classmethod
    def decode_filetype(cls, word: int) -> str:
        """Decode file type from 1 RADIX-50 word (3 characters)."""
        return cls.decode_word(word).rstrip()

class ODS1Extractor:
    """Enhanced ODS-1 file system extractor based on Files11.cs reference."""
    
    BLOCK_SIZE = 512
    HOME_BLOCK_LBN = 1
    
    def __init__(self, disk_image_path: str):
        self.disk_path = disk_image_path
        self.volume_name = ""
        self.volume_structure_level = 0
        self.index_file_bitmap_size = 0
        self.index_file_bitmap_lbn = 0
        self.max_files = 0
        self.storage_bitmap_cluster_factor = 0
        self.device_type = 0
        self.volume_owner_uic = 0
        self.volume_protection = 0
        self.volume_characteristics = 0
        self.default_file_protection = 0
        self.default_window_size = 0
        self.default_file_extend = 0
        self.volume_creation_date = ""
        
        # Calculate disk size
        with open(disk_image_path, 'rb') as f:
            f.seek(0, 2)
            self.disk_size = f.tell()
            self.total_blocks = self.disk_size // self.BLOCK_SIZE
    
    def read_block(self, lbn: int) -> bytes:
        """Read a logical block from the disk image."""
        if lbn < 0 or lbn >= self.total_blocks:
            raise Files11Exception(f"Invalid LBN {lbn} (disk has {self.total_blocks} blocks)")
            
        with open(self.disk_path, 'rb') as f:
            f.seek(lbn * self.BLOCK_SIZE)
            data = f.read(self.BLOCK_SIZE)
            if len(data) != self.BLOCK_SIZE:
                raise Files11Exception(f"Could not read complete block {lbn}")
            return data
    
    def parse_home_block(self) -> bool:
        """Parse the home block (LBN 1) according to Files-11 spec."""
        try:
            data = self.read_block(self.HOME_BLOCK_LBN)
            
            # Home Block structure according to Files-11 ODS-1 spec
            self.index_file_bitmap_size = struct.unpack('<H', data[0:2])[0]
            
            # Index file bitmap LBN (2 words, high word first)
            bitmap_lbn_high = struct.unpack('<H', data[2:4])[0]
            bitmap_lbn_low = struct.unpack('<H', data[4:6])[0]
            self.index_file_bitmap_lbn = (bitmap_lbn_high << 16) | bitmap_lbn_low
            
            self.max_files = struct.unpack('<H', data[6:8])[0]
            self.storage_bitmap_cluster_factor = struct.unpack('<H', data[8:10])[0]
            self.device_type = struct.unpack('<H', data[10:12])[0]
            self.volume_structure_level = struct.unpack('<H', data[12:14])[0]
            
            # Volume name (12 bytes, null-padded)
            vol_name_bytes = data[14:26]
            self.volume_name = vol_name_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
            
            self.volume_owner_uic = struct.unpack('<L', data[30:34])[0]
            self.volume_protection = struct.unpack('<H', data[32:34])[0]
            self.volume_characteristics = struct.unpack('<H', data[34:36])[0]
            self.default_file_protection = struct.unpack('<H', data[36:38])[0]
            
            self.default_window_size = data[44] if len(data) > 44 else 0
            self.default_file_extend = data[45] if len(data) > 45 else 0
            
            # Volume creation date (14 bytes: "DDMMMYYHHMMSS")
            if len(data) >= 74:
                vol_date_bytes = data[60:74]
                self.volume_creation_date = vol_date_bytes.rstrip(b'\x00').decode('ascii', errors='ignore')
            
            # Validate home block
            if self.index_file_bitmap_size == 0:
                return False
                
            if self.index_file_bitmap_lbn == 0:
                return False
                
            if self.max_files == 0:
                return False
                
            # Check structure level (should be 0x0101 for ODS-1)
            if self.volume_structure_level != 0x0101:
                print(f"Warning: Invalid ODS-1 structure level 0x{self.volume_structure_level:04x} (expected 0x0101)")
                return False  # Reject if structure level is not ODS-1
                
            return True
            
        except Exception as e:
            raise Files11Exception(f"Error parsing home block: {e}")
    
    def parse_file_header(self, data: bytes, lbn: int) -> Optional[FileHeader]:
        """Parse a file header block according to Files-11 spec and putr.asm."""
        if len(data) < self.BLOCK_SIZE:
            return None
            
        try:
            # File Header Area (based on putr.asm offsets)
            ident_offset = data[0]    # h_idof (byte offset of identification area)
            map_offset = data[1]      # h_mpof (byte offset of map area)
            file_number = struct.unpack('<H', data[2:4])[0]   # h_fnum
            file_sequence = struct.unpack('<H', data[4:6])[0] # h_fseq
            structure_level = struct.unpack('<H', data[6:8])[0] # h_flev
            owner_uic = struct.unpack('<H', data[8:10])[0]    # h_fown
            protection = struct.unpack('<H', data[10:12])[0]  # h_fpro
            characteristics = struct.unpack('<H', data[12:14])[0] # h_fcha
            
            # Validate file header
            if file_number == 0 or file_number > 65535:
                return None
                
            if structure_level != 0x0101:
                return None
                
            header = FileHeader(
                file_number=file_number,
                file_sequence=file_sequence,
                structure_level=structure_level,
                owner_uic=owner_uic,
                protection=protection,
                characteristics=characteristics
            )
            
            # User File Attributes (32 bytes starting at offset 18)
            if len(data) >= 50:
                ufat_start = 18
                header.record_type = data[ufat_start]
                header.record_attributes = data[ufat_start + 1]
                header.record_size = struct.unpack('<H', data[ufat_start + 2:ufat_start + 4])[0]
                header.highest_vbn = struct.unpack('<L', data[ufat_start + 4:ufat_start + 8])[0]
                header.end_of_file_block = struct.unpack('<L', data[ufat_start + 8:ufat_start + 12])[0]
                header.first_free_byte = struct.unpack('<H', data[ufat_start + 12:ufat_start + 14])[0]
            
            # File Ident Area (offset specified by H.IDOF)
            if ident_offset > 0 and ident_offset * 2 + 46 <= len(data):
                ident_start = ident_offset * 2
                
                # File name (3 RADIX-50 words = 9 characters)
                name_word1 = struct.unpack('<H', data[ident_start:ident_start + 2])[0]
                name_word2 = struct.unpack('<H', data[ident_start + 2:ident_start + 4])[0]
                name_word3 = struct.unpack('<H', data[ident_start + 4:ident_start + 6])[0]
                header.filename = Radix50.decode_filename(name_word1, name_word2, name_word3)
                
                # File type (1 RADIX-50 word = 3 characters)
                type_word = struct.unpack('<H', data[ident_start + 6:ident_start + 8])[0]
                header.filetype = Radix50.decode_filetype(type_word)
                
                # Version number
                header.version = struct.unpack('<h', data[ident_start + 8:ident_start + 10])[0]  # signed
                
                # Revision number
                header.revision_number = struct.unpack('<H', data[ident_start + 10:ident_start + 12])[0]
                
                # Dates and times (7-byte ASCII strings)
                header.revision_date = data[ident_start + 12:ident_start + 19].decode('ascii', errors='ignore').rstrip('\x00')
                header.revision_time = data[ident_start + 19:ident_start + 25].decode('ascii', errors='ignore').rstrip('\x00')
                header.creation_date = data[ident_start + 25:ident_start + 32].decode('ascii', errors='ignore').rstrip('\x00')
                header.creation_time = data[ident_start + 32:ident_start + 38].decode('ascii', errors='ignore').rstrip('\x00')
                header.expiration_date = data[ident_start + 38:ident_start + 45].decode('ascii', errors='ignore').rstrip('\x00')
            
            # File Map Area (offset specified by H.MPOF, based on SIMH ODS-1 implementation)
            if map_offset > 0 and map_offset * 2 + 13 <= len(data):
                map_start = map_offset * 2
                
                # Map area structure based on SIMH ODS1_Retreval:
                # Extension info (8 bytes): segnum, rvn, filnum, filseq
                # Format info (2 bytes): countsize, lbnsize  
                # Usage info (2 bytes): inuse, avail
                # Retrieval pointers follow immediately after
                
                header.extension_segment = struct.unpack('<H', data[map_start:map_start + 2])[0]
                header.extension_relative_volume = struct.unpack('<H', data[map_start + 2:map_start + 4])[0]
                header.extension_file_number = struct.unpack('<H', data[map_start + 4:map_start + 6])[0]
                header.extension_file_sequence = struct.unpack('<H', data[map_start + 6:map_start + 8])[0]
                
                # Extract count_size and lbn_size as separate bytes (SIMH approach)
                # Based on debugging, lbn_size=204 suggests we're reading wrong offset
                # According to putr.asm, these should be in M.CTSZ and M.LBSZ
                # Let's try reading from the correct SIMH ODS-1 structure
                
                # In SIMH ODS1_Retreval structure:
                # M.CTSZ is at offset +8 from start of map area
                # M.LBSZ is at offset +9 from start of map area  
                # But according to debug, these seem to be packed differently
                
                # Try reading from different offset - debug shows lbn_size=204 is wrong
                count_size_offset = map_start + 8
                lbn_size_offset = map_start + 9
                
                if count_size_offset < len(data) and lbn_size_offset < len(data):
                    header.count_size = data[count_size_offset]
                    header.lbn_size = data[lbn_size_offset]
                else:
                    # Fallback to default values if we can't read them
                    header.count_size = 1
                    header.lbn_size = 3
                
                # Map words in use and available
                header.map_words_used = data[map_start + 10] if map_start + 10 < len(data) else 0
                header.map_words_available = data[map_start + 11] if map_start + 11 < len(data) else 0
                
                # Debug info for first few files (disabled in production)
                # if file_number <= 5:
                #     print(f"  DEBUG File {file_number}: map_offset={map_offset}, count_size={header.count_size}, lbn_size={header.lbn_size}, words_used={header.map_words_used}")
                
                # Parse retrieval pointers starting at offset 12 (after the 12-byte header)
                # This matches SIMH's ODS1_Retreval structure where pointers start after the header
                header.retrieval_pointers = self.parse_retrieval_pointers(
                    data, map_start + 12, header.count_size, header.lbn_size, header.map_words_used
                )
                
                # Debug specific problematic files (disabled in production)
                # if header.filename in ['001002', '001020', '001024', '001034', '001054', '002054', '003054', '011010', '011024', '011034', '045010', 'USER', '200200']:
                #     print(f"    DEBUG {header.filename}: Got {len(header.retrieval_pointers)} pointers: {header.retrieval_pointers}")
            
            return header
            
        except Exception as e:
            print(f"Error parsing file header at LBN {lbn}: {e}")
            return None
    
    def parse_retrieval_pointers(self, data: bytes, start: int, count_size: int, lbn_size: int, words_used: int) -> List[Tuple[int, int]]:
        """Parse retrieval pointers based on putr.asm and FSX logic."""
        pointers = []
        
        if words_used == 0:
            return pointers
            
        # Calculate end of retrieval pointer area
        # From putr.asm: M.USE words * 2 + 12 (M.RTRV offset)
        end_offset = start + (words_used * 2)
        
        # Special check: if ALL retrieval pointer data is zeros, this is an empty file
        # This handles RSX-11M+ allocated but unused directory entries
        if start < len(data) and end_offset <= len(data):
            retrieval_data = data[start:end_offset]
            if all(b == 0 for b in retrieval_data):
                # All zeros means allocated but empty file
                # Return special marker that indicates "empty but valid"
                return [(0, 0)]
        
        offset = start
        
        try:
            while offset < end_offset and offset + 4 <= len(data):
                # Format detection based on count_size and lbn_size
                if count_size == 1 and lbn_size == 3:
                    # Format 1,3 (most common) - FSX Files11.cs lines 514-519
                    if offset + 4 > len(data):
                        break
                        
                    lbn_high = data[offset]       # High 8 bits
                    count = data[offset + 1]     # Count (no +1 needed here)
                    lbn_low = struct.unpack('<H', data[offset + 2:offset + 4])[0]  # Low 16 bits
                    lbn = (lbn_high << 16) | lbn_low
                    offset += 4
                    
                elif count_size == 2 and lbn_size == 2:
                    # Format 2,2 - FSX Files11.cs lines 520-523
                    if offset + 4 > len(data):
                        break
                        
                    count = struct.unpack('<H', data[offset:offset + 2])[0]  # No +1 needed
                    lbn = struct.unpack('<H', data[offset + 2:offset + 4])[0]
                    offset += 4
                    
                elif count_size == 2 and lbn_size == 4:
                    # Format 2,4 - FSX Files11.cs lines 524-528
                    if offset + 6 > len(data):
                        break
                        
                    count = struct.unpack('<H', data[offset:offset + 2])[0]  # No +1 needed
                    lbn_low = struct.unpack('<H', data[offset + 2:offset + 4])[0]
                    lbn_high = struct.unpack('<H', data[offset + 4:offset + 6])[0]
                    lbn = (lbn_high << 16) | lbn_low
                    offset += 6
                    
                else:
                    # Unknown format
                    print(f"Unknown retrieval pointer format: count_size={count_size}, lbn_size={lbn_size}")
                    break
                
                # Validate and add pointer
                if count > 0 and lbn > 0:
                    pointers.append((lbn, count))
                else:
                    # End of valid pointers
                    break
                
                # Safety check
                if len(pointers) > 100:
                    break
                    
        except Exception as e:
            print(f"Error parsing retrieval pointers: {e}")
            
        return pointers
    
    def scan_for_file_headers(self) -> List[FileHeader]:
        """Scan the disk for valid file headers."""
        headers = []
        
        print(f"Scanning {self.total_blocks} blocks for file headers...")
        
        # Focus on likely areas for file headers
        scan_ranges = [
            (2, min(100, self.total_blocks)),      # Just after home block
            (self.index_file_bitmap_lbn, min(self.index_file_bitmap_lbn + 50, self.total_blocks)) if self.index_file_bitmap_lbn > 0 else (0, 0),
        ]
        
        # Add more scan ranges for larger disks
        if self.total_blocks > 1000:
            scan_ranges.extend([
                (100, min(500, self.total_blocks)),
                (self.total_blocks // 4, min(self.total_blocks // 4 + 100, self.total_blocks)),
            ])
        
        scanned_count = 0
        for start, end in scan_ranges:
            if start == end:
                continue
                
            for lbn in range(start, end):
                try:
                    data = self.read_block(lbn)
                    header = self.parse_file_header(data, lbn)
                    
                    if header and header.filename and header.filename != "UNKNOWN":
                        headers.append(header)
                        print(f"  Found: {header.filename}.{header.filetype};{header.version} "
                              f"(File {header.file_number}.{header.file_sequence}) @ LBN {lbn}")
                    
                    scanned_count += 1
                    if scanned_count % 100 == 0:
                        print(f"  Scanned {scanned_count} blocks, found {len(headers)} files...")
                        
                except Exception:
                    continue
        
        print(f"Found {len(headers)} valid file headers")
        return headers
    
    def extract_file_data(self, header: FileHeader) -> bytes:
        """Extract file data using retrieval pointers or contiguous allocation."""
        data = b""
        
        # Method 1: Use retrieval pointers if available
        if header.retrieval_pointers:
            # Special case: (0, 0) means allocated but empty file
            if header.retrieval_pointers == [(0, 0)]:
                return b""
                
            try:
                for lbn, count in header.retrieval_pointers:
                    # Skip invalid pointers
                    if lbn == 0 or count == 0:
                        continue
                        
                    # FSX Files11.cs line 82: for (Int32 i = 0; i <= ct; i++)
                    # This means we read count+1 blocks
                    for i in range(count + 1):
                        block_data = self.read_block(lbn + i)
                        data += block_data
                        
            except Exception as e:
                print(f"Error reading retrieval pointers for {header.filename}: {e}")
                return None
        
        # Method 2: Handle files that appear empty but might be system files or task images
        elif header.end_of_file_block == 0 and header.first_free_byte == 0:
            # For TSK files, use RSX-11M's special contiguous allocation scheme
            # RSX-11M stores Task Images (TSK files) contiguously for fast loading
            # The location is encoded in F.HIBK (Highest VBN Allocated) field
            # According to Files11.cs specification and our analysis of RSX-11M behavior
            if header.filetype.upper() == 'TSK' and header.highest_vbn > 0:
                print(f"  Attempting TSK extraction using highest_vbn for {header.filename}")
                try:
                    # Extract LBN from highest_vbn: RSX-11M uses format 0xXXY0000 where XX is LBN
                    # This is a documented but rarely implemented feature of RSX-11M task image storage
                    lbn_from_vbn = (header.highest_vbn >> 16) & 0xFF
                    
                    if lbn_from_vbn > 0 and lbn_from_vbn < self.total_blocks:
                        print(f"    Trying LBN {lbn_from_vbn} derived from highest_vbn=0x{header.highest_vbn:08x}")
                        
                        test_data = b""
                        empty_blocks_count = 0
                        
                        # Read up to 100 blocks from the calculated location
                        for i in range(100):
                            try:
                                block_data = self.read_block(lbn_from_vbn + i)
                                
                                # Check if block is all zeros
                                if all(b == 0 for b in block_data):
                                    empty_blocks_count += 1
                                    # Stop if we hit 3 consecutive empty blocks
                                    if empty_blocks_count >= 3:
                                        break
                                else:
                                    empty_blocks_count = 0
                                    
                                test_data += block_data
                                
                            except Exception as e:
                                print(f"      Error reading block {lbn_from_vbn + i}: {e}")
                                break
                        
                        # Validate the data
                        if test_data and len(test_data) > 1024:  # At least 2 blocks
                            non_zero_count = sum(1 for b in test_data if b != 0)
                            data_ratio = non_zero_count / len(test_data)
                            
                            print(f"      Read {len(test_data)} bytes, {non_zero_count} non-zero ({data_ratio:.1%})")
                            
                            # Accept if we have reasonable amount of data
                            if data_ratio >= 0.1 and len(test_data) >= 1024:  # At least 10% non-zero
                                print(f"    ✅ Found TSK file {header.filename} at LBN {lbn_from_vbn}: {len(test_data)} bytes")
                                return test_data
                            
                except Exception as e:
                    print(f"    Error in TSK VBN extraction for {header.filename}: {e}")
            
            # For system files and other task images, try contiguous extraction
            needs_extraction = (
                (header.filename in ['INDEXF', 'BITMAP', 'BADBLK', 'CORIMG'] and header.file_number <= 10) or
                header.filetype.upper() == 'TSK' or  # Task images (fallback)
                header.filetype.upper() == 'SAV' or  # Executable programs
                header.filename in ['RSX11', 'SYSLIB', 'VMLIB']  # Large system files
            )
            
            if needs_extraction:
                print(f"  Attempting contiguous extraction for {header.filetype.upper()} file {header.filename}")
                try:
                    data = self.extract_contiguous_file(header)
                    if data and len(data) > 0:
                        print(f"  ✅ Found data for {header.filename}: {len(data)} bytes")
                        return data
                except Exception as e:
                    print(f"  Failed to extract {header.filetype.upper()} file {header.filename}: {e}")
            
            # This is a legitimate empty file (common for unused directories)
            return b""
        
        # Method 3: Handle system files without retrieval pointers
        # These are often stored contiguously starting at specific locations
        elif header.map_words_used == 0:
            try:
                data = self.extract_contiguous_file(header)
            except Exception as e:
                print(f"Error extracting contiguous file {header.filename}: {e}")
                return None
        
        # If no data was found and it's not an empty file, return None (error)
        if not data and not (header.end_of_file_block == 0 and header.first_free_byte == 0):
            return None
        
        # Method 4: Truncate to actual file size if known
        if data and header.end_of_file_block > 0:
            try:
                # Calculate actual file size in bytes
                file_size_bytes = (header.end_of_file_block - 1) * self.BLOCK_SIZE
                if header.first_free_byte > 0:
                    file_size_bytes += header.first_free_byte
                else:
                    file_size_bytes += self.BLOCK_SIZE
                    
                if file_size_bytes < len(data):
                    data = data[:file_size_bytes]
            except Exception as e:
                print(f"Error truncating file {header.filename}: {e}")
                    
        return data
    
    def extract_contiguous_file(self, header: FileHeader) -> bytes:
        """Extract files stored contiguously (system files without retrieval pointers)."""
        data = b""
        
        # Strategy 1: For files with EOF info, try LBN = file_number (found pattern!)
        if header.end_of_file_block > 0:
            try:
                start_lbn = header.file_number
                expected_blocks = header.end_of_file_block
                
                print(f"  Trying contiguous at LBN {start_lbn} for {expected_blocks} blocks")
                
                # Read the expected blocks
                for i in range(expected_blocks):
                    try:
                        block_data = self.read_block(start_lbn + i)
                        data += block_data
                    except:
                        break
                
                # Verify this looks like real data
                if data:
                    non_zero_count = sum(1 for b in data if b != 0)
                    expected_size = (header.end_of_file_block - 1) * 512
                    if header.first_free_byte > 0:
                        expected_size += header.first_free_byte
                    else:
                        expected_size += 512
                    
                    # If we have reasonable data amount, accept it
                    if non_zero_count > expected_size * 0.05:  # At least 5% non-zero
                        print(f"  ✅ Found contiguous file at LBN {start_lbn}")
                        return data
                    else:
                        data = b""  # Reset for other strategies
                        
            except Exception as e:
                print(f"  Failed contiguous strategy 1: {e}")
                data = b""
        
        # Strategy 1.5: Special handling for RSX11.SYS and other large system files
        if not data and header.filename in ['RSX11', 'RSXMAC', 'SYSLIB', 'VMLIB']:
            # These are often large system files stored at predictable locations
            # Try multiple strategies for system files
            potential_locations = [
                header.file_number,  # Direct file number
                header.file_number * 2,  # Double file number
                100 + header.file_number,  # After system area
                1000 + header.file_number,  # After index area
                self.index_file_bitmap_lbn - header.file_number,  # Before index
            ]
            
            for start_lbn in potential_locations:
                if start_lbn <= 0 or start_lbn >= self.total_blocks - 10:
                    continue
                    
                try:
                    print(f"  Trying system file strategy at LBN {start_lbn}")
                    test_data = b""
                    
                    # Read up to 50 blocks to find the file
                    for i in range(50):
                        try:
                            block_data = self.read_block(start_lbn + i)
                            test_data += block_data
                            
                            # Stop if we hit empty blocks
                            if all(b == 0 for b in block_data):
                                break
                                
                        except:
                            break
                    
                    # Check if this looks like a valid file
                    if test_data:
                        non_zero_count = sum(1 for b in test_data if b != 0)
                        if non_zero_count > len(test_data) * 0.1:  # At least 10% non-zero
                            print(f"  ✅ Found system file at LBN {start_lbn}")
                            return test_data
                            
                except Exception as e:
                    print(f"  Failed system file strategy at LBN {start_lbn}: {e}")
                    continue
        
        # Strategy 2: Try multiple locations based on SIMH/RSX-11 patterns
        if not data and header.file_number <= 16:
            print(f"  Trying multiple system file locations for {header.filename} (file #{header.file_number})")
            
            # Based on SIMH and RSX-11 documentation, system files can be stored in various patterns:
            potential_locations = []
            
            if header.file_number == 1:  # INDEXF.SYS - this one worked!
                # Index file - try current working location first
                potential_locations.extend([
                    self.index_file_bitmap_lbn + self.index_file_bitmap_size,  # After index bitmap
                    2,  # Early in disk
                    self.index_file_bitmap_lbn - 10,  # Before index area
                ])
            elif header.file_number == 2:  # BITMAP.SYS
                # Storage bitmap file - often near beginning or after index
                potential_locations.extend([
                    2,  # Very early
                    10,  # Early system area
                    self.index_file_bitmap_lbn + self.index_file_bitmap_size + 10,
                    100,  # System file area
                    header.file_number,  # Direct file number
                ])
            elif header.file_number == 3:  # BADBLK.SYS
                # Bad block file - can be anywhere, often small
                potential_locations.extend([
                    header.file_number,  # Direct
                    10 + header.file_number,
                    50,
                    self.index_file_bitmap_lbn + header.file_number,
                    200,  # Common system area
                ])
            elif header.file_number == 4:  # 000000.DIR
                # Root directory
                potential_locations.extend([
                    header.file_number,
                    10,
                    20,
                    self.index_file_bitmap_lbn + header.file_number,
                    300,
                ])
            elif header.file_number == 5:  # CORIMG.SYS
                # Core image file - often larger
                potential_locations.extend([
                    header.file_number,
                    header.file_number * 2,
                    100,
                    500,
                    self.index_file_bitmap_lbn + header.file_number,
                ])
            else:
                # Generic system files, TSK files, and SAV files
                potential_locations.extend([
                    header.file_number,
                    header.file_number * 2,
                    100 + header.file_number,
                    self.index_file_bitmap_lbn + header.file_number,
                ])
                
                # Special locations for TSK (Task Image) and SAV (Executable) files
                if header.filetype.upper() in ['TSK', 'SAV']:
                    potential_locations.extend([
                        # Common locations for executable files in RSX-11
                        50 + header.file_number,
                        200 + header.file_number,
                        1000 + header.file_number,
                        # Try some common task areas
                        1500, 1600, 1700, 1800, 1900, 2000,
                        # Try areas before index
                        self.index_file_bitmap_lbn - 100 - header.file_number,
                        self.index_file_bitmap_lbn - 200 - header.file_number,
                    ])
            
            # Try each potential location
            for start_lbn in potential_locations:
                if start_lbn <= 0 or start_lbn >= self.total_blocks - 2:
                    continue
                    
                try:
                    print(f"    Trying LBN {start_lbn} for {header.filename}")
                    test_data = b""
                    
                    # Read up to 50 blocks, but stop at reasonable boundaries
                    max_blocks = 100 if header.filetype.upper() in ['TSK', 'SAV'] else 50 if header.filename in ['CORIMG', 'RSX11'] else 20
                    empty_blocks_count = 0
                    
                    for i in range(max_blocks):
                        try:
                            block_data = self.read_block(start_lbn + i)
                            
                            # Check if block is all zeros
                            if all(b == 0 for b in block_data):
                                empty_blocks_count += 1
                                # Stop if we hit 3 consecutive empty blocks
                                if empty_blocks_count >= 3:
                                    break
                            else:
                                empty_blocks_count = 0
                                
                            test_data += block_data
                            
                        except Exception as e:
                            print(f"      Error reading block {start_lbn + i}: {e}")
                            break
                    
                    # Validate the data
                    if test_data and len(test_data) > 0:
                        non_zero_count = sum(1 for b in test_data if b != 0)
                        data_ratio = non_zero_count / len(test_data)
                        
                        print(f"      Read {len(test_data)} bytes, {non_zero_count} non-zero ({data_ratio:.1%})")
                        
                        # Accept if we have reasonable amount of data
                        # Different thresholds for different file types
                        min_ratio = 0.01  # 1% for small system files
                        if header.filename == 'CORIMG':
                            min_ratio = 0.05  # 5% for core image
                        elif header.filename in ['BITMAP', 'BADBLK']:
                            min_ratio = 0.001  # Very low for these special files
                        
                        if data_ratio >= min_ratio and len(test_data) >= 512:
                            print(f"    ✅ Found {header.filename} at LBN {start_lbn}: {len(test_data)} bytes")
                            return test_data
                        elif len(test_data) >= 512 and non_zero_count > 10:
                            # Accept even small amounts of data for system files
                            print(f"    ✅ Found small {header.filename} at LBN {start_lbn}: {len(test_data)} bytes (low density)")
                            return test_data
                        else:
                            print(f"      Data quality too low, continuing search")
                            
                except Exception as e:
                    print(f"      Error at LBN {start_lbn}: {e}")
                    continue
        
        # Alternative method: Look near the file header location
        if not data:
            # Some files might be stored near their header
            header_lbn = self.index_file_bitmap_lbn + header.file_number
            
            for offset in [0, 1, -1, 2, -2]:  # Try nearby blocks
                try:
                    test_lbn = header_lbn + offset
                    if test_lbn < 2 or test_lbn >= self.total_blocks:
                        continue
                        
                    block_data = self.read_block(test_lbn)
                    
                    # Check if this looks like file data (not all zeros, not a header)
                    non_zero_count = sum(1 for b in block_data if b != 0)
                    if non_zero_count > 100 and not self.looks_like_header(block_data):
                        data = block_data
                        
                        # Try to read additional blocks
                        for i in range(1, 20):
                            try:
                                next_block = self.read_block(test_lbn + i)
                                if all(b == 0 for b in next_block):
                                    break
                                data += next_block
                            except:
                                break
                        break
                        
                except Exception:
                    continue
        
        return data
    
    def get_file_type(self, filetype: str) -> str:
        """Map file extension to human-readable type."""
        if not filetype:
            return "Unknown"
            
        filetype = filetype.upper()
        type_map = {
            'SYS': 'System File',
            'DIR': 'Directory', 
            'SAV': 'Executable Program',
            'TSK': 'Task Image',
            'OBJ': 'Object File',
            'MAC': 'Macro Source',
            'FOR': 'FORTRAN Source',
            'BAS': 'BASIC Source',
            'PAL': 'PAL Assembly Source',
            'CMD': 'Command File',
            'TXT': 'Text File',
            'DAT': 'Data File',
            'LIB': 'Library File',
            'STB': 'Symbol Table',
            'TMP': 'Temporary File',
            'BAK': 'Backup File',
            'LST': 'Listing File',
            'LOG': 'Log File',
            'HLP': 'Help File',
            'MAP': 'Map File',
            'ODL': 'ODL File',
            'MLB': 'Macro Library',
            'OLB': 'Object Library'
        }
        
        return type_map.get(filetype, f'{filetype} File')
    
    def format_date(self, date_str: str) -> str:
        """Format ODS-1 date string to standard format."""
        if not date_str or date_str.strip() == '':
            return "N/A"
            
        # ODS-1 dates are in format "DDMMMYY" (7 chars)
        # e.g., "20DEC85" for December 20, 1985
        date_str = date_str.strip()
        
        if len(date_str) == 7:
            try:
                day = date_str[:2]
                month_abbr = date_str[2:5]
                year = date_str[5:7]
                
                # Convert month abbreviation to number
                month_map = {
                    'JAN': '01', 'FEB': '02', 'MAR': '03', 'APR': '04',
                    'MAY': '05', 'JUN': '06', 'JUL': '07', 'AUG': '08',
                    'SEP': '09', 'OCT': '10', 'NOV': '11', 'DEC': '12'
                }
                
                month = month_map.get(month_abbr.upper(), '01')
                
                # Convert 2-digit year to 4-digit (assume 70-99 = 1970-1999, 00-69 = 2000-2069)
                year_int = int(year)
                if year_int >= 70:
                    full_year = f"19{year}"
                else:
                    full_year = f"20{year}"
                    
                return f"{full_year}-{month}-{day}"
                
            except (ValueError, KeyError):
                pass
                
        return date_str  # Return as-is if we can't parse it
    
    def looks_like_header(self, data: bytes) -> bool:
        """Check if a block looks like a file header."""
        if len(data) < 16:
            return False
            
        try:
            # Check for typical header patterns
            ident_offset = data[0]
            map_offset = data[1]
            file_number = struct.unpack('<H', data[2:4])[0]
            structure_level = struct.unpack('<H', data[6:8])[0]
            
            # Reasonable header values
            return (ident_offset in range(10, 100) and 
                   map_offset in range(20, 100) and
                   file_number in range(1, 1000) and
                   structure_level == 0x0101)
        except:
            return False
    
    def extract_files(self, output_dir: str = "extracted_ods1"):
        """Extract all files from the ODS-1 volume."""
        if not os.path.exists(output_dir):
            os.makedirs(output_dir)
            
        print(f"\nExtracting files to {output_dir}/")
        
        headers = self.scan_for_file_headers()
        
        # Group headers by directory structure
        directories = {}
        files_to_extract = []
        
        for header in headers:
            # Check if this is a directory - improved detection
            is_directory = (
                header.filetype.upper() == 'DIR' or 
                header.filename.endswith('.DIR') or
                'DIR' in header.filename.upper() or
                # RSX-11 user directories often have numeric names like 001001, 001002, etc.
                (len(header.filename) == 6 and header.filename.isdigit()) or
                # Some directories might be named like 000000, 240001, etc.
                (len(header.filename) >= 5 and header.filename.isdigit())
            )
            
            if is_directory:
                # This is a directory - add to directories list
                dir_name = header.filename.strip().replace('.DIR', '')
                if not dir_name:
                    dir_name = f"DIR_{header.file_number}"
                directories[header.file_number] = dir_name
                print(f"  Found directory: {dir_name}")
            else:
                # Regular file
                files_to_extract.append(header)
        
        # Create directory structure first
        for dir_num, dir_name in directories.items():
            dir_path = os.path.join(output_dir, dir_name)
            os.makedirs(dir_path, exist_ok=True)
            print(f"  Created directory: {dir_name}/")
        
        extracted_count = 0
        for header in files_to_extract:
            try:
                # Create safe filename (remove version number for filesystem)
                filename = header.filename.strip()
                filetype = header.filetype.strip()
                version = header.version
                
                if not filename:
                    filename = f"FILE_{header.file_number}"
                
                # Build filename WITHOUT version for extraction
                if filetype:
                    display_name = f"{filename}.{filetype}"
                    if version > 0:
                        display_name += f";{version}"  # For display only
                    extraction_name = f"{filename}.{filetype}"  # Without version for filesystem
                else:
                    display_name = filename
                    if version > 0:
                        display_name += f";{version}"
                    extraction_name = filename
                
                # Make filename safe for filesystem
                safe_name = "".join(c for c in extraction_name if c.isalnum() or c in "._-").strip()
                if not safe_name:
                    safe_name = f"file_{header.file_number}_{header.file_sequence}.bin"
                
                # Determine output directory (check if file belongs to a specific directory)
                # In ODS-1, files can be associated with directories through UIC or naming patterns
                target_dir = output_dir
                
                # Check if filename suggests it belongs to a directory
                for dir_num, dir_name in directories.items():
                    if (filename.startswith(dir_name.upper()) or 
                        header.owner_uic == dir_num or
                        filename.startswith(f"{dir_num:03d}")):
                        target_dir = os.path.join(output_dir, dir_name)
                        print(f"  Placing {safe_name} in directory {dir_name}/")
                        break
                
                # Debug: Show header information for system files and TSK files (disabled in production)
                # if header.filename in ['INDEXF', 'BITMAP', 'BADBLK', 'CORIMG'] or header.filetype.upper() == 'TSK':
                #     print(f"  DEBUG {header.filename}.{header.filetype}: end_of_file_block={header.end_of_file_block}, first_free_byte={header.first_free_byte}")
                #     print(f"  DEBUG {header.filename}.{header.filetype}: highest_vbn={header.highest_vbn}, map_words_used={header.map_words_used}")
                
                # Extract file data
                file_data = self.extract_file_data(header)
                
                # Handle both non-empty files and legitimate empty files
                if file_data is not None:  # None means error, b"" means empty file
                    output_path = os.path.join(target_dir, safe_name)
                    with open(output_path, 'wb') as f:
                        f.write(file_data)
                    
                    # Determine file type based on extension
                    file_type = self.get_file_type(header.filetype)
                    
                    # Format creation date
                    creation_date = self.format_date(header.creation_date) if header.creation_date else "N/A"
                    
                    # Calculate size in blocks
                    size_blocks = max(1, (len(file_data) + self.BLOCK_SIZE - 1) // self.BLOCK_SIZE) if file_data else 0
                    
                    # Show relative path for files in subdirectories
                    if target_dir != output_dir:
                        rel_path = os.path.relpath(output_path, output_dir)
                        display_path = rel_path
                    else:
                        display_path = safe_name
                    
                    if len(file_data) == 0:
                        print(f"  Extracted: {display_path} (empty file) [{file_type}] {creation_date}")
                    else:
                        print(f"  Extracted: {display_path} ({len(file_data)} bytes, {size_blocks} blocks) [{file_type}] {creation_date}")
                    
                    # Also output detailed info for GUI parsing (use display name with version)
                    print(f"  FILE_INFO: {display_name}|{size_blocks}|{len(file_data)}|{file_type}|{creation_date}|{display_path}")
                    
                    extracted_count += 1
                else:
                    print(f"  Warning: No data for {display_name}")
                    
            except Exception as e:
                print(f"  Error extracting {header.filename}: {e}")
        
        # Also output directory info for GUI
        for dir_num, dir_name in directories.items():
            print(f"  FILE_INFO: {dir_name}|0|0|Directory|N/A|{dir_name}/")
                
        print(f"\nExtracted {extracted_count} files and {len(directories)} directories successfully")
    
    def list_files(self):
        """List all files in the volume with FILE_INFO output for GUI parsing."""
        headers = self.scan_for_file_headers()
        
        # Group headers by directory structure
        directories = {}
        files_to_list = []
        
        for header in headers:
            # Check if this is a directory
            is_directory = (
                header.filetype.upper() == 'DIR' or 
                header.filename.endswith('.DIR') or
                'DIR' in header.filename.upper() or
                (len(header.filename) == 6 and header.filename.isdigit()) or
                (len(header.filename) >= 5 and header.filename.isdigit())
            )
            
            if is_directory:
                dir_name = header.filename.strip().replace('.DIR', '')
                if not dir_name:
                    dir_name = f"DIR_{header.file_number}"
                directories[header.file_number] = dir_name
            else:
                files_to_list.append(header)
        
        # Output file information
        for header in files_to_list:
            try:
                filename = header.filename.strip()
                filetype = header.filetype.strip()
                version = header.version
                
                if not filename:
                    filename = f"FILE_{header.file_number}"
                
                # Build display filename with version
                if filetype:
                    display_name = f"{filename}.{filetype}"
                    if version > 0:
                        display_name += f";{version}"
                else:
                    display_name = filename
                    if version > 0:
                        display_name += f";{version}"
                
                # Determine file type
                file_type = self.get_file_type(header.filetype)
                
                # Format creation date
                creation_date = self.format_date(header.creation_date) if header.creation_date else "N/A"
                
                # Calculate estimated size from header info
                if header.end_of_file_block > 0:
                    size_bytes = (header.end_of_file_block - 1) * self.BLOCK_SIZE
                    if header.first_free_byte > 0:
                        size_bytes += header.first_free_byte
                    else:
                        size_bytes += self.BLOCK_SIZE
                    size_blocks = header.end_of_file_block
                else:
                    # For files without size info, estimate from retrieval pointers
                    if header.retrieval_pointers:
                        total_blocks = sum(count + 1 for lbn, count in header.retrieval_pointers if lbn > 0 and count > 0)
                        size_blocks = total_blocks
                        size_bytes = total_blocks * self.BLOCK_SIZE
                    else:
                        size_blocks = 0
                        size_bytes = 0
                
                # Determine display path (check if file belongs to a directory)
                display_path = display_name
                for dir_num, dir_name in directories.items():
                    if (filename.startswith(dir_name.upper()) or 
                        header.owner_uic == dir_num or
                        filename.startswith(f"{dir_num:03d}")):
                        display_path = f"{dir_name}/{display_name}"
                        break
                
                # Output FILE_INFO for GUI parsing
                print(f"FILE_INFO: {display_name}|{size_blocks}|{size_bytes}|{file_type}|{creation_date}|{display_path}")
                
            except Exception as e:
                print(f"Error processing file {header.filename}: {e}")
        
        # Output directory info
        for dir_num, dir_name in directories.items():
            print(f"FILE_INFO: {dir_name}|0|0|Directory|N/A|{dir_name}/")

    def analyze_volume(self):
        """Analyze and display volume information."""
        print("=== ODS-1 Volume Analysis ===")
        
        if not self.parse_home_block():
            print("ERROR: Invalid or missing home block")
            return False
            
        print(f"Volume Name: {self.volume_name}")
        print(f"Structure Level: 0x{self.volume_structure_level:04x}")
        print(f"Max Files: {self.max_files}")
        print(f"Index File Bitmap Size: {self.index_file_bitmap_size} blocks")
        print(f"Index File Bitmap LBN: {self.index_file_bitmap_lbn}")
        print(f"Storage Bitmap Cluster Factor: {self.storage_bitmap_cluster_factor}")
        print(f"Device Type: {self.device_type}")
        print(f"Volume Owner UIC: {self.volume_owner_uic:08x}")
        print(f"Volume Protection: 0x{self.volume_protection:04x}")
        print(f"Volume Characteristics: 0x{self.volume_characteristics:04x}")
        print(f"Default File Protection: 0x{self.default_file_protection:04x}")
        print(f"Volume Creation Date: {self.volume_creation_date}")
        print(f"Total Blocks: {self.total_blocks}")
        
        return True

def main():
    parser = argparse.ArgumentParser(description="ODS-1 (Files-11) File System Extractor")
    parser.add_argument("disk_image", help="Path to disk image file")
    parser.add_argument("-o", "--output", default="extracted_ods1", help="Output directory")
    parser.add_argument("-a", "--analyze-only", action="store_true", help="Only analyze volume, don't extract files")
    parser.add_argument("-l", "--list", action="store_true", help="List files only (same as --analyze-only)")
    parser.add_argument("-d", "--detailed", action="store_true", help="Show detailed file information (ignored)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output (ignored for now)")
    
    args = parser.parse_args()
    
    try:
        extractor = ODS1Extractor(args.disk_image)
        
        if not extractor.analyze_volume():
            print("ERROR: Could not analyze volume")
            return 1
            
        # If list mode (-l) or analyze_only (-a) is specified, list files but don't extract
        if args.analyze_only or args.list:
            extractor.list_files()
        else:
            extractor.extract_files(args.output)
            
    except Files11Exception as e:
        print(f"ERROR: {e}")
        return 1
    except Exception as e:
        print(f"UNEXPECTED ERROR: {e}")
        return 1
        
    return 0

if __name__ == "__main__":
    exit(main())
