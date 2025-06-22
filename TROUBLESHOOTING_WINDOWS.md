# Guía de Solución de Problemas - RT-11 Extractor Windows

## 🎯 Introducción

Esta guía te ayudará a resolver problemas comunes al ejecutar RT-11 Extractor en Windows. Los nuevos launchers incluyen diagnósticos automáticos que te guiarán paso a paso.

## 🔧 Soluciones para Problemas Comunes

### ❌ Problema 1: "No se encontró Python"

**Síntomas:**
- El launcher muestra: "ERROR: No se encontró Python 3.6+ instalado"
- O aparece: "'python' no se reconoce como comando"

**Solución Recomendada: Usar Versión Portable**
1. Descarga el paquete `RT11ExtractGUI-WIN64-Portable.zip` (o WIN32/ARM64 según tu sistema)
2. Extrae todos los archivos a una carpeta
3. Ejecuta `RT11ExtractGUI-WIN64-Portable.bat`
4. ¡No requiere instalación de Python!

**Solución Alternativa: Instalar Python**
1. Ve a [python.org](https://python.org)
2. Descarga Python 3.11 o superior
3. Durante la instalación:
   - ✅ Marca "Add Python to PATH"
   - ✅ Marca "Install for all users" (opcional)
4. Reinicia el launcher después de la instalación

### ❌ Problema 2: "No se encontró el archivo .pyz"

**Síntomas:**
- Error: "No se encontró el archivo RT11ExtractGUI-XXX.pyz"

**Solución:**
1. Verifica que ambos archivos estén en la misma carpeta:
   - `RT11ExtractGUI-WIN64.bat` (launcher)
   - `RT11ExtractGUI-WIN64.pyz` (aplicación)
2. No muevas ni renombres los archivos
3. Ejecuta el `.bat` desde la carpeta donde están ambos archivos

### ❌ Problema 3: "Error ejecutando la aplicación"

**Síntomas:**
- El launcher encuentra Python pero la aplicación falla
- Aparece un código de error

**Posibles Causas y Soluciones:**

**Versión de Python muy antigua:**
- Verifica que tienes Python 3.6 o superior
- El launcher te mostrará la versión encontrada
- Actualiza Python si es necesario

**Permisos insuficientes:**
- Ejecuta como administrador (clic derecho → "Ejecutar como administrador")
- O mueve los archivos a una carpeta donde tengas permisos de escritura

**Archivo RT-11 corrupto:**
- Verifica que el archivo .dsk/.img de RT-11 no esté dañado
- Prueba con un archivo diferente

### ❌ Problema 4: La aplicación se cierra inmediatamente

**Síntomas:**
- Una ventana se abre y se cierra rápidamente
- No aparece ningún mensaje de error

**Solución:**
1. Usa la versión portable que incluye diagnósticos completos
2. O ejecuta desde línea de comandos para ver errores:
   ```cmd
   python RT11ExtractGUI-WIN64.pyz
   ```

## 🎯 Qué Versión Usar

### Para Usuarios Sin Conocimientos Técnicos
**Recomendado: Versión Portable**
- ✅ No requiere instalación de Python
- ✅ Funciona inmediatamente
- ✅ Incluye diagnósticos completos
- 📁 Archivo: `RT11ExtractGUI-XXX-Portable.zip`

### Para Usuarios Técnicos con Python
**Recomendado: Versión RequiresPython**
- ✅ Archivo más pequeño (35 KB vs 5-7 MB)
- ✅ Usa tu instalación de Python existente
- ✅ Fácil de actualizar
- 📁 Archivo: `RT11ExtractGUI-XXX-RequiresPython.zip`

## 🖥️ Compatibilidad por Sistema

### Windows 7/8/8.1
- ✅ **WIN32**: Funciona en sistemas 32-bit y 64-bit
- ✅ **WIN64**: Solo en sistemas 64-bit
- ❌ **ARM64**: No compatible

### Windows 10
- ✅ **WIN32**: Funciona en todos los sistemas
- ✅ **WIN64**: En sistemas 64-bit (recomendado)
- ✅ **ARM64**: En dispositivos Surface Pro X y similares

### Windows 11
- ✅ **WIN64**: Opción estándar
- ✅ **ARM64**: Para sistemas ARM64 nativos

## 🔍 Diagnósticos Automáticos

Los nuevos launchers incluyen diagnósticos que automáticamente:

1. **Verifican archivos necesarios**
   - Confirman que todos los archivos estén presentes
   - Validan la integridad de Python embebido (versión portable)

2. **Buscan Python instalado** (versión RequiresPython)
   - Prueban múltiples comandos: `python`, `py -3`, `python3`
   - Muestran la versión encontrada
   - Explican cómo instalar Python si no se encuentra

3. **Reportan errores detallados**
   - Códigos de error específicos
   - Sugerencias de solución
   - Instrucciones paso a paso

4. **Proporcionan alternativas**
   - Sugieren usar versión portable si Python no está disponible
   - Recomiendan actualizar Python si la versión es muy antigua

## 🚀 Casos de Uso Recomendados

### 💼 Entorno Corporativo
- **Usar**: Versión Portable
- **Razón**: No requiere permisos de administrador para instalar Python

### 🏠 Uso Personal
- **Usar**: RequiresPython si ya tienes Python
- **Usar**: Portable si no tienes Python o no quieres instalarlo

### 🔬 Desarrollo/Testing
- **Usar**: RequiresPython
- **Razón**: Más fácil de actualizar y debuggear

### 📱 Dispositivos ARM (Surface Pro X)
- **Usar**: Versión ARM64 (portable o RequiresPython)
- **Razón**: Optimizado para arquitectura ARM64

## 🆘 Si Nada Funciona

Si has probado todas las soluciones y aún tienes problemas:

1. **Verifica tu arquitectura de Windows:**
   ```cmd
   echo %PROCESSOR_ARCHITECTURE%
   ```
   - AMD64 = usa WIN64
   - x86 = usa WIN32
   - ARM64 = usa ARM64

2. **Prueba la versión portable primero:**
   - Es la menos propensa a problemas
   - Incluye diagnósticos más detallados

3. **Ejecuta desde línea de comandos:**
   ```cmd
   # Para versión portable
   cd ruta\a\portable
   python\python.exe app\__main__.py
   
   # Para versión RequiresPython
   python RT11ExtractGUI-WIN64.pyz
   ```

4. **Verifica que no sea un problema de antivirus:**
   - Algunos antivirus bloquean ejecutables descargados
   - Agrega una excepción para la carpeta del RT-11 Extractor

## 📞 Información de Sistema

Para reportar un problema, incluye:
- Versión de Windows (`winver`)
- Arquitectura (`echo %PROCESSOR_ARCHITECTURE%`)
- Versión de Python (`python --version`) si aplica
- Mensaje de error completo
- Versión del RT-11 Extractor utilizada

---

**Los launchers mejorados están diseñados para ser autoexplicativos y guiarte paso a paso hacia la solución. ¡La mayoría de problemas se resolverán automáticamente!**
