#!/usr/bin/env python3
"""
Extractor Final OS/8
===================

Combina todos los métodos descubiertos para extraer el máximo contenido
posible de las imágenes OS/8 locales.
"""

import struct
import sys
import os
from typing import List, Tuple, Optional, Dict, Set
from dataclasses import dataclass
from collections import defaultdict

@dataclass
class OS8File:
    """Archivo encontrado"""
    name: str
    extension: str
    length: int = 0
    location: str = ""
    method: str = ""
    confidence: float = 0.0
    raw_data: bytes = b''
    
    @property
    def full_name(self) -> str:
        if self.extension:
            return f"{self.name}.{self.extension}"
        return self.name

class FinalOS8Extractor:
    """Extractor que combina todos los métodos"""
    
    def __init__(self, image_path: str):
        self.image_path = image_path
        self.BYTES_PER_SECTOR = 128
        self.SECTORS_PER_TRACK = 26
        
        with open(image_path, 'rb') as f:
            self.disk_data = f.read()
        
        print(f"Extractor Final OS/8")
        print(f"Imagen: {len(self.disk_data)} bytes")
        print(f"Aplicando todos los métodos descubiertos...")
    
    def method1_bit_decode(self) -> List[OS8File]:
        """Método 1: Decodificación de bits altos"""
        print("\nMétodo 1: Buscando texto con bits altos...")
        files = []
        
        # Buscar secuencias de 3-8 bytes en rango 0x80-0xFF
        for i in range(len(self.disk_data) - 8):
            chunk = self.disk_data[i:i+8]
            
            # Buscar secuencias donde la mayoría de bytes tienen bit alto
            high_bit_count = sum(1 for b in chunk if b >= 0x80)
            
            if high_bit_count >= 4:  # Al menos 4 bytes con bit alto
                # Intentar decodificar
                decoded_chars = []
                for b in chunk:
                    if b >= 0x80:
                        char = chr(b & 0x7F)  # Quitar bit alto
                        if char.isalpha():
                            decoded_chars.append(char)
                        else:
                            break
                    elif 32 <= b <= 126:
                        decoded_chars.append(chr(b))
                    else:
                        break
                
                if len(decoded_chars) >= 3:
                    text = ''.join(decoded_chars)
                    if text.isalpha() and len(text) <= 8:
                        # Podría ser un nombre de archivo
                        sector = i // self.BYTES_PER_SECTOR
                        track = sector // self.SECTORS_PER_TRACK
                        sect = (sector % self.SECTORS_PER_TRACK) + 1
                        
                        files.append(OS8File(
                            name=text.upper(),
                            extension="", 
                            location=f"T{track}/S{sect}",
                            method="BitDecode",
                            confidence=0.6,
                            raw_data=chunk
                        ))
        
        return files[:20]  # Limitar resultados
    
    def method2_pattern_search(self) -> List[OS8File]:
        """Método 2: Búsqueda de patrones conocidos"""
        print("\nMétodo 2: Buscando patrones conocidos de OS/8...")
        files = []
        
        # Patrones a buscar (nombres de archivos OS/8 en diferentes codificaciones)
        os8_names = ['ABSLDR', 'BASIC', 'BATCH', 'CCL', 'DIRECT', 'EDIT', 'F4', 
                     'FORLIB', 'FOTP', 'FRTS', 'HELP', 'LIST', 'LOAD', 'PASS2', 
                     'PASS3', 'PIP', 'RALF', 'RXCOPY', 'SET']
        
        for name in os8_names:
            # Buscar como ASCII normal
            name_bytes = name.encode('ascii')
            pos = self.disk_data.find(name_bytes)
            if pos >= 0:
                sector = pos // self.BYTES_PER_SECTOR
                track = sector // self.SECTORS_PER_TRACK
                sect = (sector % self.SECTORS_PER_TRACK) + 1
                
                files.append(OS8File(
                    name=name,
                    extension="SV",  # Asumir .SV por defecto
                    location=f"T{track}/S{sect}",
                    method="PatternASCII",
                    confidence=0.9
                ))
            
            # Buscar con bit alto puesto
            name_high_bytes = bytes([ord(c) | 0x80 for c in name])
            pos = self.disk_data.find(name_high_bytes)
            if pos >= 0:
                sector = pos // self.BYTES_PER_SECTOR
                track = sector // self.SECTORS_PER_TRACK
                sect = (sector % self.SECTORS_PER_TRACK) + 1
                
                files.append(OS8File(
                    name=name,
                    extension="SV",
                    location=f"T{track}/S{sect}",
                    method="PatternHighBit",
                    confidence=0.8
                ))
        
        return files
    
    def method3_word_analysis(self) -> List[OS8File]:
        """Método 3: Análisis de palabras de 12 bits"""
        print("\nMétodo 3: Analizando palabras de 12 bits...")
        files = []
        
        # Buscar en sectores que no sean principalmente '@' o 0xE5
        interesting_sectors = self.find_data_sectors()
        
        for sector_info in interesting_sectors[:10]:  # Primeros 10 sectores
            track, sect, score = sector_info
            sector_idx = (track * self.SECTORS_PER_TRACK) + (sect - 1)
            start = sector_idx * self.BYTES_PER_SECTOR
            sector_data = self.disk_data[start:start + self.BYTES_PER_SECTOR]
            
            # Analizar como directorio OS/8
            sector_files = self.analyze_sector_as_directory(sector_data, track, sect)
            files.extend(sector_files)
        
        return files
    
    def find_data_sectors(self) -> List[Tuple[int, int, int]]:
        """Encuentra sectores con datos reales"""
        sectors = []
        num_sectors = len(self.disk_data) // self.BYTES_PER_SECTOR
        
        for sector_idx in range(num_sectors):
            start = sector_idx * self.BYTES_PER_SECTOR
            sector_data = self.disk_data[start:start + self.BYTES_PER_SECTOR]
            
            # Calcular score basado en diversidad
            unique_bytes = len(set(sector_data))
            non_zero = sum(1 for b in sector_data if b != 0)
            non_at = sum(1 for b in sector_data if b != 0x40)
            non_e5 = sum(1 for b in sector_data if b != 0xE5)
            
            score = 0
            if unique_bytes > 15: score += 2
            if non_zero > 64: score += 1  
            if non_at > 64: score += 1
            if non_e5 > 64: score += 1
            
            if score >= 3:
                track = sector_idx // self.SECTORS_PER_TRACK
                sect = (sector_idx % self.SECTORS_PER_TRACK) + 1
                sectors.append((track, sect, score))
        
        return sorted(sectors, key=lambda x: x[2], reverse=True)
    
    def analyze_sector_as_directory(self, sector_data: bytes, track: int, sect: int) -> List[OS8File]:
        """Analiza un sector como posible directorio"""
        files = []
        
        # Probar diferentes interpretaciones de entradas de directorio
        for entry_size in [2, 3, 4, 5, 6]:  # Palabras por entrada
            entries_per_sector = (len(sector_data) // 2) // entry_size
            
            for entry_idx in range(min(20, entries_per_sector)):
                base_offset = entry_idx * entry_size * 2
                
                # Leer palabras de la entrada
                words = []
                for word_idx in range(entry_size):
                    word_offset = base_offset + (word_idx * 2)
                    if word_offset + 1 < len(sector_data):
                        word = struct.unpack('<H', sector_data[word_offset:word_offset + 2])[0] & 0o7777
                        words.append(word)
                
                if len(words) >= 2 and any(w != 0 for w in words):
                    # Intentar interpretar como archivo
                    file_entry = self.interpret_words_as_file(words, track, sect, entry_size)
                    if file_entry:
                        files.append(file_entry)
        
        return files
    
    def interpret_words_as_file(self, words: List[int], track: int, sect: int, entry_size: int) -> Optional[OS8File]:
        """Interpreta secuencia de palabras como archivo"""
        if len(words) < 2:
            return None
        
        # Múltiples intentos de decodificación
        decodings = []
        
        # RAD50
        name_rad50 = self.decode_rad50(words[0])
        ext_rad50 = self.decode_rad50(words[1])
        if name_rad50 and ext_rad50:
            decodings.append(("RAD50", name_rad50, ext_rad50))
        
        # SIXBIT
        name_sixbit = self.decode_sixbit(words[0])
        ext_sixbit = self.decode_sixbit(words[1])
        if name_sixbit and ext_sixbit:
            decodings.append(("SIXBIT", name_sixbit, ext_sixbit))
        
        # ASCII directo
        name_ascii = self.decode_ascii_word(words[0])
        ext_ascii = self.decode_ascii_word(words[1])
        if name_ascii and ext_ascii:
            decodings.append(("ASCII", name_ascii, ext_ascii))
        
        # Evaluar decodificaciones
        for method, name, ext in decodings:
            name = name.strip().upper()
            ext = ext.strip().upper()
            
            if (len(name) >= 3 and len(name) <= 8 and name.isalpha() and
                len(ext) >= 2 and len(ext) <= 3 and ext.isalpha()):
                
                # Calcular confianza
                confidence = self.calculate_file_confidence(name, ext, words[2:], method)
                
                if confidence > 0.4:
                    length = words[2] if len(words) > 2 and words[2] < 1000 else 0
                    
                    return OS8File(
                        name=name,
                        extension=ext,
                        length=length,
                        location=f"T{track}/S{sect}",
                        method=f"{method}-{entry_size}w",
                        confidence=confidence
                    )
        
        return None
    
    def decode_rad50(self, word: int) -> Optional[str]:
        """Decodifica RAD50"""
        try:
            chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ$.0123456789"
            result = ""
            for _ in range(3):
                char_code = word % 40
                word = word // 40
                if char_code < len(chars):
                    result = chars[char_code] + result
                else:
                    result = " " + result
            return result.strip() if len(result.strip()) >= 2 else None
        except:
            return None
    
    def decode_sixbit(self, word: int) -> Optional[str]:
        """Decodifica SIXBIT"""
        try:
            chars = " ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789+-.,:;!?&$=*()/"
            result = ""
            for i in range(2):
                char_code = (word >> (6 * (1 - i))) & 0o77
                if char_code < len(chars):
                    result += chars[char_code]
                else:
                    result += " "
            return result.strip() if len(result.strip()) >= 2 else None
        except:
            return None
    
    def decode_ascii_word(self, word: int) -> Optional[str]:
        """Decodifica palabra como ASCII directo"""
        try:
            low = word & 0xFF
            high = (word >> 8) & 0xFF
            if 32 <= low <= 126 and 32 <= high <= 126:
                return chr(low) + chr(high)
            return None
        except:
            return None
    
    def calculate_file_confidence(self, name: str, ext: str, metadata: List[int], method: str) -> float:
        """Calcula confianza del archivo"""
        confidence = 0.0
        
        # Nombres conocidos
        known_names = {'ABSLDR', 'BASIC', 'BATCH', 'BCOMP', 'BITMAP', 'BLOAD', 
                      'BOOT', 'BRTS', 'BUILD', 'CCL', 'CREF', 'DIRECT', 'EDIT',
                      'EPIC', 'FBOOT', 'FOTP', 'FUTIL', 'HELP', 'PAL8', 'PIP',
                      'RESEQ', 'RESORC', 'SABR', 'SET', 'TECO', 'F4', 'FORLIB',
                      'FRTS', 'LIST', 'LOAD', 'PASS2', 'PASS3', 'RALF', 'RXCOPY'}
        
        # Extensiones conocidas
        known_exts = {'SV', 'AF', 'FF', 'SF', 'UF', 'BN', 'BA', 'HL', 'RL', 'FL', 'PA', 'SY'}
        
        # Bonificaciones
        if name in known_names: confidence += 0.5
        if ext in known_exts: confidence += 0.3
        if metadata and len(metadata) > 0 and 1 <= metadata[0] <= 200: confidence += 0.2
        if method == "RAD50": confidence += 0.1
        if method == "SIXBIT": confidence += 0.05
        
        return min(confidence, 1.0)
    
    def method4_exhaustive_scan(self) -> List[OS8File]:
        """Método 4: Escaneo exhaustivo de toda la imagen"""
        print("\nMétodo 4: Escaneo exhaustivo...")
        files = []
        
        # Buscar cualquier secuencia que pueda ser un nombre de archivo
        for i in range(0, len(self.disk_data) - 10, 2):  # Cada palabra
            try:
                # Leer 3 palabras consecutivas
                words = []
                for j in range(3):
                    word_offset = i + (j * 2)
                    if word_offset + 1 < len(self.disk_data):
                        word = struct.unpack('<H', self.disk_data[word_offset:word_offset + 2])[0] & 0o7777
                        words.append(word)
                
                if len(words) == 3 and any(w != 0 for w in words):
                    # Intentar como nombre + extensión + longitud
                    name = self.decode_rad50(words[0])
                    ext = self.decode_rad50(words[1])
                    
                    if (name and ext and len(name.strip()) >= 3 and len(ext.strip()) >= 2 and
                        name.strip().isalpha() and ext.strip().isalpha() and words[2] < 200):
                        
                        sector = i // self.BYTES_PER_SECTOR
                        track = sector // self.SECTORS_PER_TRACK
                        sect = (sector % self.SECTORS_PER_TRACK) + 1
                        
                        confidence = self.calculate_file_confidence(name.strip(), ext.strip(), [words[2]], "RAD50")
                        
                        if confidence > 0.5:  # Solo alta confianza para escaneo exhaustivo
                            files.append(OS8File(
                                name=name.strip().upper(),
                                extension=ext.strip().upper(),
                                length=words[2],
                                location=f"T{track}/S{sect}",
                                method="Exhaustive",
                                confidence=confidence
                            ))
                            
            except:
                continue
        
        return files[:10]  # Limitar a 10 mejores resultados
    
    def extract_files(self):
        """Ejecuta todos los métodos de extracción"""
        print("=" * 60)
        print("EXTRACTOR FINAL OS/8 - TODOS LOS MÉTODOS")
        print("=" * 60)
        
        all_files = []
        
        # Ejecutar todos los métodos
        methods = [
            ("Decodificación de bits", self.method1_bit_decode),
            ("Patrones conocidos", self.method2_pattern_search), 
            ("Análisis de palabras", self.method3_word_analysis),
            ("Escaneo exhaustivo", self.method4_exhaustive_scan)
        ]
        
        for method_name, method_func in methods:
            try:
                method_files = method_func()
                all_files.extend(method_files)
                print(f"{method_name}: {len(method_files)} archivos encontrados")
            except Exception as e:
                print(f"{method_name}: Error - {e}")
        
        # Eliminar duplicados por nombre completo, manteniendo el de mayor confianza
        unique_files = {}
        for file in all_files:
            key = file.full_name
            if key not in unique_files or file.confidence > unique_files[key].confidence:
                unique_files[key] = file
        
        final_files = list(unique_files.values())
        final_files = [f for f in final_files if f.confidence >= 0.5]  # Filtro de confianza
        final_files.sort(key=lambda x: x.confidence, reverse=True)
        
        print(f"\n" + "=" * 60)
        print(f"ARCHIVOS FINALES: {len(final_files)}")
        print("=" * 60)
        
        if final_files:
            print("\nArchivos encontrados con alta confianza:")
            print("Name      Ext Length  Location    Method       Conf")
            print("-" * 60)
            
            for file in final_files:
                print(f"{file.name:<8} .{file.extension:<2} {file.length:>6}  {file.location:<10} {file.method:<12} {file.confidence:.2f}")
                
            # Mostrar resumen por método
            print(f"\nResumen por método:")
            method_counts = {}
            for file in final_files:
                method = file.method.split('-')[0]  # Quitar sufijos
                method_counts[method] = method_counts.get(method, 0) + 1
            
            for method, count in method_counts.items():
                print(f"  {method}: {count} archivos")
        else:
            print("\n❌ No se encontraron archivos con suficiente confianza")
            print("\nEsto indica que:")
            print("- La imagen podría estar en un formato no estándar")
            print("- Los archivos podrían estar comprimidos o codificados")  
            print("- La imagen podría estar corrupta o ser de otro sistema")

def main():
    if len(sys.argv) != 2:
        print("Uso: python final_os8_extractor.py <imagen>")
        sys.exit(1)
    
    extractor = FinalOS8Extractor(sys.argv[1])
    extractor.extract_files()

if __name__ == "__main__":
    main()
