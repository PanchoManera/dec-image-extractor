#!/usr/bin/env python3
"""
Script de prueba para el extractor PDP-8
Crea una imagen de prueba mínima de OS/8 y verifica que se pueda leer
"""

import struct
import os
import tempfile
from pdp8_extractor import PDP8Extractor, PDP8FileSystem, MediaType

def create_test_os8_image():
    """Crea una imagen de prueba OS/8 mínima"""
    
    # Crear imagen de 512KB (1024 bloques de 512 bytes)
    image_size = 1024 * 512
    data = bytearray(image_size)
    
    # Crear bloque home OS/8 (bloque 1, offset 512)
    home_offset = 512
    
    # Formato de bloque home OS/8:
    # Word 0: # entradas en directorio
    # Word 1: bloque inicial de área vacía  
    # Word 2: siguiente segmento (0=último)
    # Word 3: archivo tentativo (0)
    # Word 4: -(# palabras info por entrada)
    
    num_entries = 3        # 3 archivos de prueba
    empty_start = 10       # Área vacía empieza en bloque 10
    next_segment = 0       # No hay más segmentos
    tentative = 0          # No hay archivo tentativo
    info_words = -1        # 1 palabra de info (fecha) por entrada
    
    # Escribir header del bloque home
    home_words = [
        num_entries,
        empty_start, 
        next_segment,
        tentative,
        info_words & 0xFFFF,  # Complemento 2 de 1
    ]
    
    # Entradas de directorio (empiezan en word 5)
    # Cada entrada: tipo, nombre[3], longitud, job_info, fecha
    
    # Archivo 1: HELLO.TXT (tipo ASCII)
    file1_name = encode_sixbit_name("HELLO   TXT")  # Rellenado a 9 chars
    file1_entry = [
        4,  # .ASCII.
        file1_name[0], file1_name[1], file1_name[2],  # Nombre
        1,  # 1 bloque de longitud
        0,  # Job info
        0x1234,  # Fecha dummy
    ]
    
    # Archivo 2: PROG.BIN (tipo BINARY)  
    file2_name = encode_sixbit_name("PROG    BIN")
    file2_entry = [
        5,  # .BINARY.
        file2_name[0], file2_name[1], file2_name[2],
        2,  # 2 bloques
        0,  # Job info  
        0x5678,  # Fecha dummy
    ]
    
    # Archivo 3: DATA.DAT (tipo DATA)
    file3_name = encode_sixbit_name("DATA    DAT") 
    file3_entry = [
        2,  # .DATA.
        file3_name[0], file3_name[1], file3_name[2],
        1,  # 1 bloque
        0,  # Job info
        0x9ABC,  # Fecha dummy  
    ]
    
    # Combinar todas las words del bloque home
    all_words = home_words + file1_entry + file2_entry + file3_entry
    
    # Rellenar hasta 256 words (512 bytes) con ceros
    while len(all_words) < 256:
        all_words.append(0)
    
    # Empaquetar como little-endian 16-bit words
    home_block = struct.pack('<256H', *all_words)
    
    # Escribir bloque home en offset 512 (bloque 1)
    data[home_offset:home_offset + 512] = home_block
    
    # Escribir contenido de archivos de prueba
    
    # HELLO.TXT en bloque 7 (offset 7*512)
    hello_content = b"Hello, PDP-8 World!\r\nThis is a test file.\r\n"
    hello_content += b'\x00' * (512 - len(hello_content))  # Rellenar bloque
    data[7*512:8*512] = hello_content
    
    # PROG.BIN en bloques 8-9 
    prog_content = b'\x12\x34' * 512  # Datos binarios dummy
    data[8*512:10*512] = prog_content
    
    # DATA.DAT en bloque 10
    data_content = b'\xFF\x00\xAA\x55' * 128  # Patrón de prueba
    data[10*512:11*512] = data_content
    
    return bytes(data)

def encode_sixbit_name(name):
    """Codifica un nombre de 9 caracteres en 3 words SIXBIT"""
    # Asegurar que tiene exactamente 9 caracteres
    name = name.ljust(9)[:9]
    
    words = []
    for i in range(0, 9, 3):
        # Tomar 3 caracteres
        chars = name[i:i+3]
        
        # Convertir cada carácter a SIXBIT (6 bits)
        sixbit_chars = []
        for c in chars:
            if c == ' ':
                sixbit_chars.append(0)
            elif c >= '@':
                sixbit_chars.append(ord(c) - ord('@') + 32)
            else:
                sixbit_chars.append(ord(c) - ord(' '))
        
        # Empaquetar 3 chars de 6-bit en una word de 16-bit
        # Solo usamos 18 bits, perdemos 2 bits altos
        word = (sixbit_chars[0] << 10) | (sixbit_chars[1] << 4) | (sixbit_chars[2] >> 2)
        words.append(word & 0xFFFF)
    
    return words

def test_extractor():
    """Prueba el extractor con imagen generada"""
    
    print("🧪 Creando imagen de prueba OS/8...")
    test_image = create_test_os8_image()
    
    # Escribir a archivo temporal
    with tempfile.NamedTemporaryFile(delete=False, suffix='.dsk') as f:
        f.write(test_image)
        temp_file = f.name
    
    try:
        print(f"📀 Imagen de prueba creada: {temp_file}")
        print(f"📏 Tamaño: {len(test_image)} bytes")
        
        # Probar extractor
        print("\n🚀 Probando extractor...")
        extractor = PDP8Extractor(temp_file, "test_output")
        
        # Abrir imagen
        extractor.open_image()
        
        # Verificar detección
        print(f"✅ Medio detectado: {extractor.media_type.value}")
        print(f"✅ Sistema detectado: {extractor.filesystem.value}")
        
        # Leer directorio
        if extractor.filesystem == PDP8FileSystem.OS8:
            files = extractor.read_os8_directory()
            extractor.files = files
            
            print(f"✅ Archivos encontrados: {len(files)}")
            
            # Listar archivos
            extractor.list_files()
            
            # Verificar archivos esperados
            expected_files = ["HELLO   TXT", "PROG    BIN", "DATA    DAT"]
            found_files = [f.name.strip() for f in files if f.type != ".EMPTY."]
            
            print(f"\n🔍 Verificando archivos esperados...")
            for expected in expected_files:
                if any(expected in found for found in found_files):
                    print(f"✅ Encontrado: {expected}")
                else:
                    print(f"❌ Faltante: {expected}")
            
            # Intentar extraer archivos
            print(f"\n📁 Extrayendo archivos...")
            extractor.extract_all_files()
            
            # Verificar que se crearon archivos
            output_dir = "test_output"
            if os.path.exists(output_dir):
                extracted_files = os.listdir(output_dir)
                print(f"✅ Archivos extraídos: {extracted_files}")
                
                # Limpiar directorio de prueba
                import shutil
                shutil.rmtree(output_dir)
                print(f"🧹 Limpieza completada")
            
        else:
            print(f"❌ Sistema de archivos no esperado: {extractor.filesystem}")
            
        print(f"\n🎉 Prueba completada exitosamente!")
        
    except Exception as e:
        print(f"❌ Error durante prueba: {e}")
        import traceback
        traceback.print_exc()
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists(temp_file):
            os.unlink(temp_file)
            print(f"🧹 Archivo temporal eliminado: {temp_file}")

if __name__ == "__main__":
    test_extractor()
