#!/usr/bin/env python3
"""
Script simplificado para crear ejecutables Windows (.exe) verdaderos
usando el entorno virtual con las herramientas instaladas.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_cmd(cmd_str):
    """Ejecuta comando en el entorno virtual."""
    full_cmd = f"source venv_build/bin/activate && {cmd_str}"
    print(f"Ejecutando: {cmd_str}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"Salida: {result.stdout}")
    if result.stderr:
        print(f"Error: {result.stderr}")
    return result.returncode == 0

def try_nuitka_windows():
    """Intenta crear ejecutables Windows con Nuitka."""
    print("\n=== INTENTANDO NUITKA PARA WINDOWS ===")
    
    # Limpiar directorio de salida
    shutil.rmtree("dist", ignore_errors=True)
    os.makedirs("dist", exist_ok=True)
    
    architectures = [
        ("win32", "x86"),
        ("win64", "x86_64"), 
        ("winarm64", "arm64")
    ]
    
    success_count = 0
    
    for win_arch, nuitka_arch in architectures:
        print(f"\n--- Construyendo {win_arch} ---")
        
        cmd = f"""nuitka \\
            --onefile \\
            --standalone \\
            --enable-plugin=tk-inter \\
            --windows-disable-console \\
            --windows-icon-from-ico=icon.ico \\
            --target-arch={nuitka_arch} \\
            --assume-yes-for-downloads \\
            --output-dir=dist/{win_arch} \\
            rt11extract_gui.py"""
        
        if run_cmd(cmd):
            # Buscar el ejecutable
            exe_files = list(Path(f"dist/{win_arch}").rglob("*.exe"))
            if exe_files:
                exe_path = exe_files[0]
                final_name = f"RT11ExtractGUI-{win_arch}.exe"
                os.makedirs("binaries", exist_ok=True)
                shutil.copy2(exe_path, f"binaries/{final_name}")
                print(f"✓ Creado: binaries/{final_name}")
                success_count += 1
            else:
                print(f"✗ No se encontró .exe para {win_arch}")
        else:
            print(f"✗ Falló construcción de {win_arch}")
    
    return success_count

def try_pyinstaller_windows():
    """Intenta crear ejecutables Windows con PyInstaller."""
    print("\n=== INTENTANDO PYINSTALLER PARA WINDOWS ===")
    
    architectures = [
        ("win32", "x86"),
        ("win64", "x86_64"),
        ("winarm64", "arm64")
    ]
    
    success_count = 0
    
    for win_arch, pyinst_arch in architectures:
        print(f"\n--- Construyendo {win_arch} con PyInstaller ---")
        
        cmd = f"""pyinstaller \\
            --onefile \\
            --windowed \\
            --add-data icon.ico:. \\
            --icon icon.ico \\
            --target-architecture={pyinst_arch} \\
            --distpath dist/pyinst_{win_arch} \\
            --workpath build/pyinst_{win_arch} \\
            --specpath build/pyinst_{win_arch} \\
            --name RT11ExtractGUI-{win_arch} \\
            rt11extract_gui.py"""
        
        if run_cmd(cmd):
            exe_path = Path(f"dist/pyinst_{win_arch}/RT11ExtractGUI-{win_arch}.exe")
            if exe_path.exists():
                final_name = f"RT11ExtractGUI-{win_arch}.exe"
                os.makedirs("binaries", exist_ok=True)
                shutil.copy2(exe_path, f"binaries/{final_name}")
                print(f"✓ Creado: binaries/{final_name}")
                success_count += 1
            else:
                print(f"✗ No se encontró .exe para {win_arch}")
        else:
            print(f"✗ Falló construcción de {win_arch}")
    
    return success_count

def check_exe_files():
    """Verifica que los archivos .exe sean válidos."""
    print("\n=== VERIFICANDO EJECUTABLES ===")
    
    binaries_dir = Path("binaries")
    if not binaries_dir.exists():
        print("No hay directorio binaries/")
        return
    
    exe_files = list(binaries_dir.glob("*.exe"))
    if not exe_files:
        print("No se encontraron archivos .exe")
        return
    
    for exe_file in exe_files:
        print(f"\nVerificando: {exe_file}")
        
        try:
            with open(exe_file, "rb") as f:
                # Verificar magic number PE
                magic = f.read(2)
                if magic == b'MZ':
                    f.seek(60)
                    pe_offset = int.from_bytes(f.read(4), 'little')
                    f.seek(pe_offset)
                    pe_sig = f.read(4)
                    if pe_sig == b'PE\x00\x00':
                        size_mb = exe_file.stat().st_size / (1024*1024)
                        print(f"  ✓ Ejecutable Windows válido ({size_mb:.1f} MB)")
                    else:
                        print(f"  ✗ No es un ejecutable PE válido")
                else:
                    print(f"  ✗ No tiene magic number MZ")
        except Exception as e:
            print(f"  ✗ Error verificando: {e}")

def main():
    """Función principal."""
    print("=== CREADOR SIMPLE DE EJECUTABLES WINDOWS ===")
    
    # Verificar entorno virtual
    if not os.path.exists("venv_build/bin/activate"):
        print("Error: No se encuentra el entorno virtual venv_build")
        sys.exit(1)
    
    # Verificar archivo principal
    if not os.path.exists("rt11extract_gui.py"):
        print("Error: No se encuentra rt11extract_gui.py")
        sys.exit(1)
    
    # Crear directorio binaries
    os.makedirs("binaries", exist_ok=True)
    
    total_success = 0
    
    # Intentar con Nuitka primero (mejor para cross-compilation)
    total_success += try_nuitka_windows()
    
    # Si no funciona Nuitka, intentar PyInstaller
    if total_success == 0:
        total_success += try_pyinstaller_windows()
    
    # Verificar los archivos creados
    check_exe_files()
    
    # Resumen
    print(f"\n{'='*50}")
    print("RESUMEN FINAL")
    print(f"{'='*50}")
    print(f"Ejecutables Windows creados: {total_success}")
    
    if total_success > 0:
        print("\n✓ Se crearon ejecutables Windows!")
        print("Los archivos .exe están en la carpeta binaries/")
        print("Estos deberían ser ejecutables autocontenidos para Windows.")
    else:
        print("\n✗ No se pudieron crear ejecutables Windows.")
        print("La cross-compilation desde macOS a Windows es compleja.")
        print("Puede que necesites usar una máquina Windows o VM.")

if __name__ == "__main__":
    main()
