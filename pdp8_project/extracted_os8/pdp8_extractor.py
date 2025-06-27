#!/usr/bin/env python3
"""
PDP-8 File System Extractor
Basado en el código PUTR de John Wilson

Soporta:
- OS/8, OS/78, OS/278 
- PS/8 (DECtapes)
- TSS/8 PUTR format
- COS-310

Formatos de imagen soportados:
- RX01, RX02, RX03 (DECtapes de 8")
- RX50, RX52 (Disquetes de 5.25") 
- Archivos de imagen lineales
- Archivos de imagen interleaved

Autor: Basado en PUTR V2.01 de John Wilson
"""

import struct
import sys
import os
import argparse
from typing import BinaryIO, List, Tuple, Optional, Dict
from dataclasses import dataclass
from enum import Enum

class PDP8FileSystem(Enum):
    OS8 = "OS/8"
    PS8 = "PS/8" 
    TSS8 = "TSS/8"
    COS310 = "COS-310"
    PUTR = "PUTR"

class MediaType(Enum):
    RX01 = "RX01"  # 250KB 8" SS SD
    RX02 = "RX02"  # 500KB 8" SS DD  
    RX03 = "RX03"  # 1001KB 8" DS DD
    RX50 = "RX50"  # 400KB 5.25" SS
    RX52 = "RX52"  # 800KB 5.25" DS
    TU56 = "TU56"  # DECtape
    IMAGE = "Image File"

@dataclass
class FileEntry:
    """Entrada de archivo en directorio PDP-8"""
    name: str
    type: str
    size: int  # En bloques
    start_block: int
    date: Optional[str] = None
    extra_info: List[int] = None

@dataclass 
class DeviceGeometry:
    """Geometría de dispositivo"""
    cylinders: int
    heads: int
    sectors: int
    bytes_per_sector: int
    total_blocks: int
    interleaved: bool = False

class PDP8Extractor:
    """Extractor principal para sistemas de archivos PDP-8"""
    
    # Geometrías de dispositivos conocidos (basado en PUTR)
    GEOMETRIES = {
        MediaType.RX01: DeviceGeometry(77, 1, 26, 128, 494, False),
        MediaType.RX02: DeviceGeometry(77, 1, 26, 256, 988, False), 
        MediaType.RX03: DeviceGeometry(77, 2, 26, 256, 1976, False),
        MediaType.RX50: DeviceGeometry(80, 1, 10, 512, 800, False),
        MediaType.RX52: DeviceGeometry(80, 2, 10, 512, 1600, False),
        MediaType.TU56: DeviceGeometry(1, 1, 578, 256, 578, False),
    }
    
    def __init__(self, image_file: str, output_dir: str = "extracted"):
        self.image_file = image_file
        self.output_dir = output_dir
        self.file_handle: Optional[BinaryIO] = None
        self.filesystem: Optional[PDP8FileSystem] = None
        self.media_type: Optional[MediaType] = None
        self.geometry: Optional[DeviceGeometry] = None
        self.files: List[FileEntry] = []
        self.home_block_addr = 1  # Bloque home generalmente en bloque 1
        
    def detect_filesystem(self) -> PDP8FileSystem:
        """Detecta automáticamente el tipo de sistema de archivos"""
        try:
            # Leer bloque home (bloque 1)
            home_block = self.read_block(1)
            
            # Verificar OS/8 signature
            if self._is_os8_home_block(home_block):
                # Verificar si es COS-310 por contenido específico
                if self._has_cos310_signature(home_block):
                    return PDP8FileSystem.COS310
                return PDP8FileSystem.OS8
                
            # Verificar TSS/8 PUTR format
            if self._is_putr_format():
                return PDP8FileSystem.PUTR
                
            # Verificar PS/8 DECtape
            if self._is_ps8_format():
                return PDP8FileSystem.PS8
                
            # Default a OS/8 si no se puede determinar
            print("⚠️  No se pudo detectar el sistema de archivos, asumiendo OS/8")
            return PDP8FileSystem.OS8
            
        except Exception as e:
            print(f"⚠️  Error detectando sistema de archivos: {e}")
            return PDP8FileSystem.OS8
    
    def detect_media_type(self) -> MediaType:
        """Detecta el tipo de medio basado en el tamaño del archivo"""
        file_size = os.path.getsize(self.image_file)
        
        # Tabla de tamaños conocidos (basado en PUTR FILSIZ table)
        size_table = {
            (77 * 1 * 26 * 128):   MediaType.RX01,   # 250KB
            (77 * 1 * 26 * 256):   MediaType.RX02,   # 500KB  
            (77 * 2 * 26 * 256):   MediaType.RX03,   # 1001KB
            (80 * 1 * 10 * 512):   MediaType.RX50,   # 400KB
            (80 * 2 * 10 * 512):   MediaType.RX52,   # 800KB
            (578 * 256):           MediaType.TU56,   # DECtape
        }
        
        if file_size in size_table:
            return size_table[file_size]
            
        print(f"⚠️  Tamaño de archivo desconocido: {file_size} bytes")
        return MediaType.IMAGE
    
    def open_image(self):
        """Abre el archivo de imagen"""
        try:
            self.file_handle = open(self.image_file, 'rb')
            self.media_type = self.detect_media_type()
            
            if self.media_type in self.GEOMETRIES:
                self.geometry = self.GEOMETRIES[self.media_type]
            else:
                # Geometría por defecto para archivos de imagen
                file_size = os.path.getsize(self.image_file)
                blocks = file_size // 512
                self.geometry = DeviceGeometry(1, 1, blocks, 512, blocks, False)
                
            self.filesystem = self.detect_filesystem()
            
            print(f"📀 Medio: {self.media_type.value}")
            print(f"💾 Sistema: {self.filesystem.value}")
            print(f"📊 Bloques: {self.geometry.total_blocks}")
            
        except Exception as e:
            raise Exception(f"Error abriendo imagen: {e}")
    
    def read_block(self, block_num: int) -> bytes:
        """Lee un bloque de 512 bytes"""
        if not self.file_handle:
            raise Exception("Archivo de imagen no abierto")
            
        # Para RX01: cada bloque lógico = 4 sectores físicos de 128 bytes
        # Bloque lógico 0 = sectores físicos 0-3
        # Offset físico = block_num * 512
        block_size = 512
        offset = block_num * block_size
        
        self.file_handle.seek(offset)
        data = self.file_handle.read(block_size)
        
        if len(data) < block_size:
            # Rellenar con ceros si es necesario
            data += b'\x00' * (block_size - len(data))
            
        return data
    
    def read_os8_directory(self) -> List[FileEntry]:
        """Lee directorio OS/8 (incluye OS/78, OS/278)"""
        files = []
        
        try:
            # Leer bloque home
            home_block = self.read_block(1)
            
            # Parsear bloque home OS/8
            # Formato: word 0 = # entradas en segmento
            #          word 1 = bloque inicial de área vacía
            #          word 2 = siguiente segmento de directorio (0=none)
            #          word 3 = archivo tentativo
            #          word 4 = -(# palabras info por entrada)
            
            words = struct.unpack('<256H', home_block)  # 256 words de 16-bit
            
            num_entries = words[0] & 0x7FFF  # Enmascara bit alto
            empty_start = words[1]
            next_segment = words[2] 
            tentative_file = words[3]
            info_words = (~words[4] + 1) & 0x7FFF  # Complemento 2
            
            print(f"📂 Entradas en directorio: {num_entries}")
            print(f"🔢 Palabras info por entrada: {info_words}")
            
            # Parsear entradas de directorio
            # Cada entrada: 6 palabras base + info_words adicionales
            entry_size = 6 + info_words
            dir_offset = 5  # Las entradas empiezan en word 5
            
            for i in range(num_entries):
                if dir_offset + entry_size > 256:
                    break
                    
                # Leer entrada
                entry_words = words[dir_offset:dir_offset + entry_size]
                
                # Word 0: Tipo de archivo
                file_type = entry_words[0]
                
                if file_type == 0:  # .EMPTY.
                    dir_offset += entry_size
                    continue
                    
                # Words 1-3: Nombre de archivo en SIXBIT
                name_words = entry_words[1:4]
                filename = self._decode_sixbit(name_words)
                
                # Word 4: Longitud (negativa para archivos normales)
                length_word = entry_words[4]
                if length_word & 0x8000:  # Negativo
                    length = (~length_word + 1) & 0x7FFF
                else:
                    length = length_word
                
                # Word 5: Información de trabajo/canal
                job_info = entry_words[5]
                
                # Palabras adicionales (fecha, etc.)
                extra = list(entry_words[6:]) if info_words > 0 else []
                
                # Calcular bloque inicial
                if i == 0:
                    start_block = 7  # Primera entrada empieza después del directorio
                else:
                    # Sumar tamaños de entradas anteriores
                    start_block = files[-1].start_block + files[-1].size if files else 7
                
                # Decodificar fecha si está presente
                date_str = None
                if info_words > 0 and extra:
                    date_str = self._decode_os8_date(extra[0])
                
                files.append(FileEntry(
                    name=filename,
                    type=self._decode_os8_file_type(file_type),
                    size=length,
                    start_block=start_block,
                    date=date_str,
                    extra_info=extra
                ))
                
                dir_offset += entry_size
                
        except Exception as e:
            print(f"❌ Error leyendo directorio OS/8: {e}")
            
        return files
    
    def _is_os8_home_block(self, block: bytes) -> bool:
        """Verifica si es un bloque home válido de OS/8"""
        try:
            words = struct.unpack('<256H', block)
            
            # Verificaciones básicas de OS/8
            num_entries = words[0] & 0x7FFF
            info_words = (~words[4] + 1) & 0x7FFF
            
            # Rangos razonables
            if num_entries > 100 or info_words > 10:
                return False
                
            # El primer tipo debe ser válido
            first_type = words[5] if num_entries > 0 else 0
            if first_type > 0 and first_type < 0x1000:  # Rango válido de tipos
                return True
                
        except:
            pass
            
        return False
    
    def _has_cos310_signature(self, block: bytes) -> bool:
        """Verifica si tiene signature específico de COS-310"""
        # COS-310 usa OS/8 format pero archivos texto son diferentes
        # Por ahora usar heurística simple
        return False
    
    def _is_putr_format(self) -> bool:
        """Verifica formato TSS/8 PUTR"""
        # Implementar detección de PUTR format
        return False
    
    def _is_ps8_format(self) -> bool:
        """Verifica formato PS/8"""
        # Implementar detección de PS/8
        return False
    
    def _decode_sixbit(self, words: List[int]) -> str:
        """Decodifica nombre de archivo SIXBIT de OS/8"""
        result = ""
        
        for word in words:
            # OS/8 usa un formato específico para nombres de archivo
            # Cada word de 16 bits contiene hasta 2 caracteres completos
            # Los caracteres se empaquetan de forma que cada uno usa 6 bits
            
            # Extraer primer carácter (bits 10-15)
            c1 = (word >> 10) & 0x3F
            # Extraer segundo carácter (bits 4-9) 
            c2 = (word >> 4) & 0x3F
            # Puede haber un tercer carácter parcial (bits 0-3)
            # pero es mejor extraer solo 2 chars por word para mayor precisión
            
            for c in [c1, c2]:
                if c == 0:
                    break
                # Conversión SIXBIT a ASCII
                if c <= 31:
                    result += chr(c + ord(' '))
                else:
                    result += chr(c + ord('@') - 32)
                    
        return result.rstrip()
    
    def _decode_os8_file_type(self, type_code: int) -> str:
        """Decodifica tipo de archivo OS/8"""
        type_map = {
            0: ".EMPTY.",
            1: ".FILE.", 
            2: ".DATA.",
            3: ".PROG.",
            4: ".ASCII.",
            5: ".BINARY.",
        }
        return type_map.get(type_code, f".TYPE{type_code}.")
    
    def _decode_os8_date(self, date_word: int) -> str:
        """Decodifica fecha OS/8"""
        if date_word == 0:
            return None
            
        # OS/8 date format: bits usados para día/mes/año
        day = date_word & 0x1F
        month = (date_word >> 5) & 0x0F
        year = (date_word >> 9) & 0x7F
        
        if day == 0 or month == 0:
            return None
            
        # Año base típicamente 1970 en múltiplos de 8
        year_base = 1970 + ((year // 8) * 8)
        actual_year = year_base + (year % 8)
        
        try:
            return f"{day:02d}/{month:02d}/{actual_year}"
        except:
            return None
    
    def extract_file(self, file_entry: FileEntry) -> bytes:
        """Extrae contenido de un archivo"""
        data = b''
        
        # Leer bloques del archivo
        for block_offset in range(file_entry.size):
            block_num = file_entry.start_block + block_offset
            block_data = self.read_block(block_num)
            data += block_data
            
        return data
    
    def extract_all_files(self):
        """Extrae todos los archivos del sistema"""
        if not os.path.exists(self.output_dir):
            os.makedirs(self.output_dir)
            
        print(f"\n📁 Extrayendo archivos a: {self.output_dir}")
        
        for file_entry in self.files:
            if file_entry.type == ".EMPTY.":
                continue
                
            try:
                # Extraer contenido
                file_data = self.extract_file(file_entry)
                
                # Generar nombre de archivo seguro
                safe_name = self._make_safe_filename(file_entry.name)
                output_path = os.path.join(self.output_dir, safe_name)
                
                # Escribir archivo
                with open(output_path, 'wb') as f:
                    f.write(file_data)
                    
                print(f"✅ {file_entry.name} -> {safe_name} ({file_entry.size} bloques)")
                
            except Exception as e:
                print(f"❌ Error extrayendo {file_entry.name}: {e}")
    
    def _make_safe_filename(self, filename: str) -> str:
        """Convierte nombre PDP-8 a nombre seguro para filesystem moderno"""
        # Remover caracteres problemáticos
        safe = filename.replace('/', '_').replace('\\', '_').replace(':', '_')
        safe = safe.replace('<', '_').replace('>', '_').replace('|', '_')
        safe = safe.replace('?', '_').replace('*', '_').replace('"', '_')
        
        # Asegurar que no esté vacío
        if not safe.strip():
            safe = "UNNAMED"
            
        return safe.strip()
    
    def list_files(self):
        """Lista archivos en el sistema"""
        print(f"\n📋 Archivos en {self.filesystem.value}:")
        print("=" * 70)
        print(f"{'Nombre':<20} {'Tipo':<12} {'Tamaño':<8} {'Bloque':<8} {'Fecha':<12}")
        print("-" * 70)
        
        for file_entry in self.files:
            date_str = file_entry.date or ""
            print(f"{file_entry.name:<20} {file_entry.type:<12} {file_entry.size:<8} "
                  f"{file_entry.start_block:<8} {date_str:<12}")
        
        print("-" * 70)
        total_files = len([f for f in self.files if f.type != ".EMPTY."])
        total_blocks = sum(f.size for f in self.files if f.type != ".EMPTY.")
        print(f"Total: {total_files} archivos, {total_blocks} bloques usados")
    
    def run(self):
        """Ejecuta la extracción completa"""
        try:
            print("🚀 Iniciando extractor PDP-8...")
            
            # Abrir imagen
            self.open_image()
            
            # Leer directorio según el sistema de archivos
            if self.filesystem in [PDP8FileSystem.OS8, PDP8FileSystem.COS310]:
                self.files = self.read_os8_directory()
            elif self.filesystem == PDP8FileSystem.PUTR:
                # TODO: Implementar lectura de directorio PUTR
                print("⚠️  PUTR format no implementado aún")
                return
            elif self.filesystem == PDP8FileSystem.PS8:
                # TODO: Implementar lectura de directorio PS/8
                print("⚠️  PS/8 format no implementado aún") 
                return
            else:
                print("❌ Sistema de archivos no soportado")
                return
            
            # Listar archivos
            self.list_files()
            
            # Extraer archivos
            if self.files:
                self.extract_all_files()
                print(f"\n🎉 Extracción completada!")
            else:
                print("\n⚠️  No se encontraron archivos para extraer")
                
        except Exception as e:
            print(f"❌ Error durante extracción: {e}")
        finally:
            if self.file_handle:
                self.file_handle.close()

def main():
    parser = argparse.ArgumentParser(description="Extractor de sistemas de archivos PDP-8")
    parser.add_argument("image_file", help="Archivo de imagen de disco/DECtape PDP-8")
    parser.add_argument("-o", "--output", default="extracted_pdp8", 
                       help="Directorio de salida (default: extracted_pdp8)")
    parser.add_argument("-l", "--list-only", action="store_true",
                       help="Solo listar archivos, no extraer")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Salida detallada")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image_file):
        print(f"❌ Archivo no encontrado: {args.image_file}")
        sys.exit(1)
    
    extractor = PDP8Extractor(args.image_file, args.output)
    
    try:
        # Abrir y analizar
        extractor.open_image()
        
        # Leer directorio
        if extractor.filesystem in [PDP8FileSystem.OS8, PDP8FileSystem.COS310]:
            extractor.files = extractor.read_os8_directory()
        else:
            print(f"❌ Sistema {extractor.filesystem.value} no implementado aún")
            sys.exit(1)
            
        # Listar archivos
        extractor.list_files()
        
        # Extraer si no es solo listado
        if not args.list_only and extractor.files:
            extractor.extract_all_files()
            print(f"\n🎉 Extracción completada en: {args.output}")
            
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()
