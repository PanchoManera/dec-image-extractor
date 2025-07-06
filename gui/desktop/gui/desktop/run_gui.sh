#!/bin/bash

# RT-11 Extractor GUI Launcher
# Activa el entorno virtual y lanza la GUI con soporte FUSE

echo "🚀 Iniciando RT-11 Extractor GUI..."

# Cambiar al directorio del script
cd "$(dirname "$0")"

# Verificar si existe el entorno virtual
if [ ! -d "venv" ]; then
    echo "⚠️  Entorno virtual no encontrado. Creándolo..."
    python3 -m venv venv
    source venv/bin/activate
    echo "📦 Instalando dependencias..."
    pip install fusepy pillow
else
    # Activar el entorno virtual existente
    source venv/bin/activate
fi

# Verificar que fusepy esté instalado
python -c "import fusepy" 2>/dev/null
if [ $? -ne 0 ]; then
    echo "📦 Instalando fusepy..."
    pip install fusepy pillow
fi

echo "✅ Entorno virtual activado con soporte FUSE"
echo "🖥️  Lanzando GUI..."

# Lanzar la GUI
python rt11extract_gui.py

echo "👋 GUI cerrada"
