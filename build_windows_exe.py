#!/usr/bin/env python3
"""
Script para crear ejecutables Windows (.exe) verdaderos y autocontenidos
desde macOS usando múltiples herramientas de cross-compilation.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, cwd=None, check=True):
    """Ejecuta un comando y retorna el resultado."""
    print(f"Ejecutando: {' '.join(cmd)}")
    try:
        result = subprocess.run(cmd, cwd=cwd, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"Salida: {result.stdout}")
        return result
    except subprocess.CalledProcessError as e:
        print(f"Error ejecutando comando: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return None

def install_dependencies():
    """Instala las dependencias necesarias."""
    print("Instalando dependencias para cross-compilation...")
    
    # Instalar Nuitka
    run_command([sys.executable, "-m", "pip", "install", "nuitka", "ordered-set"])
    
    # Instalar auto-py-to-exe 
    run_command([sys.executable, "-m", "pip", "install", "auto-py-to-exe"])
    
    # Instalar cx_Freeze
    run_command([sys.executable, "-m", "pip", "install", "cx_Freeze"])
    
    # Instalar pyinstaller
    run_command([sys.executable, "-m", "pip", "install", "pyinstaller"])

def create_nuitka_exe(target_arch):
    """Crea ejecutable usando Nuitka con cross-compilation."""
    print(f"\n=== Creando ejecutable Windows {target_arch} con Nuitka ===")
    
    # Mapeo de arquitecturas
    arch_map = {
        "win32": "x86",
        "win64": "x86_64", 
        "winarm64": "arm64"
    }
    
    nuitka_arch = arch_map.get(target_arch, "x86_64")
    output_dir = f"dist/nuitka_{target_arch}"
    os.makedirs(output_dir, exist_ok=True)
    
    cmd = [
        sys.executable, "-m", "nuitka",
        "--onefile",
        "--standalone",
        "--enable-plugin=tk-inter",
        "--windows-disable-console",
        f"--windows-icon-from-ico=icon.ico",
        f"--target-arch={nuitka_arch}",
        "--assume-yes-for-downloads",
        f"--output-dir={output_dir}",
        "rt11extract_gui.py"
    ]
    
    result = run_command(cmd, check=False)
    if result and result.returncode == 0:
        # Buscar el ejecutable generado
        exe_files = list(Path(output_dir).rglob("*.exe"))
        if exe_files:
            exe_path = exe_files[0]
            final_name = f"RT11ExtractGUI-{target_arch}.exe"
            final_path = Path("binaries") / final_name
            os.makedirs("binaries", exist_ok=True)
            shutil.copy2(exe_path, final_path)
            print(f"✓ Ejecutable creado: {final_path}")
            return True
    
    print(f"✗ Falló la creación con Nuitka para {target_arch}")
    return False

def create_pyinstaller_exe(target_arch):
    """Crea ejecutable usando PyInstaller con cross-compilation."""
    print(f"\n=== Creando ejecutable Windows {target_arch} con PyInstaller ===")
    
    # Mapeo de arquitecturas para PyInstaller
    arch_map = {
        "win32": "--target-architecture=x86",
        "win64": "--target-architecture=x86_64",
        "winarm64": "--target-architecture=arm64"
    }
    
    arch_flag = arch_map.get(target_arch, "--target-architecture=x86_64")
    
    cmd = [
        sys.executable, "-m", "PyInstaller",
        "--onefile",
        "--windowed",
        "--add-data", "icon.ico:.",
        "--icon", "icon.ico",
        arch_flag,
        "--distpath", f"dist/pyinstaller_{target_arch}",
        "--workpath", f"build/pyinstaller_{target_arch}",
        "--specpath", f"build/pyinstaller_{target_arch}",
        "--name", f"RT11ExtractGUI-{target_arch}",
        "rt11extract_gui.py"
    ]
    
    result = run_command(cmd, check=False)
    if result and result.returncode == 0:
        exe_path = Path(f"dist/pyinstaller_{target_arch}/RT11ExtractGUI-{target_arch}.exe")
        if exe_path.exists():
            final_path = Path("binaries") / f"RT11ExtractGUI-{target_arch}.exe"
            os.makedirs("binaries", exist_ok=True)
            shutil.copy2(exe_path, final_path)
            print(f"✓ Ejecutable creado: {final_path}")
            return True
    
    print(f"✗ Falló la creación con PyInstaller para {target_arch}")
    return False

def create_cxfreeze_exe(target_arch):
    """Crea ejecutable usando cx_Freeze."""
    print(f"\n=== Creando ejecutable Windows {target_arch} con cx_Freeze ===")
    
    # Crear setup.py temporal para cx_Freeze
    setup_content = f'''
import sys
from cx_Freeze import setup, Executable

# Mapeo de arquitecturas
arch_map = {{
    "win32": "win32",
    "win64": "win-amd64", 
    "winarm64": "win-arm64"
}}

target_arch = "{target_arch}"
platform = arch_map.get(target_arch, "win-amd64")

build_options = {{
    "packages": ["tkinter", "PIL", "os", "sys", "struct", "datetime"],
    "excludes": [],
    "include_files": [("icon.ico", "icon.ico")],
    "build_exe": f"dist/cxfreeze_{{target_arch}}"
}}

executables = [
    Executable(
        "rt11extract_gui.py",
        base="Win32GUI",  # Para Windows GUI sin consola
        target_name=f"RT11ExtractGUI-{{target_arch}}.exe",
        icon="icon.ico"
    )
]

setup(
    name="RT11ExtractGUI",
    version="1.0",
    description="RT-11 File System Extractor",
    options={{"build_exe": build_options}},
    executables=executables
)
'''
    
    with open("setup_temp.py", "w") as f:
        f.write(setup_content)
    
    try:
        cmd = [sys.executable, "setup_temp.py", "build"]
        result = run_command(cmd, check=False)
        
        if result and result.returncode == 0:
            exe_path = Path(f"dist/cxfreeze_{target_arch}/RT11ExtractGUI-{target_arch}.exe")
            if exe_path.exists():
                final_path = Path("binaries") / f"RT11ExtractGUI-{target_arch}.exe"
                os.makedirs("binaries", exist_ok=True)
                shutil.copy2(exe_path, final_path)
                print(f"✓ Ejecutable creado: {final_path}")
                return True
        
        print(f"✗ Falló la creación con cx_Freeze para {target_arch}")
        return False
        
    finally:
        # Limpiar archivo temporal
        if os.path.exists("setup_temp.py"):
            os.remove("setup_temp.py")

def check_exe_format(exe_path):
    """Verifica si el archivo es realmente un ejecutable Windows."""
    try:
        with open(exe_path, "rb") as f:
            # Leer los primeros bytes para verificar el formato PE
            magic = f.read(2)
            if magic == b'MZ':  # DOS header
                f.seek(60)  # Offset to PE header
                pe_offset = int.from_bytes(f.read(4), 'little')
                f.seek(pe_offset)
                pe_signature = f.read(4)
                if pe_signature == b'PE\x00\x00':
                    print(f"✓ {exe_path} es un ejecutable Windows válido (PE)")
                    return True
        
        print(f"✗ {exe_path} NO es un ejecutable Windows válido")
        return False
    except Exception as e:
        print(f"Error verificando {exe_path}: {e}")
        return False

def main():
    """Función principal."""
    print("=== Creador de Ejecutables Windows (.exe) ===")
    print("Intentando crear ejecutables autocontenidos para Windows...")
    
    # Verificar que estamos en el directorio correcto
    if not os.path.exists("rt11extract_gui.py"):
        print("Error: No se encuentra rt11extract_gui.py")
        sys.exit(1)
    
    # Instalar dependencias
    install_dependencies()
    
    # Crear directorio de binarios
    os.makedirs("binaries", exist_ok=True)
    
    # Arquitecturas a construir
    architectures = ["win32", "win64", "winarm64"]
    
    results = {}
    
    for arch in architectures:
        print(f"\n{'='*60}")
        print(f"CONSTRUYENDO PARA {arch.upper()}")
        print(f"{'='*60}")
        
        # Intentar con diferentes herramientas
        success = False
        
        # 1. Intentar con Nuitka (mejor para cross-compilation)
        if create_nuitka_exe(arch):
            success = True
        
        # 2. Si Nuitka falla, intentar PyInstaller
        elif create_pyinstaller_exe(arch):
            success = True
        
        # 3. Si ambos fallan, intentar cx_Freeze
        elif create_cxfreeze_exe(arch):
            success = True
        
        results[arch] = success
    
    # Verificar los ejecutables creados
    print(f"\n{'='*60}")
    print("VERIFICANDO EJECUTABLES CREADOS")
    print(f"{'='*60}")
    
    binaries_dir = Path("binaries")
    if binaries_dir.exists():
        for exe_file in binaries_dir.glob("*.exe"):
            print(f"\nVerificando: {exe_file}")
            if check_exe_format(exe_file):
                size = exe_file.stat().st_size / (1024*1024)  # MB
                print(f"  Tamaño: {size:.1f} MB")
            else:
                print(f"  ⚠️  ADVERTENCIA: No es un ejecutable Windows válido")
    
    # Resumen final
    print(f"\n{'='*60}")
    print("RESUMEN DE CONSTRUCCIÓN")
    print(f"{'='*60}")
    
    for arch, success in results.items():
        status = "✓ ÉXITO" if success else "✗ FALLÓ"
        print(f"{arch.upper()}: {status}")
    
    successful_builds = sum(results.values())
    print(f"\nEjecutables creados exitosamente: {successful_builds}/3")
    
    if successful_builds > 0:
        print(f"\nLos ejecutables están en la carpeta 'binaries/'")
        print("Estos son ejecutables Windows autocontenidos (.exe) que deberían")
        print("funcionar en máquinas Windows sin necesidad de Python instalado.")
    else:
        print("\n⚠️  No se pudo crear ningún ejecutable Windows.")
        print("Esto puede deberse a limitaciones de cross-compilation desde macOS.")

if __name__ == "__main__":
    main()
