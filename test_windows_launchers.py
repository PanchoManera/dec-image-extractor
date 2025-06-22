#!/usr/bin/env python3
"""
Script de pruebas para verificar launchers de Windows
Simula problemas comunes y muestra los nuevos diagnósticos
"""

import subprocess
import sys
from pathlib import Path

def simulate_windows_launcher_test():
    """
    Simula problemas típicos de los launchers Windows
    y muestra cómo los nuevos scripts los diagnostican
    """
    print("🔍 Simulador de Problemas de Launchers Windows")
    print("=" * 55)
    
    base_dir = Path.cwd()
    windows_dir = base_dir / "binaries" / "windows"
    
    if not windows_dir.exists():
        print("❌ Directorio binaries/windows no existe")
        print("   Ejecuta primero: ./build_windows_final.py")
        return
    
    print("\n📋 PROBLEMAS TÍPICOS EN WINDOWS Y SUS DIAGNÓSTICOS:")
    print("=" * 55)
    
    # Problema 1: Python no está en PATH
    print("\n🔴 PROBLEMA 1: Python no está instalado/en PATH")
    print("   Lo que ve el usuario:")
    print("   - 'python' no se reconoce como comando")
    print("   - El .bat termina inmediatamente")
    print("\n✅ NUEVA SOLUCIÓN:")
    print("   - Prueba múltiples comandos: python, py -3, python3")
    print("   - Muestra versiones encontradas")
    print("   - Guía paso a paso para instalar Python")
    print("   - Sugiere usar versión portable como alternativa")
    
    # Problema 2: Archivo .pyz no encontrado
    print("\n🔴 PROBLEMA 2: Archivos no están en el directorio correcto")
    print("   Lo que ve el usuario:")
    print("   - Error: No se puede abrir el archivo .pyz")
    print("\n✅ NUEVA SOLUCIÓN:")
    print("   - Verifica que el .pyz exista antes de ejecutar")
    print("   - Instruye al usuario a verificar archivos")
    print("   - Cambia al directorio correcto automáticamente")
    
    # Problema 3: Python demasiado viejo
    print("\n🔴 PROBLEMA 3: Versión de Python incompatible")
    print("   Lo que ve el usuario:")
    print("   - Error críptico de sintaxis o importación")
    print("\n✅ NUEVA SOLUCIÓN:")
    print("   - Muestra la versión de Python encontrada")
    print("   - Especifica versión mínima requerida (3.6+)")
    print("   - Recomienda actualizar Python")
    
    # Mostrar archivos disponibles
    print("\n📂 ARCHIVOS DISPONIBLES PARA PRUEBA:")
    print("=" * 40)
    
    for arch in ["win32", "win64", "arm64"]:
        arch_dir = windows_dir / arch
        if arch_dir.exists():
            print(f"\n🔷 {arch.upper()}:")
            
            # Zipapp launcher
            launcher = arch_dir / f"RT11ExtractGUI-{arch.upper()}.bat"
            if launcher.exists():
                print(f"   📄 {launcher.name}")
                print(f"      Tamaño: {launcher.stat().st_size} bytes")
            
            # Portable launcher
            portable = arch_dir / "portable" / f"RT11ExtractGUI-{arch.upper()}-Portable.bat"
            if portable.exists():
                print(f"   📄 {portable.name}")
                print(f"      Tamaño: {portable.stat().st_size} bytes")
    
    print("\n💡 RECOMENDACIONES PARA PROBAR EN WINDOWS:")
    print("=" * 50)
    print("1. Copia los archivos a una máquina Windows")
    print("2. Prueba PRIMERO la versión portable (no requiere Python)")
    print("3. Si usas la versión normal, instala Python desde python.org")
    print("4. Los nuevos launchers te guiarán paso a paso")
    
    print("\n🎯 CASOS DE PRUEBA RECOMENDADOS:")
    print("=" * 35)
    test_cases = [
        "Windows 10 sin Python → usar portable",
        "Windows 11 con Python 3.8 → usar launcher normal",
        "Windows Server → usar portable por seguridad",
        "Windows en VM → cualquier versión funciona",
        "Windows ARM64 → usar versión ARM64 específica"
    ]
    
    for i, case in enumerate(test_cases, 1):
        print(f"{i}. {case}")

def check_launcher_syntax():
    """Verifica que los archivos .bat tengan sintaxis correcta"""
    print("\n🔧 VERIFICACIÓN DE SINTAXIS DE LAUNCHERS:")
    print("=" * 45)
    
    base_dir = Path.cwd()
    windows_dir = base_dir / "binaries" / "windows"
    
    bat_files = list(windows_dir.rglob("*.bat"))
    
    if not bat_files:
        print("❌ No se encontraron archivos .bat")
        return
    
    for bat_file in bat_files:
        print(f"\n📄 {bat_file.relative_to(base_dir)}")
        
        # Verificaciones básicas
        content = bat_file.read_text(encoding='utf-8')
        
        checks = [
            ("Inicia con @echo off", content.startswith("@echo off")),
            ("Usa setlocal", "setlocal" in content),
            ("Cambia directorio", "cd /d" in content),
            ("Verifica archivos", "if not exist" in content),
            ("Maneja errores", "errorlevel" in content),
            ("Termina con endlocal", "endlocal" in content),
            ("Tiene pausas", "pause" in content)
        ]
        
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            print(f"  {status} {check_name}")
        
        # Mostrar tamaño
        size_kb = bat_file.stat().st_size / 1024
        print(f"  📏 Tamaño: {size_kb:.1f} KB")

def main():
    simulate_windows_launcher_test()
    check_launcher_syntax()
    
    print("\n🎉 VERIFICACIÓN COMPLETADA")
    print("Los nuevos launchers incluyen diagnósticos mejorados para")
    print("ayudar a los usuarios a resolver problemas comunes en Windows.")

if __name__ == "__main__":
    main()
