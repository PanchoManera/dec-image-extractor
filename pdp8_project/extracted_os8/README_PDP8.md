# Extractor de Sistemas de Archivos PDP-8

Este extractor está basado en el código fuente de **PUTR V2.01** de John Wilson, un programa completo para transferir archivos entre diferentes sistemas DEC.

## Sistemas de Archivos Soportados

### Implementados
- **OS/8** - Sistema operativo principal del PDP-8
- **OS/78** - Variante para disquetes RX01/RX02
- **OS/278** - Variante para disquetes RX50/RX52
- **COS-310** - Sistema que usa formato OS/8 con archivos texto especiales

### En Desarrollo
- **PS/8** - Sistema para DECtapes
- **TSS/8** - Sistema de tiempo compartido
- **PUTR** - Formato específico de TSS/8

## Formatos de Imagen Soportados

### Disquetes de 8"
- **RX01** - 250KB, Single Sided, Single Density (77×1×26×128)
- **RX02** - 500KB, Single Sided, Double Density (77×1×26×256)  
- **RX03** - 1001KB, Double Sided, Double Density (77×2×26×256)

### Disquetes de 5.25"
- **RX50** - 400KB, Single Sided (80×1×10×512)
- **RX52** - 800KB, Double Sided (80×2×10×512)

### DECtapes
- **TU56** - DECtape (578×256 bytes)

### Archivos de Imagen
- Archivos lineales de bloques de 512 bytes
- Archivos interleaved (orden de sectores alterado para velocidad)

## Uso

### Instalación
```bash
# Hacer ejecutable
chmod +x pdp8_extractor.py

# Opcionalmente instalar dependencias (solo Python estándar requerido)
python3 -m pip install --user dataclasses typing
```

### Uso Básico
```bash
# Listar archivos sin extraer
./pdp8_extractor.py -l imagen_os8.dsk

# Extraer todos los archivos
./pdp8_extractor.py imagen_os8.dsk

# Extraer a directorio específico
./pdp8_extractor.py -o mi_extraccion imagen_os8.dsk
```

### Ejemplos
```bash
# Disquete OS/8 RX50
./pdp8_extractor.py os8_system.rx50

# Disquete OS/78 RX02  
./pdp8_extractor.py -o extracted_os78 os78_utilities.rx02

# Imagen de disco grande
./pdp8_extractor.py -l large_os8_disk.img
```

## Formato de Directorio OS/8

El extractor entiende el formato de directorio OS/8:

### Bloque Home (Bloque 1)
```
Word 0: Número de entradas en el segmento de directorio
Word 1: Bloque inicial del área vacía  
Word 2: Puntero al siguiente segmento de directorio (0=último)
Word 3: Archivo tentativo (normalmente 0)
Word 4: -(Número de palabras de información adicional por entrada)
Word 5+: Entradas de directorio
```

### Entrada de Directorio
```
Word 0: Tipo de archivo
Word 1-3: Nombre de archivo en codificación SIXBIT
Word 4: Longitud en bloques (negativa para archivos normales)
Word 5: Información de trabajo/canal
Word 6+: Información adicional (fecha, etc.) si está presente
```

### Tipos de Archivo
- `0` - `.EMPTY.` (área vacía)
- `1` - `.FILE.` (archivo genérico)
- `2` - `.DATA.` (archivo de datos)  
- `3` - `.PROG.` (programa)
- `4` - `.ASCII.` (texto ASCII)
- `5` - `.BINARY.` (binario)

## Codificación SIXBIT

Los nombres de archivo usan codificación SIXBIT (6 bits por carácter):
- `0-31`: Caracteres de control y especiales
- `32-63`: `@A-Z[\]^_` y espacio

## Limitaciones

### Implementadas
- Solo OS/8 y variantes están completamente implementados
- Los archivos se extraen como datos binarios (sin conversión de texto)
- No se maneja interleaving automáticamente

### Por Implementar
- PS/8 DECtape format
- TSS/8 PUTR format  
- Conversión automática de archivos texto ASCII
- Soporte para imágenes interleaved
- Verificación de checksums
- Extracción de metadatos extendidos

## Arquitectura del Código

El extractor está organizado en clases:

- `PDP8Extractor` - Clase principal que maneja la extracción
- `FileEntry` - Representa un archivo en el directorio
- `DeviceGeometry` - Información sobre geometría del dispositivo
- `PDP8FileSystem` - Enumeración de sistemas de archivos
- `MediaType` - Enumeración de tipos de medios

### Métodos Principales

- `detect_filesystem()` - Auto-detecta el sistema de archivos
- `detect_media_type()` - Detecta tipo de medio por tamaño
- `read_os8_directory()` - Lee directorio OS/8
- `extract_file()` - Extrae contenido de un archivo
- `_decode_sixbit()` - Decodifica nombres SIXBIT

## Basado en PUTR

Este extractor está basado en el análisis del código fuente de PUTR V2.01:

```
File transfer program, knows many DEC formats.

By John Wilson <wilson@dbit.com>.

Copyright (C) 1995-2001 By John Wilson. All rights reserved.
```

PUTR es un programa completo que soporta:
- 12+ sistemas de archivos DEC
- 30+ tipos de dispositivos
- Múltiples interfaces (floppy, SCSI, COM ports, image files)
- Conversión automática ASCII/binaria
- Verificación y reparación de sistemas de archivos

## Referencias

- PUTR V2.01 Source Code
- PDP-8 System Reference Manual
- OS/8 System Reference Manual  
- DECtape Format Specification
- RX01/RX02/RX50 Technical Manuals

## Contribuir

Para añadir soporte para más sistemas:

1. Implementar función de detección en `detect_filesystem()`
2. Añadir método de lectura de directorio específico
3. Actualizar `run()` para manejar el nuevo sistema
4. Añadir tests con imágenes de ejemplo

El código está diseñado para ser extensible siguiendo los patrones establecidos en PUTR.
