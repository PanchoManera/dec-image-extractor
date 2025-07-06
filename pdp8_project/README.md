# Extractor de Archivos OS/8

Este proyecto contiene un extractor de archivos para el sistema operativo OS/8 del PDP-8, desarrollado desde cero basándose en las especificaciones de SIMH y documentación oficial.

## Características

- **Formato soportado**: Imágenes de disco RX01 (256,256 bytes) y RX02 (512,512 bytes)
- **Estructura del disco**: 77 tracks × 26 sectores por track
- **Decodificación**: Formato RAD50 (Radix-50) para nombres de archivo
- **Directorio**: Ubicación automática del directorio OS/8 en el disco

## Archivos del proyecto

### Archivos principales
- `os8_extractor.py` - Extractor principal desde cero
- `find_os8_directory.py` - Analizador para encontrar la ubicación del directorio
- `examine_os8.py` - Herramienta de análisis hexadecimal de sectores

### Imagen de prueba
- `os8_rx.rx01` - Imagen de disco RX01 con sistema OS/8 (256 KB)

### Archivos anteriores (en carpeta old/)
- Scripts del proyecto anterior movidos por organización

## Uso

### Extractor principal
```bash
python os8_extractor.py os8_rx.rx01
```

### Analizador de directorio
```bash
python find_os8_directory.py os8_rx.rx01
```

### Examinador hexadecimal
```bash
python examine_os8.py os8_rx.rx01
```

## Resultados obtenidos

El extractor ha identificado exitosamente **13 archivos** en la imagen de prueba:

| Archivo     | Tamaño | Bloque | Longitud | Tipo detectado |
|-------------|--------|--------|----------|----------------|
| BL.BHN      | 768 B  | 1152   | 1318     | data           |
| AAL.AXE     | 384 B  | 600    | 586      | data           |
| A.QAAW      | 1.3 KB | 194    | 2400     | data           |
| H$.TR       | 896 B  | 608    | 1591     | data           |
| I.AEM       | 2.0 KB | 143    | 4010     | data           |
| AXH.TB      | 256 B  | 1760   | 271      | data           |
| APH.A0Z     | 111 B  | 446    | 111      | data           |
| QE.AYX      | 1.4 KB | 398    | 2660     | data           |
| 1M.6R       | 1.9 KB | 1024   | 3600     | OpenPGP Secret Key |
| HR.9U       | 512 B  | 822    | 866      | data           |
| IT.1        | 640 B  | 609    | 1041     | Matlab v4 mat-file |
| A73.IY      | 1.0 KB | 87     | 1827     | data           |
| S0.2        | 8 B    | 624    | 8        | data           |

## Descubrimientos técnicos

### Ubicación del directorio
- **Encontrado en**: Track 6, Sector 1 (no en los primeros sectores como se esperaba inicialmente)
- **Sectores adicionales**: Track 6, Sectores 2 y 3 contienen entradas adicionales
- **Formato de entrada**: 4 palabras de 12 bits por entrada de archivo

### Formato de datos
- **Palabras PDP-8**: 12 bits empaquetados en 16 bits (little-endian)
- **Codificación de nombres**: RAD50 (Radix-50) base 40
- **Estructura de entrada**:
  - Palabra 1: Primera parte del nombre (RAD50)
  - Palabra 2: Segunda parte del nombre/extensión (RAD50)  
  - Palabra 3: Bloque de inicio del archivo
  - Palabra 4: Longitud del archivo

### Padding y datos especiales
- **Sectores iniciales**: Llenos de valor 0x40 (64 decimal, '@' ASCII)
- **Entradas de padding**: Valor 0o2745 (1509 decimal) indica espacio no utilizado
- **Filtros aplicados**: Exclusión de nombres que empiezan con "80" y validación de metadatos

## Tecnologías utilizadas

- **Python 3**: Lenguaje principal
- **struct**: Para manejo de datos binarios
- **SIMH**: Como referencia para especificaciones del formato RX
- **Documentación OS/8**: Para entender la estructura del sistema de archivos

## Referencias

- Código fuente de SIMH: `simh/PDP8/pdp8_rx.c`
- Especificaciones del formato RX01/RX02
- Documentación del sistema operativo OS/8
- Formato de codificación RAD50 (Radix-50)

## Estado del proyecto

✅ **Completado exitosamente**
- Localización automática del directorio
- Decodificación correcta de nombres de archivo RAD50
- Extracción exitosa de todos los archivos identificados
- Validación de metadatos y filtrado de entradas inválidas

## Desarrollador

Proyecto desarrollado por asistente IA, basado en especificaciones técnicas y análisis de formatos históricos de computadoras.
