#!/usr/bin/env python3
"""
Script de diagnóstico para analizar la imagen OS/8 RX01
"""

import struct
import sys

def analyze_home_block(image_file):
    """Analiza el bloque home de la imagen"""
    
    with open(image_file, 'rb') as f:
        # Leer bloque 0 (primer bloque)
        block0 = f.read(512)
        
        # Leer bloque 1 (bloque home típico de OS/8)
        f.seek(512)
        block1 = f.read(512)
        
        print(f"📁 Analizando: {image_file}")
        print(f"📏 Tamaño del archivo: {f.seek(0, 2)} bytes")
        
        print("\n🔍 Bloque 0 (primeros 32 bytes):")
        print_hex_dump(block0[:32])
        
        print("\n🔍 Bloque 1 (bloque home - primeros 32 bytes):")
        print_hex_dump(block1[:32])
        
        # Analizar bloque 1 como palabras de 16-bit
        words = struct.unpack('<256H', block1)
        
        print("\n📊 Interpretación del bloque home (primeras 10 words):")
        for i in range(10):
            print(f"Word {i:2d}: {words[i]:04X} ({words[i]:5d}) {format_word_interpretation(i, words[i])}")
        
        # Probar diferentes interpretaciones
        print("\n🧪 Posibles interpretaciones:")
        
        # Interpretación 1: OS/8 estándar
        print("\n1️⃣  OS/8 estándar (bloque 1):")
        interpret_os8_standard(words)
        
        # Interpretación 2: Big-endian
        words_be = struct.unpack('>256H', block1)
        print("\n2️⃣  Big-endian (bloque 1):")
        interpret_os8_standard(words_be)
        
        # Interpretación 3: Bloque 0 como directorio
        words_block0 = struct.unpack('<256H', block0)
        print("\n3️⃣  Bloque 0 como directorio:")
        interpret_os8_standard(words_block0)

def print_hex_dump(data):
    """Imprime dump hexadecimal de los datos"""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{i:04X}: {hex_str:<47} {ascii_str}")

def format_word_interpretation(index, word):
    """Formatea la interpretación de una word según su posición"""
    interpretations = {
        0: "# entradas en directorio",
        1: "bloque inicial área vacía", 
        2: "siguiente segmento (0=último)",
        3: "archivo tentativo",
        4: "-(# palabras info por entrada)",
        5: "primera entrada - tipo",
        6: "primera entrada - nombre[0]",
        7: "primera entrada - nombre[1]",
        8: "primera entrada - nombre[2]",
        9: "primera entrada - longitud",
    }
    return interpretations.get(index, "")

def interpret_os8_standard(words):
    """Interpreta words como bloque home OS/8 estándar"""
    
    num_entries = words[0] & 0x7FFF
    empty_start = words[1]
    next_segment = words[2]
    tentative = words[3]
    info_words_raw = words[4]
    info_words = (~info_words_raw + 1) & 0x7FFF if info_words_raw & 0x8000 else info_words_raw
    
    print(f"   Entradas: {num_entries}")
    print(f"   Área vacía en bloque: {empty_start}")
    print(f"   Siguiente segmento: {next_segment}")
    print(f"   Archivo tentativo: {tentative}")
    print(f"   Palabras info (raw): {info_words_raw:04X} -> interpretado: {info_words}")
    
    # Verificar si los valores son razonables
    reasonable = (
        0 <= num_entries <= 100 and
        0 <= empty_start <= 1000 and
        0 <= info_words <= 10 and
        next_segment == 0  # Para imagen simple
    )
    
    print(f"   ✅ Razonable: {reasonable}")
    
    if reasonable and num_entries > 0:
        print(f"   📂 Analizando primera entrada:")
        entry_size = 6 + info_words
        if entry_size <= 10:  # Máximo razonable
            entry_start = 5
            entry_words = words[entry_start:entry_start + entry_size]
            
            file_type = entry_words[0]
            name_words = entry_words[1:4]
            length = entry_words[4]
            
            print(f"      Tipo: {file_type}")
            print(f"      Nombre words: {[f'{w:04X}' for w in name_words]}")
            print(f"      Longitud: {length}")
            
            # Intentar decodificar nombre
            try:
                name = decode_sixbit(name_words)
                print(f"      Nombre decodificado: '{name}'")
            except:
                print(f"      Error decodificando nombre")

def decode_sixbit(words):
    """Decodifica nombre SIXBIT simple"""
    result = ""
    for word in words:
        c1 = (word >> 10) & 0x3F
        c2 = (word >> 4) & 0x3F
        
        for c in [c1, c2]:
            if c == 0:
                break
            if c <= 31:
                result += chr(c + ord(' '))
            else:
                result += chr(c + ord('@') - 32)
    return result.rstrip()

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 debug_rx01.py <archivo_imagen>")
        sys.exit(1)
    
    analyze_home_block(sys.argv[1])
