# 🔓 Solución: "No se encontró el archivo .pyz" en Windows

## 🎯 El Problema

Cuando ejecutas el launcher de RT-11 Extractor en Windows ARM64 (o cualquier Windows), aparece:

```
ERROR: No se encontró el archivo RT11ExtractGUI-ARM64.pyz
```

**Pero el archivo SÍ está ahí.** Este es un problema común de Windows que bloquea automáticamente archivos descargados de internet por seguridad.

## 🔍 ¿Por qué pasa esto?

Windows incluye un sistema de seguridad llamado "Zone.Identifier" que:
1. **Marca archivos descargados** con una etiqueta especial
2. **Bloquea archivos desconocidos** como `.pyz` (que Windows no reconoce)
3. **Los hace "invisibles"** para algunos comandos y scripts

## ✅ Soluciones (3 métodos)

### 🚀 Método 1: Script Automático (Más Fácil)

1. **Busca el archivo** `unblock_files.ps1` en la carpeta donde extraíste el ZIP
2. **Clic derecho** en `unblock_files.ps1`
3. **Selecciona** "Ejecutar con PowerShell"
4. **El script desbloqueará** automáticamente todos los archivos `.pyz`
5. **Ejecuta** el launcher `.bat` normalmente

### 🔧 Método 2: Desbloqueo Manual

1. **Clic derecho** en el archivo `RT11ExtractGUI-ARM64.pyz`
2. **Selecciona** "Propiedades"
3. **Ve a la pestaña** "General"
4. **Busca** la sección "Seguridad" al final
5. **Marca** la casilla "Desbloquear" si aparece
6. **Clic** "Aplicar" y "Aceptar"
7. **Ejecuta** el launcher `.bat`

### 🎯 Método 3: Usar Versión Portable (Sin problemas)

1. **Descarga** el paquete `RT11ExtractGUI-ARM64-Portable.zip`
2. **Extrae** todos los archivos
3. **Ejecuta** `RT11ExtractGUI-ARM64-Portable.bat`
4. **No requiere** Python ni desbloquear archivos

## 📱 Específico para Windows ARM64

Si estás en Windows ARM64 (Surface Pro X, etc.):

- ✅ **Usa** `RT11ExtractGUI-ARM64-*.zip` (versión correcta)
- ❌ **No uses** WIN32 o WIN64 (funcionarán pero más lento)
- 🎯 **Recomendado**: Versión ARM64 Portable para mejor rendimiento

## 🔍 Cómo verificar si está bloqueado

En PowerShell:
```powershell
Get-Item "RT11ExtractGUI-ARM64.pyz" | Select-Object Name, @{Name="Blocked";Expression={Get-Content "$($_.FullName):Zone.Identifier" -ErrorAction SilentlyContinue}}
```

Si muestra contenido en "Blocked", el archivo está bloqueado.

## 🛠️ Prevención para el futuro

Para evitar este problema:

1. **Extrae siempre** los ZIP en carpetas locales (no Desktop o Downloads)
2. **Usa antivirus moderno** que no sea tan agresivo
3. **Prefiere versiones portables** para distribución

## ⚡ Script de Diagnóstico Rápido

Puedes usar este comando en CMD para verificar:

```cmd
dir RT11ExtractGUI-ARM64.*
```

Si aparece el archivo pero el launcher dice que no existe, está bloqueado.

## 🎉 Una vez solucionado

Después de desbloquear:
1. El launcher **detectará Python** automáticamente
2. **Mostrará** la versión encontrada
3. **Ejecutará** RT-11 Extractor correctamente
4. El problema **no volverá a ocurrir** con estos archivos

## 💡 Recomendación Final

**Para Windows ARM64, la mejor opción es:**
1. Descarga `RT11ExtractGUI-ARM64-Portable.zip`
2. Extrae en una carpeta local
3. Ejecuta directamente sin preocuparte por bloqueos

Esta versión:
- ✅ No requiere Python instalado
- ✅ No tiene problemas de archivos bloqueados
- ✅ Está optimizada para ARM64
- ✅ Funciona inmediatamente

---

**Este problema es común en Windows y tiene solución simple. Los nuevos launchers incluyen instrucciones automáticas para guiarte paso a paso.**
