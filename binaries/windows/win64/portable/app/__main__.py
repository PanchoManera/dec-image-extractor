#!/usr/bin/env python3
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
