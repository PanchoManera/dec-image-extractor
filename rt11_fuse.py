#!/usr/bin/env python3
"""
RT-11 FUSE Driver
=================

Driver FUSE para montar imágenes DSK de RT-11 como sistemas de archivos.
Permite navegar y acceder a archivos RT-11 como si fueran archivos normales.

Uso:
    python3 rt11_fuse.py <imagen.dsk> <punto_montaje>

Ejemplo:
    python3 rt11_fuse.py disk.dsk /mnt/rt11

Desmontaje:
    fusermount -u /mnt/rt11  (Linux)
    umount /mnt/rt11         (macOS)
"""

import os
import sys
import errno
import stat
import time
import logging
from pathlib import Path
from typing import Dict, List, Optional, Union
import struct

# Importar FUSE
try:
    from fuse import FUSE, FuseOSError, Operations, LoggingMixIn
except ImportError:
    print("Error: fusepy no está instalado.")
    print("Instálalo con: pip install fusepy")
    sys.exit(1)

# Importar necesarios módulos para RT-11
import subprocess
import tempfile
from pathlib import Path

class RT11Extractor:
    def __init__(self, image_path):
        self.image_path = image_path
        # Cargar y validar imagen
        self.validate_filesystem()

    def list_files(self):
        #... lógicamente listado de archivos según tu implementación existente
        pass

    def extract_file_data(self, entry):
        #... lógica para extraer archivo
        pass

    def validate_filesystem(self):
        # Validar el sistema de archivos RT-11
        pass

class RT11FileSystem(LoggingMixIn, Operations):
    """
    Sistema de archivos FUSE para imágenes RT-11
    """
    
    def __init__(self, disk_image_path: str):
        self.disk_image_path = disk_image_path
        self.extractor = None
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
        
        # Inicializar el extractor
        self._initialize_extractor()
        
    def _initialize_extractor(self):
        """Inicializar el extractor RT-11"""
        try:
            self.extractor = RT11Extractor(self.disk_image_path)
            self.logger.info(f"Montando imagen RT-11: {self.disk_image_path}")
            self._scan_files()
        except Exception as e:
            self.logger.error(f"Error inicializando extractor: {e}")
            raise FuseOSError(errno.EIO)
    
    def _scan_files(self):
        """Escanear archivos de la imagen RT-11"""
        try:
            current_time = time.time()
            if current_time - self.last_scan_time < self.cache_timeout:
                return  # Cache aún válido
                
            self.files_cache.clear()
            self.file_data_cache.clear()
            
            # Obtener lista de archivos
            files = self.extractor.list_files()
            
            for file_entry in files:
                if file_entry.is_valid and not file_entry.is_unused:
                    filename = file_entry.full_filename
                    # Normalizar nombre de archivo para FUSE
                    safe_filename = self._make_safe_filename(filename)
                    self.files_cache[safe_filename] = file_entry
                    
            self.last_scan_time = current_time
            self.logger.info(f"Escaneados {len(self.files_cache)} archivos")
            
        except Exception as e:
            self.logger.error(f"Error escaneando archivos: {e}")
            raise FuseOSError(errno.EIO)
    
    def _make_safe_filename(self, filename: str) -> str:
        """Convertir nombre de archivo RT-11 a nombre seguro para FUSE"""
        # RT-11 permite algunos caracteres que pueden ser problemáticos
        safe_name = filename.replace('$', '_DOLLAR_')
        safe_name = safe_name.replace('?', '_QUESTION_')
        return safe_name.upper()
    
    def _get_file_data(self, filename: str) -> bytes:
        """Obtener datos de un archivo, con cache"""
        if filename in self.file_data_cache:
            return self.file_data_cache[filename]
            
        if filename not in self.files_cache:
            raise FuseOSError(errno.ENOENT)
            
        try:
            file_entry = self.files_cache[filename]
            data = self.extractor.extract_file_data(file_entry)
            
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
        size_bytes = file_entry.length * 512  # RT-11 usa bloques de 512 bytes
        
        # Determinar fecha de modificación
        mtime = time.time()
        if file_entry.creation_date:
            try:
                # RT-11 usa formato de fecha específico
                mtime = self._rt11_date_to_unix(file_entry.creation_date)
            except:
                pass
        
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
    
    def _rt11_date_to_unix(self, rt11_date: int) -> float:
        """Convertir fecha RT-11 a timestamp Unix"""
        # RT-11 usa formato de fecha específico
        # Esto es una aproximación - necesitarías implementar el formato exacto
        try:
            # RT-11 fecha base es aproximadamente 1970
            base_year = 1970
            days = rt11_date
            timestamp = (days * 24 * 60 * 60) + time.mktime((base_year, 1, 1, 0, 0, 0, 0, 0, 0))
            return timestamp
        except:
            return time.time()
    
    # Métodos adicionales para información del sistema de archivos
    
    def statfs(self, path):
        """Información del sistema de archivos"""
        try:
            total_blocks = 0
            used_blocks = 0
            
            for file_entry in self.files_cache.values():
                total_blocks += file_entry.length
                if not file_entry.is_unused:
                    used_blocks += file_entry.length
            
            # Si no tenemos información, usar valores por defecto
            if total_blocks == 0:
                total_blocks = 1000
                
            free_blocks = total_blocks - used_blocks
            
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


def main():
    """Función principal"""
    if len(sys.argv) != 3:
        print("Uso: python3 rt11_fuse.py <imagen.dsk> <punto_montaje>")
        print()
        print("Ejemplos:")
        print("  python3 rt11_fuse.py disk.dsk /mnt/rt11")
        print("  python3 rt11_fuse.py image.imd ~/rt11_mount")
        print()
        print("Para desmontar:")
        print("  fusermount -u /mnt/rt11  (Linux)")
        print("  umount /mnt/rt11         (macOS)")
        sys.exit(1)
    
    disk_image = sys.argv[1]
    mount_point = sys.argv[2]
    
    # Verificar que la imagen existe
    if not os.path.exists(disk_image):
        print(f"Error: La imagen {disk_image} no existe")
        sys.exit(1)
    
    # Verificar que el punto de montaje existe
    if not os.path.exists(mount_point):
        print(f"Error: El punto de montaje {mount_point} no existe")
        print(f"Crea el directorio primero: mkdir -p {mount_point}")
        sys.exit(1)
    
    # Verificar que el punto de montaje está vacío
    if os.listdir(mount_point):
        print(f"Advertencia: El punto de montaje {mount_point} no está vacío")
    
    print(f"Montando {disk_image} en {mount_point}")
    print("Presiona Ctrl+C para desmontar")
    
    # Crear y ejecutar el sistema de archivos FUSE
    fs = RT11FileSystem(disk_image)
    
    try:
        FUSE(fs, mount_point, nothreads=True, foreground=True, 
             debug=False, allow_other=False)
    except KeyboardInterrupt:
        print("\nDesmontando...")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()
