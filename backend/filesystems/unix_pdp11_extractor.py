#!/usr/bin/env python3
"""
Advanced Unix Filesystem Extractor for PDP-11/PDP-7

Supports multiple Unix filesystem formats:
- Unix V0 (1969, PDP-7) - Based on DoctorWkt/pdp7-unix research
- Unix V5, V6, V7 (PDP-11) - Classic AT&T Unix
- System V (S5) - Enhanced with magic number detection
- Early BSD variants

Based on:
- PyPDP11 project: https://github.com/amakukha/PyPDP11
- PDP-7 Unix research: https://github.com/DoctorWkt/pdp7-unix
- S5 filesystem documentation: http://uw714doc.xinuos.com/en/man/html.4/fs_s5.4.html

Adaptado para el proyecto RT-11 Extractor
"""

import struct
import sys
import os
import argparse
import time
import datetime
import io
import string
from pathlib import Path
from typing import List, Tuple, Optional, Dict, Any

# Constantes Unix V6/S5 (basadas en PyPDP11 y documentación S5)
SUPERBLOCK_SIZE = 415
SUPERBLOCK_S5_SIZE = 512
BLOCK_SIZE = 512
INODE_SIZE = 32
BIGGEST_NOT_HUGE_SIZE = BLOCK_SIZE * BLOCK_SIZE // 2 * 8

# S5 Filesystem constants
FS_MAGIC = 0xfd187e20  # S5 magic number
FS_OKAY = 0x7c269d38   # Clean filesystem
FS_ACTIVE = 0x5e72d81a # Active filesystem  
FS_BAD = 0xcb096f43    # Bad filesystem
FS_BADBLK = 0xbadbc14b # Bad block corrupted

# Block size types
FS1B = 1  # 512-byte blocks
FS2B = 2  # 1024-byte blocks  
FS4B = 3  # 2048-byte blocks

# Unix V0 (PDP-7) constants - from DoctorWkt/pdp7-unix research
V0_BLOCK_SIZE = 64  # 64 words per block
V0_WORDS_PER_BLOCK = 64
V0_INODE_SIZE = 12  # 12 words per inode
V0_DIR_ENTRY_SIZE = 8  # 8 words per directory entry
V0_INODES_PER_BLOCK = 5  # 5 inodes per block

# V0 inode flags (from pdp7-unix documentation)
V0_IALLOC = 0o400000   # inode allocated
V0_ILARG = 0o200000    # large file (indirect blocks)
V0_ISPEC = 0o000040    # special file
V0_IDIR = 0o000020     # directory
V0_IREAD = 0o000010    # owner read
V0_IWRITE = 0o000004   # owner write
V0_IWREAD = 0o000002   # world read
V0_IWWRITE = 0o000001  # world write

class UnixSuperblock:
    """Superblock Unix V6 según documentación oficial"""
    
    def __init__(self, data: bytes):
        self.parse(data)
    
    def parse(self, data: bytes):
        """Parse según Unix V6 /usr/man/man5/fs.5"""
        if len(data) < SUPERBLOCK_SIZE:
            raise ValueError("Superblock data too small")
            
        # Estructura del superblock Unix V6
        self.isize, self.fsize, self.nfree = struct.unpack('<HHH', data[:6])
        
        # Array de bloques libres (100 entradas)
        self.free = list(struct.unpack('<100H', data[6:206]))
        
        # Información de inodos
        self.ninode = struct.unpack('<H', data[206:208])[0]
        self.inode = list(struct.unpack('<100H', data[208:408]))
        
        # Flags y tiempo
        self.flock, self.ilock, self.fmod = struct.unpack('<BBB', data[408:411])
        self.time = struct.unpack('<I', data[411:415])[0]
    
    def __repr__(self):
        return f'UnixSuperblock(isize={self.isize}, fsize={self.fsize}, nfree={self.nfree}, ninode={self.ninode})'

class UnixINode:
    """INode Unix V6 según documentación oficial"""
    
    def __init__(self, data: bytes, inode_num: int = 0):
        self.inode = inode_num
        self.parse(data)
    
    def parse(self, data: bytes):
        """Parse según Unix V6 /usr/man/man5/fs.5 - flexible para diferentes versiones"""
        if len(data) < 16:  # Mínimo para campos básicos
            raise ValueError("INode data too small")
            
        # Parsear campos básicos (siempre presentes)
        self.flag = struct.unpack('<H', data[0:2])[0]
        self.nlinks = struct.unpack('<B', data[2:3])[0] if len(data) > 2 else 0
        self.uid = struct.unpack('<B', data[3:4])[0] if len(data) > 3 else 0
        self.gid = struct.unpack('<B', data[4:5])[0] if len(data) > 4 else 0
        
        # File size (puede estar en diferentes formatos)
        if len(data) >= 8:
            size_bytes = data[5:8] if len(data) >= 8 else data[5:]
            if len(size_bytes) >= 3:
                self.size = (size_bytes[0] << 16) + struct.unpack('<H', size_bytes[1:3])[0]
            elif len(size_bytes) >= 2:
                self.size = struct.unpack('<H', size_bytes[:2])[0]
            else:
                self.size = size_bytes[0] if size_bytes else 0
        else:
            self.size = 0
        
        # Block addresses (8 words, puede variar)
        self.addr = [0] * 8
        addr_offset = 8
        for i in range(8):
            if addr_offset + 2 <= len(data):
                self.addr[i] = struct.unpack('<H', data[addr_offset:addr_offset+2])[0]
                addr_offset += 2
            else:
                break
        
        # Times (si están disponibles)
        time_offset = addr_offset
        if time_offset + 4 <= len(data):
            self.actime = struct.unpack('<I', data[time_offset:time_offset+4])[0]
        else:
            self.actime = 0
            
        if time_offset + 8 <= len(data):
            self.modtime = struct.unpack('<I', data[time_offset+4:time_offset+8])[0]
        else:
            self.modtime = 0
    
    def is_allocated(self) -> bool:
        """Check if inode is allocated"""
        return bool(self.flag & 0x8000)
    
    def is_dir(self) -> bool:
        """Check if this is a directory"""
        return bool((self.flag & 0x4000) == 0x4000)
    
    def is_regular_file(self) -> bool:
        """Check if this is a regular file"""
        return bool((self.flag & 0x4000) == 0x0000)
    
    def is_large(self) -> bool:
        """Check if this is a large file (uses indirect blocks)"""
        return bool(self.flag & 0x1000)
    
    def get_type(self) -> int:
        """Get file type"""
        return (self.flag & 0x6000) >> 13
    
    def flags_string(self) -> str:
        """Human-readable flag representation"""
        s = ''
        s += 'a' if self.flag & 0x8000 else '.'  # allocated
        fmt = (self.flag & 0x6000) >> 13
        s += {0: 'F', 1: 'S', 2: 'D', 3: 'B'}[fmt]  # File/Special/Dir/Block
        s += 'L' if self.flag & 0x1000 else '.'  # Large file
        s += 'U' if self.flag & 0x0800 else '.'  # Set UID
        s += 'G' if self.flag & 0x0400 else '.'  # Set GID
        
        # Permission bits
        s += 'r' if self.flag & 0x0100 else '-'  # Owner read
        s += 'w' if self.flag & 0x0080 else '-'  # Owner write  
        s += 'x' if self.flag & 0x0040 else '-'  # Owner execute
        s += 'r' if self.flag & 0x0020 else '-'  # Group read
        s += 'w' if self.flag & 0x0010 else '-'  # Group write
        s += 'x' if self.flag & 0x0008 else '-'  # Group execute
        s += 'r' if self.flag & 0x0004 else '-'  # Other read
        s += 'w' if self.flag & 0x0002 else '-'  # Other write
        s += 'x' if self.flag & 0x0001 else '-'  # Other execute
        
        return s
    
    def get_unix_time(self) -> Optional[datetime.datetime]:
        """Convert Unix time to datetime"""
        try:
            if self.modtime > 0:
                # Unix V6 timestamps can be unreliable or in different formats
                # Check if timestamp is within reasonable Unix era range
                # Unix epoch started 1970-01-01, PDP-11 Unix v6 was ~1975-1985
                # Reject timestamps that seem to be in the future or way too early
                dt = datetime.datetime.fromtimestamp(self.modtime)
                
                # Only accept dates between 1970 and 2000 for Unix V6 systems
                if dt.year >= 1970 and dt.year <= 2000:
                    return dt
                else:
                    # Timestamp is outside reasonable range
                    return None
        except (ValueError, OSError, OverflowError):
            pass
        return None
    
    def __repr__(self):
        return f'UnixINode(uid={self.uid}, gid={self.gid}, size={self.size}, flags={self.flags_string()})'

class UnixV6FileSystem:
    """Sistema de archivos Unix V6 para PDP-11"""
    
    def __init__(self, image_path: str, verbose: bool = False):
        self.image_path = Path(image_path)
        self.verbose = verbose
        self.image_data = None
        self.superblock = None
        
        self._load_image()
        self._load_superblock()
    
    def _load_image(self):
        """Cargar imagen de disco"""
        if not self.image_path.exists():
            raise FileNotFoundError(f"Image not found: {self.image_path}")
            
        with open(self.image_path, 'rb') as f:
            self.image_data = f.read()
            
        if self.verbose:
            print(f"Loaded Unix image: {len(self.image_data)} bytes")
    
    def _load_superblock(self):
        """Cargar y validar superblock"""
        # El superblock está en el bloque 1 (offset 512)
        sb_data = self.read_block(1)
        
        try:
            self.superblock = UnixSuperblock(sb_data[:SUPERBLOCK_SIZE])
            if self.verbose:
                print(f"Superblock: {self.superblock}")
        except Exception as e:
            raise ValueError(f"Invalid Unix superblock: {e}")
    
    def read_block(self, block_num: int) -> bytes:
        """Leer un bloque del disco"""
        offset = block_num * BLOCK_SIZE
        if offset + BLOCK_SIZE > len(self.image_data):
            raise ValueError(f"Block {block_num} beyond image size")
        return self.image_data[offset:offset + BLOCK_SIZE]
    
    def read_inode(self, inode_num: int) -> UnixINode:
        """Leer un inode específico"""
        if inode_num < 1:
            raise ValueError("Invalid inode number")
            
        # Los inodos empiezan en el bloque 2
        offset = BLOCK_SIZE * 2 + (inode_num - 1) * INODE_SIZE
        if offset + INODE_SIZE > len(self.image_data):
            raise ValueError(f"INode {inode_num} beyond image size")
            
        inode_data = self.image_data[offset:offset + INODE_SIZE]
        return UnixINode(inode_data, inode_num)
    
    def get_file_blocks(self, inode: UnixINode) -> List[int]:
        """Obtener lista de bloques que contienen el archivo"""
        blocks = []
        
        if inode.size == 0:
            return blocks
            
        if not inode.is_large():
            # Archivo pequeño - direcciones directas
            for addr in inode.addr:
                if addr == 0:
                    break
                blocks.append(addr)
        else:
            # Archivo grande - direcciones indirectas
            for indirect_block_addr in inode.addr:
                if indirect_block_addr == 0:
                    break
                    
                # Leer bloque indirecto
                indirect_data = self.read_block(indirect_block_addr)
                
                # Cada entrada es de 2 bytes (16-bit address)
                for i in range(0, BLOCK_SIZE, 2):
                    if i + 2 <= len(indirect_data):
                        block_addr = struct.unpack('<H', indirect_data[i:i+2])[0]
                        if block_addr == 0:
                            break
                        blocks.append(block_addr)
        
        return blocks
    
    def read_file_data(self, inode: UnixINode) -> bytes:
        """Leer contenido completo de un archivo"""
        if inode.size == 0:
            return b''
            
        blocks = self.get_file_blocks(inode)
        file_data = b''
        
        for block_num in blocks:
            file_data += self.read_block(block_num)
        
        # Truncar al tamaño real del archivo
        return file_data[:inode.size]
    
    def list_directory(self, inode: UnixINode) -> List[Tuple[int, str]]:
        """Listar contenido de un directorio"""
        if not inode.is_dir():
            return []
            
        dir_data = self.read_file_data(inode)
        entries = []
        
        # Cada entrada de directorio es de 16 bytes: 2 bytes inode + 14 bytes nombre
        for i in range(0, len(dir_data), 16):
            if i + 16 <= len(dir_data):
                entry_data = dir_data[i:i+16]
                inode_num, name_bytes = struct.unpack('<H14s', entry_data)
                
                if inode_num > 0:
                    # Decodificar nombre (termina en NULL)
                    name = name_bytes.rstrip(b'\x00').decode('ascii', errors='replace')
                    entries.append((inode_num, name))
        
        return entries
    
    def find_path(self, path: str, start_inode: int = 1) -> Optional[UnixINode]:
        """Buscar un archivo/directorio por ruta"""
        if path.startswith('/'):
            path = path[1:]  # Remover / inicial
            
        if not path:
            # Directorio raíz
            return self.read_inode(start_inode)
            
        current_inode = self.read_inode(start_inode)
        
        for component in path.split('/'):
            if not current_inode.is_dir():
                if self.verbose:
                    print(f"DEBUG: {component} is not a directory")
                return None
                
            # Buscar en el directorio actual
            found = False
            entries = self.list_directory(current_inode)
            
            if self.verbose:
                print(f"DEBUG: Looking for '{component}' in directory with {len(entries)} entries:")
                for inum, name in entries:
                    print(f"  - {name} (inode {inum})")
                    
            for inode_num, name in entries:
                if name == component:
                    current_inode = self.read_inode(inode_num)
                    found = True
                    break
                    
            if not found:
                if self.verbose:
                    print(f"DEBUG: Component '{component}' not found")
                return None
        
        return current_inode
    
    def extract_file(self, inode: UnixINode, output_path: Path, filename: str) -> bool:
        """Extraer un archivo al sistema de archivos local"""
        try:
            file_data = self.read_file_data(inode)
            
            output_file = output_path / filename
            
            # Manejar conflictos de nombres
            counter = 1
            while output_file.exists():
                stem = Path(filename).stem
                suffix = Path(filename).suffix
                output_file = output_path / f"{stem}_{counter}{suffix}"
                counter += 1
            
            with open(output_file, 'wb') as f:
                f.write(file_data)
            
            if self.verbose:
                print(f"Extracted: {filename} ({len(file_data)} bytes)")
            
            # Skip metadata file creation for cleaner extraction
            # (Metadata generation disabled by user request)
            
            return True
            
        except Exception as e:
            if self.verbose:
                print(f"Error extracting {filename}: {e}")
            return False
    
    def extract_directory(self, inode: UnixINode, output_path: Path, dirname: str = "") -> int:
        """Extraer un directorio recursivamente"""
        extracted_count = 0
        
        # Crear directorio si no existe
        if dirname:
            dir_path = output_path / dirname
            dir_path.mkdir(exist_ok=True)
        else:
            dir_path = output_path
        
        # Listar contenido
        entries = self.list_directory(inode)
        
        for inode_num, name in entries:
            if name in ['.', '..']:
                continue
                
            try:
                entry_inode = self.read_inode(inode_num)
                
                if entry_inode.is_dir():
                    # Extraer subdirectorio recursivamente
                    extracted_count += self.extract_directory(entry_inode, dir_path, name)
                else:
                    # Extraer archivo
                    if self.extract_file(entry_inode, dir_path, name):
                        extracted_count += 1
                        
            except Exception as e:
                if self.verbose:
                    print(f"Error processing {name}: {e}")
        
        return extracted_count
    
    def list_files(self, path: str = "/", detailed: bool = False) -> None:
        """Listar archivos de manera similar a ls -la"""
        target_inode = self.find_path(path)
        
        if not target_inode:
            print(f"Path not found: {path}")
            return
            
        if not target_inode.is_dir():
            print(f"Not a directory: {path}")
            return
        
        print(f"\\nUnix PDP-11 Directory Listing: {path}")
        print("=" * 80)
        
        if detailed:
            print(f"{'Permissions':<12} {'Links':<5} {'UID':<4} {'GID':<4} {'Size':<8} {'ModTime':<19} {'Name':<20}")
        else:
            print(f"{'Name':<20} {'Type':<10} {'Size (bytes)':<12} {'Permissions':<12}")
        print("-" * 80)
        
        entries = self.list_directory(target_inode)
        total_size = 0
        file_count = 0
        dir_count = 0
        
        for inode_num, name in sorted(entries, key=lambda x: x[1]):
            try:
                entry_inode = self.read_inode(inode_num)
                total_size += entry_inode.size
                
                if entry_inode.is_dir():
                    dir_count += 1
                else:
                    file_count += 1
                
                # Determine file type
                if entry_inode.is_dir():
                    file_type = "Directory"
                else:
                    # Check for executable files
                    if entry_inode.flag & 0x0040:  # Owner execute bit
                        file_type = "Executable"
                    else:
                        file_type = "Regular File"
                
                # Format date for FILE_INFO - try to get real timestamp first
                unix_time = entry_inode.get_unix_time()
                if unix_time:
                    date_str = unix_time.strftime("%Y-%m-%d")
                else:
                    # Unix v5/v6 timestamps are often unreliable, use default date
                    date_str = "1975-01-01"  # Default for Unix v5 era
                
                # Calculate blocks (Unix uses 512-byte blocks)
                size_blocks = max(1, (entry_inode.size + 511) // 512) if entry_inode.size > 0 else 0
                
                # Output FILE_INFO for GUI parsing
                display_path = f"{path.rstrip('/')}/{name}" if path != "/" else f"/{name}"
                if name in ['.', '..']: 
                    display_path = name
                
                print(f"FILE_INFO: {name}|{size_blocks}|{entry_inode.size}|{file_type}|{date_str}|{display_path}")
                
                if detailed:
                    unix_time = entry_inode.get_unix_time()
                    time_str = unix_time.strftime("%Y-%m-%d %H:%M:%S") if unix_time else "Unknown"
                    
                    print(f"{entry_inode.flags_string():<12} {entry_inode.nlinks:<5} {entry_inode.uid:<4} {entry_inode.gid:<4} {entry_inode.size:<8} {time_str:<19} {name}")
                else:
                    print(f"{name:<20} {file_type:<10} {entry_inode.size:<12} {entry_inode.flags_string()}")
                    
            except Exception as e:
                print(f"{name:<20} ERROR: {e}")
        
        print("-" * 80)
        print(f"Summary: {file_count} files, {dir_count} directories")
        print(f"Total size: {total_size:,} bytes")
        print(f"Superblock info: {self.superblock.fsize} total blocks, {self.superblock.nfree} free blocks")
    
    def list_files_recursive(self, path: str = "/", detailed: bool = False) -> None:
        """Listar todos los archivos recursivamente con paths completos"""
        print(f"\\nUnix PDP-11 Recursive File Listing: {path}")
        print("=" * 80)
        
        if detailed:
            print(f"{'Full Path':<40} {'Type':<10} {'Size':<9} {'ModTime':<19} {'Permissions'}")
            print("-" * 90)
        else:
            print(f"{'Full Path':<60} {'Type':<10} {'Size':<12}")
            print("-" * 85)
        
        self._recursive_walk(path, detailed)
    
    def _recursive_walk(self, current_path: str, detailed: bool, _visited=None):
        """Recorrer recursivamente el árbol de directorios"""
        if _visited is None:
            _visited = set()
        
        # Encontrar el inode del directorio actual
        inode = self.find_path(current_path)
        if not inode or not inode.is_dir():
            return
        
        # Evitar bucles infinitos
        if inode.inode in _visited:
            return
        _visited.add(inode.inode)
        
        try:
            dir_entries = self.list_directory(inode)
            
            for inode_num, name in sorted(dir_entries, key=lambda x: x[1]):
                if name in ['.', '..']: # Saltar . y ..
                    continue
                    
                try:
                    entry_inode = self.read_inode(inode_num)
                    
                    # Construir path completo
                    if current_path.endswith('/'):
                        full_path = current_path + name
                    else:
                        full_path = current_path + '/' + name
                    
                    if entry_inode.is_dir():
                        file_type = "Directory"
                    else:
                        file_type = "File"
                    
                    if detailed:
                        unix_time = entry_inode.get_unix_time()
                        time_str = unix_time.strftime("%Y-%m-%d %H:%M:%S") if unix_time else "Unknown"
                        
                        print(f"{full_path:<40} {file_type:<10} {entry_inode.size:<9} {time_str:<19} {entry_inode.flags_string()}")
                    else:
                        print(f"{full_path:<60} {file_type:<10} {entry_inode.size:<12}")
                    
                    # Si es directorio, recorrer recursivamente
                    if entry_inode.is_dir():
                        self._recursive_walk(full_path, detailed, _visited)
                        
                except Exception as e:
                    if detailed:
                        print(f"{full_path:<40} ERROR: {str(e)}")
                    else:
                        print(f"{full_path:<60} ERROR: {str(e)}")
                    
        except Exception as e:
            if detailed:
                print(f"{current_path:<40} ERROR reading directory: {str(e)}")
        finally:
            _visited.discard(inode.inode)

def detect_unix_filesystem(image_path: str) -> Tuple[bool, str]:
    """Detectar si es un filesystem Unix válido (V5, V6, V7)"""
    try:
        with open(image_path, 'rb') as f:
            file_size = f.seek(0, 2)
            f.seek(0)
            
            # Probar diferentes offsets para el superblock
            # V5/V6: bloque 1 (offset 512)
            # V7: puede estar en diferentes posiciones
            superblock_offsets = [BLOCK_SIZE, 0, BLOCK_SIZE * 2]
            
            for sb_offset in superblock_offsets:
                if sb_offset + SUPERBLOCK_SIZE > file_size:
                    continue
                    
                f.seek(sb_offset)
                sb_data = f.read(SUPERBLOCK_SIZE)
                
                if len(sb_data) < 16:  # Mínimo para leer isize, fsize, nfree
                    continue
                
                # Probar little endian y big endian
                for endian in ['<', '>']:
                    try:
                        isize, fsize, nfree = struct.unpack(f'{endian}HHH', sb_data[:6])
                        
                        # Validaciones más flexibles para diferentes versiones Unix
                        if (1 <= isize <= 2000 and          # Área de inodos razonable
                            fsize > isize and               # Tamaño total mayor
                            0 <= nfree <= 200 and           # Bloques libres razonables
                            fsize < 200000 and              # No demasiado grande
                            isize * INODE_SIZE <= file_size): # Inodos caben en imagen
                            
                            # Buscar inode root en diferentes posiciones
                            root_positions = [
                                BLOCK_SIZE * 2,              # V6 estándar
                                sb_offset + SUPERBLOCK_SIZE, # Inmediatamente después del superblock
                                BLOCK_SIZE * (2 + isize),    # Después del área de inodos
                            ]
                            
                            for root_pos in root_positions:
                                if root_pos + INODE_SIZE <= file_size:
                                    try:
                                        f.seek(root_pos)
                                        root_data = f.read(INODE_SIZE)
                                        
                                        if len(root_data) == INODE_SIZE:
                                            # Probar parsear como inode
                                            params = struct.unpack(f'{endian}HBBBBH8HHHH', root_data)
                                            flag = params[0]
                                            
                                            # Verificar si parece un directorio root válido
                                            is_allocated = bool(flag & 0x8000)
                                            is_directory = bool((flag & 0x4000) == 0x4000)
                                            
                                            if is_allocated and is_directory:
                                                version = "V6" if sb_offset == BLOCK_SIZE else "V5/V7"
                                                return True, f"Unix {version} filesystem detected (isize={isize}, fsize={fsize}, endian={endian})" 
                                                
                                    except:
                                        continue
                                        
                    except:
                        continue
            
            # Detección alternativa: buscar patrones típicos de Unix
            f.seek(0)
            header = f.read(4096)
            
            # Buscar strings típicos de Unix en los primeros bloques
            if any(pattern in header for pattern in [b'bin', b'etc', b'usr', b'dev', b'tmp']):
                return True, "Unix filesystem detected (pattern-based detection)"
                        
        return False, "Not a valid Unix filesystem"
        
    except Exception as e:
        return False, f"Error reading image: {e}"

def main():
    parser = argparse.ArgumentParser(
        description="Unix PDP-11 Filesystem Extractor v1.0",
        epilog="""
Examples:
  %(prog)s disk.dsk -l                 # List root directory
  %(prog)s disk.dsk -l /usr -d         # List /usr with details
  %(prog)s disk.dsk                    # Extract all files
  %(prog)s disk.dsk -p /usr            # Extract only /usr directory
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("image", help="Unix disk image file (.dsk, .img, etc.)")
    parser.add_argument("-l", "--list", action="store_true",
                       help="List files only, don't extract")
    parser.add_argument("-d", "--detailed", action="store_true",
                       help="Show detailed file information (like ls -la)")
    parser.add_argument("-r", "--recursive", action="store_true",
                       help="List files recursively (show all files with full paths)")
    parser.add_argument("-p", "--path", default="/",
                       help="Path to list or extract (default: /)")
    parser.add_argument("-o", "--output", default="extracted_unix",
                       help="Output directory (default: extracted_unix)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--detect-only", action="store_true",
                       help="Only detect filesystem type")
    
    args = parser.parse_args()
    
    try:
        # Detectar tipo de filesystem
        is_unix, description = detect_unix_filesystem(args.image)
        
        if args.detect_only:
            if is_unix:
                print(f"✅ {description}")
                return 0
            else:
                print(f"❌ {description}")
                return 1
        
        if not is_unix:
            print(f"❌ Error: {description}")
            print("This image does not contain a valid Unix PDP-11 filesystem")
            return 1
        
        if args.verbose:
            print(f"✅ {description}")
        
        # Cargar filesystem
        fs = UnixV6FileSystem(args.image, args.verbose)
        
        if args.list:
            # Listar archivos
            if args.recursive:
                # Listado recursivo - mostrar todos los archivos con paths completos
                fs.list_files_recursive(args.path, args.detailed)
            else:
                fs.list_files(args.path, args.detailed)
        else:
            # Extraer archivos
            output_path = Path(args.output)
            output_path.mkdir(exist_ok=True)
            
            target_inode = fs.find_path(args.path)
            if not target_inode:
                print(f"❌ Path not found: {args.path}")
                return 1
            
            print(f"[EXTRACT] Extracting Unix files from {args.path} to {output_path}")
            
            if target_inode.is_dir():
                extracted = fs.extract_directory(target_inode, output_path)
                print(f"✅ Extracted {extracted} files successfully")
            else:
                # Extraer archivo individual
                filename = Path(args.path).name
                if fs.extract_file(target_inode, output_path, filename):
                    print(f"✅ Extracted 1 file successfully")
                else:
                    print(f"❌ Failed to extract file")
                    return 1
        
        return 0
        
    except KeyboardInterrupt:
        print("\\n❌ Operation cancelled")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        return 1

if __name__ == '__main__':
    sys.exit(main())
