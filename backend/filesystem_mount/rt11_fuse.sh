#!/bin/bash

# RT-11 FUSE Driver Wrapper
# =========================
# Este script activa el entorno virtual y ejecuta el driver FUSE

# Directorio del script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
VENV_DIR="$SCRIPT_DIR/venv"
FUSE_SCRIPT="$SCRIPT_DIR/rt11_fuse_complete.py"

# Verificar que el entorno virtual existe
if [[ ! -d "$VENV_DIR" ]]; then
    echo "Error: Entorno virtual no encontrado en $VENV_DIR"
    echo "Ejecuta primero: ./setup_fuse_fixed.sh"
    exit 1
fi

# Verificar que el script FUSE existe
if [[ ! -f "$FUSE_SCRIPT" ]]; then
    echo "Error: Script FUSE no encontrado en $FUSE_SCRIPT"
    exit 1
fi

# Activar entorno virtual y ejecutar script
source "$VENV_DIR/bin/activate"
python3 "$FUSE_SCRIPT" "$@"
