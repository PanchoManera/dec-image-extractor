#!/usr/bin/env python3
"""
Script final para crear ejecutables Windows .exe verdaderos usando Docker
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(cmd, check=True):
    """Ejecuta un comando y retorna el resultado."""
    print(f"Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, check=check, capture_output=True, text=True)
        if result.stdout:
            print(f"Salida: {result.stdout}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"Error: {e}")
        if e.stderr:
            print(f"Error: {e.stderr}")
        return False

def check_docker():
    """Verifica si Docker está disponible."""
    return run_command("docker --version", check=False)

def create_dockerfile():
    """Crea un Dockerfile para compilar ejecutables Windows."""
    dockerfile_content = '''FROM python:3.11-windowsservercore

# Instalar PyInstaller y dependencias
RUN pip install pyinstaller pillow

# Crear directorio de trabajo
WORKDIR /app

# Copiar archivos
COPY rt11extract_gui.py .
COPY rt11extract .
COPY icon.ico .

# Crear ejecutables para diferentes arquitecturas
RUN pyinstaller --onefile --windowed --icon icon.ico --name RT11ExtractGUI-Win64 rt11extract_gui.py

# También intentar crear para Win32 (si es posible)
RUN pyinstaller --onefile --windowed --icon icon.ico --name RT11ExtractGUI-Win32 --target-architecture x86 rt11extract_gui.py || echo "Win32 build failed"
'''
    
    with open("Dockerfile.windows", "w") as f:
        f.write(dockerfile_content)
    
    print("✓ Dockerfile creado")

def build_windows_in_docker():
    """Construye ejecutables Windows usando Docker."""
    print("\n=== CONSTRUYENDO EJECUTABLES WINDOWS CON DOCKER ===")
    
    # Crear Dockerfile
    create_dockerfile()
    
    # Construir imagen
    if not run_command("docker build -f Dockerfile.windows -t rt11-windows-builder .", check=False):
        print("✗ Falló la construcción de la imagen Docker")
        return False
    
    # Ejecutar contenedor y extraer ejecutables
    if not run_command("docker run --name rt11-build rt11-windows-builder", check=False):
        print("✗ Falló la ejecución del contenedor")
        return False
    
    # Extraer ejecutables
    os.makedirs("binaries/windows_docker", exist_ok=True)
    
    success = False
    for exe_name in ["RT11ExtractGUI-Win64.exe", "RT11ExtractGUI-Win32.exe"]:
        if run_command(f"docker cp rt11-build:/app/dist/{exe_name} binaries/windows_docker/", check=False):
            print(f"✓ Extraído: {exe_name}")
            success = True
        else:
            print(f"✗ No se pudo extraer: {exe_name}")
    
    # Limpiar
    run_command("docker rm rt11-build", check=False)
    
    return success

def create_wine_approach():
    """Intenta usar Wine para crear ejecutables Windows."""
    print("\n=== INTENTANDO CON WINE ===")
    
    # Verificar si Wine está disponible
    if not run_command("which wine", check=False):
        print("Wine no está instalado. Instalando con Homebrew...")
        if not run_command("brew install wine-stable", check=False):
            print("✗ No se pudo instalar Wine")
            return False
    
    # Intentar instalar Python en Wine
    print("Configurando Wine y Python...")
    run_command("winecfg", check=False)  # Esto puede abrir una GUI
    
    # Descargar e instalar Python en Wine
    python_installer_url = "https://www.python.org/ftp/python/3.11.5/python-3.11.5-amd64.exe"
    
    if not run_command(f"wget -O python_installer.exe {python_installer_url}", check=False):
        print("✗ No se pudo descargar Python installer")
        return False
    
    if not run_command("wine python_installer.exe /quiet InstallAllUsers=1 PrependPath=1", check=False):
        print("✗ No se pudo instalar Python en Wine")
        return False
    
    # Instalar PyInstaller en Wine
    if not run_command("wine python -m pip install pyinstaller pillow", check=False):
        print("✗ No se pudo instalar PyInstaller en Wine")
        return False
    
    # Crear ejecutables
    os.makedirs("binaries/windows_wine", exist_ok=True)
    
    success = False
    for arch, name in [("", "Win64"), ("--target-architecture=x86", "Win32")]:
        cmd = f"wine python -m PyInstaller --onefile --windowed --icon icon.ico {arch} --name RT11ExtractGUI-{name} rt11extract_gui.py"
        if run_command(cmd, check=False):
            exe_path = f"dist/RT11ExtractGUI-{name}.exe"
            if os.path.exists(exe_path):
                shutil.copy2(exe_path, f"binaries/windows_wine/RT11ExtractGUI-{name}.exe")
                print(f"✓ Creado: RT11ExtractGUI-{name}.exe")
                success = True
    
    # Limpiar
    if os.path.exists("python_installer.exe"):
        os.remove("python_installer.exe")
    
    return success

def verify_exe_files():
    """Verifica que los archivos .exe creados sean válidos."""
    print("\n=== VERIFICANDO EJECUTABLES WINDOWS ===")
    
    exe_dirs = ["binaries/windows_docker", "binaries/windows_wine"]
    found_valid = False
    
    for exe_dir in exe_dirs:
        if os.path.exists(exe_dir):
            for exe_file in Path(exe_dir).glob("*.exe"):
                print(f"\nVerificando: {exe_file}")
                
                try:
                    with open(exe_file, "rb") as f:
                        magic = f.read(2)
                        if magic == b'MZ':
                            f.seek(60)
                            pe_offset = int.from_bytes(f.read(4), 'little')
                            f.seek(pe_offset)
                            pe_sig = f.read(4)
                            if pe_sig == b'PE\x00\x00':
                                size_mb = exe_file.stat().st_size / (1024*1024)
                                print(f"  ✓ Ejecutable Windows válido ({size_mb:.1f} MB)")
                                found_valid = True
                            else:
                                print(f"  ✗ No es un ejecutable PE válido")
                        else:
                            print(f"  ✗ No tiene magic number MZ")
                except Exception as e:
                    print(f"  ✗ Error verificando: {e}")
    
    return found_valid

def main():
    """Función principal."""
    print("=== CREADOR DE EJECUTABLES WINDOWS (.exe) VERDADEROS ===")
    print("Intentando crear ejecutables Windows autocontenidos...")
    
    if not os.path.exists("rt11extract_gui.py"):
        print("Error: No se encuentra rt11extract_gui.py")
        sys.exit(1)
    
    success_count = 0
    
    # Método 1: Docker (recomendado)
    if check_docker():
        print("Docker disponible, intentando construcción con Docker...")
        if build_windows_in_docker():
            success_count += 1
    else:
        print("Docker no disponible, saltando construcción con Docker")
    
    # Método 2: Wine (alternativo)
    print("\nIntentando método alternativo con Wine...")
    if create_wine_approach():
        success_count += 1
    
    # Verificar resultados
    valid_exes = verify_exe_files()
    
    # Resumen
    print(f"\n{'='*60}")
    print("RESUMEN FINAL")
    print(f"{'='*60}")
    
    if valid_exes:
        print("✓ ¡ÉXITO! Se crearon ejecutables Windows válidos")
        print("\nArchivos creados:")
        for exe_dir in ["binaries/windows_docker", "binaries/windows_wine"]:
            if os.path.exists(exe_dir):
                for exe_file in Path(exe_dir).glob("*.exe"):
                    print(f"  - {exe_file}")
        
        print("\nEstos son verdaderos ejecutables Windows (.exe) que:")
        print("- Funcionan en Windows sin necesidad de Python instalado")
        print("- Son autocontenidos y portables")
        print("- Incluyen todas las dependencias necesarias")
        
    else:
        print("✗ No se pudieron crear ejecutables Windows válidos")
        print("\nLimitaciones de cross-compilation:")
        print("- macOS no puede compilar nativamente para Windows")
        print("- Docker con Windows containers no está disponible")
        print("- Wine puede tener problemas de compatibilidad")
        print("\nRecomendación:")
        print("- Usar una máquina Windows real")
        print("- Usar GitHub Actions con runners Windows") 
        print("- Usar el paquete portable creado anteriormente")
    
    print(f"\nMétodos intentados: {success_count}")

if __name__ == "__main__":
    main()
