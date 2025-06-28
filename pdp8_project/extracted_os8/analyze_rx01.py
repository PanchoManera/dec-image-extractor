#!/usr/bin/env python3
"""
Análisis completo de imagen RX01 OS/8
Basado en las especificaciones reales del RX01
"""

import struct
import sys

def analyze_rx01_image(image_file):
    """Analiza imagen RX01 con geometría correcta"""
    
    with open(image_file, 'rb') as f:
        file_size = f.seek(0, 2)
        f.seek(0)
        
        print(f"📁 Analizando imagen RX01: {image_file}")
        print(f"📏 Tamaño: {file_size} bytes")
        
        # RX01 real: 77 tracks, 1 head, 26 sectors, 128 bytes/sector
        # Total: 77 * 1 * 26 * 128 = 256,256 bytes ✓
        
        tracks = 77
        heads = 1  
        sectors_per_track = 26
        bytes_per_sector = 128
        
        print(f"📀 Geometría RX01:")
        print(f"   Tracks: {tracks}")
        print(f"   Heads: {heads}")
        print(f"   Sectors/track: {sectors_per_track}")
        print(f"   Bytes/sector: {bytes_per_sector}")
        print(f"   Total sectores: {tracks * heads * sectors_per_track}")
        
        # En OS/8, los bloques lógicos son de 256 words = 512 bytes
        # Cada bloque lógico = 4 sectores físicos del RX01
        logical_block_size = 512
        sectors_per_block = logical_block_size // bytes_per_sector  # = 4
        total_logical_blocks = (tracks * heads * sectors_per_track) // sectors_per_block
        
        print(f"\n💾 Geometría lógica OS/8:")
        print(f"   Bytes/bloque lógico: {logical_block_size}")
        print(f"   Sectores/bloque: {sectors_per_block}")
        print(f"   Bloques lógicos totales: {total_logical_blocks}")
        
        # Buscar directorio OS/8 en los primeros bloques lógicos
        print(f"\n🔍 Buscando directorio OS/8...")
        
        for logical_block in range(10):
            # Calcular offset físico
            physical_offset = logical_block * logical_block_size
            
            f.seek(physical_offset)
            block_data = f.read(logical_block_size)
            
            if len(block_data) < logical_block_size:
                continue
                
            print(f"\n📊 Bloque lógico {logical_block} (offset {physical_offset:04X}):")
            
            # Mostrar primeros bytes
            print(f"   Primeros 32 bytes:")
            print_hex_dump(block_data[:32], "   ")
            
            # Interpretar como words de 16-bit
            words = struct.unpack('<256H', block_data)
            
            # Verificar si es directorio OS/8
            if is_os8_directory(words):
                print(f"   ✅ ¡Directorio OS/8 encontrado!")
                analyze_os8_directory(words)
            else:
                # Mostrar interpretación básica
                print(f"   Words 0-4: {[f'{w:04X}' for w in words[:5]]}")
                
                # Buscar patrones ASCII
                ascii_chars = []
                for i in range(0, min(64, len(block_data)), 2):
                    if i+1 < len(block_data):
                        char_pair = block_data[i:i+2]
                        for b in char_pair:
                            if 32 <= b <= 126:
                                ascii_chars.append(chr(b))
                            else:
                                ascii_chars.append('.')
                
                if ascii_chars:
                    ascii_text = ''.join(ascii_chars[:32])
                    print(f"   Texto ASCII: '{ascii_text}'")

def is_os8_directory(words):
    """Verifica si las words parecen un directorio OS/8"""
    if len(words) < 10:
        return False
        
    num_entries = words[0] & 0x7FFF
    empty_start = words[1] 
    next_segment = words[2]
    info_words_raw = words[4]
    
    # Calcular info_words correctamente
    if info_words_raw == 0:
        info_words = 0
    elif info_words_raw & 0x8000:  # Negativo
        info_words = (~info_words_raw + 1) & 0x7FFF
    else:
        info_words = info_words_raw
    
    # Criterios más amplios
    return (
        1 <= num_entries <= 40 and
        7 <= empty_start <= 300 and  # Para RX01, máximo ~494 bloques
        next_segment == 0 and        # Imagen simple
        0 <= info_words <= 3
    )

def analyze_os8_directory(words):
    """Analiza directorio OS/8 encontrado"""
    
    num_entries = words[0] & 0x7FFF
    empty_start = words[1]
    next_segment = words[2] 
    tentative = words[3]
    info_words_raw = words[4]
    
    if info_words_raw == 0:
        info_words = 0
    elif info_words_raw & 0x8000:
        info_words = (~info_words_raw + 1) & 0x7FFF
    else:
        info_words = info_words_raw
    
    print(f"   📂 Directorio OS/8:")
    print(f"      Entradas: {num_entries}")
    print(f"      Área vacía en bloque: {empty_start}")
    print(f"      Siguiente segmento: {next_segment}")
    print(f"      Archivo tentativo: {tentative}")
    print(f"      Info words: {info_words} (raw: {info_words_raw:04X})")
    
    # Listar archivos
    entry_size = 6 + info_words
    dir_offset = 5
    
    print(f"\n   📋 Archivos encontrados:")
    print(f"      {'#':<3} {'Nombre':<12} {'Tipo':<10} {'Tamaño':<6} {'Info'}")
    print(f"      {'-'*3} {'-'*12} {'-'*10} {'-'*6} {'-'*10}")
    
    file_count = 0
    current_block = 7  # Los archivos suelen empezar en bloque 7
    
    for i in range(num_entries):
        if dir_offset + entry_size > len(words):
            break
            
        entry_words = words[dir_offset:dir_offset + entry_size]
        
        file_type = entry_words[0]
        name_words = entry_words[1:4]
        length = entry_words[4]
        job_info = entry_words[5]
        extra = entry_words[6:] if info_words > 0 else []
        
        # Saltar entradas vacías
        if file_type == 0:  # .EMPTY.
            dir_offset += entry_size
            continue
            
        # Decodificar nombre
        try:
            name = decode_sixbit_os8(name_words)
        except:
            name = "???"
            
        # Decodificar tipo
        type_names = {
            0: ".EMPTY.", 1: ".FILE.", 2: ".DATA.", 
            3: ".PROG.", 4: ".ASCII.", 5: ".BINARY."
        }
        type_str = type_names.get(file_type, f".{file_type}.")
        
        # Información adicional
        extra_info = ""
        if extra:
            # Intentar decodificar fecha
            date_word = extra[0]
            if date_word != 0:
                day = date_word & 0x1F
                month = (date_word >> 5) & 0x0F  
                year = (date_word >> 9) & 0x7F
                if day > 0 and month > 0:
                    extra_info = f"{day:02d}/{month:02d}"
        
        print(f"      {i+1:3d} {name:<12} {type_str:<10} {length:6d} {extra_info}")
        
        file_count += 1
        current_block += length
        dir_offset += entry_size
    
    print(f"\n   📊 Resumen: {file_count} archivos, espacio usado hasta bloque ~{current_block}")

def decode_sixbit_os8(words):
    """Decodifica nombre SIXBIT para OS/8"""
    result = ""
    
    for word in words:
        # OS/8 SIXBIT: cada word tiene 2-3 caracteres
        # Extraer caracteres de 6 bits
        c1 = (word >> 10) & 0x3F
        c2 = (word >> 4) & 0x3F
        
        for c in [c1, c2]:
            if c == 0:
                break
            # Mapeo SIXBIT a ASCII
            if c <= 31:
                result += chr(c + ord(' '))
            else:
                result += chr(c + ord('@') - 32)
    
    return result.rstrip()

def print_hex_dump(data, prefix=""):
    """Imprime dump hexadecimal con prefijo"""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{prefix}{i:04X}: {hex_str:<47} {ascii_str}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 analyze_rx01.py <archivo_imagen>")
        sys.exit(1)
    
    analyze_rx01_image(sys.argv[1])
