#!/usr/bin/env python3
"""
Busca el bloque de directorio OS/8 en toda la imagen
"""

import struct
import sys

def find_directory_block(image_file):
    """Busca el bloque de directorio en toda la imagen"""
    
    with open(image_file, 'rb') as f:
        file_size = f.seek(0, 2)
        f.seek(0)
        
        print(f"📁 Buscando directorio en: {image_file}")
        print(f"📏 Tamaño: {file_size} bytes")
        
        # Tamaño de bloque para RX01 podría ser 256 o 512 bytes
        for block_size in [256, 512, 128]:
            print(f"\n🔍 Probando tamaño de bloque: {block_size} bytes")
            
            num_blocks = file_size // block_size
            print(f"   Total de bloques: {num_blocks}")
            
            # Buscar en los primeros 10 bloques
            for block_num in range(min(10, num_blocks)):
                f.seek(block_num * block_size)
                block_data = f.read(block_size)
                
                if len(block_data) < block_size:
                    continue
                
                # Intentar interpretar como directorio OS/8
                if block_size == 256:
                    words = struct.unpack('<128H', block_data)
                elif block_size == 512:
                    words = struct.unpack('<256H', block_data)
                else:  # 128 bytes
                    words = struct.unpack('<64H', block_data)
                
                # Verificar si parece un bloque home OS/8
                if is_plausible_os8_home(words):
                    print(f"\n✅ Posible directorio encontrado en bloque {block_num} (tamaño {block_size}):")
                    analyze_directory_block(words, block_num, block_size)
                    
                    # También mostrar dump hex
                    print(f"\n📄 Dump hexadecimal (primeros 64 bytes):")
                    print_hex_dump(block_data[:64])

def is_plausible_os8_home(words):
    """Verifica si las words parecen un bloque home OS/8 válido"""
    if len(words) < 10:
        return False
        
    num_entries = words[0] & 0x7FFF
    empty_start = words[1]
    next_segment = words[2]
    info_words_raw = words[4]
    info_words = (~info_words_raw + 1) & 0x7FFF if info_words_raw & 0x8000 else info_words_raw
    
    # Criterios razonables para OS/8
    return (
        1 <= num_entries <= 50 and           # Número razonable de archivos
        5 <= empty_start <= 500 and         # Área vacía en lugar razonable
        (next_segment == 0 or next_segment < 100) and  # Siguiente segmento razonable
        0 <= info_words <= 5                # Info words razonable
    )

def analyze_directory_block(words, block_num, block_size):
    """Analiza un bloque que parece ser directorio OS/8"""
    
    num_entries = words[0] & 0x7FFF
    empty_start = words[1]
    next_segment = words[2]
    tentative = words[3]
    info_words_raw = words[4]
    info_words = (~info_words_raw + 1) & 0x7FFF if info_words_raw & 0x8000 else info_words_raw
    
    print(f"   📊 Estadísticas del directorio:")
    print(f"      Entradas: {num_entries}")
    print(f"      Área vacía en bloque: {empty_start}")
    print(f"      Siguiente segmento: {next_segment}")
    print(f"      Archivo tentativo: {tentative}")
    print(f"      Palabras info: {info_words}")
    
    # Analizar algunas entradas
    entry_size = 6 + info_words
    print(f"\n   📂 Primeras entradas (tamaño {entry_size} words):")
    
    dir_offset = 5  # Las entradas empiezan en word 5
    for i in range(min(5, num_entries)):
        if dir_offset + entry_size > len(words):
            break
            
        entry_words = words[dir_offset:dir_offset + entry_size]
        
        file_type = entry_words[0]
        name_words = entry_words[1:4]
        length = entry_words[4]
        job_info = entry_words[5]
        extra = entry_words[6:] if info_words > 0 else []
        
        # Decodificar nombre
        try:
            name = decode_sixbit(name_words)
        except:
            name = "???"
        
        # Decodificar tipo
        type_names = {0: ".EMPTY.", 1: ".FILE.", 2: ".DATA.", 3: ".PROG.", 4: ".ASCII.", 5: ".BINARY."}
        type_str = type_names.get(file_type, f".TYPE{file_type}.")
        
        print(f"      {i+1:2d}. '{name:<12}' {type_str:<10} {length:3d} bloques")
        
        dir_offset += entry_size

def decode_sixbit(words):
    """Decodifica nombre SIXBIT"""
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

def print_hex_dump(data):
    """Imprime dump hexadecimal"""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"      {i:04X}: {hex_str:<47} {ascii_str}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 find_directory.py <archivo_imagen>")
        sys.exit(1)
    
    find_directory_block(sys.argv[1])
