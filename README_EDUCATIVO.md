# RT-11 Extractor Educativo - Versión para Estudiantes

## 🎓 Propósito Educativo

Esta es una versión simplificada y educativa del extractor RT-11, especialmente diseñada para enseñar el sistema **RADIX-50** a estudiantes de **Organización de Computadoras**.

## 🚀 Cómo usar

### Ejecución básica
```bash
python3 rt11extract_educativo.py
```

El programa mostrará automáticamente:
1. **Tabla de caracteres RADIX-50** completa
2. **Ejemplos paso a paso** de codificación y decodificación
3. **Demostración completa** con nombres de archivos RT-11
4. **Ejercicios propuestos** para estudiantes

## 📚 Qué aprenderás

### 1. Sistema RADIX-50
- Por qué se inventó (limitaciones de memoria en los años 70)
- Cómo funciona matemáticamente
- Los 40 caracteres permitidos exactamente

### 2. Codificación paso a paso
El programa muestra **cada paso** del proceso:
```
🔧 CODIFICANDO A RADIX-50: 'ABC'
========================================
Texto normalizado: 'ABC'

Paso 1: Procesando carácter 'A' (posición 1)
  'A' está en posición 1 del conjunto RADIX-50
  Contribución: 1 × 40² = 1 × 1600 = 1600
  Resultado acumulado: 1600

Paso 2: Procesando carácter 'B' (posición 2)
  'B' está en posición 2 del conjunto RADIX-50
  Contribución: 2 × 40¹ = 2 × 40 = 80
  Resultado acumulado: 1680

Paso 3: Procesando carácter 'C' (posición 3)
  'C' está en posición 3 del conjunto RADIX-50
  Contribución: 3 × 40⁰ = 3 × 1 = 3
  Resultado acumulado: 1683

✅ RESULTADO FINAL: 1683 (0x0693)
```

### 3. Decodificación paso a paso
```
🔍 DECODIFICANDO RADIX-50: 1683 (0x0693)
==================================================
Paso 1: Carácter #3
  1683 % 40 = 3
  Posición 3 → 'C'
  Resultado parcial: 'C'
  Número restante: 42

Paso 2: Carácter #2
  42 % 40 = 2
  Posición 2 → 'B'
  Resultado parcial: 'BC'
  Número restante: 1

Paso 3: Carácter #1
  1 % 40 = 1
  Posición 1 → 'A'
  Resultado parcial: 'ABC'
  Número restante: 0

✅ RESULTADO FINAL: 'ABC'
```

### 4. Nombres de archivo RT-11 completos
Muestra cómo se almacena un archivo como `HELLO.TXT`:
- Palabra 1: `HEL` → 13012
- Palabra 2: `LO ` → 19800  
- Palabra 3: `TXT` → 32980

## 🔧 Funciones principales educativas

### `radix50_decodificar_paso_a_paso(numero)`
Decodifica un número de 16 bits mostrando cada operación matemática.

### `radix50_codificar_paso_a_paso(texto)`
Codifica texto a RADIX-50 mostrando cada multiplicación y suma.

### `decodificar_nombre_archivo_rt11(palabra1, palabra2, palabra3)`
Decodifica un nombre de archivo completo desde 3 palabras de 16 bits.

### `mostrar_tabla_radix50()`
Muestra la tabla completa con posiciones en binario, octal y hexadecimal.

## 🧮 Ejercicios para estudiantes

1. **¿Cuál es el número RADIX-50 para 'PDP'?**
   - Modifica el código para calcularlo
   - Verifica el resultado decodificando

2. **¿Qué texto representa el número 12345?**
   - Usa la función de decodificación
   - Explica cada paso

3. **¿Por qué RADIX-50 usa exactamente 40 caracteres?**
   - Considera las limitaciones de 16 bits
   - Calcula 40³ y compáralo con 2¹⁶

4. **¿Cuál es la máxima palabra de 16 bits en RADIX-50?**
   - Calcula 40³ - 1
   - ¿Por qué no se puede usar 2¹⁶ - 1?

5. **¿Cómo almacenarías el archivo 'PROGRAM.ASM'?**
   - Divídelo en 3 palabras
   - Calcula cada palabra manualmente
   - Verifica con el programa

## 🎯 Conceptos clave para entender

### Eficiencia del RADIX-50
- **40³ = 64,000** combinaciones posibles
- **2¹⁶ = 65,536** valores en 16 bits
- **Eficiencia: 97.7%** de uso del espacio disponible

### Limitaciones históricas
- **Memoria muy limitada** en computadoras PDP-11
- **Necesidad de compactar** nombres de archivos
- **Solo caracteres esenciales** (sin minúsculas, pocos símbolos)

### Matemática base-40
- Similar a cambio de base decimal a binario
- Cada "dígito" puede ser 0-39 en lugar de 0-9
- **Fórmula:** `valor = d₁×40² + d₂×40¹ + d₃×40⁰`

## 🔍 Comparación con el código original

### Versión original (`rt11extract`)
- Código complejo, orientado a funcionalidad
- Manejo de errores avanzado
- Muchas características adicionales
- Difícil de entender para principiantes

### Versión educativa (`rt11extract_educativo.py`)
- **Cada paso explicado** con print statements
- **Comentarios extensivos** en español
- **Ejemplos interactivos** automáticos
- **Enfoque pedagógico** en RADIX-50

## 🛠️ Modificaciones sugeridas para profesores

### Para hacer el código más interactivo:
```python
# Agregar entrada del usuario
texto = input("Ingresa un texto para codificar: ")
resultado = radix50_codificar_paso_a_paso(texto)
```

### Para crear ejercicios específicos:
```python
# Crear problemas aleatorios
import random
numero = random.randint(1, 63999)
print(f"Decodifica este número: {numero}")
```

### Para validar respuestas de estudiantes:
```python
def verificar_respuesta(numero_estudiante, texto_correcto):
    resultado = radix50_decodificar_paso_a_paso(numero_estudiante)
    return resultado.strip() == texto_correcto.strip()
```

## 📖 Referencias adicionales

- **RT-11 System Reference Manual** - Digital Equipment Corporation
- **PDP-11 Architecture** - Para entender el contexto histórico
- **Sistemas de numeración** - Base matemática del RADIX-50

## 🤝 Cómo contribuir

1. **Agrega más ejemplos** educativos
2. **Mejora las explicaciones** paso a paso
3. **Crea ejercicios adicionales** para estudiantes
4. **Traduce comentarios** a otros idiomas
5. **Agrega visualizaciones** (ASCII art, diagramas)

## 📝 Notas para instructores

- **Tiempo estimado:** 45-60 minutos de clase
- **Prerrequisitos:** Sistemas de numeración, aritmética modular básica
- **Objetivos:** Entender codificación de datos, limitaciones históricas, matemática aplicada
- **Evaluación:** Resolver ejercicios de codificación/decodificación manual

---

**¡Disfruta aprendiendo sobre la historia de la computación y los sistemas de codificación!** 🎉
