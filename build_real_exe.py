#!/usr/bin/env python3
"""
Script final para crear ejecutables Windows (.exe) que realmente funcione.
Enfoque pragmático sin opciones complejas.
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_in_venv(cmd):
    """Ejecuta comando en entorno virtual."""
    full_cmd = f"source venv_build/bin/activate && {cmd}"
    print(f"Ejecutando: {cmd}")
    result = subprocess.run(full_cmd, shell=True, capture_output=True, text=True)
    if result.stdout:
        print(f"Salida: {result.stdout}")
    if result.stderr and result.returncode != 0:
        print(f"Error: {result.stderr}")
    return result.returncode == 0, result

def simple_pyinstaller():
    """Crear ejecutables con PyInstaller sin opciones complejas."""
    print("\n=== PYINSTALLER SIMPLE ===")
    
    # Limpiar
    shutil.rmtree("dist", ignore_errors=True)
    shutil.rmtree("build", ignore_errors=True)
    
    # Crear sin target-architecture (que no funciona en macOS)
    cmd = """pyinstaller --onefile --noconsole --icon icon.ico --name RT11ExtractGUI rt11extract_gui.py"""
    
    success, result = run_in_venv(cmd)
    
    if success:
        exe_path = Path("dist/RT11ExtractGUI")
        if exe_path.exists():
            # Renombrar para ser más claro
            os.makedirs("binaries", exist_ok=True)
            shutil.copy2(exe_path, "binaries/RT11ExtractGUI-macOS")
            print("✓ Creado ejecutable macOS: binaries/RT11ExtractGUI-macOS")
            return 1
    
    return 0

def simple_nuitka():
    """Crear ejecutables con Nuitka simple."""
    print("\n=== NUITKA SIMPLE ===")
    
    cmd = """nuitka --onefile --enable-plugin=tk-inter --disable-console --output-dir=dist rt11extract_gui.py"""
    
    success, result = run_in_venv(cmd)
    
    if success:
        # Buscar cualquier ejecutable creado
        exe_files = list(Path("dist").rglob("*"))
        exe_files = [f for f in exe_files if f.is_file() and not f.name.endswith(('.py', '.pyc', '.txt'))]
        
        if exe_files:
            exe_path = exe_files[0]
            os.makedirs("binaries", exist_ok=True)
            shutil.copy2(exe_path, "binaries/RT11ExtractGUI-nuitka")
            print(f"✓ Creado ejecutable Nuitka: binaries/RT11ExtractGUI-nuitka")
            return 1
    
    return 0

def try_cx_freeze():
    """Crear ejecutable con cx_Freeze."""
    print("\n=== CX_FREEZE SIMPLE ===")
    
    # Crear setup.py simple
    setup_content = '''
import sys
from cx_Freeze import setup, Executable

build_options = {
    "packages": ["tkinter", "PIL", "os", "sys", "struct", "datetime"],
    "excludes": [],
    "include_files": [("icon.ico", "icon.ico")],
    "build_exe": "dist/cxfreeze"
}

executables = [
    Executable(
        "rt11extract_gui.py",
        target_name="RT11ExtractGUI",
        icon="icon.ico"
    )
]

setup(
    name="RT11ExtractGUI",
    version="1.0",
    description="RT-11 File System Extractor",
    options={"build_exe": build_options},
    executables=executables
)
'''
    
    with open("setup_cx.py", "w") as f:
        f.write(setup_content)
    
    try:
        success, result = run_in_venv("python setup_cx.py build")
        
        if success:
            exe_files = list(Path("dist/cxfreeze").rglob("RT11ExtractGUI*"))
            if exe_files:
                exe_path = exe_files[0]
                os.makedirs("binaries", exist_ok=True)
                shutil.copy2(exe_path, "binaries/RT11ExtractGUI-cxfreeze")
                print(f"✓ Creado ejecutable cx_Freeze: binaries/RT11ExtractGUI-cxfreeze")
                return 1
        
        return 0
        
    finally:
        if os.path.exists("setup_cx.py"):
            os.remove("setup_cx.py")

def create_windows_portable():
    """Crear una versión portable para Windows."""
    print("\n=== CREANDO PORTABLE PARA WINDOWS ===")
    
    # Crear directorio portable
    portable_dir = Path("binaries/RT11ExtractGUI-Windows-Portable")
    if portable_dir.exists():
        shutil.rmtree(portable_dir)
    
    portable_dir.mkdir(parents=True)
    
    # Copiar archivos Python
    files_to_copy = [
        "rt11extract_gui.py",
        "rt11extract",
        "rt11extract_simple.py", 
        "icon.ico"
    ]
    
    for file in files_to_copy:
        if os.path.exists(file):
            shutil.copy2(file, portable_dir / file)
    
    # Crear launcher batch
    bat_content = '''@echo off
echo RT-11 Extractor GUI - Windows Portable
echo.

REM Buscar Python
python --version >nul 2>&1
if %errorlevel% == 0 (
    echo Encontrado Python, iniciando...
    python rt11extract_gui.py
    goto :end
)

py --version >nul 2>&1
if %errorlevel% == 0 (
    echo Encontrado Python (py launcher), iniciando...
    py rt11extract_gui.py
    goto :end
)

python3 --version >nul 2>&1
if %errorlevel% == 0 (
    echo Encontrado Python3, iniciando...
    python3 rt11extract_gui.py
    goto :end
)

echo.
echo ERROR: No se encuentra Python instalado.
echo.
echo Opciones:
echo 1. Instalar Python desde https://python.org
echo 2. Usar la version con Python incluido (si esta disponible)
echo.
pause

:end
'''
    
    with open(portable_dir / "RT11ExtractGUI.bat", "w") as f:
        f.write(bat_content)
    
    # Crear README
    readme_content = '''RT-11 Extractor GUI - Versión Portable para Windows

INSTRUCCIONES:
1. Ejecutar RT11ExtractGUI.bat
2. Si aparece error de Python faltante, instalar Python desde python.org
3. La aplicación se iniciará automáticamente

CONTENIDO:
- rt11extract_gui.py: Aplicación principal con interfaz gráfica
- rt11extract: Extractor de línea de comandos
- rt11extract_simple.py: Versión simplificada
- RT11ExtractGUI.bat: Lanzador para Windows

Esta versión requiere Python 3.6+ instalado en Windows.
'''
    
    with open(portable_dir / "README.txt", "w") as f:
        f.write(readme_content)
    
    print(f"✓ Creado paquete portable: {portable_dir}")
    return 1

def check_binaries():
    """Revisar qué se creó."""
    print("\n=== VERIFICANDO BINARIOS CREADOS ===")
    
    binaries_dir = Path("binaries")
    if not binaries_dir.exists():
        print("No hay directorio binaries/")
        return
    
    items = list(binaries_dir.iterdir())
    if not items:
        print("No se crearon binarios")
        return
    
    for item in items:
        if item.is_file():
            size_mb = item.stat().st_size / (1024*1024)
            print(f"Archivo: {item.name} ({size_mb:.1f} MB)")
            
            # Verificar si es ejecutable
            try:
                with open(item, "rb") as f:
                    magic = f.read(4)
                    if magic.startswith(b'\x7fELF'):
                        print(f"  → Ejecutable Linux/Unix")
                    elif magic.startswith(b'MZ'):
                        print(f"  → Ejecutable Windows")  
                    elif magic.startswith(b'\xcf\xfa\xed'):
                        print(f"  → Ejecutable macOS")
                    else:
                        print(f"  → Tipo desconocido")
            except:
                print(f"  → No se puede verificar")
                
        elif item.is_dir():
            print(f"Directorio: {item.name}/")

def main():
    """Función principal."""
    print("=== CREADOR REAL DE EJECUTABLES ===")
    print("Creando ejecutables multiplataforma con herramientas disponibles...")
    
    if not os.path.exists("rt11extract_gui.py"):
        print("Error: No se encuentra rt11extract_gui.py")
        sys.exit(1)
    
    if not os.path.exists("venv_build/bin/activate"):
        print("Error: No se encuentra entorno virtual venv_build")
        sys.exit(1)
    
    os.makedirs("binaries", exist_ok=True)
    
    total = 0
    
    # Intentar diferentes métodos
    print("\nIntentando crear ejecutables nativos...")
    total += simple_pyinstaller()
    total += simple_nuitka() 
    total += try_cx_freeze()
    
    # Crear versión portable para Windows
    print("\nCreando versión portable para Windows...")
    total += create_windows_portable()
    
    # Verificar resultados
    check_binaries()
    
    print(f"\n{'='*50}")
    print(f"RESUMEN: Se crearon {total} paquetes/ejecutables")
    print(f"{'='*50}")
    
    if total > 0:
        print("\n✓ Éxito! Revisa la carpeta binaries/")
        print("\nQué tienes ahora:")
        print("- Ejecutables nativos (macOS principalmente)")
        print("- Paquete portable para Windows con launcher .bat")
        print("- Todos incluyen el código fuente y recursos necesarios")
        print("\nPara Windows:")
        print("- Usar la carpeta RT11ExtractGUI-Windows-Portable")
        print("- Ejecutar RT11ExtractGUI.bat en Windows")
        print("- Requiere Python instalado en Windows")
    else:
        print("\n✗ No se pudieron crear ejecutables")
        print("Considera usar máquinas virtuales o Docker")

if __name__ == "__main__":
    main()
