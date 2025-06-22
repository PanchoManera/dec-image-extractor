# GitHub Actions - Compilación Automática Multiplataforma

Este proyecto incluye un workflow de GitHub Actions que compila automáticamente ejecutables para Windows, macOS y Linux.

## ¿Qué hace el workflow?

El workflow `build-executables.yml` compila automáticamente:

### Windows (usando PyInstaller nativo)
- **Windows x64**: RT11ExtractGUI-Winx64.exe + RT11Extract-Winx64.exe
- **Windows x86**: RT11ExtractGUI-Winx86.exe + RT11Extract-Winx86.exe  
- **Windows ARM64**: RT11ExtractGUI-Winarm64.exe + RT11Extract-Winarm64.exe

### macOS (usando PyInstaller nativo)
- **macOS x64**: RT11ExtractGUI-macOS-x64 + RT11Extract-macOS-x64
- **macOS ARM64**: RT11ExtractGUI-macOS-ARM64 + RT11Extract-macOS-ARM64

### Linux (usando PyInstaller nativo)
- **Linux x64**: RT11ExtractGUI-Linux-x64 + RT11Extract-Linux-x64

## ¿Cuándo se ejecuta?

El workflow se ejecuta automáticamente cuando:
- Haces push a la rama `main` o `master`
- Creas un Pull Request hacia `main` o `master`
- Creas un tag que empiece con `v` (ej: `v1.0.0`)
- Lo ejecutas manualmente desde GitHub

## Cómo ejecutar manualmente

1. Ve a tu repositorio en GitHub
2. Clic en la pestaña "Actions"
3. Selecciona "Build RT-11 Extractor Executables"
4. Clic en "Run workflow"
5. Selecciona la rama y clic en "Run workflow"

## Cómo descargar los ejecutables

### Desde GitHub Actions (cualquier build)
1. Ve a la pestaña "Actions"
2. Clic en el build que te interese
3. Baja hasta "Artifacts"
4. Descarga los archivos ZIP que necesites:
   - `RT11Extractor-Windows-x64.zip`
   - `RT11Extractor-Windows-x86.zip`
   - `RT11Extractor-Windows-arm64.zip`
   - `RT11Extractor-macOS-x64.zip`
   - `RT11Extractor-macOS-arm64.zip`
   - `RT11Extractor-Linux-x64.zip`
   - `BUILD_SUMMARY.md` (resumen de lo construido)

### Desde Releases (solo tags)
Si creas un tag (ej: `v1.0.0`), se creará automáticamente un Release con todos los ejecutables.

1. Ve a la pestaña "Releases"
2. Descarga directamente los archivos ZIP

## Crear un Release automático

Para crear un release con todos los ejecutables:

```bash
# Crea y push un tag
git tag v1.0.0
git push origin v1.0.0
```

Esto activará el workflow y creará automáticamente un Release en GitHub con todos los ejecutables.

## Ventajas de GitHub Actions

✅ **Compilación nativa**: Cada plataforma compila en su propio runner nativo
✅ **Verdaderos .exe**: Los archivos Windows son ejecutables .exe nativos
✅ **Sin cross-compilation**: Evita todos los problemas de Wine/Docker
✅ **Automático**: Se ejecuta automáticamente en cada push/tag
✅ **Múltiples arquitecturas**: Soporta x64, x86, ARM64
✅ **Distribución fácil**: Genera archivos listos para distribuir
✅ **Gratis**: GitHub Actions es gratuito para repositorios públicos

## Estructura de los archivos generados

Cada plataforma genera un paquete con:
```
RT11Extractor-Windows-x64/
├── RT11ExtractGUI-Winx64.exe    # Interfaz gráfica
├── RT11Extract-Winx64.exe       # Línea de comandos
├── README.md                    # Documentación del proyecto
└── README_Windows.txt           # Instrucciones específicas de Windows

RT11Extractor-macOS-arm64/
├── RT11ExtractGUI-macOS-ARM64   # Interfaz gráfica
├── RT11Extract-macOS-ARM64      # Línea de comandos
├── README.md                    # Documentación del proyecto
└── README_macOS.txt             # Instrucciones específicas de macOS

RT11Extractor-Linux-x64/
├── RT11ExtractGUI-Linux-x64     # Interfaz gráfica
├── RT11Extract-Linux-x64        # Línea de comandos
├── README.md                    # Documentación del proyecto
└── README_Linux.txt             # Instrucciones específicas de Linux
```

## Solución de problemas

### El workflow falla
- Revisa los logs en la pestaña Actions
- Asegúrate de que todos los archivos necesarios estén en el repositorio
- Verifica que `rt11extract_gui.py`, `rt11extract`, `icon.ico` e `images.png` existan

### Los ejecutables no funcionan
- Los ejecutables Windows requieren Windows 7 o superior
- Los ejecutables macOS requieren macOS 10.13 o superior
- Los ejecutables Linux requieren una distribución con glibc 2.17+ (Ubuntu 14.04+, CentOS 7+)

### Modificar el workflow
El archivo `.github/workflows/build-executables.yml` se puede editar para:
- Cambiar versiones de Python
- Agregar más dependencias
- Modificar parámetros de PyInstaller
- Agregar más plataformas o arquitecturas

## Comparación con compilación local

| Método | Windows .exe | macOS nativo | Linux nativo | Tiempo | Complejidad |
|--------|--------------|--------------|--------------|--------|-------------|
| **GitHub Actions** | ✅ Sí | ✅ Sí | ✅ Sí | ~15 min | ⭐ Fácil |
| Compilación local | ❌ Solo bundle | ✅ Sí | ❌ Solo bundle | ~30 min | ⭐⭐⭐ Complejo |
| Wine + Docker | ⚠️ Inestable | ❌ No | ⚠️ Inestable | ~45 min | ⭐⭐⭐⭐⭐ Muy complejo |

**Recomendación**: Usar GitHub Actions para distribución oficial y compilación local solo para desarrollo/testing.
