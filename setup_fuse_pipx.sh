#!/bin/bash

# Script de configuración RT-11 FUSE usando pipx (Alternativo)
# ============================================================

set -e

echo "RT-11 FUSE Driver - Configuración con pipx"
echo "==========================================="
echo

# Función para verificar si un comando existe
command_exists() {
    command -v "$1" >/dev/null 2>&1
}

# Verificar Python 3
if ! command_exists python3; then
    echo "Error: Python 3 no está instalado"
    exit 1
fi

echo "✓ Python 3 encontrado: $(python3 --version)"

# Verificar/instalar pipx
if ! command_exists pipx; then
    echo "pipx no encontrado. Instalando..."
    if command_exists brew; then
        brew install pipx
        pipx ensurepath
    else
        echo "Por favor instala pipx manualmente:"
        echo "  brew install pipx"
        exit 1
    fi
else
    echo "✓ pipx encontrado"
fi

# Verificar macFUSE
if [[ ! -f "/usr/local/lib/libfuse.dylib" && ! -f "/opt/homebrew/lib/libfuse.dylib" ]]; then
    echo "⚠️  macFUSE no está instalado"
    echo "Instalando con Homebrew..."
    if command_exists brew; then
        brew install --cask macfuse
    else
        echo "Instala macFUSE desde: https://osxfuse.github.io/"
        exit 1
    fi
else
    echo "✓ macFUSE encontrado"
fi

# Instalar fusepy con pipx
echo "Instalando fusepy con pipx..."
pipx install fusepy

echo "✓ fusepy instalado con pipx"
echo
echo "Uso:"
echo "  pipx run fusepy"
echo
echo "O usa el wrapper: ./rt11_fuse.sh"
