# Proyecto Extractores de Sistemas de Archivos DEC

Este proyecto contiene extractores para sistemas de archivos históricos de Digital Equipment Corporation (DEC), específicamente enfocados en los sistemas PDP-8 y PDP-11.

## Archivos del Proyecto

### Extractor PDP-8
- **`pdp8_extractor.py`** - Extractor principal para sistemas PDP-8
- **`test_pdp8_extractor.py`** - Script de prueba con imagen sintética
- **`README_PDP8.md`** - Documentación completa del extractor PDP-8

### Código Fuente de Referencia
- **`putr.asm`** - Código fuente completo de PUTR V2.01 de John Wilson
- **`README_PUTR.md`** - Análisis del código PUTR

## Sistemas Soportados

### PDP-8 (Implementado)
- **OS/8** - Sistema operativo principal del PDP-8
- **OS/78** - Variante para disquetes RX01/RX02
- **OS/278** - Variante para disquetes RX50/RX52
- **COS-310** - Sistema que usa formato OS/8

### PDP-8 (En Desarrollo)
- **PS/8** - Sistema para DECtapes
- **TSS/8** - Sistema de tiempo compartido
- **PUTR** - Formato específico de TSS/8

## Medios Soportados

### Disquetes de 8"
- **RX01** - 250KB, Single Sided, Single Density
- **RX02** - 500KB, Single Sided, Double Density
- **RX03** - 1001KB, Double Sided, Double Density

### Disquetes de 5.25"
- **RX50** - 400KB, Single Sided
- **RX52** - 800KB, Double Sided

### DECtapes
- **TU56** - DECtape estándar

### Archivos de Imagen
- Archivos de imagen lineales (sector por sector)
- Archivos de imagen interleaved (para velocidad en hardware original)

## Ejemplos de Uso

### Extractor PDP-8

```bash
# Instalar (solo requiere Python 3)
chmod +x pdp8_extractor.py

# Listar archivos sin extraer
./pdp8_extractor.py -l sistema_os8.dsk

# Extraer todos los archivos
./pdp8_extractor.py sistema_os8.dsk

# Extraer a directorio específico
./pdp8_extractor.py -o extracted_files sistema_os8.dsk

# Probar con imagen sintética
python3 test_pdp8_extractor.py
```

### Salida de Ejemplo

```
🚀 Iniciando extractor PDP-8...
📀 Medio: RX50
💾 Sistema: OS/8
📊 Bloques: 800

📂 Entradas en directorio: 12
🔢 Palabras info por entrada: 1

📋 Archivos en OS/8:
======================================================================
Nombre               Tipo         Tamaño   Bloque   Fecha       
----------------------------------------------------------------------
SYSTEM   BIN         .BINARY.     15       7        12/03/1985  
EDITOR   BIN         .BINARY.     8        22       15/03/1985  
BASIC    BIN         .BINARY.     24       30       20/03/1985  
HELLO    TXT         .ASCII.      1        54       22/03/1985  
----------------------------------------------------------------------
Total: 4 archivos, 48 bloques usados

📁 Extrayendo archivos a: extracted_pdp8
✅ SYSTEM   BIN -> SYSTEM_BIN (15 bloques)
✅ EDITOR   BIN -> EDITOR_BIN (8 bloques)  
✅ BASIC    BIN -> BASIC_BIN (24 bloques)
✅ HELLO    TXT -> HELLO_TXT (1 bloques)

🎉 Extracción completada!
```

## Arquitectura Técnica

### Formato de Directorio OS/8

El extractor implementa una interpretación completa del formato de directorio OS/8:

```
Bloque Home (Bloque 1):
  Word 0: Número de entradas en directorio
  Word 1: Bloque inicial del área vacía  
  Word 2: Puntero al siguiente segmento (0=último)
  Word 3: Archivo tentativo (normalmente 0)
  Word 4: -(Número de palabras info adicional)
  Word 5+: Entradas de directorio

Entrada de Directorio:
  Word 0: Tipo de archivo (.ASCII., .BINARY., etc.)
  Words 1-3: Nombre en codificación SIXBIT
  Word 4: Longitud en bloques
  Word 5: Información de trabajo/canal
  Word 6+: Información adicional (fecha, etc.)
```

### Codificación SIXBIT

Los nombres de archivo usan codificación SIXBIT de 6 bits por carácter:
- Permite caracteres `A-Z`, dígitos, y algunos especiales
- Cada word de 16 bits contiene aproximadamente 2.67 caracteres
- El extractor maneja la decodificación automáticamente

## Basado en PUTR

Este proyecto está basado en el análisis detallado del código fuente de **PUTR V2.01** de John Wilson, un programa histórico completo para transferencia de archivos entre sistemas DEC.

### Características de PUTR Original

- Soporte para 12+ sistemas de archivos DEC
- 30+ tipos de dispositivos y medios
- Interfaces múltiples (floppy, SCSI, COM ports, archivos imagen)
- Conversión automática ASCII/binaria
- Verificación y reparación de sistemas de archivos
- Detección automática de tipos de medio y sistemas de archivos

### Créditos

```
PUTR V2.01 - Peripheral Utility Transfer Routines
By John Wilson <wilson@dbit.com>
Copyright (C) 1995-2001 By John Wilson. All rights reserved.
```

## Desarrollo Futuro

### Próximas Implementaciones

1. **PS/8 DECtape Support**
   - Lectura de directorio PS/8
   - Manejo de interleave específico de DECtape
   - Soporte para archivos de múltiples segmentos

2. **TSS/8 PUTR Format**
   - Detección automática de TSS/8
   - Extracción de archivos PUTR
   - Manejo de estructura de directorios TSS/8

3. **Mejoras Generales**
   - Conversión automática de archivos ASCII
   - Soporte para imágenes interleaved
   - Verificación de checksums
   - Interfaz gráfica opcional

### Contribuir

Para añadir soporte para nuevos sistemas:

1. Estudiar el código PUTR relevante en `putr.asm`
2. Implementar función de detección en `detect_filesystem()`
3. Añadir método de lectura de directorio específico
4. Actualizar la función `run()` para manejar el nuevo sistema
5. Crear tests con imágenes de ejemplo

## Referencias Técnicas

- **PUTR V2.01 Source Code** - Implementación de referencia
- **PDP-8 System Reference Manual** - Especificaciones del hardware
- **OS/8 System Reference Manual** - Formato de sistema de archivos
- **DECtape Format Specification** - Estructura de DECtapes
- **DEC Peripheral Manuals** - RX01, RX02, RX50, TU56, etc.

## Limitaciones Conocidas

### Implementadas
- Solo OS/8 y variantes completamente funcionales
- Archivos extraídos como datos binarios (sin conversión)
- No maneja automáticamente imágenes interleaved
- Detección de filesystem basada en heurísticas

### Notas de Compatibilidad
- Probado con Python 3.6+
- Solo dependencias de biblioteca estándar
- Compatible con Linux, macOS, Windows
- Archivos de salida preservan estructura original

Este proyecto representa un esfuerzo por preservar y hacer accesibles los datos históricos almacenados en medios de los sistemas PDP-8 de DEC, utilizando como base el conocimiento acumulado en herramientas históricas como PUTR.
