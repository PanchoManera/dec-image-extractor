# RT-11 FUSE Driver

Driver FUSE para montar imágenes DSK de RT-11 como sistemas de archivos normales. Permite navegar y acceder a archivos RT-11 como si fueran archivos locales.

## 🚀 Características

- **Montaje en tiempo real**: Monta imágenes DSK, IMD y otros formatos RT-11
- **Solo lectura**: Protege las imágenes originales de modificaciones accidentales
- **Cache inteligente**: Optimiza el acceso a archivos frecuentemente utilizados
- **Multiplataforma**: Compatible con macOS y Linux
- **Integración nativa**: Utiliza tu extractor `rt11extract` existente

## 📋 Requisitos

### macOS
- Python 3.6+
- macFUSE (https://osxfuse.github.io/)
- pip3

### Linux
- Python 3.6+
- FUSE (fuse, libfuse-dev)
- pip3

## 🛠️ Instalación

### Instalación automática

Ejecuta el script de configuración:

```bash
chmod +x setup_fuse.sh
./setup_fuse.sh
```

### Instalación manual

1. **Instalar FUSE**:
   ```bash
   # macOS (con Homebrew)
   brew install --cask macfuse
   
   # Linux (Ubuntu/Debian)
   sudo apt install fuse libfuse-dev
   
   # Linux (CentOS/RHEL)
   sudo yum install fuse fuse-devel
   ```

2. **Instalar fusepy**:
   ```bash
   pip3 install fusepy
   ```

3. **Hacer ejecutables los scripts**:
   ```bash
   chmod +x rt11_fuse_complete.py
   chmod +x rt11extract
   ```

## 📖 Uso

### Sintaxis básica

```bash
./rt11_fuse_complete.py <imagen.dsk> <punto_montaje>
```

### Ejemplos

```bash
# Crear directorio de montaje
mkdir ~/rt11_mount

# Montar imagen RT-11
./rt11_fuse_complete.py disk.dsk ~/rt11_mount

# Navegar archivos (en otra terminal)
ls ~/rt11_mount/
cat ~/rt11_mount/HELLO.TXT
cp ~/rt11_mount/PROG.SAV ~/Desktop/

# Desmontar
umount ~/rt11_mount        # macOS
fusermount -u ~/rt11_mount # Linux
```

### Montaje con opciones específicas

```bash
# Mostrar información de depuración
./rt11_fuse_complete.py -d disk.dsk ~/rt11_mount

# Permitir acceso a otros usuarios (Linux)
./rt11_fuse_complete.py -o allow_other disk.dsk ~/rt11_mount
```

## 🔧 Características técnicas

### Formatos soportados
- `.dsk` - Imágenes de disco RT-11 estándar
- `.imd` - ImageDisk format
- `.raw` - Imágenes raw de disco
- `.img` - Imágenes de disco genéricas

### Limitaciones
- **Solo lectura**: No se pueden modificar archivos en la imagen montada
- **Sin directorios**: RT-11 no tiene subdirectorios, todos los archivos están en la raíz
- **Nombres de archivo**: Algunos caracteres especiales se convierten a versiones seguras

### Conversión de nombres de archivo

Algunos caracteres de RT-11 se convierten para compatibilidad con sistemas modernos:

| RT-11 | FUSE    |
|-------|---------|
| `$`   | `_DOLLAR_` |
| `?`   | `_QUESTION_` |
| `*`   | `_STAR_` |

## 🐛 Solución de problemas

### Error: "fusepy no está instalado"
```bash
pip3 install fusepy
```

### Error: "macFUSE no está instalado" (macOS)
1. Descarga macFUSE desde https://osxfuse.github.io/
2. O instala con Homebrew: `brew install --cask macfuse`

### Error: "Transport endpoint is not connected"
El punto de montaje puede estar corrupto:
```bash
# Linux
fusermount -u ~/rt11_mount

# macOS  
umount ~/rt11_mount
```

### Permisos denegados (Linux)
Asegúrate de estar en el grupo `fuse`:
```bash
sudo usermod -a -G fuse $USER
# Cerrar sesión y volver a iniciar
```

### El driver no encuentra archivos
Verifica que tu extractor `rt11extract` funciona:
```bash
./rt11extract disk.dsk
```

## 🔍 Información técnica

### Arquitectura

El driver FUSE utiliza tu extractor `rt11extract` existente:

1. **Escaneo**: Ejecuta `rt11extract` para obtener la lista de archivos
2. **Cache**: Mantiene un cache de metadatos de archivo por 30 segundos
3. **Extracción**: Para leer archivos, ejecuta `rt11extract` en un directorio temporal
4. **Limpieza**: Limpia automáticamente los archivos temporales

### Logging

Los logs se escriben a la consola y contienen información útil para depuración:

```bash
./rt11_fuse_complete.py disk.dsk ~/rt11_mount
# 2024-06-23 15:41:34 - RT11-FUSE - INFO - Montando imagen RT-11: disk.dsk
# 2024-06-23 15:41:34 - RT11-FUSE - INFO - Escaneados 25 archivos
```

### Rendimiento

- **Cache de metadatos**: 30 segundos por defecto
- **Cache de datos**: Archivos < 1MB se mantienen en memoria
- **Extracción bajo demanda**: Los archivos se extraen solo cuando se accede a ellos

## 🤝 Integración con herramientas

### Con Finder (macOS)
Los archivos montados aparecen normalmente en Finder y pueden ser:
- Copiados con arrastrar y soltar
- Abiertos con aplicaciones predeterminadas
- Visualizados con Vista Rápida (Espacio)

### Con explorador de archivos (Linux)
Funciona con nautilus, dolphin, thunar y otros exploradores.

### Con línea de comandos
Todos los comandos estándar funcionan:
```bash
ls, cat, cp, find, grep, hexdump, file, etc.
```

### Con editores de texto
Los archivos pueden abrirse directamente:
```bash
vim ~/rt11_mount/PROG.MAC
code ~/rt11_mount/DATA.TXT
nano ~/rt11_mount/CONFIG.SYS
```

## 📚 Casos de uso

### Desarrollo retro
```bash
# Montar disco de desarrollo
./rt11_fuse_complete.py dev.dsk ~/rt11_dev

# Copiar código fuente para análisis
cp ~/rt11_dev/*.MAC ~/modern_project/rt11_sources/

# Ver archivos de configuración
cat ~/rt11_dev/CONFIG.SYS
```

### Recuperación de datos
```bash
# Montar disco dañado
./rt11_fuse_complete.py damaged.dsk ~/recovery

# Copiar archivos válidos
find ~/recovery -type f -exec cp {} ~/backup/ \;
```

### Análisis forense
```bash
# Montar imagen para análisis
./rt11_fuse_complete.py evidence.dsk ~/analysis

# Buscar patrones
grep -r "password" ~/analysis/
hexdump -C ~/analysis/SYSTEM.SYS | less
```

## 🔗 Enlaces útiles

- [RT-11 Documentation](http://bitsavers.org/pdf/dec/pdp11/rt11/)
- [macFUSE](https://osxfuse.github.io/)
- [FUSE Documentation](https://www.kernel.org/doc/html/latest/filesystems/fuse.html)
- [fusepy on GitHub](https://github.com/fusepy/fusepy)

## 💡 Consejos

1. **Usa directorios vacíos** para puntos de montaje
2. **Desmonta siempre** antes de mover o eliminar imágenes
3. **Haz copias de seguridad** antes de trabajar con imágenes valiosas
4. **Usa el cache** - el segundo acceso a archivos es mucho más rápido
5. **Combina con otras herramientas** - funciona bien con git, rsync, etc.

---

¡Disfruta explorando tus imágenes RT-11 de forma nativa! 🎉
