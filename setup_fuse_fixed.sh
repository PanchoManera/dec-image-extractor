#!/bin/bash

# Script de configuración para RT-11 FUSE Driver (Actualizado para macOS)
# ========================================================================

set -e

echo "RT-11 FUSE Driver - Configuración (macOS)"
echo "=========================================="
echo

# Detectar sistema operativo
if [[ "$OSTYPE" == "darwin"* ]]; then
    OS="macOS"
elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
    OS="Linux"
else
    echo "Sistema operativo no soportado: $OSTYPE"
    exit 1
fi

echo "Sistema detectado: $OS"
echo

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python 3
if ! command_exists python3; then
    echo "Error: Python 3 no está instalado"
    echo "Instala Python 3 desde https://www.python.org/"
    exit 1
fi

echo "✓ Python 3 encontrado: $(python3 --version)"

# Instalar FUSE según el sistema operativo
if [[ "$OS" == "macOS" ]]; then
    echo
    echo "Configurando FUSE para macOS..."
    
    # Verificar si macFUSE está instalado
    if [[ ! -f "/usr/local/lib/libfuse.dylib" && ! -f "/opt/homebrew/lib/libfuse.dylib" ]]; then
        echo "⚠️  macFUSE no está instalado"
        echo
        echo "Opciones de instalación:"
        echo "1. Descargar desde: https://osxfuse.github.io/"
        echo "2. Instalar con Homebrew: brew install --cask macfuse"
        echo
        read -p "¿Quieres intentar instalar con Homebrew? (y/n): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            if command_exists brew; then
                echo "Instalando macFUSE con Homebrew..."
                brew install --cask macfuse
            else
                echo "Homebrew no está instalado. Descarga macFUSE manualmente desde:"
                echo "https://osxfuse.github.io/"
                exit 1
            fi
        else
            echo "Por favor instala macFUSE manualmente y vuelve a ejecutar este script"
            exit 1
        fi
    else
        echo "✓ macFUSE encontrado"
    fi

elif [[ "$OS" == "Linux" ]]; then
    echo
    echo "Configurando FUSE para Linux..."
    
    # Verificar si FUSE está instalado
    if ! command_exists fusermount; then
        echo "⚠️  FUSE no está instalado"
        echo "Instalando FUSE..."
        
        if command_exists apt; then
            sudo apt update
            sudo apt install -y fuse libfuse-dev
        elif command_exists yum; then
            sudo yum install -y fuse fuse-devel
        elif command_exists dnf; then
            sudo dnf install -y fuse fuse-devel
        else
            echo "Error: No se pudo instalar FUSE automáticamente"
            echo "Instala manualmente: sudo apt install fuse libfuse-dev"
            exit 1
        fi
    else
        echo "✓ FUSE encontrado"
    fi
    
    # Agregar usuario al grupo fuse si existe
    if getent group fuse > /dev/null; then
        if ! groups $USER | grep -q fuse; then
            echo "Agregando usuario al grupo fuse..."
            sudo usermod -a -G fuse $USER
            echo "⚠️  Necesitas cerrar sesión y volver a iniciar para que los cambios tengan efecto"
        fi
    fi
fi

echo
echo "Configurando entorno virtual de Python..."

# Crear entorno virtual si no existe
VENV_DIR="./venv"
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Creando entorno virtual..."
    python3 -m venv "$VENV_DIR"
else
    echo "✓ Entorno virtual ya existe"
fi

# Activar entorno virtual e instalar dependencias
echo "Instalando fusepy en entorno virtual..."
source "$VENV_DIR/bin/activate"
pip install --upgrade pip
pip install fusepy

echo "✓ fusepy instalado en entorno virtual"

# Hacer ejecutables los scripts
echo
echo "Configurando permisos..."
chmod +x rt11_fuse_complete.py
chmod +x rt11_fuse.sh
chmod +x rt11extract

if [[ -f "rt11extract_gui.py" ]]; then
    chmod +x rt11extract_gui.py
fi

echo "✓ Permisos configurados"

# Crear directorio de montaje de ejemplo
MOUNT_DIR="$HOME/rt11_mount"
if [[ ! -d "$MOUNT_DIR" ]]; then
    mkdir -p "$MOUNT_DIR"
    echo "✓ Directorio de montaje creado: $MOUNT_DIR"
fi

echo
echo "Configuración completada ✓"
echo
echo "Uso del driver FUSE:"
echo "==================="
echo
echo "Para montar una imagen RT-11:"
echo "  ./rt11_fuse.sh imagen.dsk $MOUNT_DIR"
echo
echo "Para desmontar:"
if [[ "$OS" == "macOS" ]]; then
    echo "  umount $MOUNT_DIR"
else
    echo "  fusermount -u $MOUNT_DIR"
fi
echo
echo "Ejemplo completo:"
echo "  ./rt11_fuse.sh disk.dsk $MOUNT_DIR"
echo "  ls $MOUNT_DIR  # Ver archivos RT-11"
echo "  cat $MOUNT_DIR/ARCHIVO.TXT  # Leer archivo"
if [[ "$OS" == "macOS" ]]; then
    echo "  umount $MOUNT_DIR  # Desmontar"
else
    echo "  fusermount -u $MOUNT_DIR  # Desmontar"
fi
echo

# Verificar instalación
echo "Verificando instalación..."
if source "$VENV_DIR/bin/activate" && python3 -c "import fuse; print('✓ FUSE Python binding OK')"; then
    echo "✓ Instalación verificada correctamente"
else
    echo "⚠️  Hubo problemas con la instalación"
fi

if [[ "$OS" == "Linux" ]] && getent group fuse > /dev/null && ! groups $USER | grep -q fuse; then
    echo "⚠️  IMPORTANTE: Necesitas cerrar sesión y volver a iniciar para usar FUSE"
fi

echo
echo "¡Listo para usar con: ./rt11_fuse.sh imagen.dsk punto_montaje!"
