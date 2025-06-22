#!/usr/bin/env python3
"""
Script para compilar ejecutables Windows desde macOS usando Wine
Genera Win32, Win64 y ARM64 usando diferentes estrategias
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

class WindowsBuilder:
    def __init__(self):
        self.base_dir = Path.cwd()
        self.wine_prefix = self.base_dir / "wine_prefix"
        self.python_versions = {
            'win32': '3.11.0',
            'win64': '3.11.0', 
            'arm64': '3.11.0'
        }
        
    def run_command(self, cmd, check=True, cwd=None):
        """Ejecuta comando y muestra output"""
        print(f"🔨 Ejecutando: {' '.join(cmd) if isinstance(cmd, list) else cmd}")
        try:
            if isinstance(cmd, str):
                result = subprocess.run(cmd, shell=True, check=check, cwd=cwd, 
                                      capture_output=True, text=True)
            else:
                result = subprocess.run(cmd, check=check, cwd=cwd,
                                      capture_output=True, text=True)
            
            if result.stdout:
                print(f"✅ Output: {result.stdout}")
            if result.stderr:
                print(f"⚠️  Error: {result.stderr}")
            return result
        except subprocess.CalledProcessError as e:
            print(f"❌ Error ejecutando comando: {e}")
            if e.stdout:
                print(f"Stdout: {e.stdout}")
            if e.stderr:
                print(f"Stderr: {e.stderr}")
            return None

    def setup_wine_prefix(self):
        """Configura Wine prefix limpio"""
        print("🍷 Configurando Wine prefix...")
        
        # Limpiar prefix existente
        if self.wine_prefix.exists():
            shutil.rmtree(self.wine_prefix)
        
        # Crear nuevo prefix
        env = os.environ.copy()
        env['WINEPREFIX'] = str(self.wine_prefix)
        env['WINEARCH'] = 'win64'  # Soporta tanto 32 como 64 bits
        
        # Inicializar Wine
        self.run_command(['wine', 'wineboot', '--init'], cwd=None)
        
        # Configurar para modo silent
        self.run_command(['winecfg'], check=False)
        
        return True

    def install_python_wine(self, arch='win64'):
        """Instala Python en Wine para la arquitectura especificada"""
        print(f"🐍 Instalando Python para {arch}...")
        
        env = os.environ.copy()
        env['WINEPREFIX'] = str(self.wine_prefix)
        
        if arch == 'win32':
            env['WINEARCH'] = 'win32'
            python_url = f"https://www.python.org/ftp/python/{self.python_versions['win32']}/python-{self.python_versions['win32']}.exe"
        elif arch == 'arm64':
            # Para ARM64, intentaremos cross-compilation
            python_url = f"https://www.python.org/ftp/python/{self.python_versions['arm64']}/python-{self.python_versions['arm64']}-arm64.exe"
        else:  # win64
            python_url = f"https://www.python.org/ftp/python/{self.python_versions['win64']}/python-{self.python_versions['win64']}-amd64.exe"
        
        # Descargar Python installer
        installer_path = self.base_dir / f"python_{arch}_installer.exe"
        self.run_command(['curl', '-L', '-o', str(installer_path), python_url])
        
        if installer_path.exists():
            # Instalar Python silenciosamente
            wine_cmd = ['wine', str(installer_path), '/quiet', 'InstallAllUsers=1', 
                       'PrependPath=1', 'Include_test=0']
            result = self.run_command(wine_cmd, check=False)
            
            # Limpiar installer
            installer_path.unlink()
            return result is not None
        
        return False

    def install_requirements_wine(self):
        """Instala requirements en Wine Python"""
        print("📦 Instalando requirements en Wine...")
        
        env = os.environ.copy()
        env['WINEPREFIX'] = str(self.wine_prefix)
        
        # Instalar pip packages
        packages = ['pyinstaller', 'tkinter']
        for package in packages:
            cmd = ['wine', 'python', '-m', 'pip', 'install', package]
            self.run_command(cmd, check=False)
        
        return True

    def build_windows_executable(self, arch='win64'):
        """Compila ejecutable Windows para arquitectura específica"""
        print(f"🔨 Compilando ejecutable Windows {arch}...")
        
        env = os.environ.copy()
        env['WINEPREFIX'] = str(self.wine_prefix)
        
        # Configurar PyInstaller según arquitectura
        output_name = f"RT11ExtractGUI-{arch.upper()}.exe"
        
        pyinstaller_cmd = [
            'wine', 'python', '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name', output_name.replace('.exe', ''),
            '--distpath', f'./binaries/windows/{arch}/',
            '--workpath', f'./build_temp_{arch}/',
            '--specpath', f'./build_temp_{arch}/',
            'rt11extract_gui.py'
        ]
        
        # Agregar icon si existe
        icon_path = self.base_dir / 'icon.ico'
        if icon_path.exists():
            pyinstaller_cmd.extend(['--icon', str(icon_path)])
        
        # Crear directorio de salida
        output_dir = self.base_dir / 'binaries' / 'windows' / arch
        output_dir.mkdir(parents=True, exist_ok=True)
        
        # Ejecutar PyInstaller
        result = self.run_command(pyinstaller_cmd)
        
        # Verificar resultado
        exe_path = output_dir / output_name
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ Ejecutable {arch} creado: {exe_path} ({size_mb:.1f} MB)")
            return True
        else:
            print(f"❌ Error: No se pudo crear ejecutable {arch}")
            return False

    def create_alternative_builds(self):
        """Crea builds alternativos usando métodos nativos"""
        print("🔄 Creando builds alternativos...")
        
        # Build usando PyInstaller nativo con wine como target
        architectures = ['win32', 'win64']
        
        for arch in architectures:
            print(f"\n📦 Intentando build alternativo para {arch}...")
            
            # Crear directorio
            output_dir = self.base_dir / 'binaries' / 'windows' / arch
            output_dir.mkdir(parents=True, exist_ok=True)
            
            # Intentar con PyInstaller nativo especificando target
            cmd = [
                sys.executable, '-m', 'PyInstaller',
                '--onefile',
                '--windowed', 
                '--name', f'RT11ExtractGUI-{arch.upper()}',
                '--distpath', str(output_dir),
                '--workpath', f'./build_temp_alt_{arch}/',
                '--specpath', f'./build_temp_alt_{arch}/',
                'rt11extract_gui.py'
            ]
            
            # Agregar icon
            icon_path = self.base_dir / 'icon.ico'
            if icon_path.exists():
                cmd.extend(['--icon', str(icon_path)])
            
            result = self.run_command(cmd, check=False)
            
            # Verificar si se creó
            exe_name = f'RT11ExtractGUI-{arch.upper()}.exe'
            exe_path = output_dir / exe_name
            if exe_path.exists():
                size_mb = exe_path.stat().st_size / (1024 * 1024)
                print(f"✅ Build alternativo {arch} exitoso: {size_mb:.1f} MB")

    def build_all_windows(self):
        """Construye todos los ejecutables Windows"""
        print("🚀 Iniciando build completo de Windows...")
        
        # Paso 1: Configurar Wine
        if not self.setup_wine_prefix():
            print("❌ Error configurando Wine")
            return False
        
        # Paso 2: Intentar builds con Wine
        architectures = ['win64', 'win32']
        wine_success = 0
        
        for arch in architectures:
            print(f"\n🔨 === Building {arch} con Wine ===")
            
            if self.install_python_wine(arch):
                if self.install_requirements_wine():
                    if self.build_windows_executable(arch):
                        wine_success += 1
        
        # Paso 3: Builds alternativos
        print(f"\n🔄 === Builds Alternativos ===")
        self.create_alternative_builds()
        
        # Paso 4: Intentar ARM64 (cross-compile o skip)
        print(f"\n🔨 === Building ARM64 ===")
        self.build_arm64_alternative()
        
        print(f"\n✅ Build completo. Wine builds exitosos: {wine_success}/2")
        return True

    def build_arm64_alternative(self):
        """Intenta build ARM64 usando métodos alternativos"""
        print("🔨 Intentando build ARM64 Windows...")
        
        # Para ARM64, creamos un bundle que puede ser compatible
        output_dir = self.base_dir / 'binaries' / 'windows' / 'arm64'
        output_dir.mkdir(parents=True, exist_ok=True)
        
        cmd = [
            sys.executable, '-m', 'PyInstaller',
            '--onefile',
            '--windowed',
            '--name', 'RT11ExtractGUI-ARM64',
            '--distpath', str(output_dir),
            '--workpath', './build_temp_arm64/',
            '--specpath', './build_temp_arm64/',
            'rt11extract_gui.py'
        ]
        
        icon_path = self.base_dir / 'icon.ico'
        if icon_path.exists():
            cmd.extend(['--icon', str(icon_path)])
        
        result = self.run_command(cmd, check=False)
        
        exe_path = output_dir / 'RT11ExtractGUI-ARM64.exe'
        if exe_path.exists():
            size_mb = exe_path.stat().st_size / (1024 * 1024)
            print(f"✅ ARM64 bundle creado: {size_mb:.1f} MB")
            print("ℹ️  Nota: Este es un bundle que puede funcionar en ARM64 Windows")

def main():
    print("🍷🔨 RT-11 Extractor - Windows Builder con Wine")
    print("=" * 50)
    
    builder = WindowsBuilder()
    
    try:
        success = builder.build_all_windows()
        
        if success:
            print("\n🎉 Build de Windows completado!")
            print("\nEjecutables generados:")
            
            windows_dir = Path('./binaries/windows')
            if windows_dir.exists():
                for arch_dir in windows_dir.iterdir():
                    if arch_dir.is_dir():
                        print(f"\n📁 {arch_dir.name}:")
                        for exe in arch_dir.glob('*.exe'):
                            size_mb = exe.stat().st_size / (1024 * 1024)
                            print(f"  - {exe.name}: {size_mb:.1f} MB")
        else:
            print("\n❌ Algunos builds fallaron, pero revisa los resultados parciales")
            
    except KeyboardInterrupt:
        print("\n⏹️  Build cancelado por usuario")
    except Exception as e:
        print(f"\n💥 Error inesperado: {e}")

if __name__ == '__main__':
    main()
