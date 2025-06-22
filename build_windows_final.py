#!/usr/bin/env python3
"""
Generador de ejecutables Windows reales para RT-11 Extractor
Crea ejecutables que funcionen en Windows sin dependencias externas
"""

import os
import sys
import zipfile
import shutil
import urllib.request
from pathlib import Path

class WindowsExecutableBuilder:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.temp_dir = self.base_dir / "temp_windows_build"
        self.output_dir = self.base_dir / "binaries" / "windows"
        
        # URLs de Python embebido
        self.python_urls = {
            "win32": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-win32.zip",
            "win64": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-amd64.zip", 
            "arm64": "https://www.python.org/ftp/python/3.11.9/python-3.11.9-embed-arm64.zip"
        }
    
    def setup_temp_directory(self):
        """Prepara directorio temporal con código fuente"""
        print("📁 Preparando archivos fuente...")
        
        # Limpiar y crear directorio temporal
        if self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
        self.temp_dir.mkdir()
        
        # Copiar archivos fuente
        source_files = [
            "rt11extract_gui.py",
            "rt11extract_simple.py", 
            "images.png",
            "rt11extract"
        ]
        
        for file in source_files:
            if Path(file).exists():
                shutil.copy(file, self.temp_dir)
                print(f"  ✓ {file}")
        
        # Crear __main__.py para zipapp
        main_content = """#!/usr/bin/env python3
import sys
import os

# Agregar directorio actual al path
sys.path.insert(0, os.path.dirname(__file__))

# Importar y ejecutar GUI
try:
    from rt11extract_gui import main
    if __name__ == "__main__":
        main()
except ImportError as e:
    print(f"Error: No se pudo importar rt11extract_gui: {e}")
    input("Presiona Enter para continuar...")
"""
        
        (self.temp_dir / "__main__.py").write_text(main_content)
        print("  ✓ __main__.py")
    
    def create_zipapp(self, arch):
        """Crea un zipapp Python para la arquitectura especificada"""
        print(f"📦 Creando zipapp para {arch}...")
        
        arch_dir = self.output_dir / arch
        arch_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear zipapp
        zipapp_path = arch_dir / f"RT11ExtractGUI-{arch.upper()}.pyz"
        
        with zipfile.ZipFile(zipapp_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in self.temp_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(self.temp_dir)
                    zf.write(file_path, arcname)
        
        print(f"  ✓ Zipapp creado: {zipapp_path.name} ({zipapp_path.stat().st_size} bytes)")
        return zipapp_path
    
    def create_launcher_script(self, arch):
        """Crea script launcher .bat para Windows"""
        print(f"🚀 Creando launcher para {arch}...")
        
        arch_dir = self.output_dir / arch
        
        # Script .bat mejorado con diagnósticos
        launcher_content = f"""@echo off
setlocal enabledelayedexpansion
title RT-11 Extractor for {arch.upper()}
cd /d "%~dp0"

echo ================================================
echo RT-11 Extractor para Windows {arch.upper()}
echo ================================================
echo.
echo Buscando Python instalado...
echo.

REM Verificar si existe el archivo zipapp
if not exist "RT11ExtractGUI-{arch.upper()}.pyz" (
    echo ERROR: No se encontro el archivo RT11ExtractGUI-{arch.upper()}.pyz
    echo.
    echo POSIBLES CAUSAS:
    echo 1. Los archivos no estan en la misma carpeta
    echo 2. Windows bloqueo el archivo por seguridad
    echo 3. El archivo fue renombrado o movido
    echo.
    echo SOLUCION:
    echo 1. Verifica que estos archivos esten juntos:
    echo    - RT11ExtractGUI-{arch.upper()}.bat
    echo    - RT11ExtractGUI-{arch.upper()}.pyz
    echo.
    echo 2. Si Windows bloqueo el archivo:
    echo    - Clic derecho en RT11ExtractGUI-{arch.upper()}.pyz
    echo    - Selecciona 'Propiedades'
    echo    - En la pestana 'General', busca 'Seguridad'
    echo    - Marca 'Desbloquear' si aparece
    echo    - Clic 'Aplicar' y 'Aceptar'
    echo.
    echo 3. ALTERNATIVA: Usa la version portable
    echo    No requiere desbloquear archivos
    echo.
    pause
    goto :end
)

REM Intentar python command
echo Probando 'python'...
python --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Encontrado: python
    for /f "tokens=2" %%i in ('python --version 2^>^&1') do set PYTHON_VER=%%i
    echo Version: !PYTHON_VER!
    echo.
    echo Ejecutando RT-11 Extractor...
    python "RT11ExtractGUI-{arch.upper()}.pyz" %*
    if %errorlevel% equ 0 goto :success
    echo Error ejecutando con 'python'
    echo.
)

REM Intentar py launcher
echo Probando 'py -3'...
py -3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Encontrado: py launcher
    for /f "tokens=2" %%i in ('py -3 --version 2^>^&1') do set PYTHON_VER=%%i
    echo Version: !PYTHON_VER!
    echo.
    echo Ejecutando RT-11 Extractor...
    py -3 "RT11ExtractGUI-{arch.upper()}.pyz" %*
    if %errorlevel% equ 0 goto :success
    echo Error ejecutando con 'py -3'
    echo.
)

REM Intentar python3
echo Probando 'python3'...
python3 --version >nul 2>&1
if %errorlevel% equ 0 (
    echo Encontrado: python3
    for /f "tokens=2" %%i in ('python3 --version 2^>^&1') do set PYTHON_VER=%%i
    echo Version: !PYTHON_VER!
    echo.
    echo Ejecutando RT-11 Extractor...
    python3 "RT11ExtractGUI-{arch.upper()}.pyz" %*
    if %errorlevel% equ 0 goto :success
    echo Error ejecutando con 'python3'
    echo.
)

REM Si llegamos aqui, Python no se encontro
echo ================================================
echo ERROR: No se encontro Python 3.6+ instalado
echo ================================================
echo.
echo SOLUCION:
echo 1. Ve a https://python.org
echo 2. Descarga Python 3.11 o superior
echo 3. Durante la instalacion:
echo    - Marca "Add Python to PATH"
echo    - Marca "Install for all users" (opcional)
echo 4. Reinicia esta aplicacion
echo.
echo ALTERNATIVA:
echo Usa la version portable que no requiere Python
echo.
echo Presiona cualquier tecla para salir...
pause >nul
goto :end

:success
echo.
echo ================================================
echo RT-11 Extractor terminado correctamente
echo ================================================
pause
goto :end

:end
endlocal
"""
        
        launcher_path = arch_dir / f"RT11ExtractGUI-{arch.upper()}.bat"
        launcher_path.write_text(launcher_content, encoding='utf-8')
        
        print(f"  ✓ Launcher creado: {launcher_path.name}")
        return launcher_path
    
    def download_python_embedded(self, arch):
        """Descarga Python embebido para crear ejecutable portable"""
        print(f"⬇️  Descargando Python embebido para {arch}...")
        
        if arch not in self.python_urls:
            print(f"  ❌ Arquitectura {arch} no soportada")
            return None
        
        arch_dir = self.output_dir / arch / "portable"
        arch_dir.mkdir(parents=True, exist_ok=True)
        
        # Descargar Python embebido
        python_zip = arch_dir / f"python-{arch}.zip"
        if not python_zip.exists():
            print(f"  📥 Descargando desde {self.python_urls[arch]}")
            try:
                urllib.request.urlretrieve(self.python_urls[arch], python_zip)
                print(f"  ✓ Descargado: {python_zip.name}")
            except Exception as e:
                print(f"  ❌ Error descargando: {e}")
                return None
        else:
            print(f"  ✓ Ya existe: {python_zip.name}")
        
        # Extraer Python
        python_dir = arch_dir / "python"
        if not python_dir.exists():
            print(f"  📂 Extrayendo Python...")
            with zipfile.ZipFile(python_zip, 'r') as zf:
                zf.extractall(python_dir)
            print(f"  ✓ Python extraído en: {python_dir}")
        
        return python_dir
    
    def create_portable_executable(self, arch):
        """Crea ejecutable portable con Python embebido"""
        print(f"🎯 Creando ejecutable portable para {arch}...")
        
        # Descargar Python embebido
        python_dir = self.download_python_embedded(arch)
        if not python_dir:
            return None
        
        portable_dir = self.output_dir / arch / "portable"
        app_dir = portable_dir / "app"
        app_dir.mkdir(exist_ok=True)
        
        # Copiar código fuente
        for file_path in self.temp_dir.rglob("*"):
            if file_path.is_file():
                dest_path = app_dir / file_path.relative_to(self.temp_dir)
                dest_path.parent.mkdir(parents=True, exist_ok=True)
                shutil.copy2(file_path, dest_path)
        
        # Crear launcher portable mejorado
        launcher_content = f"""@echo off
setlocal enabledelayedexpansion
title RT-11 Extractor Portable {arch.upper()}
cd /d "%~dp0"

echo ========================================================
echo RT-11 Extractor Portable para Windows {arch.upper()}
echo ========================================================
echo.
echo Verificando archivos necesarios...
echo.

REM Verificar Python embebido
if not exist "python\\python.exe" (
    echo ERROR: No se encontro python\\python.exe
    echo.
    echo La carpeta python debe contener:
    echo - python.exe
    echo - python{arch[3:] if len(arch) > 3 else ""}.dll
    echo - Bibliotecas Python
    echo.
    echo Verifica que la descarga se completo correctamente
    pause
    exit /b 1
)

REM Verificar aplicacion
if not exist "app\\__main__.py" (
    echo ERROR: No se encontro app\\__main__.py
    echo Verifica que la carpeta app este completa
    pause
    exit /b 1
)

REM Verificar motor RT-11
if not exist "app\\rt11extract" (
    echo ERROR: No se encontro el motor rt11extract
    echo Verifica que todos los archivos esten presentes
    pause
    exit /b 1
)

echo Todos los archivos encontrados correctamente
echo.
echo Iniciando RT-11 Extractor...
echo.

REM Ejecutar aplicacion
python\\python.exe app\\__main__.py %*
set EXIT_CODE=%errorlevel%

echo.
if %EXIT_CODE% equ 0 (
    echo ========================================================
    echo RT-11 Extractor terminado correctamente
    echo ========================================================
) else (
    echo ========================================================
    echo Error ejecutando RT-11 Extractor (Codigo: %EXIT_CODE%)
    echo ========================================================
    echo.
    echo Posibles causas:
    echo - Archivo RT-11 no valido
    echo - Permisos insuficientes
    echo - Archivo corrupto
    echo.
    echo Intenta ejecutar desde linea de comandos para mas detalles:
    echo python\\python.exe app\\__main__.py
)

echo.
echo Presiona cualquier tecla para salir...
pause >nul
endlocal
exit /b %EXIT_CODE%
"""
        
        launcher_path = portable_dir / f"RT11ExtractGUI-{arch.upper()}-Portable.bat"
        launcher_path.write_text(launcher_content, encoding='utf-8')
        
        print(f"  ✓ Portable creado: {launcher_path}")
        
        # Crear README
        readme_content = f"""RT-11 Extractor Portable {arch.upper()}
=====================================

Este es un ejecutable portable que NO requiere instalacion de Python.

COMO USAR:
1. Ejecuta RT11ExtractGUI-{arch.upper()}-Portable.bat
2. La aplicacion se abrira automaticamente

CONTENIDO:
- python/: Python embebido v3.11.9
- app/: Codigo fuente de RT-11 Extractor  
- RT11ExtractGUI-{arch.upper()}-Portable.bat: Launcher

COMPATIBILIDAD:
- Windows {arch.upper()}
- No requiere instalacion de Python
- Totalmente portable

Desarrollado para Windows desde macOS ARM64
"""
        
        (portable_dir / "README.txt").write_text(readme_content, encoding='utf-8')
        
        return launcher_path
    
    def build_all_windows_executables(self):
        """Construye todos los ejecutables Windows"""
        print("🪟 RT-11 Extractor - Constructor de Ejecutables Windows")
        print("=" * 60)
        
        # Preparar archivos fuente
        self.setup_temp_directory()
        
        # Crear ejecutables para cada arquitectura
        architectures = ["win32", "win64", "arm64"]
        
        for arch in architectures:
            print(f"\n🔨 === Construyendo {arch.upper()} ===")
            
            # Método 1: Zipapp + Launcher (requiere Python instalado)
            zipapp_path = self.create_zipapp(arch)
            launcher_path = self.create_launcher_script(arch)
            
            # Método 2: Portable con Python embebido
            portable_path = self.create_portable_executable(arch)
            
            print(f"✅ {arch.upper()} completado")
        
        # Limpiar directorio temporal
        shutil.rmtree(self.temp_dir)
        
        print(f"\n🎉 ¡TODOS LOS EJECUTABLES WINDOWS CREADOS!")
        self.show_summary()
    
    def show_summary(self):
        """Muestra resumen de archivos creados"""
        print(f"\n📋 RESUMEN DE EJECUTABLES CREADOS:")
        print("=" * 50)
        
        for arch in ["win32", "win64", "arm64"]:
            print(f"\n🔷 {arch.upper()}:")
            
            arch_dir = self.output_dir / arch
            if arch_dir.exists():
                # Zipapp + Launcher
                zipapp = arch_dir / f"RT11ExtractGUI-{arch.upper()}.pyz"
                launcher = arch_dir / f"RT11ExtractGUI-{arch.upper()}.bat"
                
                if zipapp.exists():
                    size_mb = zipapp.stat().st_size / 1024
                    print(f"  📦 Zipapp: {zipapp.name} ({size_mb:.1f} KB)")
                
                if launcher.exists():
                    print(f"  🚀 Launcher: {launcher.name}")
                
                # Portable
                portable_dir = arch_dir / "portable"
                if portable_dir.exists():
                    portable_launcher = portable_dir / f"RT11ExtractGUI-{arch.upper()}-Portable.bat"
                    if portable_launcher.exists():
                        print(f"  🎯 Portable: {portable_launcher.name}")
        
        print(f"\n💡 COMO USAR:")
        print("1. Zipapp (.pyz + .bat): Requiere Python 3.6+ instalado en Windows")
        print("2. Portable: No requiere Python, todo incluido")
        print("\n📂 Ubicación: ./binaries/windows/")

def main():
    builder = WindowsExecutableBuilder()
    builder.build_all_windows_executables()

if __name__ == "__main__":
    main()
