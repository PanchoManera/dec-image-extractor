#!/usr/bin/env python3
"""
RT-11 Disk Image Extractor - VERSIÓN EDUCATIVA
===============================================

Esta es una versión simplificada y educativa del extractor RT-11,
especialmente diseñada para enseñar el sistema RADIX-50 a estudiantes
de Organización de Computadoras.

RADIX-50: ¿Qué es y por qué es importante?
==========================================

El RADIX-50 es un sistema de codificación usado en computadoras PDP-11
para almacenar nombres de archivos de forma compacta. Fue necesario porque:

1. La memoria era MUY limitada en los años 70
2. Necesitaban almacenar nombres de archivos en pocas palabras de 16 bits
3. Solo necesitaban un conjunto limitado de caracteres

¿Cómo funciona RADIX-50?
========================

Imaginen que tenemos solo 40 caracteres permitidos:
- Espacio (posición 0)
- A-Z (posiciones 1-26) 
- $ . ? (posiciones 27-29)
- 0-9 (posiciones 30-39)

Con estos 40 caracteres, podemos codificar 3 caracteres en una palabra de 16 bits:
- Cada carácter ocupa log₂(40) ≈ 5.3 bits
- 3 caracteres × 5.3 bits ≈ 16 bits ¡Perfecto!

La fórmula es: valor = char1×40² + char2×40¹ + char3×40⁰
"""

import struct
import sys
import os
from pathlib import Path
from typing import Optional, List, Tuple

# =============================================================================
# PARTE 1: DEFINICIÓN DEL CONJUNTO DE CARACTERES RADIX-50
# =============================================================================

# Los 40 caracteres permitidos en RADIX-50 (¡EXACTAMENTE 40!)
# Posición 0: espacio, posiciones 1-26: A-Z, etc.
CARACTERES_RADIX50 = ' ABCDEFGHIJKLMNOPQRSTUVWXYZ$.?0123456789'

print("CONJUNTO DE CARACTERES RADIX-50:")
print("================================")
for i, char in enumerate(CARACTERES_RADIX50):
    if char == ' ':
        print(f"Posición {i:2d}: ESPACIO")
    else:
        print(f"Posición {i:2d}: '{char}'")
print(f"\nTotal de caracteres: {len(CARACTERES_RADIX50)}")
print()

# =============================================================================
# PARTE 2: FUNCIONES DE CONVERSIÓN RADIX-50 (EXPLICADAS PASO A PASO)
# =============================================================================

def radix50_decodificar_paso_a_paso(numero_16bits: int) -> str:
    """
    Decodifica un número de 16 bits a 3 caracteres RADIX-50
    
    EXPLICACIÓN PASO A PASO:
    ========================
    
    Ejemplo: si numero_16bits = 1234
    
    Paso 1: Obtener el tercer carácter (el menos significativo)
    posicion_char3 = 1234 % 40 = 34 → carácter '4'
    
    Paso 2: "Quitar" el tercer carácter dividiendo por 40
    resto = 1234 // 40 = 30
    
    Paso 3: Obtener el segundo carácter
    posicion_char2 = 30 % 40 = 30 → carácter '0'
    
    Paso 4: "Quitar" el segundo carácter dividiendo por 40
    resto = 30 // 40 = 0
    
    Paso 5: Obtener el primer carácter
    posicion_char1 = 0 % 40 = 0 → carácter ' ' (espacio)
    
    Resultado: " 04"
    """
    
    print(f"\n🔍 DECODIFICANDO RADIX-50: {numero_16bits} (0x{numero_16bits:04X})")
    print("=" * 50)
    
    # Caso especial: si es 0, son 3 espacios
    if numero_16bits == 0:
        print("Número es 0 → tres espacios")
        return "   "
    
    # Verificar que el número está en el rango válido
    if numero_16bits >= 40**3:  # 40³ = 64000
        print(f"⚠️  NÚMERO DEMASIADO GRANDE: {numero_16bits} >= {40**3}")
        return "???"
    
    resultado = ""
    numero_temporal = numero_16bits
    
    # Decodificar de derecha a izquierda (menos significativo a más significativo)
    for posicion in [3, 2, 1]:  # Tercer, segundo, primer carácter
        posicion_caracter = numero_temporal % 40
        numero_temporal = numero_temporal // 40
        
        print(f"Paso {4-posicion}: Carácter #{posicion}")
        print(f"  {numero_temporal * 40 + posicion_caracter} % 40 = {posicion_caracter}")
        
        if posicion_caracter >= len(CARACTERES_RADIX50):
            print(f"  ⚠️  POSICIÓN INVÁLIDA: {posicion_caracter}")
            caracter = "?"
        else:
            caracter = CARACTERES_RADIX50[posicion_caracter]
            if caracter == ' ':
                print(f"  Posición {posicion_caracter} → ESPACIO")
            else:
                print(f"  Posición {posicion_caracter} → '{caracter}'")
        
        resultado = caracter + resultado  # Insertar al principio
        print(f"  Resultado parcial: '{resultado}'")
        print(f"  Número restante: {numero_temporal}")
        print()
    
    print(f"✅ RESULTADO FINAL: '{resultado}'")
    return resultado


def radix50_codificar_paso_a_paso(texto: str) -> int:
    """
    Codifica hasta 3 caracteres de texto en un número de 16 bits RADIX-50
    
    EXPLICACIÓN PASO A PASO:
    ========================
    
    Ejemplo: si texto = "ABC"
    
    Paso 1: Convertir a mayúsculas y ajustar a 3 caracteres
    "ABC" → "ABC" (ya tiene 3 caracteres)
    
    Paso 2: Encontrar la posición de cada carácter
    'A' → posición 1
    'B' → posición 2  
    'C' → posición 3
    
    Paso 3: Aplicar la fórmula RADIX-50
    resultado = 1×40² + 2×40¹ + 3×40⁰
    resultado = 1×1600 + 2×40 + 3×1
    resultado = 1600 + 80 + 3 = 1683
    """
    
    print(f"\n🔧 CODIFICANDO A RADIX-50: '{texto}'")
    print("=" * 40)
    
    # Paso 1: Normalizar el texto
    texto_normalizado = texto.upper().ljust(3)[:3]  # Mayúsculas, exactamente 3 chars
    print(f"Texto normalizado: '{texto_normalizado}'")
    
    resultado = 0
    
    # Paso 2: Procesar cada carácter
    for i, caracter in enumerate(texto_normalizado):
        print(f"\nPaso {i+1}: Procesando carácter '{caracter}' (posición {i+1})")
        
        # Encontrar la posición del carácter en RADIX-50
        try:
            posicion = CARACTERES_RADIX50.index(caracter)
            print(f"  '{caracter}' está en posición {posicion} del conjunto RADIX-50")
        except ValueError:
            print(f"  ⚠️  '{caracter}' NO ESTÁ en el conjunto RADIX-50, usando espacio")
            posicion = 0  # Usar espacio para caracteres inválidos
        
        # Calcular la contribución de este carácter
        potencia = 40 ** (2 - i)  # 40², 40¹, 40⁰
        contribucion = posicion * potencia
        
        print(f"  Contribución: {posicion} × 40^{2-i} = {posicion} × {potencia} = {contribucion}")
        
        resultado += contribucion
        print(f"  Resultado acumulado: {resultado}")
    
    print(f"\n✅ RESULTADO FINAL: {resultado} (0x{resultado:04X})")
    return resultado


def decodificar_nombre_archivo_rt11(palabra1: int, palabra2: int, palabra3: int) -> Tuple[str, str]:
    """
    Decodifica un nombre de archivo RT-11 completo desde 3 palabras RADIX-50
    
    EXPLICACIÓN DEL FORMATO RT-11:
    ==============================
    
    Los nombres de archivo RT-11 se almacenan en 3 palabras de 16 bits:
    
    Palabra 1: Primeros 3 caracteres del nombre (ej: "FIL")
    Palabra 2: Siguientes 3 caracteres del nombre (ej: "E  ") 
    Palabra 3: Extensión de 3 caracteres (ej: "TXT")
    
    Resultado: "FILE.TXT"
    
    Limitaciones:
    - Nombre: máximo 6 caracteres
    - Extensión: máximo 3 caracteres
    - Solo caracteres RADIX-50 permitidos
    """
    
    print(f"\n📁 DECODIFICANDO NOMBRE DE ARCHIVO RT-11")
    print("=" * 45)
    print(f"Palabra 1: {palabra1:5d} (0x{palabra1:04X})")
    print(f"Palabra 2: {palabra2:5d} (0x{palabra2:04X})")
    print(f"Palabra 3: {palabra3:5d} (0x{palabra3:04X})")
    
    try:
        # Decodificar cada parte
        print("\n🔍 Decodificando palabra 1 (primeros 3 chars del nombre):")
        parte1 = radix50_decodificar_paso_a_paso(palabra1)
        
        print("\n🔍 Decodificando palabra 2 (siguientes 3 chars del nombre):")
        parte2 = radix50_decodificar_paso_a_paso(palabra2)
        
        print("\n🔍 Decodificando palabra 3 (extensión):")
        parte3 = radix50_decodificar_paso_a_paso(palabra3)
        
        # Combinar nombre (quitar espacios al final)
        nombre_completo = (parte1 + parte2).rstrip()
        extension = parte3.rstrip()
        
        print(f"\n📋 ANÁLISIS DEL RESULTADO:")
        print(f"Parte 1 del nombre: '{parte1}'")
        print(f"Parte 2 del nombre: '{parte2}'") 
        print(f"Nombre completo: '{nombre_completo}'")
        print(f"Extensión: '{extension}'")
        
        # Validaciones básicas
        if not nombre_completo or len(nombre_completo) > 6:
            print("⚠️  NOMBRE INVÁLIDO (vacío o muy largo)")
            return None, None
            
        if extension and len(extension) > 3:
            print("⚠️  EXTENSIÓN INVÁLIDA (muy larga)")
            return None, None
        
        print(f"✅ ARCHIVO VÁLIDO: '{nombre_completo}' extensión '{extension}'")
        return nombre_completo, extension
        
    except Exception as e:
        print(f"❌ ERROR decodificando: {e}")
        return None, None


# =============================================================================
# PARTE 3: DEMOSTRACIÓN INTERACTIVA
# =============================================================================

def demo_radix50():
    """
    Demostración interactiva del sistema RADIX-50
    """
    print("\n" + "="*60)
    print("DEMOSTRACIÓN INTERACTIVA DEL SISTEMA RADIX-50")
    print("="*60)
    
    # Ejemplos de decodificación
    ejemplos_numeros = [
        0,      # Espacios
        1,      # " A"
        40,     # "A "
        1600,   # "A  "
        1681,   # "ABC"
        12345,  # Ejemplo random
    ]
    
    print("\n📚 EJEMPLOS DE DECODIFICACIÓN:")
    print("-" * 40)
    
    for numero in ejemplos_numeros:
        resultado = radix50_decodificar_paso_a_paso(numero)
        print(f"Entrada: {numero:5d} → Salida: '{resultado}'")
    
    # Ejemplos de codificación
    ejemplos_texto = [
        "A",
        "AB", 
        "ABC",
        "123",
        "FILE",
        "$$$"
    ]
    
    print("\n📚 EJEMPLOS DE CODIFICACIÓN:")
    print("-" * 40)
    
    for texto in ejemplos_texto:
        resultado = radix50_codificar_paso_a_paso(texto)
        print(f"Entrada: '{texto}' → Salida: {resultado}")
    
    # Ejemplo completo de nombre de archivo
    print("\n📚 EJEMPLO COMPLETO: NOMBRE DE ARCHIVO RT-11")
    print("-" * 50)
    
    # Simular el archivo "HELLO.TXT"
    print("Ejemplo: queremos almacenar 'HELLO.TXT'")
    print("Paso 1: Dividir en partes")
    print("  Nombre: 'HELLO' → 'HEL' + 'LO '")
    print("  Extensión: 'TXT'")
    
    palabra1 = radix50_codificar_paso_a_paso("HEL")
    palabra2 = radix50_codificar_paso_a_paso("LO ")  
    palabra3 = radix50_codificar_paso_a_paso("TXT")
    
    print(f"\nPalabras almacenadas:")
    print(f"  Palabra 1: {palabra1} (HEL)")
    print(f"  Palabra 2: {palabra2} (LO )")
    print(f"  Palabra 3: {palabra3} (TXT)")
    
    print("\nAhora decodificamos de vuelta:")
    nombre, extension = decodificar_nombre_archivo_rt11(palabra1, palabra2, palabra3)
    
    if nombre and extension:
        print(f"\n🎉 ¡ÉXITO! Archivo reconstruido: '{nombre}.{extension}'")
    else:
        print(f"\n❌ Error en la reconstrucción")


# =============================================================================
# PARTE 4: FUNCIÓN PRINCIPAL EDUCATIVA
# =============================================================================

def main():
    """
    Función principal del programa educativo
    """
    print("RT-11 EXTRACTOR EDUCATIVO")
    print("=" * 25)
    print("Versión especial para enseñar RADIX-50")
    print("Autor: Basado en rt11extract original")
    print()
    
    print("Este programa está diseñado para ayudar a estudiantes de")
    print("Organización de Computadoras a entender cómo funcionaba")
    print("el sistema RADIX-50 en las computadoras PDP-11.")
    print()
    
    # Ejecutar demostración
    demo_radix50()
    
    print("\n" + "="*60)
    print("EJERCICIOS PROPUESTOS PARA ESTUDIANTES:")
    print("="*60)
    print("1. ¿Cuál es el número RADIX-50 para 'PDP'?")
    print("2. ¿Qué texto representa el número 12345?")
    print("3. ¿Por qué RADIX-50 usa exactamente 40 caracteres?")
    print("4. ¿Cuál es la máxima palabra de 16 bits en RADIX-50?")
    print("5. ¿Cómo almacenarías el archivo 'PROGRAM.ASM'?")
    print()
    print("¡Modifica este código para experimentar!")


# =============================================================================
# PARTE 5: FUNCIONES AUXILIARES (SIMPLIFICADAS)
# =============================================================================

def mostrar_tabla_radix50():
    """
    Muestra una tabla completa de los caracteres RADIX-50
    """
    print("\nTABLA COMPLETA DE CARACTERES RADIX-50")
    print("=" * 40)
    print("Pos | Char | Binario | Octal | Hex")
    print("-" * 40)
    
    for i, char in enumerate(CARACTERES_RADIX50):
        char_display = "SPACE" if char == ' ' else char
        print(f"{i:2d}  | {char_display:5s} | {i:07b} | {i:3o} | {i:2X}")


def calcular_estadisticas_radix50():
    """
    Calcula estadísticas interesantes sobre RADIX-50
    """
    print("\nESTADÍSTICAS INTERESANTES DE RADIX-50")
    print("=" * 40)
    print(f"Número de caracteres: {len(CARACTERES_RADIX50)}")
    print(f"Bits necesarios por carácter: {len(CARACTERES_RADIX50).bit_length() - 1}")
    print(f"Máximo valor de 3 caracteres: {40**3 - 1}")
    print(f"Bits necesarios para 3 chars: {(40**3 - 1).bit_length()}")
    print(f"Eficiencia vs 16 bits: {((40**3 - 1).bit_length() / 16) * 100:.1f}%")
    print()
    print("¡Por eso funcionaba tan bien en computadoras de 16 bits!")


if __name__ == '__main__':
    # Si se ejecuta directamente, mostrar la demostración educativa
    main()
    
    # Funciones adicionales para experimentar
    print("\n" + "="*60)
    print("INFORMACIÓN ADICIONAL:")
    print("="*60)
    
    mostrar_tabla_radix50()
    calcular_estadisticas_radix50()
    
    print("\n🎓 FIN DEL PROGRAMA EDUCATIVO")
    print("Modifica el código para experimentar más!")
