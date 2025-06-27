#!/usr/bin/env python3
"""
Smart RT-11 Extractor with Filesystem Detection
Detecta automáticamente el tipo de filesystem y proporciona mejores mensajes de error
"""

import struct
import sys
import os
import argparse
from pathlib import Path

def detect_filesystem_type(image_path):
    """Detecta el tipo de filesystem en la imagen de disco"""
    try:
        with open(image_path, 'rb') as f:
            # Leer los primeros bloques para detectar el filesystem
            f.seek(0)
            boot_block = f.read(512)
            
            f.seek(512)  # Block 1 
            block1 = f.read(512)
            
            f.seek(1024) # Block 2
            block2 = f.read(512)
            
            # Detectar RT-11
            # Buscar patrones típicos de RT-11
            if detect_rt11_patterns(f, image_path):
                return "RT-11", "Filesystem RT-11 detectado"
            
            # Detectar BSD UFS
            if detect_bsd_ufs(block1, block2):
                return "BSD-UFS", "Filesystem BSD Unix (UFS/FFS) detectado"
            
            # Detectar RSX-11M Files-11
            if detect_files11(boot_block, block1):
                return "Files-11", "Filesystem RSX-11M Files-11 detectado"
            
            # Detectar Unix
            if detect_unix_filesystem(boot_block, block1, block2):
                return "Unix", "Filesystem Unix detectado"
            
            # Verificar si está vacío o corrupto
            if is_empty_or_corrupted(boot_block, block1, block2):
                return "Empty/Corrupt", "Imagen vacía o corrupta"
                
            return "Unknown", "Tipo de filesystem no reconocido"
            
    except Exception as e:
        return "Error", f"Error leyendo la imagen: {e}"

def detect_rt11_patterns(f, image_path):
    """Detecta patrones específicos de RT-11"""
    try:
        # Primero buscar en posiciones estándares
        for block_offset in [6, 7, 8, 9, 10]:  # Posiciones comunes del directorio
            if check_rt11_at_offset(f, block_offset * 512):
                return True
        
        # Búsqueda más amplia en caso de formatos no estándares
        # Buscar cada 128 bytes en los primeros 50KB
        file_size = f.seek(0, 2)  # Obtener tamaño del archivo
        f.seek(0)
        
        for offset in range(0, min(file_size, 50000), 128):
            if check_rt11_at_offset(f, offset):
                return True
                
        return False
    except:
        return False

def check_rt11_at_offset(f, offset):
    """Verifica si hay un directorio RT-11 válido en el offset dado"""
    try:
        f.seek(offset)
        data = f.read(512)
        
        if len(data) >= 10:
            # Leer header de directorio RT-11
            try:
                words = struct.unpack('<5H', data[:10])
                total_segs, next_seg, highest_seg, extra_bytes, start_blk = words
                
                # Validar rangos típicos de RT-11
                if (1 <= total_segs <= 31 and 
                    next_seg <= 31 and
                    highest_seg <= 31 and
                    extra_bytes <= 100 and
                    start_blk < 10000):
                    
                    # Verificar que hay entradas de archivo válidas
                    if has_valid_rt11_entries(data[10:], extra_bytes):
                        return True
            except:
                pass
        return False
    except:
        return False

def has_valid_rt11_entries(data, extra_bytes=0):
    """Verifica si hay entradas de archivo RT-11 válidas"""
    try:
        entry_size = 14 + extra_bytes
        offset = 0
        while offset <= len(data) - entry_size:
            try:
                # Leer entrada básica de 14 bytes
                entry = struct.unpack('<7H', data[offset:offset+14])
                status = entry[0]
                
                # Comprobar bits de estado RT-11
                if status & 0x400:  # Bit de archivo permanente
                    return True
                if status & 0x100:  # Bit de archivo tentativo  
                    return True
                    
                offset += entry_size
                if offset > 200:  # No buscar demasiado
                    break
            except:
                offset += 14  # Saltar entrada problemática
        return False
    except:
        return False

def detect_bsd_ufs(block1, block2):
    """Detecta filesystem BSD UFS/FFS"""
    try:
        # Buscar magic numbers de UFS
        # UFS1 magic: 0x011954 o 0x009BAD  
        # UFS2 magic: 0x19540119
        
        for block in [block1, block2]:
            if len(block) >= 4:
                # Buscar en diferentes offsets
                for offset in [0, 512-4, 256, 128]:
                    if offset + 4 <= len(block):
                        magic = struct.unpack('<I', block[offset:offset+4])[0]
                        if magic in [0x011954, 0x009BAD, 0x19540119]:
                            return True
                        
                        # También buscar en big endian
                        magic = struct.unpack('>I', block[offset:offset+4])[0] 
                        if magic in [0x011954, 0x009BAD, 0x19540119]:
                            return True
        return False
    except:
        return False

def detect_files11(boot_block, block1):
    """Detecta RSX-11M Files-11"""
    try:
        # Files-11 tiene estructuras específicas
        # Buscar patrones típicos en el home block
        for block in [boot_block, block1]:
            if len(block) >= 512:
                # Buscar strings típicos de RSX-11M
                block_str = block.replace(b'\x00', b' ').decode('ascii', errors='ignore')
                if any(pattern in block_str.upper() for pattern in ['RSX11', 'FILES11', 'RSX-11', 'SYSTEM']):
                    return True
                    
                # Buscar patrones binarios de Files-11
                if b'RSX' in block or b'FILES' in block:
                    return True
        return False
    except:
        return False

def detect_unix_filesystem(boot_block, block1, block2):
    """Detecta filesystems Unix genéricos"""
    try:
        for block in [boot_block, block1, block2]:
            if len(block) >= 32:
                block_str = block.replace(b'\x00', b' ').decode('ascii', errors='ignore')
                # Buscar strings típicos de Unix
                if any(pattern in block_str.upper() for pattern in ['UNIX', 'ULTRIX', 'BSD', '/BIN/', '/USR/']):
                    return True
        return False
    except:
        return False

def is_empty_or_corrupted(boot_block, block1, block2):
    """Detecta si la imagen está vacía o corrupta"""
    try:
        # Verificar si todos los bloques son zeros
        if (boot_block == b'\x00' * len(boot_block) and
            block1 == b'\x00' * len(block1) and
            block2 == b'\x00' * len(block2)):
            return True
            
        # Verificar si hay muy pocos datos no-zero
        total_bytes = len(boot_block) + len(block1) + len(block2)
        non_zero_bytes = sum(1 for b in boot_block + block1 + block2 if b != 0)
        
        if non_zero_bytes < total_bytes * 0.01:  # Menos del 1% son no-zero
            return True
            
        return False
    except:
        return True

def main():
    parser = argparse.ArgumentParser(
        description="Smart RT-11 Extractor with Filesystem Detection",
        epilog="""
Este extractor detecta automáticamente el tipo de filesystem antes de intentar extraer.
Soporta RT-11 y detecta otros filesystems para dar mejores mensajes de error.
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("image", help="Archivo de imagen de disco (.dsk, .img, etc.)")
    parser.add_argument("-d", "--detect-only", action="store_true",
                       help="Solo detectar el tipo de filesystem, no extraer")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Salida detallada")
    
    args = parser.parse_args()
    
    if not os.path.exists(args.image):
        print(f"❌ Error: Archivo '{args.image}' no encontrado")
        return 1
    
    print(f"🔍 Analizando: {args.image}")
    print("-" * 50)
    
    # Detectar tipo de filesystem
    fs_type, description = detect_filesystem_type(args.image)
    
    # Mostrar resultado de detección
    if fs_type == "RT-11":
        print(f"✅ {description}")
        print("   Compatible con este extractor")
    elif fs_type == "BSD-UFS":
        print(f"🔶 {description}")
        print("   ⚠️  No compatible: Use herramientas BSD/Unix para extraer")
        print("   💡 Sugerencia: mount, fsck.ufs, o herramientas similares")
    elif fs_type == "Files-11":
        print(f"🔶 {description}")
        print("   ⚠️  No compatible: Use herramientas RSX-11M/VMS")
        print("   💡 Sugerencia: PUTR.exe o herramientas Files-11")
    elif fs_type == "Unix":
        print(f"🔶 {description}")
        print("   ⚠️  No compatible: Use herramientas Unix apropiadas")
    elif fs_type == "Empty/Corrupt":
        print(f"❌ {description}")
        print("   ⚠️  La imagen puede estar dañada o vacía")
    else:
        print(f"❓ {description}")
        print("   ⚠️  Tipo desconocido, puede no ser compatible")
    
    if args.detect_only:
        return 0
    
    # Si es RT-11, intentar extraer
    if fs_type == "RT-11":
        print("\n🚀 Procediendo con extracción RT-11...")
        
        # Llamar al extractor original
        import subprocess
        try:
            cmd = ["./rt11extract", args.image, "-l"]
            if args.verbose:
                cmd.append("-v")
            
            result = subprocess.run(cmd, capture_output=True, text=True)
            
            if result.returncode == 0:
                print(result.stdout)
                return 0
            else:
                print(f"❌ Error en extracción: {result.stderr}")
                return 1
                
        except Exception as e:
            print(f"❌ Error ejecutando extractor: {e}")
            return 1
    else:
        print(f"\n⏹️  No se puede extraer: Filesystem {fs_type} no soportado")
        return 1

if __name__ == '__main__':
    sys.exit(main())
