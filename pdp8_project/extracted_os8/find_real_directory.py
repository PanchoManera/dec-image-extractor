#!/usr/bin/env python3
"""
Busca exhaustivamente el directorio OS/8 real en la imagen RX01
Basado en los archivos listados en la web pdp8online.com
"""

import struct
import sys

# Archivos esperados según la web
EXPECTED_FILES = [
    "ABSLDR.SV", "BASIC.AF", "BASIC.FF", "BASIC.SF", "BASIC.SV", 
    "BASIC.UF", "BATCH.SV", "BCOMP.SV", "BITMAP.SV", "BLOAD.SV",
    "BOOT.SV", "BRTS.SV", "BUILD.SV", "CCL.SV", "CREF.SV", 
    "DIRECT.SV", "EABRTS.BN", "ECHO.SV", "EDIT.SV", "EPIC.SV"
]

def find_real_os8_directory(image_file):
    """Busca el directorio OS/8 real escaneando toda la imagen"""
    
    with open(image_file, 'rb') as f:
        file_size = f.seek(0, 2)
        f.seek(0)
        
        print(f"🔍 Buscando directorio OS/8 real en: {image_file}")
        print(f"📏 Tamaño: {file_size} bytes")
        print(f"📂 Buscando archivos como: {', '.join(EXPECTED_FILES[:5])}...")
        
        # Buscar en todos los bloques de 512 bytes
        total_blocks = file_size // 512
        print(f"🔢 Total de bloques a examinar: {total_blocks}")
        
        found_directories = []
        
        for block_num in range(total_blocks):
            f.seek(block_num * 512)
            block_data = f.read(512)
            
            if len(block_data) < 512:
                continue
            
            # Verificar si este bloque podría ser un directorio OS/8
            if is_potential_os8_directory(block_data, block_num):
                directory_info = analyze_os8_directory_block(block_data, block_num)
                if directory_info:
                    found_directories.append(directory_info)
        
        print(f"\n✅ Directorios potenciales encontrados: {len(found_directories)}")
        
        # Analizar cada directorio encontrado
        for i, dir_info in enumerate(found_directories):
            print(f"\n📂 Directorio {i+1} (bloque {dir_info['block']}):")
            print(f"   Entradas: {dir_info['num_entries']}")
            print(f"   Archivos encontrados:")
            
            for j, file_info in enumerate(dir_info['files'][:10]):  # Mostrar hasta 10
                print(f"      {j+1:2d}. {file_info['name']:<12} {file_info['type']:<10} {file_info['size']:3d} bloques")
            
            # Verificar cuántos archivos esperados están presentes
            found_expected = 0
            for file_info in dir_info['files']:
                if file_info['name'] in EXPECTED_FILES:
                    found_expected += 1
            
            print(f"   ✅ Archivos esperados encontrados: {found_expected}/{len(EXPECTED_FILES)}")
            
            if found_expected > 5:  # Si encontramos más de 5 archivos esperados
                print(f"   🎯 ¡Este parece ser el directorio correcto!")
                return dir_info
        
        return None

def is_potential_os8_directory(block_data, block_num):
    """Verifica si un bloque podría ser un directorio OS/8"""
    
    try:
        words = struct.unpack('<256H', block_data)
        
        # Criterios básicos para directorio OS/8
        num_entries = words[0] & 0x7FFF
        empty_start = words[1]
        next_segment = words[2]
        info_words_raw = words[4]
        
        # Calcular info_words
        if info_words_raw == 0:
            info_words = 0
        elif info_words_raw & 0x8000:
            info_words = (~info_words_raw + 1) & 0x7FFF
        else:
            info_words = info_words_raw
        
        # Criterios más flexibles
        if (1 <= num_entries <= 50 and 
            7 <= empty_start <= 500 and
            next_segment == 0 and
            0 <= info_words <= 5):
            
            # Verificar que al menos una entrada parece válida
            entry_size = 6 + info_words
            if entry_size <= 10:  # Tamaño razonable
                first_entry_start = 5
                if first_entry_start + entry_size <= 256:
                    first_type = words[first_entry_start]
                    if 0 <= first_type <= 10:  # Tipo de archivo razonable
                        return True
        
        return False
        
    except:
        return False

def analyze_os8_directory_block(block_data, block_num):
    """Analiza un bloque que parece ser directorio OS/8"""
    
    try:
        words = struct.unpack('<256H', block_data)
        
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
        
        files = []
        entry_size = 6 + info_words
        dir_offset = 5
        
        for i in range(num_entries):
            if dir_offset + entry_size > 256:
                break
                
            entry_words = words[dir_offset:dir_offset + entry_size]
            
            file_type = entry_words[0]
            name_words = entry_words[1:4]
            length = entry_words[4]
            job_info = entry_words[5]
            extra = entry_words[6:] if info_words > 0 else []
            
            # Saltar entradas vacías
            if file_type == 0:
                dir_offset += entry_size
                continue
            
            # Decodificar nombre
            try:
                name = decode_sixbit_name(name_words)
                if name and len(name.strip()) > 0:
                    # Decodificar tipo
                    type_names = {
                        0: ".EMPTY.", 1: ".FILE.", 2: ".DATA.",
                        3: ".PROG.", 4: ".ASCII.", 5: ".BINARY."
                    }
                    type_str = type_names.get(file_type, f".{file_type}.")
                    
                    files.append({
                        'name': name,
                        'type': type_str,
                        'size': length,
                        'file_type': file_type
                    })
            except:
                pass
                
            dir_offset += entry_size
        
        return {
            'block': block_num,
            'num_entries': num_entries,
            'empty_start': empty_start,
            'info_words': info_words,
            'files': files
        }
        
    except Exception as e:
        return None

def decode_sixbit_name(words):
    """Decodifica nombre SIXBIT de OS/8"""
    
    result = ""
    
    for word in words:
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

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 find_real_directory.py <archivo_imagen>")
        sys.exit(1)
    
    directory_info = find_real_os8_directory(sys.argv[1])
    
    if directory_info:
        print(f"\n🎉 Directorio OS/8 encontrado en bloque {directory_info['block']}!")
        print(f"   Total de archivos: {len(directory_info['files'])}")
        
        # Mostrar archivos que coinciden con los esperados
        print(f"\n📋 Archivos que coinciden con la web:")
        for file_info in directory_info['files']:
            if file_info['name'] in EXPECTED_FILES:
                print(f"   ✅ {file_info['name']}")
    else:
        print(f"\n❌ No se encontró un directorio OS/8 válido")
        print(f"   La imagen podría tener un formato diferente al esperado")
