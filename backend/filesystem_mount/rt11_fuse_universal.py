#!/usr/bin/env python3
"""
Universal PDP-11 FUSE Driver
============================

Driver FUSE universal para montar imágenes DSK de RT-11 y Unix PDP-11
como sistemas de archivos, preservando la estructura de directorios.

Soporta:
- RT-11 (archivo plano en la raíz)
- Unix V5/V6/V7 (estructura de directorios completa)

Uso:
    python3 rt11_fuse_universal.py <imagen.dsk> <punto_montaje>

Ejemplo:
    python3 rt11_fuse_universal.py disk.dsk /mnt/pdp11

Desmontaje:
    fusermount -u /mnt/pdp11  (Linux)
    umount /mnt/pdp11         (macOS)

Requisitos:
    pip install fusepy
"""

import os
import sys
import errno
import stat
import time
import logging
import subprocess
import tempfile
import json
from pathlib import Path
from typing import Dict, List, Optional, Union

# Importar FUSE - Try embedded version first, then system version
try:
    # First try to import from embedded fusepy
    script_dir = Path(__file__).parent.parent
    fusepy_embedded_path = script_dir / "fusepy_embedded"
    if fusepy_embedded_path.exists():
        import sys
        sys.path.insert(0, str(fusepy_embedded_path))
        print(f"DEBUG: Using embedded fusepy from {fusepy_embedded_path}")
    
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
    print("DEBUG: fusepy imported successfully")
except ImportError as e:
    print(f"Error: fusepy no está instalado. Details: {e}")
    print("Instálalo con: pip install fusepy")
    
    # Debug information about search paths
    print(f"DEBUG: Python path: {sys.path[:5]}...")
    script_dir = Path(__file__).parent.parent
    fusepy_embedded_path = script_dir / "fusepy_embedded"
    print(f"DEBUG: Looking for embedded fusepy at: {fusepy_embedded_path}")
    print(f"DEBUG: Embedded path exists: {fusepy_embedded_path.exists()}")
    if fusepy_embedded_path.exists():
        print(f"DEBUG: Contents: {list(fusepy_embedded_path.iterdir()) if fusepy_embedded_path.is_dir() else 'Not a directory'}")
    
    sys.exit(1)

class FileEntry:
    """Representación universal de un archivo (RT-11 o Unix)"""
    def __init__(self, path: str, size_bytes: int, is_dir: bool = False, 
                 mtime: float = None, mode: int = None):
        self.path = path.strip('/')  # Normalizar path
        self.size_bytes = size_bytes
        self.is_dir = is_dir
        self.mtime = mtime or time.time()
        self.mode = mode or (stat.S_IFDIR | 0o755 if is_dir else stat.S_IFREG | 0o644)
        
    @property
    def name(self):
        """Obtener solo el nombre del archivo"""
        return os.path.basename(self.path)
    
    @property
    def parent_path(self):
        """Obtener el directorio padre"""
        parent = os.path.dirname(self.path)
        return parent if parent != '' else '/'

class UniversalExtractorWrapper:
    """Wrapper universal para extraer archivos de RT-11 y Unix"""
    
    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.logger = logging.getLogger('UniversalExtractor')
        self._file_data_cache = {}  # Cache para datos de archivos
        self._extracted_dir = None  # Directorio de extracción persistente
        self.filesystem_type = "unknown"
        
        # Encontrar el extractor universal
        self.rt11extract_path = self._find_extractor()
        
        # Detectar tipo de filesystem
        self._detect_filesystem_type()
        
    def _find_extractor(self) -> Path:
        """Encontrar el extractor universal en diferentes ubicaciones"""
        script_dir = Path(__file__).parent
        
        # Use the same path resolution strategy that works in the GUI
        # Put direct paths FIRST to avoid broken symlinks
        possible_paths = [
            script_dir.parent / "extractors" / "rt11extract",  # Direct path to extractor (FIRST PRIORITY)
            script_dir.parent / "extractors" / "universal_extractor.py",  # Direct path to universal extractor
            script_dir / "rt11extract",           # Symlink to extractor (if exists)
            script_dir / "rt11extract_cli",       # Symlink to extractor (if exists)
            script_dir / "pdp11_smart_extractor.py",  # Symlink to universal_extractor.py (if exists)
            script_dir / "pdp11_smart_extractor_windows.py",  # Windows-compatible wrapper
        ]
        
        for path in possible_paths:
            if path.exists():
                self.logger.info(f"Found extractor at: {path}")
                return path
        
        # Si pdp11_smart_extractor.py no existe (problema con enlaces simbólicos en Windows),
        # intentar encontrar universal_extractor.py directamente
        universal_extractor_path = script_dir.parent / "extractors" / "universal_extractor.py"
        if universal_extractor_path.exists():
            self.logger.info(f"Found universal extractor at: {universal_extractor_path}")
            return universal_extractor_path
        
        # Buscar en PATH como último recurso
        import shutil
        system_extractor = shutil.which("rt11extract") or shutil.which("rt11extract_cli")
        if system_extractor:
            path = Path(system_extractor)
            self.logger.info(f"Found extractor in PATH: {path}")
            return path
        
        raise Exception(f"No extractor found. Tried: {[str(p) for p in possible_paths]} and {universal_extractor_path}")
    
    def _detect_filesystem_type(self):
        """Detectar el tipo de filesystem (RT-11 o Unix)"""
        try:
            # Ejecutar con flag de detección
            cmd = [str(self.rt11extract_path), str(self.image_path), "-l", "-v"]
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
            
            if result.returncode == 0:
                output = result.stdout.lower()
                if "unix" in output or "directory listing:" in output:
                    self.filesystem_type = "unix"
                    self.logger.info("Detected Unix filesystem")
                elif "rt-11" in output or ".sav" in output or ".bas" in output:
                    self.filesystem_type = "rt11"
                    self.logger.info("Detected RT-11 filesystem")
                else:
                    self.filesystem_type = "rt11"  # Default
                    self.logger.info("Unknown filesystem, defaulting to RT-11")
            else:
                self.filesystem_type = "rt11"  # Default
                self.logger.warning("Could not detect filesystem type, defaulting to RT-11")
                
        except Exception as e:
            self.logger.error(f"Error detecting filesystem: {e}")
            self.filesystem_type = "rt11"  # Default
    
    def list_files(self) -> List[FileEntry]:
        """Obtener lista de archivos extrayendo a directorio temporal persistente"""
        if self._extracted_dir and Path(self._extracted_dir).exists():
            # Usar directorio existente
            return self._scan_extracted_files(Path(self._extracted_dir))
        
        try:
            # Crear directorio temporal persistente
            self._extracted_dir = tempfile.mkdtemp(prefix="fuse_pdp11_")
            temp_path = Path(self._extracted_dir)
            
            self.logger.info(f"Extracting files to: {temp_path}")
            
            # Ejecutar extractor para extraer todos los archivos
            # Determine if we need to use python to run the script
            if self.rt11extract_path.suffix == '.py':
                cmd = ["python3", str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
            else:
                cmd = [str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
            
            self.logger.info(f"Running command: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=120)
            
            self.logger.info(f"Command exit code: {result.returncode}")
            if result.stdout:
                self.logger.info(f"Command stdout: {result.stdout[:500]}...")  # First 500 chars
            if result.stderr:
                self.logger.info(f"Command stderr: {result.stderr[:500]}...")  # First 500 chars
            
            if result.returncode != 0:
                self.logger.error(f"Extractor failed with exit code {result.returncode}")
                self.logger.error(f"Stderr: {result.stderr}")
                return []
            
            # Escanear archivos extraídos
            files = self._scan_extracted_files(temp_path)
            self.logger.info(f"Found {len(files)} files/directories")
            return files
            
        except subprocess.TimeoutExpired:
            self.logger.error("Extractor timeout")
            return []
        except Exception as e:
            self.logger.error(f"Error running extractor: {e}")
            return []
    
    def _scan_extracted_files(self, base_path: Path) -> List[FileEntry]:
        """Escanear archivos extraídos y crear estructura de directorios"""
        files = []
        
        # Agregar directorio raíz
        if self.filesystem_type == "unix":
            files.append(FileEntry("/", 0, is_dir=True))
        
        # Escanear recursivamente
        for item_path in base_path.rglob('*'):
            if item_path.name.endswith('.rt11info'):
                continue
                
            # Calcular path relativo
            rel_path = item_path.relative_to(base_path)
            virtual_path = str(rel_path).replace(os.sep, '/')
            
            # Para RT-11, todos los archivos van en la raíz
            if self.filesystem_type == "rt11":
                virtual_path = rel_path.name
            
            if item_path.is_file():
                size_bytes = item_path.stat().st_size
                mtime = item_path.stat().st_mtime
                
                entry = FileEntry(virtual_path, size_bytes, is_dir=False, mtime=mtime)
                files.append(entry)
                
                # Cache de datos del archivo
                self._file_data_cache[virtual_path] = item_path
                
            elif item_path.is_dir() and self.filesystem_type == "unix":
                # Solo crear directorios para Unix
                entry = FileEntry(virtual_path, 0, is_dir=True, 
                                mtime=item_path.stat().st_mtime)
                files.append(entry)
                
                # También cache el directorio
                self._file_data_cache[virtual_path] = item_path
        
        return files
    
    def get_file_data(self, path: str) -> Optional[bytes]:
        """Obtener datos de un archivo específico"""
        path = path.strip('/')
        
        if path in self._file_data_cache:
            cached_path = self._file_data_cache[path]
            if isinstance(cached_path, Path) and cached_path.is_file():
                try:
                    return cached_path.read_bytes()
                except Exception as e:
                    self.logger.error(f"Error reading cached file {path}: {e}")
        
        return None
    
    def cleanup(self):
        """Limpiar archivos temporales"""
        if self._extracted_dir and Path(self._extracted_dir).exists():
            import shutil
            try:
                shutil.rmtree(self._extracted_dir)
                self.logger.info(f"Cleaned up temporary directory: {self._extracted_dir}")
            except Exception as e:
                self.logger.error(f"Error cleaning up: {e}")

class UniversalFuseFS(LoggingMixIn, Operations):
    """Sistema de archivos FUSE universal para RT-11 y Unix"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.extractor = UniversalExtractorWrapper(image_path)
        self.files_cache = {}  # Cache de archivos por path
        self.dir_cache = {}    # Cache de directorios
        
        # Configurar logging
        logging.basicConfig(level=logging.INFO)
        self.logger = logging.getLogger('UniversalFUSE')
        
        self.refresh_file_list()
    
    def refresh_file_list(self):
        """Actualizar cache de archivos"""
        files = self.extractor.list_files()
        self.files_cache.clear()
        self.dir_cache.clear()
        
        # Crear cache por path
        for entry in files:
            path = '/' + entry.path if not entry.path.startswith('/') else entry.path
            if path == '//':
                path = '/'
            
            self.files_cache[path] = entry
            
            # Si es un directorio, agregarlo al cache de directorios
            if entry.is_dir:
                self.dir_cache[path] = []
            
            # Agregar al directorio padre
            parent_path = entry.parent_path
            if parent_path != '.':
                parent = '/' + parent_path if not parent_path.startswith('/') else parent_path
            else:
                parent = '/'
            
            if parent != path:  # Evitar bucles
                if parent not in self.dir_cache:
                    self.dir_cache[parent] = []
                
                # Agregar este archivo/directorio al listado del padre
                if entry.name not in self.dir_cache[parent]:
                    self.dir_cache[parent].append(entry.name)
        
        # Crear directorios padre que puedan faltar
        all_paths = set()
        for entry in files:
            parts = entry.path.split('/')
            current_path = ''
            for part in parts[:-1]:  # Excluir el archivo final
                if part:
                    current_path += '/' + part
                    all_paths.add(current_path)
        
        # Asegurar que todos los directorios padre existen en el cache
        for dir_path in all_paths:
            if dir_path not in self.dir_cache:
                self.dir_cache[dir_path] = []
        
        # Asegurar que la raíz existe
        if '/' not in self.dir_cache:
            self.dir_cache['/'] = []
        
        self.logger.info(f"Cached {len(self.files_cache)} files and {len(self.dir_cache)} directories")
    
    def getattr(self, path, fh=None):
        """Obtener atributos de archivo/directorio"""
        if path in self.files_cache:
            entry = self.files_cache[path]
            attrs = {
                'st_mode': entry.mode,
                'st_size': entry.size_bytes,
                'st_mtime': entry.mtime,
                'st_atime': entry.mtime,
                'st_ctime': entry.mtime,
                'st_nlink': 2 if entry.is_dir else 1,
                'st_uid': os.getuid(),
                'st_gid': os.getgid(),
            }
            return attrs
        
        # Si es un directorio conocido
        if path in self.dir_cache:
            attrs = {
                'st_mode': stat.S_IFDIR | 0o755,
                'st_size': 0,
                'st_mtime': time.time(),
                'st_atime': time.time(),
                'st_ctime': time.time(),
                'st_nlink': 2,
                'st_uid': os.getuid(),
                'st_gid': os.getgid(),
            }
            return attrs
        
        raise FuseOSError(errno.ENOENT)
    
    def readdir(self, path, fh):
        """Listar contenido de directorio"""
        entries = ['.', '..']
        
        if path in self.dir_cache:
            entries.extend(self.dir_cache[path])
        
        return entries
    
    def read(self, path, size, offset, fh):
        """Leer datos de archivo"""
        if path not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
        
        entry = self.files_cache[path]
        if entry.is_dir:
            raise FuseOSError(errno.EISDIR)
        
        # Obtener datos del archivo
        data = self.extractor.get_file_data(entry.path)
        if data is None:
            raise FuseOSError(errno.EIO)
        
        # Aplicar offset y size
        end = min(offset + size, len(data))
        return data[offset:end]
    
    def open(self, path, flags):
        """Abrir archivo"""
        if path not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
        
        entry = self.files_cache[path]
        if entry.is_dir:
            raise FuseOSError(errno.EISDIR)
        
        return 0  # Dummy file handle
    
    def release(self, path, fh):
        """Cerrar archivo"""
        return 0
    
    def destroy(self, path):
        """Limpiar al desmontar"""
        self.logger.info("Filesystem unmounting, cleaning up...")
        try:
            self.extractor.cleanup()
        except Exception as e:
            self.logger.error(f"Error during cleanup: {e}")

def main():
    if len(sys.argv) != 3:
        print("Uso: python3 rt11_fuse_universal.py <imagen.dsk> <punto_montaje>")
        print("")
        print("Ejemplo:")
        print("  python3 rt11_fuse_universal.py disk.dsk /mnt/pdp11")
        print("")
        print("Desmontaje:")
        print("  Linux: fusermount -u /mnt/pdp11")
        print("  macOS: umount /mnt/pdp11")
        sys.exit(1)
    
    image_path = sys.argv[1]
    mount_point = sys.argv[2]
    
    # Verificar que la imagen existe
    if not os.path.exists(image_path):
        print(f"Error: La imagen '{image_path}' no existe")
        sys.exit(1)
    
    # Verificar que el punto de montaje existe
    if not os.path.exists(mount_point):
        print(f"Error: El punto de montaje '{mount_point}' no existe")
        sys.exit(1)
    
    # Crear sistema de archivos FUSE
    try:
        fs = UniversalFuseFS(image_path)
        print(f"Mounting {image_path} at {mount_point}")
        print(f"Filesystem type: {fs.extractor.filesystem_type}")
        print(f"Files cached: {len(fs.files_cache)}")
        print("Press Ctrl+C to unmount")
        
        FUSE(fs, mount_point, foreground=True, allow_other=False, nothreads=True)
        
    except KeyboardInterrupt:
        print("\nUnmounting...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
