#!/usr/bin/env python3
"""
Decodificador específico para el formato encontrado en la imagen RX01
"""

import struct
import sys

def decode_rx01_format(image_file):
    """Decodifica el formato específico de la imagen RX01"""
    
    with open(image_file, 'rb') as f:
        file_size = f.seek(0, 2)
        f.seek(0)
        
        print(f"📁 Decodificando formato RX01: {image_file}")
        print(f"📏 Tamaño: {file_size} bytes")
        
        # Los bloques 1-6 parecen contener entradas de directorio
        # Patrón observado: C4 C4 D9 F1 40 C4 C1 E3 C1 ...
        
        print(f"\n🔍 Analizando bloques de directorio:")
        
        directory_entries = []
        
        # Analizar bloques que parecen tener entradas
        for block_num in range(1, 7):
            offset = block_num * 512
            f.seek(offset)
            block_data = f.read(512)
            
            print(f"\n📊 Bloque {block_num}:")
            
            # Mostrar primeros bytes como hex y ASCII
            print_detailed_analysis(block_data[:32], f"   Bloque {block_num}")
            
            # Intentar decodificar como entrada de directorio
            entry = decode_directory_entry(block_data)
            if entry:
                directory_entries.append(entry)
                print(f"   ✅ Entrada: {entry}")
        
        print(f"\n📋 Resumen de entradas encontradas:")
        print(f"{'#':<3} {'Nombre':<12} {'Extensión':<4} {'Info'}")
        print(f"{'-'*3} {'-'*12} {'-'*4} {'-'*20}")
        
        for i, entry in enumerate(directory_entries):
            print(f"{i+1:3d} {entry.get('name', 'N/A'):<12} {entry.get('ext', 'N/A'):<4} {entry.get('info', '')}")
        
        # Buscar bloque 0 que podría tener información del directorio
        print(f"\n🔍 Analizando bloque 0 (posible bootstrap/info):")
        f.seek(0)
        block0 = f.read(512)
        
        # El bloque 0 está lleno de 0x40 ('@'), que podría ser padding
        # Vamos a buscar el directorio real en otro lugar
        
        # Los archivos pueden empezar en bloque 7+
        print(f"\n📂 Buscando contenido de archivos (bloque 7+):")
        f.seek(7 * 512)
        file_content = f.read(512)
        
        print(f"   Primeros 64 bytes del bloque 7:")
        print_hex_dump(file_content[:64], "   ")
        
        # Buscar texto ASCII recognizable
        ascii_content = extract_ascii_strings(file_content)
        if ascii_content:
            print(f"   📝 Contenido ASCII encontrado:")
            for line in ascii_content[:5]:  # Mostrar hasta 5 líneas
                print(f"      '{line}'")

def decode_directory_entry(block_data):
    """Intenta decodificar una entrada de directorio del formato específico"""
    
    # Los patrones que vemos son consistentes:
    # C4 C4 D9 F1 40 C4 C1 E3 C1 [XX XX] 40 40 40 40 40
    
    if len(block_data) < 32:
        return None
    
    # Convertir primeros bytes a caracteres para ver si hay un patrón
    chars = []
    for i in range(16):
        b = block_data[i]
        if 0x40 <= b <= 0xFF:  # Rango ASCII extendido típico de DEC
            # Convertir del código DEC/SIXBIT a ASCII
            if b == 0x40:
                chars.append(' ')
            elif 0x41 <= b <= 0x5A:  # A-Z
                chars.append(chr(b))
            elif 0xC1 <= b <= 0xDA:  # a-z en algunos códigos DEC
                chars.append(chr(b - 0x80))
            elif 0xF0 <= b <= 0xF9:  # 0-9 en algunos códigos DEC
                chars.append(chr(b - 0xF0 + ord('0')))
            else:
                chars.append('?')
        else:
            chars.append('.')
    
    name_part = ''.join(chars[:8]).strip()
    ext_part = ''.join(chars[8:12]).strip()
    
    # Buscar patrones específicos que indiquen nombres de archivo
    if len(name_part) > 1 and not all(c in ' .?' for c in name_part):
        # Los bytes siguientes podrían ser longitud, fecha, etc.
        info_bytes = block_data[16:20]
        
        return {
            'name': name_part,
            'ext': ext_part,
            'info': f"info_bytes: {' '.join(f'{b:02X}' for b in info_bytes)}",
            'raw_start': ' '.join(f'{b:02X}' for b in block_data[:16])
        }
    
    return None

def print_detailed_analysis(data, label):
    """Imprime análisis detallado de los datos"""
    
    print(f"{label} - Hex: {' '.join(f'{b:02X}' for b in data)}")
    
    # Intentar varias interpretaciones de caracteres
    ascii_chars = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in data)
    print(f"{label} - ASCII: '{ascii_chars}'")
    
    # Interpretación DEC/SIXBIT
    dec_chars = []
    for b in data:
        if b == 0x40:
            dec_chars.append(' ')
        elif 0x41 <= b <= 0x5A:  # A-Z mayúsculas 
            dec_chars.append(chr(b))
        elif 0xC1 <= b <= 0xDA:  # Posible a-z en formato DEC
            dec_chars.append(chr(b - 0x80))
        elif 0xF0 <= b <= 0xF9:  # Posible 0-9 en formato DEC
            dec_chars.append(chr(b - 0xF0 + ord('0')))
        else:
            dec_chars.append('.')
    
    dec_text = ''.join(dec_chars)
    print(f"{label} - DEC: '{dec_text}'")

def extract_ascii_strings(data):
    """Extrae strings ASCII legibles de los datos"""
    
    strings = []
    current_string = ""
    
    for b in data:
        if 32 <= b <= 126:  # Caracteres ASCII imprimibles
            current_string += chr(b)
        else:
            if len(current_string) >= 3:  # Strings de al menos 3 caracteres
                strings.append(current_string)
            current_string = ""
    
    # Agregar último string si existe
    if len(current_string) >= 3:
        strings.append(current_string)
    
    return strings

def print_hex_dump(data, prefix=""):
    """Imprime dump hexadecimal con prefijo"""
    for i in range(0, len(data), 16):
        chunk = data[i:i+16]
        hex_str = ' '.join(f'{b:02X}' for b in chunk)
        ascii_str = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in chunk)
        print(f"{prefix}{i:04X}: {hex_str:<47} {ascii_str}")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 decode_rx01_format.py <archivo_imagen>")
        sys.exit(1)
    
    decode_rx01_format(sys.argv[1])
