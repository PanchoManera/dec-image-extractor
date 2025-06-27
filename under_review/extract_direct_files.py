#!/usr/bin/env python3
"""
Extractor Directo de Archivos PDP-8
Basado en el análisis de patrones encontrados - extrae archivos directamente por sectores
"""

import os
import sys
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class DirectFile:
    """Representa un archivo encontrado directamente"""
    sector: int
    filename: str
    data: bytes
    size: int

class DirectFileExtractor:
    """Extractor directo de archivos basado en patrones SIXBIT"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image_data = None
        self.sector_size = 128
        self.found_files = []
        
    def load_image(self) -> bool:
        """Cargar imagen del disco"""
        try:
            with open(self.image_path, 'rb') as f:
                self.image_data = f.read()
            print(f"Cargada imagen: {len(self.image_data)} bytes")
            return True
        except Exception as e:
            print(f"Error cargando imagen: {e}")
            return False
    
    def decode_sixbit_string(self, data: bytes, max_length: int = 12) -> str:
        """
        Decodifica una cadena SIXBIT desde bytes
        SIXBIT: each byte & 0x3F + 0x40 = ASCII character
        """
        chars = []
        for i, byte in enumerate(data[:max_length]):
            if byte == 0x40:  # Space
                chars.append(' ')
            elif byte == 0x00:  # Null/padding
                break
            elif 0xC1 <= byte <= 0xDA:  # Letters A-Z in SIXBIT
                chars.append(chr((byte & 0x3F) + 0x40))
            elif 0xF0 <= byte <= 0xF9:  # Numbers 0-9 in SIXBIT  
                chars.append(chr((byte & 0x3F) + 0x40))
            elif 0x40 <= byte <= 0x7F:  # Direct ASCII
                chars.append(chr(byte))
            else:
                # Try direct conversion
                if 32 <= byte <= 126:
                    chars.append(chr(byte))
                else:
                    break
        
        return ''.join(chars).strip()
    
    def extract_filename_from_sector(self, sector_data: bytes) -> Optional[str]:
        """
        Intenta extraer un nombre de archivo del inicio de un sector
        Basado en los patrones que encontramos
        """
        if len(sector_data) < 8:
            return None
        
        # Patrón 1: Primeros 4-8 bytes como nombre de archivo SIXBIT
        filename = self.decode_sixbit_string(sector_data[:8])
        
        # Validar que parece un nombre de archivo válido
        if len(filename) >= 3 and len(filename) <= 12:
            # Verificar que contiene solo caracteres válidos para nombres de archivo
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789. ')
            if all(c in valid_chars for c in filename.upper()):
                return filename.upper().strip()
        
        # Patrón 2: Intentar con los primeros 4 bytes solamente
        filename = self.decode_sixbit_string(sector_data[:4])
        if len(filename) >= 3 and len(filename) <= 8:
            valid_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789')
            if all(c in valid_chars for c in filename.upper()):
                return filename.upper().strip()
        
        return None
    
    def is_interesting_sector(self, sector_data: bytes) -> bool:
        """
        Determina si un sector contiene datos interesantes (no solo espacios)
        """
        if len(sector_data) == 0:
            return False
        
        # Contar bytes únicos
        unique_bytes = len(set(sector_data))
        
        # Contar espacios (0x40)
        space_count = sector_data.count(0x40)
        space_ratio = space_count / len(sector_data)
        
        # Contar nulls (0x00)
        null_count = sector_data.count(0x00)
        null_ratio = null_count / len(sector_data)
        
        # Criterios para sector interesante:
        # 1. Más de 5 bytes únicos
        # 2. No es principalmente espacios (menos del 80%)
        # 3. No es principalmente nulls (menos del 60%)
        return (unique_bytes > 5 and 
                space_ratio < 0.8 and 
                null_ratio < 0.6)
    
    def get_file_content_size(self, sector_data: bytes) -> int:
        """
        Estima el tamaño real del contenido del archivo en el sector
        Busca el final de datos significativos
        """
        # Buscar desde el final hacia atrás el último byte no-null no-space
        content_end = len(sector_data)
        
        for i in range(len(sector_data) - 1, -1, -1):
            if sector_data[i] != 0x00 and sector_data[i] != 0x40:
                content_end = i + 1
                break
        
        return max(content_end, 16)  # Mínimo 16 bytes
    
    def scan_for_files(self) -> List[DirectFile]:
        """
        Escanea toda la imagen buscando sectores que contengan archivos
        """
        files = []
        total_sectors = len(self.image_data) // self.sector_size
        
        print(f"Escaneando {total_sectors} sectores...")
        
        for sector_num in range(total_sectors):
            offset = sector_num * self.sector_size
            sector_data = self.image_data[offset:offset + self.sector_size]
            
            # Solo procesar sectores interesantes
            if not self.is_interesting_sector(sector_data):
                continue
            
            # Intentar extraer nombre de archivo
            filename = self.extract_filename_from_sector(sector_data)
            
            if filename:
                # Determinar tamaño del contenido
                content_size = self.get_file_content_size(sector_data)
                
                file_obj = DirectFile(
                    sector=sector_num,
                    filename=filename,
                    data=sector_data[:content_size],
                    size=content_size
                )
                
                files.append(file_obj)
                print(f"  Archivo encontrado en sector {sector_num}: '{filename}' ({content_size} bytes)")
            
            # También reportar sectores interesantes sin nombre de archivo válido
            elif len(set(sector_data)) > 10:
                # Mostrar primeros bytes para análisis manual
                first_bytes = ' '.join(f'{b:02x}' for b in sector_data[:16])
                decoded = self.decode_sixbit_string(sector_data[:8])
                print(f"  Sector {sector_num} interesante: {first_bytes} -> '{decoded}'")
        
        return files
    
    def extract_multi_sector_files(self) -> List[DirectFile]:
        """
        Busca archivos que puedan ocupar múltiples sectores consecutivos
        """
        files = []
        total_sectors = len(self.image_data) // self.sector_size
        
        print(f"\nBuscando archivos multi-sector...")
        
        sector = 0
        while sector < total_sectors:
            offset = sector * self.sector_size
            sector_data = self.image_data[offset:offset + self.sector_size]
            
            # Buscar inicio de archivo (sector con nombre)
            filename = self.extract_filename_from_sector(sector_data)
            
            if filename and self.is_interesting_sector(sector_data):
                # Encontrado posible inicio de archivo
                file_data = bytearray(sector_data)
                file_sectors = 1
                
                # Buscar sectores consecutivos que parezcan continuación
                next_sector = sector + 1
                while next_sector < total_sectors:
                    next_offset = next_sector * self.sector_size
                    next_data = self.image_data[next_offset:next_offset + self.sector_size]
                    
                    # Si el siguiente sector tiene otro nombre de archivo, parar
                    if self.extract_filename_from_sector(next_data):
                        break
                    
                    # Si el sector es interesante (no vacío), incluirlo
                    if self.is_interesting_sector(next_data):
                        file_data.extend(next_data)
                        file_sectors += 1
                        next_sector += 1
                    else:
                        # Si encontramos muchos sectores vacíos, parar
                        empty_count = 0
                        temp_sector = next_sector
                        while temp_sector < min(next_sector + 3, total_sectors):
                            temp_offset = temp_sector * self.sector_size
                            temp_data = self.image_data[temp_offset:temp_offset + self.sector_size]
                            if not self.is_interesting_sector(temp_data):
                                empty_count += 1
                            temp_sector += 1
                        
                        if empty_count >= 2:
                            break
                        else:
                            file_data.extend(next_data)
                            file_sectors += 1
                            next_sector += 1
                
                # Determinar tamaño real del archivo
                content_size = self.get_file_content_size(bytes(file_data))
                
                if file_sectors > 1 or content_size > 64:  # Solo archivos significativos
                    file_obj = DirectFile(
                        sector=sector,
                        filename=f"{filename}",
                        data=bytes(file_data[:content_size]),
                        size=content_size
                    )
                    
                    files.append(file_obj)
                    print(f"  Archivo multi-sector: '{filename}' sectores {sector}-{sector + file_sectors - 1} ({content_size} bytes)")
                
                sector = next_sector
            else:
                sector += 1
        
        return files
    
    def save_files(self, files: List[DirectFile], output_dir: str):
        """Guarda los archivos extraídos"""
        os.makedirs(output_dir, exist_ok=True)
        
        print(f"\n=== GUARDANDO ARCHIVOS EN {output_dir} ===")
        
        for i, file_obj in enumerate(files):
            # Crear nombre de archivo seguro
            safe_filename = file_obj.filename.replace('/', '_').replace('\\', '_').replace('?', '_')
            
            # Si no tiene extensión, añadir .bin o detectar tipo
            if '.' not in safe_filename:
                if self.looks_like_text(file_obj.data):
                    safe_filename += ".txt"
                else:
                    safe_filename += ".bin"
            
            # Evitar duplicados
            filepath = os.path.join(output_dir, f"s{file_obj.sector:03d}_{safe_filename}")
            
            try:
                with open(filepath, 'wb') as f:
                    f.write(file_obj.data)
                print(f"  Guardado: {filepath} ({file_obj.size} bytes)")
            except Exception as e:
                print(f"  Error guardando {filepath}: {e}")
    
    def looks_like_text(self, data: bytes) -> bool:
        """Determina si los datos parecen texto"""
        if len(data) == 0:
            return False
        
        printable_count = sum(1 for b in data if 32 <= b <= 126 or b in [9, 10, 13])
        return printable_count / len(data) > 0.7
    
    def extract_all(self, output_dir: str = "extracted_direct"):
        """Rutina principal de extracción"""
        if not self.load_image():
            return False
        
        print("=== EXTRACTOR DIRECTO DE ARCHIVOS PDP-8 ===")
        
        # Búsqueda de archivos de un solo sector
        single_files = self.scan_for_files()
        
        # Búsqueda de archivos multi-sector
        multi_files = self.extract_multi_sector_files()
        
        # Combinar y eliminar duplicados
        all_files = []
        seen_sectors = set()
        
        # Priorizar archivos multi-sector
        for file_obj in multi_files:
            if file_obj.sector not in seen_sectors:
                all_files.append(file_obj)
                seen_sectors.add(file_obj.sector)
        
        # Añadir archivos de un solo sector que no estén ya incluidos
        for file_obj in single_files:
            if file_obj.sector not in seen_sectors:
                all_files.append(file_obj)
                seen_sectors.add(file_obj.sector)
        
        if not all_files:
            print("No se encontraron archivos para extraer")
            return False
        
        # Guardar archivos
        self.save_files(all_files, output_dir)
        
        print(f"\n=== RESUMEN ===")
        print(f"Archivos extraídos: {len(all_files)}")
        print(f"Directorio de salida: {output_dir}")
        
        # Listar archivos extraídos
        print(f"\n=== ARCHIVOS EXTRAÍDOS ===")
        for file_obj in sorted(all_files, key=lambda x: x.sector):
            file_type = "texto" if self.looks_like_text(file_obj.data) else "binario"
            print(f"  Sector {file_obj.sector:3d}: {file_obj.filename:<12} {file_obj.size:4d} bytes ({file_type})")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Uso: python extract_direct_files.py <imagen_disco>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Archivo {image_path} no encontrado")
        sys.exit(1)
    
    extractor = DirectFileExtractor(image_path)
    
    if extractor.extract_all():
        print("\n¡Extracción exitosa!")
    else:
        print("\nExtracción falló!")
        sys.exit(1)

if __name__ == "__main__":
    main()
