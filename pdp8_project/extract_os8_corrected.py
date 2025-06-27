#!/usr/bin/env python3
"""
Extractor OS/8 Corregido
Basado en el análisis de PUTR.ASM y decodificación SIXBIT
"""

import struct
import os
import sys
from typing import List, Tuple, Optional
from dataclasses import dataclass

@dataclass
class OS8File:
    """Representa un archivo OS/8"""
    filename: str
    extension: str
    start_block: int
    length: int
    is_empty: bool = False

class OS8Extractor:
    """Extractor OS/8 con interleave correcto y decodificación SIXBIT"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.image_data = None
        self.sector_size = 128
        self.sectors_per_track = 26
        self.files = []
        
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
    
    def rx01_interleave(self, logical_sector: int, track: int = 0) -> int:
        """
        Aplica interleave RX01 basado en PUTR.ASM
        Para PDP-8: 2:1 interleave, sin skew
        """
        # PUTR: ISEC=(ISEC-1)*2, IF(ISEC.GE.26) ISEC=ISEC-25
        physical_sector = (logical_sector * 2) % self.sectors_per_track
        return physical_sector
    
    def read_sector(self, logical_sector: int, apply_interleave: bool = True) -> Optional[bytes]:
        """Lee un sector lógico, aplicando interleave si se especifica"""
        if apply_interleave:
            physical_sector = self.rx01_interleave(logical_sector)
        else:
            physical_sector = logical_sector
        
        offset = physical_sector * self.sector_size
        
        if offset + self.sector_size > len(self.image_data):
            return None
        
        return self.image_data[offset:offset + self.sector_size]
    
    def bytes_to_12bit_words(self, data: bytes) -> List[int]:
        """Convierte bytes a palabras de 12 bits (formato PDP-8)"""
        words = []
        i = 0
        while i + 2 < len(data):
            # Combina 3 bytes en 2 palabras de 12 bits
            w1 = data[i] | ((data[i+1] & 0x0F) << 8)
            w2 = (data[i+1] >> 4) | (data[i+2] << 4)
            words.extend([w1 & 0xFFF, w2 & 0xFFF])
            i += 3
        return words
    
    def decode_sixbit_filename(self, words: List[int]) -> Tuple[str, str]:
        """
        Decodifica nombre de archivo OS/8 usando SIXBIT
        OS/8 empaqueta 2 caracteres por palabra, 6 bits cada uno
        """
        chars = []
        
        # Primeras 4 palabras contienen el nombre del archivo (8 caracteres max)
        for word in words[:4]:
            char1 = (word >> 6) & 0o77  # 6 bits superiores
            char2 = word & 0o77         # 6 bits inferiores
            
            # Convertir a SIXBIT: añadir 0x40 para obtener ASCII
            if char1 >= 1:  # Skip si es 0 (padding)
                c1 = chr((char1 & 0x3F) + 0x40) if char1 != 0 else ' '
                chars.append(c1)
            if char2 >= 1:
                c2 = chr((char2 & 0x3F) + 0x40) if char2 != 0 else ' '
                chars.append(c2)
        
        filename = ''.join(chars).strip()
        
        # Palabra 4 contiene la extensión
        if len(words) > 4:
            ext_word = words[4]
            ext_char1 = (ext_word >> 6) & 0o77
            ext_char2 = ext_word & 0o77
            
            ext_chars = []
            if ext_char1 >= 1:
                ext_chars.append(chr((ext_char1 & 0x3F) + 0x40))
            if ext_char2 >= 1:
                ext_chars.append(chr((ext_char2 & 0x3F) + 0x40))
            
            extension = ''.join(ext_chars).strip()
        else:
            extension = ""
        
        return filename, extension
    
    def check_os8_directory_header(self, words: List[int]) -> Tuple[bool, dict]:
        """Verifica si las palabras representan un header de directorio OS/8 válido"""
        if len(words) < 5:
            return False, {}
        
        # Header del directorio OS/8:
        # Palabra 0: -(número de entradas)
        # Palabra 1: siguiente segmento de directorio (0 si es el último)
        # Palabra 2: número de bloque inicial
        # Palabra 3: -(palabras de información adicional)
        # Palabra 4: unused/reserved
        
        num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
        next_segment = words[1] & 0xFFF
        start_block = words[2] & 0xFFF
        info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
        
        info = {
            'entries': num_entries,
            'next_segment': next_segment,
            'start_block': start_block,
            'info_words': info_words,
            'raw_header': words[:5]
        }
        
        # Validación razonable para OS/8
        valid = (
            1 <= num_entries <= 50 and      # Número razonable de entradas
            0 <= next_segment <= 6 and      # Máximo 6 segmentos de directorio
            7 <= start_block <= 2000 and    # Bloque de inicio razonable (archivos empiezan después del directorio)
            0 <= info_words <= 3             # Pocas palabras de información adicional
        )
        
        return valid, info
    
    def find_os8_directory(self) -> Tuple[bool, int, bool]:
        """
        Busca el directorio OS/8 en el disco
        Retorna: (encontrado, sector, con_interleave)
        """
        print("Buscando directorio OS/8...")
        
        # Buscar en más sectores y con criterios menos estrictos
        for logical_sector in range(0, 30):  # Expandir búsqueda
            for apply_interleave in [True, False]:
                sector_data = self.read_sector(logical_sector, apply_interleave)
                if not sector_data:
                    continue
                
                # Saltar sectores que son principalmente espacios
                if len(set(sector_data[:64])) <= 2:
                    continue
                
                words = self.bytes_to_12bit_words(sector_data)
                valid, info = self.check_os8_directory_header(words)
                
                interleave_str = "con interleave" if apply_interleave else "sin interleave"
                
                # Debug: mostrar sectores interesantes aunque no sean válidos
                if len(words) >= 5:
                    print(f"Sector {logical_sector} ({interleave_str}): "
                          f"entries={info.get('entries', 'N/A')}, "
                          f"next={info.get('next_segment', 'N/A')}, "
                          f"start={info.get('start_block', 'N/A')}, "
                          f"info={info.get('info_words', 'N/A')} -> {'VÁLIDO' if valid else 'inválido'}")
                
                if valid:
                    print(f"¡Directorio OS/8 encontrado en sector lógico {logical_sector} ({interleave_str})!")
                    print(f"  Entradas: {info['entries']}")
                    print(f"  Siguiente segmento: {info['next_segment']}")
                    print(f"  Bloque inicial: {info['start_block']}")
                    print(f"  Palabras info: {info['info_words']}")
                    return True, logical_sector, apply_interleave
        
        print("Directorio OS/8 no encontrado. Intentando con criterios más flexibles...")
        
        # Segunda pasada con criterios más flexibles
        for logical_sector in range(0, 30):
            for apply_interleave in [True, False]:
                sector_data = self.read_sector(logical_sector, apply_interleave)
                if not sector_data or len(set(sector_data[:64])) <= 2:
                    continue
                
                words = self.bytes_to_12bit_words(sector_data)
                if len(words) < 5:
                    continue
                
                # Criterios más flexibles
                num_entries = (0o10000 - words[0]) & 0xFFF if words[0] != 0 else 0
                next_segment = words[1] & 0xFFF
                start_block = words[2] & 0xFFF
                info_words = (0o10000 - words[3]) & 0xFFF if words[3] != 0 else 0
                
                # Validación más flexible
                flexible_valid = (
                    1 <= num_entries <= 100 and     # Más entradas permitidas
                    0 <= next_segment <= 10 and     # Más segmentos
                    1 <= start_block <= 3000 and    # Rango más amplio
                    0 <= info_words <= 10           # Más palabras de info
                )
                
                if flexible_valid:
                    interleave_str = "con interleave" if apply_interleave else "sin interleave"
                    print(f"\n*** DIRECTORIO ENCONTRADO CON CRITERIOS FLEXIBLES ***")
                    print(f"Sector {logical_sector} ({interleave_str}):")
                    print(f"  Entradas: {num_entries}")
                    print(f"  Siguiente segmento: {next_segment}")
                    print(f"  Bloque inicial: {start_block}")
                    print(f"  Palabras info: {info_words}")
                    
                    info = {
                        'entries': num_entries,
                        'next_segment': next_segment,
                        'start_block': start_block,
                        'info_words': info_words,
                        'raw_header': words[:5]
                    }
                    
                    return True, logical_sector, apply_interleave
        
        print("\n=== TERCERA PASADA: INTERPRETACIÓN 16-BIT ===")
        # Intentar interpretar como palabras de 16-bit en lugar de 12-bit
        for logical_sector in range(0, 30):
            for apply_interleave in [True, False]:
                sector_data = self.read_sector(logical_sector, apply_interleave)
                if not sector_data or len(set(sector_data[:64])) <= 2:
                    continue
                
                # Interpretar como palabras de 16-bit little endian
                words_16 = []
                for i in range(0, len(sector_data)-1, 2):
                    word = sector_data[i] | (sector_data[i+1] << 8)
                    words_16.append(word & 0xFFF)  # Máscara a 12 bits
                
                if len(words_16) < 5:
                    continue
                
                # Evaluar como directorio OS/8
                num_entries = (0o10000 - words_16[0]) & 0xFFF if words_16[0] != 0 else 0
                next_segment = words_16[1] & 0xFFF
                start_block = words_16[2] & 0xFFF
                info_words = (0o10000 - words_16[3]) & 0xFFF if words_16[3] != 0 else 0
                
                interleave_str = "con interleave" if apply_interleave else "sin interleave"
                print(f"16-bit Sector {logical_sector} ({interleave_str}): "
                      f"entries={num_entries}, next={next_segment}, start={start_block}, info={info_words}")
                
                # Criterios especiales para casos prometedores
                special_valid = (
                    (info_words == 0 and 1 <= num_entries <= 20 and 200 <= start_block <= 500) or
                    (next_segment == 0 and 1 <= num_entries <= 50 and 50 <= start_block <= 1000)
                )
                
                if special_valid:
                    print(f"\n*** DIRECTORIO ENCONTRADO (16-BIT) ***")
                    print(f"Sector {logical_sector} ({interleave_str}):")
                    print(f"  Entradas: {num_entries}")
                    print(f"  Siguiente segmento: {next_segment}")
                    print(f"  Bloque inicial: {start_block}")
                    print(f"  Palabras info: {info_words}")
                    
                    # Crear el objeto info con el formato correcto
                    info = {
                        'entries': num_entries,
                        'next_segment': next_segment,
                        'start_block': start_block,
                        'info_words': info_words,
                        'raw_header': words_16[:5]
                    }
                    
                    # Usar el método 16-bit temporalmente
                    self._use_16bit_words = True
                    return True, logical_sector, apply_interleave
        
        print("Directorio OS/8 no encontrado ni con criterios flexibles")
        return False, 0, False
    
    def parse_os8_directory(self, start_sector: int, use_interleave: bool) -> List[OS8File]:
        """Parsea el directorio OS/8 completo"""
        files = []
        current_sector = start_sector
        current_file_block = 0
        
        while current_sector > 0:
            print(f"Leyendo segmento de directorio en sector {current_sector}")
            
            sector_data = self.read_sector(current_sector, use_interleave)
            if not sector_data:
                break
            
            words = self.bytes_to_12bit_words(sector_data)
            valid, info = self.check_os8_directory_header(words)
            
            if not valid:
                print(f"Header de directorio inválido en sector {current_sector}")
                break
            
            # Si es el primer segmento, usar start_block del header
            if current_file_block == 0:
                current_file_block = info['start_block']
            
            # Parsear entradas de archivo
            entry_start = 5  # Después del header
            for entry_num in range(info['entries']):
                entry_offset = entry_start + entry_num * (6 + info['info_words'])
                
                if entry_offset + 5 + info['info_words'] >= len(words):
                    break
                
                # Comprobar si es entrada vacía
                if words[entry_offset] == 0:
                    file_entry = OS8File(
                        filename="<EMPTY>",
                        extension="",
                        start_block=0,
                        length=0,
                        is_empty=True
                    )
                else:
                    # Extraer nombre de archivo
                    filename_words = words[entry_offset:entry_offset + 5]
                    filename, extension = self.decode_sixbit_filename(filename_words)
                    
                    # Saltar palabras de información
                    length_offset = entry_offset + 5 + info['info_words']
                    
                    # Obtener longitud del archivo
                    if length_offset < len(words):
                        length_word = words[length_offset]
                        file_length = (0o10000 - length_word) & 0xFFF if length_word != 0 else 0
                    else:
                        file_length = 0
                    
                    file_entry = OS8File(
                        filename=filename,
                        extension=extension,
                        start_block=current_file_block,
                        length=file_length
                    )
                    
                    current_file_block += file_length
                
                files.append(file_entry)
                
                if not file_entry.is_empty:
                    print(f"  Archivo: {file_entry.filename}.{file_entry.extension} "
                          f"(bloque {file_entry.start_block}, {file_entry.length} bloques)")
            
            # Siguiente segmento
            current_sector = info['next_segment']
        
        return files
    
    def extract_file(self, file_info: OS8File, output_dir: str, use_interleave: bool) -> bool:
        """Extrae un archivo individual"""
        if file_info.is_empty or file_info.length == 0:
            return False
        
        try:
            # Crear nombre de archivo seguro
            if file_info.extension:
                filename = f"{file_info.filename}.{file_info.extension}"
            else:
                filename = file_info.filename
            
            # Reemplazar caracteres problemáticos
            filename = filename.replace('/', '_').replace('\\', '_').replace('?', '_')
            filepath = os.path.join(output_dir, filename)
            
            print(f"Extrayendo {filename}...")
            
            with open(filepath, 'wb') as f:
                for block_num in range(file_info.start_block, file_info.start_block + file_info.length):
                    # Convertir número de bloque a sector
                    # En OS/8, cada bloque = 1 sector de 128 bytes
                    block_data = self.read_sector(block_num, use_interleave)
                    if block_data:
                        f.write(block_data)
                    else:
                        print(f"  Advertencia: No se pudo leer el bloque {block_num}")
            
            print(f"  Extraído: {filename} ({file_info.length} bloques)")
            return True
            
        except Exception as e:
            print(f"Error extrayendo {file_info.filename}: {e}")
            return False
    
    def extract_all(self, output_dir: str = "extracted_os8_corrected") -> bool:
        """Rutina principal de extracción"""
        if not self.load_image():
            return False
        
        # Crear directorio de salida
        os.makedirs(output_dir, exist_ok=True)
        
        # Buscar directorio OS/8
        found, dir_sector, use_interleave = self.find_os8_directory()
        if not found:
            print("Error: No se encontró directorio OS/8 válido")
            return False
        
        # Parsear directorio
        self.files = self.parse_os8_directory(dir_sector, use_interleave)
        
        if not self.files:
            print("Error: No se encontraron archivos en el directorio")
            return False
        
        print(f"\nEncontrados {len(self.files)} archivos")
        
        # Extraer archivos
        extracted_count = 0
        for file_info in self.files:
            if not file_info.is_empty and self.extract_file(file_info, output_dir, use_interleave):
                extracted_count += 1
        
        print(f"\n=== EXTRACCIÓN COMPLETADA ===")
        print(f"Archivos extraídos: {extracted_count}")
        print(f"Directorio de salida: {output_dir}")
        print(f"Interleave usado: {'Sí' if use_interleave else 'No'}")
        
        # Mostrar listado final
        print(f"\n=== LISTADO DE ARCHIVOS ===")
        for file_info in self.files:
            if not file_info.is_empty:
                ext_str = f".{file_info.extension}" if file_info.extension else ""
                print(f"{file_info.filename}{ext_str:<10} {file_info.length:>4} bloques")
        
        return True

def main():
    if len(sys.argv) != 2:
        print("Uso: python extract_os8_corrected.py <imagen_disco>")
        sys.exit(1)
    
    image_path = sys.argv[1]
    if not os.path.exists(image_path):
        print(f"Error: Archivo {image_path} no encontrado")
        sys.exit(1)
    
    extractor = OS8Extractor(image_path)
    
    if extractor.extract_all():
        print("\n¡Extracción exitosa!")
    else:
        print("\nExtracción falló!")
        sys.exit(1)

if __name__ == "__main__":
    main()
