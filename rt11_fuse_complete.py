#!/usr/bin/env python3
"""
RT-11 FUSE Driver
=================

Driver FUSE para montar imágenes DSK de RT-11 como sistemas de archivos.
Permite navegar y acceder a archivos RT-11 como si fueran archivos normales.

Este driver utiliza tu extractor rt11extract existente.

Uso:
    python3 rt11_fuse_complete.py <imagen.dsk> <punto_montaje>

Ejemplo:
    python3 rt11_fuse_complete.py disk.dsk /mnt/rt11

Desmontaje:
    fusermount -u /mnt/rt11  (Linux)
    umount /mnt/rt11         (macOS)

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
from typing import Dict, List, Optional

# Importar FUSE
try:
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
except ImportError:
    print("Error: fusepy no está instalado.")
    print("Instálalo con: pip install fusepy")
    sys.exit(1)

class RT11FileEntry:
    """Representación simplificada de un archivo RT-11"""
    def __init__(self, filename, file_type, size_blocks, start_block, status=0):
        self.filename = filename.strip()
        self.file_type = file_type.strip()
        self.size_blocks = size_blocks
        self.start_block = start_block
        self.status = status
        self.creation_date = None
        
    @property
    def full_filename(self):
        if self.file_type:
            return f"{self.filename}.{self.file_type}"
        return self.filename
    
    @property
    def size_bytes(self):
        return self.size_blocks * 512
    
    @property
    def is_protected(self):
        # Bit de protección básico
        return (self.status & 0x0100) != 0
    
    @property
    def is_valid(self):
        return len(self.filename.strip()) > 0

class RT11ExtractorWrapper:
    """Wrapper para usar tu extractor rt11extract existente"""
    
    def __init__(self, image_path: str):
        self.image_path = Path(image_path)
        self.logger = logging.getLogger('RT11-Extractor')
        self._file_data_cache = {}  # Cache para datos de archivos
        
        # Find rt11extract in different possible locations
        # Handle PyInstaller executable vs script mode
        if getattr(sys, 'frozen', False):
            # Running as PyInstaller executable
            # Get the actual app bundle path from _MEIPASS
            bundle_path = None
            if hasattr(sys, '_MEIPASS'):
                # Try to find the actual .app bundle path
                current_path = Path(sys.executable)
                # Walk up to find .app bundle
                for parent in current_path.parents:
                    if parent.name.endswith('.app'):
                        bundle_path = parent
                        break
            
            if bundle_path:
                script_dir = bundle_path / "Contents" / "Resources"
                possible_paths = [
                    bundle_path / "Contents" / "MacOS" / "rt11extract_cli",  # In macOS bundle MacOS folder
                    script_dir / "rt11extract_cli",  # In Resources folder
                    script_dir / "rt11extract",      # Script version in Resources
                ]
            else:
                # Fallback if we can't find bundle
                script_dir = Path(sys.executable).parent
                possible_paths = [
                    script_dir / "rt11extract_cli",
                    script_dir / "rt11extract",
                ]
        else:
            # Running as script
            script_dir = Path(__file__).parent
            possible_paths = [
                script_dir / "rt11extract_cli",  # Standalone executable (preferred)
                script_dir / "rt11extract",      # Script version
                script_dir.parent / "MacOS" / "rt11extract_cli",  # In macOS bundle MacOS folder
                script_dir.parent.parent / "MacOS" / "rt11extract_cli",  # Alternative bundle path
            ]
        
        self.rt11extract_path = None
        for path in possible_paths:
            if path.exists():
                self.rt11extract_path = path
                self.logger.info(f"Found rt11extract at: {path}")
                break
        
        # Verificar que el extractor existe
        if not self.rt11extract_path:
            # Try to find it in PATH as last resort
            import shutil
            system_rt11extract = shutil.which("rt11extract_cli") or shutil.which("rt11extract")
            if system_rt11extract:
                self.rt11extract_path = Path(system_rt11extract)
                self.logger.info(f"Found rt11extract in PATH: {self.rt11extract_path}")
            else:
                raise Exception(f"rt11extract no encontrado en ninguna ubicación. Intenté: {[str(p) for p in possible_paths]}")
        
        # Hacer el extractor ejecutable
        try:
            os.chmod(self.rt11extract_path, 0o755)
        except (OSError, PermissionError):
            # Ignore chmod errors for system executables
            pass
        
    def list_files(self) -> List[RT11FileEntry]:
        """Obtener lista de archivos extrayendo a directorio temporal"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Ejecutar rt11extract para extraer todos los archivos
                cmd = [str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
                
                if result.returncode != 0:
                    self.logger.error(f"rt11extract falló: {result.stderr}")
                    return []
                
                # Escanear archivos extraídos
                files = []
                for file_path in temp_path.iterdir():
                    if file_path.is_file() and not file_path.name.endswith('.rt11info'):
                        filename = file_path.name
                        size_bytes = file_path.stat().st_size
                        size_blocks = (size_bytes + 511) // 512  # Redondear hacia arriba
                        
                        # Separar nombre y extensión
                        if '.' in filename:
                            name, ext = filename.rsplit('.', 1)
                        else:
                            name, ext = filename, ""
                        
                        entry = RT11FileEntry(name, ext, size_blocks, 0)
                        files.append(entry)
                        
                        # Guardar datos del archivo para cache
                        self._file_data_cache[filename] = file_path.read_bytes()
                
                self.logger.info(f"Encontrados {len(files)} archivos")
                return files
                
        except subprocess.TimeoutExpired:
            self.logger.error("rt11extract timeout")
            return []
        except Exception as e:
            self.logger.error(f"Error ejecutando rt11extract: {e}")
            return []
    
    def _parse_file_list(self, output: str) -> List[RT11FileEntry]:
        """Parsear la salida de rt11extract para obtener lista de archivos"""
        files = []
        
        # Buscar la sección de archivos en la salida
        lines = output.split('\n')
        in_file_list = False
        
        for line in lines:
            line = line.strip()
            
            # Detectar inicio de listado de archivos
            if "Directory Listing" in line or "files found" in line.lower():
                in_file_list = True
                continue
            
            # Detectar fin de listado
            if in_file_list and (line.startswith("Summary:") or line.startswith("Extraction")):
                break
                
            # Parsear líneas de archivos
            if in_file_list and line and not line.startswith('-') and not line.startswith('Filename'):
                try:
                    # Formato esperado: filename.ext   type   size   status   start   category
                    parts = line.split()
                    if len(parts) >= 3:
                        full_name = parts[0]
                        if '.' in full_name:
                            filename, file_type = full_name.rsplit('.', 1)
                        else:
                            filename = full_name
                            file_type = ""
                        
                        # Extraer tamaño (puede estar en KB o bloques)
                        size_str = parts[2]
                        if size_str.isdigit():
                            size_blocks = int(size_str)
                        else:
                            # Asumir que está en KB, convertir a bloques
                            size_kb = int(size_str.replace('KB', '').replace('kb', ''))
                            size_blocks = (size_kb * 1024) // 512
                        
                        # Crear entrada de archivo
                        entry = RT11FileEntry(filename, file_type, size_blocks, 0)
                        files.append(entry)
                        
                except (ValueError, IndexError) as e:
                    self.logger.debug(f"No se pudo parsear línea: {line} - {e}")
                    continue
        
        self.logger.info(f"Parseados {len(files)} archivos de la salida de rt11extract")
        return files
    
    def extract_file_data(self, filename: str) -> bytes:
        """Extraer datos de un archivo específico"""
        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                temp_path = Path(temp_dir)
                
                # Ejecutar rt11extract para extraer solo este archivo
                cmd = [str(self.rt11extract_path), str(self.image_path), "-o", str(temp_path)]
                result = subprocess.run(cmd, capture_output=True, text=True, timeout=30)
                
                if result.returncode != 0:
                    self.logger.error(f"Error extrayendo {filename}: {result.stderr}")
                    return b''
                
                # Buscar el archivo extraído
                extracted_file = temp_path / filename
                if extracted_file.exists():
                    return extracted_file.read_bytes()
                
                # Buscar con diferentes variaciones del nombre
                for file in temp_path.glob("*"):
                    if file.name.upper() == filename.upper():
                        return file.read_bytes()
                
                self.logger.error(f"Archivo {filename} no encontrado después de la extracción")
                return b''
                
        except subprocess.TimeoutExpired:
            self.logger.error(f"Timeout extrayendo {filename}")
            return b''
        except Exception as e:
            self.logger.error(f"Error extrayendo {filename}: {e}")
            return b''

class RT11FileSystem(LoggingMixIn, Operations):
    """Sistema de archivos FUSE para imágenes RT-11"""
    
    def __init__(self, disk_image_path: str):
        self.disk_image_path = disk_image_path
        self.extractor = RT11ExtractorWrapper(disk_image_path)
        self.files_cache: Dict[str, RT11FileEntry] = {}
        self.file_data_cache: Dict[str, bytes] = {}
        self.last_scan_time = 0
        self.cache_timeout = 30  # Cache por 30 segundos
        
        # Configurar logging
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger('RT11-FUSE')
        
        # Escanear archivos inicialmente
        self._scan_files()
    
    def _scan_files(self):
        """Escanear archivos de la imagen RT-11"""
        try:
            current_time = time.time()
            if current_time - self.last_scan_time < self.cache_timeout:
                return  # Cache aún válido
                
            self.logger.info("Escaneando archivos RT-11...")
            self.files_cache.clear()
            self.file_data_cache.clear()
            
            # Obtener lista de archivos
            files = self.extractor.list_files()
            
            for file_entry in files:
                if file_entry.is_valid:
                    filename = file_entry.full_filename
                    # Normalizar nombre de archivo para FUSE
                    safe_filename = self._make_safe_filename(filename)
                    self.files_cache[safe_filename] = file_entry
                    
                    # Copiar datos del cache del extractor si están disponibles
                    if filename in self.extractor._file_data_cache:
                        self.file_data_cache[safe_filename] = self.extractor._file_data_cache[filename]
                    
            self.last_scan_time = current_time
            self.logger.info(f"Escaneados {len(self.files_cache)} archivos")
            
        except Exception as e:
            self.logger.error(f"Error escaneando archivos: {e}")
            # No lanzar excepción aquí, permitir que el montaje continúe
    
    def _make_safe_filename(self, filename: str) -> str:
        """Convertir nombre de archivo RT-11 a nombre seguro para FUSE"""
        # RT-11 permite algunos caracteres que pueden ser problemáticos
        safe_name = filename.replace('$', '_DOLLAR_')
        safe_name = safe_name.replace('?', '_QUESTION_')
        safe_name = safe_name.replace('*', '_STAR_')
        return safe_name.upper()
    
    def _get_file_data(self, filename: str) -> bytes:
        """Obtener datos de un archivo, con cache"""
        if filename in self.file_data_cache:
            return self.file_data_cache[filename]
            
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        try:
            # Convertir nombre seguro de vuelta al nombre original
            original_name = filename.replace('_DOLLAR_', '$')
            original_name = original_name.replace('_QUESTION_', '?')
            original_name = original_name.replace('_STAR_', '*')
            
            data = self.extractor.extract_file_data(original_name)
            
            # Cache los datos si el archivo no es muy grande
            if len(data) < 1024 * 1024:  # 1MB
                self.file_data_cache[filename] = data
                
            return data
            
        except Exception as e:
            self.logger.error(f"Error extrayendo archivo {filename}: {e}")
            raise FuseOSError(errno.EIO)

    # Métodos requeridos por FUSE
    
    def getattr(self, path, fh=None):
        """Obtener atributos de archivo/directorio"""
        self._scan_files()
        
        if path == '/':
            # Directorio raíz
            st = dict(
                st_mode=(stat.S_IFDIR | 0o755),
                st_ctime=time.time(),
                st_mtime=time.time(),
                st_atime=time.time(),
                st_nlink=2,
                st_size=0,
                st_uid=os.getuid(),
                st_gid=os.getgid()
            )
            return st
        
        filename = path[1:]  # Remover '/' inicial
        
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        file_entry = self.files_cache[filename]
        
        # Calcular tamaño en bytes
        size_bytes = file_entry.size_bytes
        
        # Fecha de modificación por defecto
        mtime = time.time()
        
        st = dict(
            st_mode=(stat.S_IFREG | 0o644),
            st_ctime=mtime,
            st_mtime=mtime, 
            st_atime=mtime,
            st_nlink=1,
            st_size=size_bytes,
            st_uid=os.getuid(),
            st_gid=os.getgid()
        )
        
        # Archivos protegidos son solo lectura
        if file_entry.is_protected:
            st['st_mode'] = stat.S_IFREG | 0o444
            
        return st
    
    def readdir(self, path, fh):
        """Listar contenidos del directorio"""
        if path != '/':
            raise FuseOSError(errno.ENOTDIR)
            
        self._scan_files()
        
        entries = ['.', '..']
        entries.extend(self.files_cache.keys())
        
        for entry in entries:
            yield entry
    
    def open(self, path, flags):
        """Abrir archivo"""
        filename = path[1:]
        
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        # Solo lectura
        if flags & (os.O_WRONLY | os.O_RDWR):
            raise FuseOSError(errno.EACCES)
            
        return 0
    
    def read(self, path, size, offset, fh):
        """Leer datos del archivo"""
        filename = path[1:]
        
        try:
            data = self._get_file_data(filename)
            
            # Leer fragmento solicitado
            end = offset + size
            return data[offset:end]
            
        except Exception as e:
            self.logger.error(f"Error leyendo {filename}: {e}")
            raise FuseOSError(errno.EIO)
    
    def statfs(self, path):
        """Información del sistema de archivos"""
        try:
            total_blocks = 0
            used_blocks = 0
            
            for file_entry in self.files_cache.values():
                total_blocks += file_entry.size_blocks
                used_blocks += file_entry.size_blocks
            
            # Si no tenemos información, usar valores por defecto
            if total_blocks == 0:
                total_blocks = 1000
                
            free_blocks = max(0, total_blocks - used_blocks)
            
            return dict(
                f_bsize=512,      # Tamaño de bloque
                f_frsize=512,     # Tamaño de fragmento  
                f_blocks=total_blocks,
                f_bfree=free_blocks,
                f_bavail=free_blocks,
                f_files=len(self.files_cache),
                f_ffree=0,
                f_favail=0,
                f_namemax=255
            )
        except:
            # Valores por defecto en caso de error
            return dict(
                f_bsize=512,
                f_frsize=512,
                f_blocks=1000,
                f_bfree=100,
                f_bavail=100,
                f_files=len(self.files_cache),
                f_ffree=0,
                f_favail=0,
                f_namemax=255
            )

def check_requirements():
    """Verificar requisitos del sistema"""
    # Verificar que FUSE está disponible
    try:
        import fuse
    except ImportError:
        print("Error: fusepy no está instalado.")
        print("Instálalo con: pip install fusepy")
        return False
    
    # En macOS, verificar que macFUSE está instalado
    if sys.platform == 'darwin':
        if not os.path.exists('/usr/local/lib/libfuse.dylib') and \
           not os.path.exists('/opt/homebrew/lib/libfuse.dylib'):
            print("Error: macFUSE no parece estar instalado.")
            print("Descárgalo desde: https://osxfuse.github.io/")
            return False
    
    return True

def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("RT-11 FUSE Driver")
        print("=================")
        print()
        print("Uso: python3 rt11_fuse_complete.py <imagen.dsk> <punto_montaje>")
        print()
        print("Ejemplos:")
        print("  python3 rt11_fuse_complete.py disk.dsk /mnt/rt11")
        print("  python3 rt11_fuse_complete.py image.imd ~/rt11_mount")
        print()
        print("Para desmontar:")
        print("  fusermount -u /mnt/rt11  (Linux)")
        print("  umount /mnt/rt11         (macOS)")
        print()
        print("Requisitos:")
        print("  - fusepy: pip install fusepy")
        print("  - macFUSE (macOS): https://osxfuse.github.io/")
        sys.exit(1)
    
    if not check_requirements():
        sys.exit(1)
    
    disk_image = sys.argv[1]
    mount_point = sys.argv[2]
    
    # Verificar que la imagen existe
    if not os.path.exists(disk_image):
        print(f"Error: La imagen {disk_image} no existe")
        sys.exit(1)
    
    # Expandir el path del punto de montaje
    mount_point = os.path.expanduser(mount_point)
    
    # Crear el punto de montaje si no existe
    if not os.path.exists(mount_point):
        try:
            os.makedirs(mount_point)
            print(f"Creado directorio de montaje: {mount_point}")
        except Exception as e:
            print(f"Error creando directorio de montaje {mount_point}: {e}")
            sys.exit(1)
    
    # Verificar que el punto de montaje está vacío
    if os.listdir(mount_point):
        print(f"Advertencia: El punto de montaje {mount_point} no está vacío")
        print("Se recomienda usar un directorio vacío")
    
    print(f"Montando imagen RT-11: {disk_image}")
    print(f"Punto de montaje: {mount_point}")
    print("Presiona Ctrl+C para desmontar")
    print()
    
    # Crear y ejecutar el sistema de archivos FUSE
    try:
        fs = RT11FileSystem(disk_image)
        
        # Opciones de montaje
        fuse_options = {
            'nothreads': True,
            'foreground': True,   # Ejecutar en foreground pero sin debug
            'debug': False,       # Desactivar debug completamente
            'allow_other': False
        }
        
        # En macOS, agregar opciones específicas
        if sys.platform == 'darwin':
            fuse_options['volname'] = f"RT11-{Path(disk_image).stem}"
        
        FUSE(fs, mount_point, **fuse_options)
        
    except KeyboardInterrupt:
        print("\nDesmontando...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == '__main__':
    main()
