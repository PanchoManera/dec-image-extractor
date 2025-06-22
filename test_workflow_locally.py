#!/usr/bin/env python3
"""
Script para probar localmente algunos comandos del workflow de GitHub Actions.
Esto simula la parte de macOS del workflow para verificar que funciona.
"""

import os
import subprocess
import sys
from pathlib import Path

def run_command(cmd, cwd=None):
    """Ejecuta un comando y muestra el resultado"""
    print(f"\n🔧 Ejecutando: {cmd}")
    try:
        result = subprocess.run(cmd, shell=True, cwd=cwd, 
                              capture_output=True, text=True, check=True)
        if result.stdout:
            print(f"✅ Salida:\n{result.stdout}")
        return result.returncode == 0
    except subprocess.CalledProcessError as e:
        print(f"❌ Error (código {e.returncode}):")
        if e.stdout:
            print(f"Stdout: {e.stdout}")
        if e.stderr:
            print(f"Stderr: {e.stderr}")
        return False

def check_files():
    """Verifica que los archivos necesarios existan"""
    print("\n📁 Verificando archivos necesarios...")
    
    required_files = [
        'rt11extract_gui.py',
        'rt11extract',
        'icon.ico',
        'images.png'
    ]
    
    missing_files = []
    for file in required_files:
        if not Path(file).exists():
            missing_files.append(file)
        else:
            print(f"✅ {file}")
    
    if missing_files:
        print(f"❌ Archivos faltantes: {', '.join(missing_files)}")
        return False
    
    return True

def test_pyinstaller_installation():
    """Prueba la instalación de PyInstaller"""
    print("\n🐍 Probando PyInstaller...")
    
    # Instalar PyInstaller si no está instalado
    if not run_command("pip install pyinstaller pillow"):
        print("❌ No se pudo instalar PyInstaller")
        return False
    
    # Verificar que PyInstaller funciona
    if not run_command("pyinstaller --version"):
        print("❌ PyInstaller no funciona correctamente")
        return False
    
    return True

def test_macos_build():
    """Prueba la compilación para macOS (similar al workflow)"""
    print("\n🍎 Probando compilación macOS ARM64...")
    
    # Limpiar builds anteriores
    run_command("rm -rf build dist *.spec")
    
    # Compilar GUI
    cmd_gui = 'pyinstaller --onefile --windowed --name "RT11ExtractGUI-macOS-ARM64-Test" --icon="icon.ico" --add-data "images.png:." --target-arch arm64 rt11extract_gui.py'
    if not run_command(cmd_gui):
        print("❌ No se pudo compilar la GUI")
        return False
    
    # Compilar CLI
    cmd_cli = 'pyinstaller --onefile --name "RT11Extract-macOS-ARM64-Test" --icon="icon.ico" --target-arch arm64 rt11extract'
    if not run_command(cmd_cli):
        print("❌ No se pudo compilar la CLI")
        return False
    
    # Verificar que los ejecutables se crearon
    gui_exe = Path("dist/RT11ExtractGUI-macOS-ARM64-Test")
    cli_exe = Path("dist/RT11Extract-macOS-ARM64-Test")
    
    if gui_exe.exists() and cli_exe.exists():
        print(f"✅ Ejecutables creados:")
        print(f"   - GUI: {gui_exe} ({gui_exe.stat().st_size} bytes)")
        print(f"   - CLI: {cli_exe} ({cli_exe.stat().st_size} bytes)")
        return True
    else:
        print("❌ No se encontraron los ejecutables")
        return False

def create_test_package():
    """Crea un paquete de prueba similar al workflow"""
    print("\n📦 Creando paquete de prueba...")
    
    package_dir = Path("RT11Extractor-macOS-arm64-Test")
    package_dir.mkdir(exist_ok=True)
    
    # Copiar ejecutables
    gui_src = Path("dist/RT11ExtractGUI-macOS-ARM64-Test")
    cli_src = Path("dist/RT11Extract-macOS-ARM64-Test")
    
    if gui_src.exists():
        run_command(f"cp '{gui_src}' '{package_dir}/'")
        run_command(f"chmod +x '{package_dir/gui_src.name}'")
    
    if cli_src.exists():
        run_command(f"cp '{cli_src}' '{package_dir}/'")
        run_command(f"chmod +x '{package_dir/cli_src.name}'")
    
    # Copiar README
    if Path("README.md").exists():
        run_command(f"cp README.md '{package_dir}/'")
    
    # Crear README específico
    readme_content = """RT-11 Extractor para macOS ARM64 (Prueba Local)

Ejecutables incluidos:
- RT11ExtractGUI-macOS-ARM64-Test (Interfaz gráfica)
- RT11Extract-macOS-ARM64-Test (Línea de comandos)

Para usar desde Terminal, otorgue permisos de ejecución si es necesario:
chmod +x RT11Extract*

Esta es una versión de prueba compilada localmente.
"""
    
    with open(package_dir / "README_macOS_Test.txt", "w") as f:
        f.write(readme_content)
    
    print(f"✅ Paquete creado en: {package_dir}")
    
    # Mostrar contenido
    run_command(f"ls -la '{package_dir}'")
    
    return True

def main():
    """Función principal"""
    print("🚀 Probando workflow de GitHub Actions localmente")
    print("=" * 50)
    
    # Verificar archivos
    if not check_files():
        print("❌ Faltan archivos necesarios")
        return 1
    
    # Probar PyInstaller
    if not test_pyinstaller_installation():
        print("❌ PyInstaller no funciona")
        return 1
    
    # Probar compilación
    if not test_macos_build():
        print("❌ La compilación falló")
        return 1
    
    # Crear paquete
    if not create_test_package():
        print("❌ No se pudo crear el paquete")
        return 1
    
    print("\n🎉 ¡Prueba local exitosa!")
    print("\nEsto significa que el workflow de GitHub Actions debería funcionar.")
    print("Puedes subir los cambios y el workflow compilará automáticamente para todas las plataformas.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())
