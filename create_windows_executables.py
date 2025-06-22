#!/usr/bin/env python3
"""
Crear ejecutables Windows verdaderos usando métodos alternativos
"""

import os
import sys
import zipfile
import shutil
from pathlib import Path

def create_python_zipapp_exe():
    """Crea ejecutables Windows usando Python zipapp + launcher"""
    
    print("📦 Creando ejecutables Windows usando zipapp...")
    
    # Crear directorio temporal
    temp_dir = Path("temp_windows_build")
    temp_dir.mkdir(exist_ok=True)
    
    # Copiar archivos fuente
    shutil.copy("rt11extract_gui.py", temp_dir)
    shutil.copy("rt11extract_simple.py", temp_dir)
    shutil.copy("images.png", temp_dir)
    shutil.copy("rt11extract", temp_dir / "rt11extract")
    
    # Crear __main__.py
    main_content = '''#!/usr/bin/env python3
import sys
import os
sys.path.insert(0, os.path.dirname(__file__))
from rt11extract_gui import main
if __name__ == "__main__":
    main()
'''
    
    (temp_dir / "__main__.py").write_text(main_content)
    
    # Crear diferentes arquitecturas
    architectures = ["win32", "win64", "arm64"]
    
    for arch in architectures:
        print(f"🔨 Creando {arch}...")
        
        # Crear directorio de salida
        output_dir = Path("binaries/windows") / arch
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Crear ZIP con todo el código
        zip_path = output_dir / f"RT11ExtractGUI-{arch.upper()}.pyz"
        with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zf:
            for file_path in temp_dir.rglob("*"):
                if file_path.is_file():
                    arcname = file_path.relative_to(temp_dir)
                    zf.write(file_path, arcname)
        
        # Crear launcher batch
        launcher_content = f'''@echo off
REM RT-11 Extractor for {arch.upper()}
REM This requires Python 3.6+ to be installed on Windows

REM Try different Python executables
python "%~dp0RT11ExtractGUI-{arch.upper()}.pyz" %*
if errorlevel 1 (
    py -3 "%~dp0RT11ExtractGUI-{arch.upper()}.pyz" %*
    if errorlevel 1 (
        python3 "%~dp0RT11ExtractGUI-{arch.upper()}.pyz" %*
        if errorlevel 1 (
            echo Error: Python 3.6+ not found. Please install Python from python.org
            pause
        )
    )
)
'''
        
        batch_path = output_dir / f"RT11ExtractGUI-{arch.upper()}.bat"
        batch_path.write_text(launcher_content)
        
        print(f"✅ {arch} creado: {zip_path} + {batch_path}")
    
    # Limpiar
    shutil.rmtree(temp_dir)
    
    return True

def create_portable_windows_exe():
    """Crea un ejecutable portable usando embed Python"""
    
    print("🎯 Creando ejecutables portables...")
    
    script_content = '''
import os
import sys
import urllib.request
import zipfile
import subprocess
from pathlib import Path

def download_python_embed():
    """Descarga Python embebido para Windows"""
    urls = {
        "win32": "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-win32.zip",
        "win64": "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-amd64.zip",
        "arm64": "https://www.python.org/ftp/python/3.11.0/python-3.11.0-embed-arm64.zip"
    }
    
    for arch, url in urls.items():
        print(f"📥 Descargando Python embebido {arch}...")
        
        output_dir = Path("binaries/windows") / arch / "portable"
        output_dir.mkdir(parents=True, exist_ok=True)
        
        zip_path = output_dir / f"python-embed-{arch}.zip"
        
        # Descargar si no existe
        if not zip_path.exists():
            urllib.request.urlretrieve(url, zip_path)
        
        # Extraer Python
        python_dir = output_dir / "python"
        if not python_dir.exists():
            with zipfile.ZipFile(zip_path, 'r') as zf:
                zf.extractall(python_dir)
        
        # Copiar código fuente
        app_dir = output_dir / "app"
        app_dir.mkdir(exist_ok=True)
        
        import shutil
        shutil.copy("rt11extract_gui.py", app_dir)
        shutil.copy("rt11extract_simple.py", app_dir) 
        shutil.copy("images.png", app_dir)
        shutil.copy("rt11extract", app_dir / "rt11extract")
        
        # Crear launcher
        launcher = f"""@echo off
cd /d "%~dp0"
python\\python.exe app\\rt11extract_gui.py %*
pause
"""
        
        (output_dir / f"RT11ExtractGUI-{arch.upper()}.bat").write_text(launcher)
        
        print(f"✅ Portable {arch} creado en {output_dir}")

if __name__ == "__main__":
    download_python_embed()

'''
    
    script_path = Path("create_portable.py")
    script_path.write_text(script_content)
    
    return script_path

def main():
    print("🪟 Creador de Ejecutables Windows Verdaderos")
    print("=" * 50)
    
    # Método 1: Zipapp + Batch launcher
    print("\n📦 Método 1: Python zipapp + launcher")
    create_python_zipapp_exe()
    
    # Método 2: Script para crear portables
    print("\n🎯 Método 2: Creando script para ejecutables portables")
    script = create_portable_windows_exe()
    print(f"✅ Script creado: {script}")
    print("💡 Ejecuta 'python create_portable.py' para descargar Python embebido")
    
    print("\n🎉 Ejecutables Windows creados!")
    print("\nFormas de usar:")
    print("1. Zipapp (.pyz): Requiere Python instalado en Windows")
    print("2. Portable: Incluye Python embebido, funciona sin instalación")
    
    # Mostrar resultados
    print("\n📁 Archivos generados:")
    for exe in Path("binaries/windows").rglob("RT11ExtractGUI-*"):
        size = exe.stat().st_size if exe.is_file() else 0
        print(f"  {exe}: {size} bytes")

if __name__ == "__main__":
    main()
