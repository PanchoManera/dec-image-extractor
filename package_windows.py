#!/usr/bin/env python3
"""
Empaquetador de ejecutables Windows para RT-11 Extractor
Crea archivos ZIP listos para distribución
"""

import zipfile
import shutil
from pathlib import Path

def create_distribution_packages():
    """Crea paquetes de distribución comprimidos"""
    print("📦 RT-11 Extractor - Empaquetador de Distribución Windows")
    print("=" * 60)
    
    base_dir = Path.cwd()
    windows_dir = base_dir / "binaries" / "windows"
    dist_dir = base_dir / "dist" / "windows"
    
    # Crear directorio de distribución
    dist_dir.mkdir(parents=True, exist_ok=True)
    
    architectures = ["win32", "win64", "arm64"]
    
    for arch in architectures:
        print(f"\n📦 === Empaquetando {arch.upper()} ===")
        
        arch_dir = windows_dir / arch
        if not arch_dir.exists():
            print(f"  ❌ Directorio {arch} no encontrado")
            continue
        
        # Paquete 1: Zipapp (requiere Python instalado)
        zipapp_package = dist_dir / f"RT11ExtractGUI-{arch.upper()}-RequiresPython.zip"
        print(f"  🎯 Creando {zipapp_package.name}...")
        
        with zipfile.ZipFile(zipapp_package, 'w', zipfile.ZIP_DEFLATED) as zf:
            # Agregar zipapp
            zipapp_file = arch_dir / f"RT11ExtractGUI-{arch.upper()}.pyz"
            if zipapp_file.exists():
                zf.write(zipapp_file, zipapp_file.name)
            
            # Agregar launcher
            launcher_file = arch_dir / f"RT11ExtractGUI-{arch.upper()}.bat"
            if launcher_file.exists():
                zf.write(launcher_file, launcher_file.name)
            
            # Agregar script de desbloqueo PowerShell
            unblock_script_path = base_dir / "unblock_files.ps1"
            if unblock_script_path.exists():
                zf.write(unblock_script_path, "unblock_files.ps1")
            
            # Agregar README mejorado
            readme_content = f"""RT-11 Extractor para Windows {arch.upper()}
============================================

REQUISITOS:
- Windows {arch.upper()}
- Python 3.6 o superior instalado
- Python debe estar en el PATH del sistema

COMO USAR:
1. Extrae todos los archivos a una carpeta
2. Si Windows bloquea archivos:
   - Ejecuta: unblock_files.ps1 (clic derecho → Ejecutar con PowerShell)
   - O desbloquea manualmente: clic derecho en .pyz → Propiedades → Desbloquear
3. Ejecuta RT11ExtractGUI-{arch.upper()}.bat
4. La aplicación se abrirá automáticamente

ARCHIVOS INCLUIDOS:
- RT11ExtractGUI-{arch.upper()}.bat: Launcher de Windows
- RT11ExtractGUI-{arch.upper()}.pyz: Aplicación Python comprimida
- unblock_files.ps1: Script para desbloquear archivos automáticamente
- README.txt: Este archivo

SOLUCION DE PROBLEMAS:
Si aparece "No se encontró el archivo .pyz":
1. Verifica que ambos archivos (.bat y .pyz) estén en la misma carpeta
2. Ejecuta unblock_files.ps1 para desbloquear archivos
3. O desbloquea manualmente: clic derecho → Propiedades → Desbloquear

INSTALACION DE PYTHON:
Si no tienes Python instalado:
1. Ve a https://python.org
2. Descarga Python 3.11 o superior
3. Durante la instalación, marca "Add Python to PATH"

ALTERNATIVA:
Usa la versión Portable que no requiere Python instalado.

Desarrollado para Windows desde macOS ARM64
Tamaño del paquete: ~37 KB
"""
            zf.writestr("README.txt", readme_content)
        
        zipapp_size = zipapp_package.stat().st_size / 1024
        print(f"    ✓ Creado: {zipapp_size:.1f} KB")
        
        # Paquete 2: Portable (incluye Python embebido)
        portable_dir = arch_dir / "portable"
        if portable_dir.exists():
            portable_package = dist_dir / f"RT11ExtractGUI-{arch.upper()}-Portable.zip"
            print(f"  🎯 Creando {portable_package.name}...")
            
            with zipfile.ZipFile(portable_package, 'w', zipfile.ZIP_DEFLATED) as zf:
                # Agregar todo el contenido portable
                for file_path in portable_dir.rglob("*"):
                    if file_path.is_file() and not file_path.name.endswith(".zip"):
                        arcname = file_path.relative_to(portable_dir)
                        zf.write(file_path, arcname)
            
            portable_size = portable_package.stat().st_size / (1024 * 1024)
            print(f"    ✓ Creado: {portable_size:.1f} MB")
        
        print(f"  ✅ {arch.upper()} empaquetado")
    
    print(f"\n🎉 ¡TODOS LOS PAQUETES CREADOS!")
    show_distribution_summary(dist_dir)

def show_distribution_summary(dist_dir):
    """Muestra resumen de paquetes creados"""
    print(f"\n📋 PAQUETES DE DISTRIBUCIÓN CREADOS:")
    print("=" * 50)
    
    packages = list(dist_dir.glob("*.zip"))
    packages.sort()
    
    total_size = 0
    
    for package in packages:
        size_mb = package.stat().st_size / (1024 * 1024)
        total_size += size_mb
        
        if "RequiresPython" in package.name:
            print(f"📦 {package.name} ({size_mb:.2f} MB) - Requiere Python")
        elif "Portable" in package.name:
            print(f"🎯 {package.name} ({size_mb:.2f} MB) - Totalmente portable")
    
    print(f"\n💾 Tamaño total: {total_size:.1f} MB")
    print(f"📂 Ubicación: {dist_dir}")
    
    print(f"\n💡 RECOMENDACIONES:")
    print("• Para usuarios con Python: Usar paquetes 'RequiresPython' (más pequeños)")
    print("• Para usuarios sin Python: Usar paquetes 'Portable' (más grandes)")
    print("• Los paquetes portables son ideales para distribución masiva")

def main():
    create_distribution_packages()

if __name__ == "__main__":
    main()
