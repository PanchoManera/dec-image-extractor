# Documentación Técnica RT-11

## 📋 Resumen

Este directorio contiene documentación técnica completa sobre el sistema de archivos RT-11 y el funcionamiento del extractor.

## 📚 Archivos Disponibles

### 📄 Documentación Principal
- **`RT11_Technical_Guide.md`** - Guía técnica completa en formato Markdown
- **`RT11_Technical_Guide.pdf`** - Versión PDF profesional de la guía técnica
- **`generate_technical_pdf.py`** - Script para generar el PDF desde el Markdown

### 🎯 Contenido de la Documentación

La documentación técnica incluye:

1. **Introducción e Historia**
   - Contexto histórico de RT-11 y PDP-11
   - Importancia en la preservación de software

2. **Estructura del Sistema de Archivos**
   - Anatomía física del disco RT-11
   - Home Block y su estructura
   - Organización del directorio

3. **Codificación RADIX-50**
   - Explicación completa del sistema de codificación
   - Algoritmos de decodificación
   - Ejemplos prácticos

4. **Formato de Fechas RT-11**
   - Estructura de 16 bits para fechas
   - Manejo de eras y años base
   - Algoritmos de conversión

5. **Proceso de Extracción**
   - Análisis paso a paso de cómo funciona el extractor
   - Fases de procesamiento
   - Manejo de errores

6. **Casos Especiales**
   - Recuperación de archivos dañados
   - Validación de integridad
   - Diagnóstico de problemas

7. **Ejemplos Prácticos**
   - Decodificación manual de nombres
   - Interpretación de fechas
   - Análisis de cabeceras

8. **Apéndices de Referencia**
   - Tabla completa RADIX-50
   - Códigos de estado
   - Tipos de dispositivo

## 🔄 Generación del PDF

### Requisitos

```bash
pip install reportlab
```

### Generar PDF

```bash
python3 generate_technical_pdf.py
```

El script:
- ✅ Lee el archivo `RT11_Technical_Guide.md`
- ✅ Convierte Markdown a PDF con formato profesional
- ✅ Agrega página de título con logo DEC
- ✅ Genera tabla de contenidos automática
- ✅ Aplica estilos técnicos profesionales
- ✅ Formatea tablas y código con colores

### Características del PDF

- **Formato**: A4 profesional
- **Estilos**: Tipografía técnica con colores DEC
- **Organización**: Tabla de contenidos navegable
- **Tablas**: Formato profesional con headers destacados
- **Código**: Bloques resaltados con fondo gris
- **Página de título**: Logo DEC y información del proyecto

## 🎨 Personalización

### Modificar Estilos

Edita el archivo `generate_technical_pdf.py` en la función `setup_custom_styles()`:

```python
# Cambiar colores principales
textColor=HexColor('#1f4e79')  # Azul DEC
backColor=HexColor('#f0f4f8')  # Fondo suave

# Modificar fuentes
fontName='Helvetica-Bold'      # Headers
fontName='Times-Roman'         # Texto normal
fontName='Courier'             # Código
```

### Agregar Contenido

1. **Editar Markdown**: Modifica `RT11_Technical_Guide.md`
2. **Regenerar PDF**: Ejecuta `python3 generate_technical_pdf.py`
3. **Automático**: El PDF se actualiza con todos los cambios

## 📖 Uso de la Documentación

### Para Desarrolladores
- Entender la estructura interna de RT-11
- Implementar extractores personalizados
- Debuggear problemas de extracción
- Validar integridad de imágenes

### Para Investigadores
- Comprender sistemas históricos
- Preservar software legacy
- Analizar formatos de archivo antiguos
- Estudiar evolución de sistemas de archivos

### Para Usuarios Avanzados
- Diagnosticar imágenes problemáticas
- Entender procesos de recuperación
- Configurar extracciones especializadas
- Validar resultados de extracción

## 🔧 Solución de Problemas

### Error: reportlab no encontrado
```bash
pip install reportlab
# o
pip3 install reportlab
```

### Error: archivo Markdown no encontrado
Asegúrate de que `RT11_Technical_Guide.md` existe en el mismo directorio.

### PDF malformado
Verifica que el Markdown tenga formato válido:
- Headers con `#`, `##`, `###`
- Tablas con `|` correctamente formateadas
- Bloques de código con ` ``` `

### Problemas de codificación
El script maneja automáticamente UTF-8, pero si hay caracteres especiales:
```python
# En generate_technical_pdf.py
with open(md_path, 'r', encoding='utf-8') as f:
```

## 📈 Métricas del Documento

- **Páginas**: ~40-50 páginas en PDF
- **Palabras**: ~15,000 palabras
- **Secciones**: 12 secciones principales
- **Ejemplos**: 15+ ejemplos de código
- **Tablas**: 8 tablas de referencia
- **Diagramas**: Representaciones ASCII de estructuras

## 🤝 Contribuir

### Mejorar Documentación
1. Edita `RT11_Technical_Guide.md`
2. Agrega ejemplos o explicaciones
3. Regenera el PDF
4. Haz commit de ambos archivos

### Mejorar Generador PDF
1. Modifica `generate_technical_pdf.py`
2. Mejora estilos o funcionalidad
3. Prueba generación
4. Documenta cambios

## 📞 Soporte

Para preguntas sobre la documentación técnica:
1. Revisa los ejemplos en el documento
2. Consulta los apéndices de referencia
3. Verifica la sección de solución de problemas
4. Compara con el código fuente del extractor

---

*Esta documentación es parte del proyecto RT-11 Extractor para preservación de software histórico*
