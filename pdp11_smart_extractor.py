#!/usr/bin/env python3
"""
PDP-11 Smart Extractor
Extractor inteligente que detecta automáticamente el tipo de filesystem
y utiliza el extractor apropiado.

Soporta:
- RT-11 (todas las versiones)
- Unix V5, V6, V7 para PDP-11
- Detección automática de tipo

Basado en:
- RT-11 Extractor (proyecto local)
- PyPDP11 Unix implementation
"""

import sys
import os
import argparse
import subprocess
from pathlib import Path

def detect_filesystem_type(image_path: str) -> tuple[str, str]:
    """
    Detecta el tipo de filesystem en la imagen
    Retorna (tipo, descripción)
    """
    
    # Probar RT-11 primero
    try:
        result = subprocess.run(
            ["./rt11extract_smart.py", image_path, "-d"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0 and "RT-11" in result.stdout:
            return "RT-11", result.stdout.strip()
    except:
        pass
    
    # Probar Unix PDP-11
    try:
        result = subprocess.run(
            ["./unix_pdp11_extractor.py", image_path, "--detect-only"],
            capture_output=True, text=True, timeout=30
        )
        
        if result.returncode == 0 and "Unix" in result.stdout:
            return "Unix", result.stdout.strip()
    except:
        pass
    
    # Detección manual básica si los scripts fallan
    try:
        with open(image_path, 'rb') as f:
            # Leer algunos bloques
            f.seek(0)
            boot_block = f.read(512)
            
            f.seek(512)
            block1 = f.read(512)
            
            # Buscar patrones RT-11
            if any(pattern in boot_block + block1 for pattern in [b'RT11', b'RT-11']):
                return "RT-11", "RT-11 filesystem detected (pattern-based)"
            
            # Buscar patrones Unix
            if any(pattern in boot_block + block1 for pattern in [b'bin', b'etc', b'usr', b'dev']):
                return "Unix", "Unix filesystem detected (pattern-based)"
                
    except:
        pass
    
    return "Unknown", "Unknown filesystem type"

def extract_rt11(image_path: str, output_dir: str, list_only: bool = False, verbose: bool = False):
    """Extraer usando RT-11 extractor"""
    cmd = ["./rt11extract", image_path]
    
    if list_only:
        cmd.append("-l")
    else:
        cmd.extend(["-o", output_dir])
    
    if verbose:
        cmd.append("-v")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running RT-11 extractor: {e}")
        return False

def extract_unix(image_path: str, output_dir: str, list_only: bool = False, 
                detailed: bool = False, path: str = "/", verbose: bool = False):
    """Extraer usando Unix extractor"""
    cmd = ["./unix_pdp11_extractor.py", image_path]
    
    if list_only:
        cmd.append("-l")
        if path != "/":
            cmd.extend(["-p", path])
        if detailed:
            cmd.append("-d")
    else:
        cmd.extend(["-o", output_dir])
        if path != "/":
            cmd.extend(["-p", path])
    
    if verbose:
        cmd.append("-v")
    
    try:
        result = subprocess.run(cmd, capture_output=False, text=True)
        return result.returncode == 0
    except Exception as e:
        print(f"❌ Error running Unix extractor: {e}")
        return False

def main():
    parser = argparse.ArgumentParser(
        description="PDP-11 Smart Extractor - Auto-detects RT-11 or Unix filesystems",
        epilog="""
This extractor automatically detects whether a disk image contains:
- RT-11 filesystem (any version)
- Unix V5/V6/V7 filesystem

Examples:
  %(prog)s disk.dsk                    # Auto-detect and extract all files
  %(prog)s disk.dsk -l                 # Auto-detect and list files
  %(prog)s disk.dsk -l -d              # List with detailed info (Unix only)
  %(prog)s disk.dsk -p /usr            # Extract specific path (Unix only)
  %(prog)s disk.dsk --detect-only      # Only detect filesystem type
        """,
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument("image", help="Disk image file (.dsk, .img, etc.)")
    parser.add_argument("-l", "--list", action="store_true",
                       help="List files only, don't extract")
    parser.add_argument("-d", "--detailed", action="store_true",
                       help="Show detailed file information (Unix only)")
    parser.add_argument("-p", "--path", default="/",
                       help="Path to extract (Unix only, default: /)")
    parser.add_argument("-o", "--output", default="extracted_pdp11",
                       help="Output directory (default: extracted_pdp11)")
    parser.add_argument("-v", "--verbose", action="store_true",
                       help="Verbose output")
    parser.add_argument("--detect-only", action="store_true",
                       help="Only detect filesystem type")
    parser.add_argument("--force-type", choices=["rt11", "unix"],
                       help="Force filesystem type instead of auto-detecting")
    
    args = parser.parse_args()
    
    # Verificar que el archivo existe
    if not os.path.exists(args.image):
        print(f"❌ Error: File '{args.image}' not found")
        return 1
    
    print(f"🔍 Analyzing: {args.image}")
    print("-" * 50)
    
    # Detectar tipo de filesystem
    if args.force_type:
        fs_type = args.force_type.upper()
        description = f"Forced {fs_type} filesystem"
    else:
        fs_type, description = detect_filesystem_type(args.image)
    
    # Mostrar resultado de detección
    if fs_type == "RT-11":
        print("✅ RT-11 Filesystem Detected")
        print("   📀 Compatible with RT-11 extractor")
    elif fs_type == "Unix":
        print("✅ Unix PDP-11 Filesystem Detected")  
        print("   🐧 Compatible with Unix extractor")
    else:
        print("❓ Unknown Filesystem Type")
        print("   ⚠️  Cannot determine filesystem type")
    
    if description:
        print(f"   💡 {description}")
    
    if args.detect_only:
        return 0 if fs_type != "Unknown" else 1
    
    print()
    
    # Proceder con extracción según el tipo detectado
    if fs_type == "RT-11":
        print("🚀 Using RT-11 Extractor...")
        success = extract_rt11(args.image, args.output, args.list, args.verbose)
        
    elif fs_type == "Unix":
        print("🚀 Using Unix PDP-11 Extractor...")
        success = extract_unix(args.image, args.output, args.list, 
                             args.detailed, args.path, args.verbose)
        
    else:
        print("❌ Cannot extract: Unknown filesystem type")
        print("💡 Try using --force-type to force a specific extractor")
        return 1
    
    if success:
        if args.list:
            print("\n✅ Listing completed successfully")
        else:
            print(f"\n✅ Extraction completed successfully")
            print(f"📁 Output directory: {Path(args.output).absolute()}")
    else:
        print("\n❌ Operation failed")
        return 1
    
    return 0

if __name__ == '__main__':
    sys.exit(main())
