#!/usr/bin/env python3
"""
Análisis profundo de imagen RX01 OS/8
Busca directorios con múltiples estrategias y parámetros
"""

import struct
import sys
from pathlib import Path

def decode_sixbit(word):
    """Decodifica una palabra de 12 bits en formato SIXBIT"""
    if word == 0:
        return "      "
    
    chars = []
    for i in range(2):
        char_code = (word >> (6 * (1 - i))) & 0x3F
        if char_code == 0:
            chars.append(' ')
        elif 1 <= char_code <= 26:
            chars.append(chr(ord('A') + char_code - 1))
        elif 27 <= char_code <= 36:
            chars.append(chr(ord('0') + char_code - 27))
        elif char_code == 37:
            chars.append('.')
        elif char_code == 38:
            chars.append(' ')
        else:
            chars.append('?')
    return ''.join(chars)

def analyze_potential_directory(data, offset, block_size):
    """Analiza si los datos en offset podrían ser un directorio OS/8"""
    if offset + 16 > len(data):
        return None
    
    try:
        # Leer las primeras palabras como posible home block
        words = []
        for i in range(8):
            if offset + i*2 + 1 < len(data):
                word = struct.unpack('<H', data[offset + i*2:offset + i*2 + 2])[0]
                words.append(word)
        
        if len(words) < 4:
            return None
            
        # Interpretar como home block
        num_entries = words[0] & 0xFFF  # 12 bits bajos
        words_per_entry = words[1] & 0xFFF
        
        # Filtros de sanidad
        if num_entries == 0 or num_entries > 1000:
            return None
        if words_per_entry < 2 or words_per_entry > 20:
            return None
            
        # Buscar entradas de directorio
        entries = []
        entry_start = offset + 16  # Después del home block
        
        for i in range(min(num_entries, 100)):  # Limitar a 100 entradas
            entry_offset = entry_start + i * words_per_entry * 2
            if entry_offset + words_per_entry * 2 > len(data):
                break
                
            # Leer entrada
            entry_words = []
            for j in range(words_per_entry):
                if entry_offset + j*2 + 1 < len(data):
                    word = struct.unpack('<H', data[entry_offset + j*2:entry_offset + j*2 + 2])[0]
                    entry_words.append(word)
            
            if len(entry_words) >= 2:
                # Intentar decodificar nombre
                name1 = decode_sixbit(entry_words[0])
                name2 = decode_sixbit(entry_words[1])
                filename = (name1 + name2).strip()
                
                if filename and not filename.isspace() and len(filename.replace('?', '')) > 0:
                    entries.append({
                        'name': filename,
                        'words': entry_words
                    })
        
        if len(entries) > 0:
            return {
                'offset': offset,
                'block_size': block_size,
                'num_entries': num_entries,
                'words_per_entry': words_per_entry,
                'entries': entries,
                'home_words': words
            }
    except:
        pass
    
    return None

def search_with_different_strategies(filename):
    """Busca directorios con diferentes estrategias"""
    print(f"🔍 Análisis profundo de: {filename}")
    
    with open(filename, 'rb') as f:
        data = f.read()
    
    print(f"📏 Tamaño: {len(data)} bytes")
    
    strategies = [
        # (block_size, stride, description)
        (128, 128, "Sectores físicos RX01 (128 bytes)"),
        (256, 256, "Bloques de 256 bytes"),
        (512, 512, "Bloques lógicos OS/8 (512 bytes)"),
        (1024, 1024, "Bloques grandes (1024 bytes)"),
        (128, 64, "Sectores con stride 64"),
        (256, 128, "Bloques 256 con stride 128"),
    ]
    
    all_results = []
    
    for block_size, stride, description in strategies:
        print(f"\n📂 Estrategia: {description}")
        print(f"   Tamaño de bloque: {block_size}, stride: {stride}")
        
        results = []
        max_offset = len(data) - block_size
        
        for offset in range(0, max_offset, stride):
            result = analyze_potential_directory(data, offset, block_size)
            if result:
                results.append(result)
        
        if results:
            print(f"   ✅ Encontrados {len(results)} directorios potenciales")
            for i, result in enumerate(results[:3]):  # Mostrar solo los primeros 3
                print(f"      📍 Offset {result['offset']:6d} (0x{result['offset']:04X}): {len(result['entries'])} archivos")
                for entry in result['entries'][:5]:  # Primeros 5 archivos
                    print(f"         - {entry['name']}")
                if len(result['entries']) > 5:
                    print(f"         ... y {len(result['entries']) - 5} más")
        else:
            print(f"   ❌ No se encontraron directorios")
        
        all_results.extend(results)
    
    # Buscar el mejor resultado
    if all_results:
        print(f"\n🎯 RESUMEN: Se encontraron {len(all_results)} directorios potenciales en total")
        
        # Ordenar por número de entradas
        all_results.sort(key=lambda x: len(x['entries']), reverse=True)
        
        print(f"\n🏆 MEJOR CANDIDATO:")
        best = all_results[0]
        print(f"   📍 Offset: {best['offset']} (0x{best['offset']:04X})")
        print(f"   📦 Tamaño de bloque: {best['block_size']}")
        print(f"   📊 Entradas en directorio: {best['num_entries']}")
        print(f"   📋 Palabras por entrada: {best['words_per_entry']}")
        print(f"   📁 Archivos encontrados: {len(best['entries'])}")
        
        print(f"\n📋 Lista de archivos:")
        for entry in best['entries']:
            print(f"   - {entry['name']}")
        
        # Mostrar también home block words
        print(f"\n🏠 Home block words:")
        for i, word in enumerate(best['home_words']):
            print(f"   Word {i}: 0x{word:04X} ({word})")
            
    else:
        print(f"\n❌ No se encontró ningún directorio válido con ninguna estrategia")
        
        # Como último recurso, buscar patrones ASCII
        print(f"\n🔤 Buscando patrones ASCII...")
        ascii_blocks = []
        for offset in range(0, len(data) - 512, 128):
            block = data[offset:offset+512]
            ascii_count = sum(1 for b in block if 32 <= b <= 126)
            if ascii_count > 100:  # Si más del 20% son ASCII imprimibles
                ascii_blocks.append((offset, ascii_count))
        
        if ascii_blocks:
            print(f"   ✅ Encontrados {len(ascii_blocks)} bloques con contenido ASCII")
            for offset, count in ascii_blocks[:5]:
                print(f"      📍 Offset {offset:6d}: {count} caracteres ASCII")
                # Mostrar una muestra
                sample = data[offset:offset+64]
                ascii_sample = ''.join(chr(b) if 32 <= b <= 126 else '.' for b in sample)
                print(f"         Muestra: {ascii_sample}")
        else:
            print(f"   ❌ No se encontraron bloques con contenido ASCII significativo")

if __name__ == "__main__":
    if len(sys.argv) != 2:
        print("Uso: python3 deep_rx01_analysis.py <imagen_rx01>")
        sys.exit(1)
    
    image_file = sys.argv[1]
    if not Path(image_file).exists():
        print(f"Error: No se encuentra el archivo {image_file}")
        sys.exit(1)
    
    search_with_different_strategies(image_file)
