#!/usr/bin/env python3
"""
RADIX-50 Interactivo - Laboratorio de Experimentación
=====================================================

Este script permite a los estudiantes experimentar interactivamente
con el sistema RADIX-50, resolver ejercicios y verificar respuestas.

Perfecto para usar en laboratorios de Organización de Computadoras.
"""

import sys
import random
from rt11extract_educativo import (
    CARACTERES_RADIX50,
    radix50_decodificar_paso_a_paso,
    radix50_codificar_paso_a_paso,
    decodificar_nombre_archivo_rt11
)

def limpiar_pantalla():
    """Limpia la pantalla (funciona en Windows, Linux, Mac)"""
    import os
    os.system('cls' if os.name == 'nt' else 'clear')

def mostrar_menu():
    """Muestra el menú principal"""
    print("\n" + "="*50)
    print("🎓 LABORATORIO INTERACTIVO RADIX-50")
    print("="*50)
    print("1. 🔢 Codificar texto a RADIX-50")
    print("2. 🔤 Decodificar número RADIX-50")
    print("3. 📁 Trabajar con nombres de archivo RT-11")
    print("4. 🎯 Ejercicios automáticos")
    print("5. 📚 Ver tabla de caracteres")
    print("6. 🧮 Calculadora RADIX-50")
    print("7. 🏆 Quiz de práctica")
    print("8. ❌ Salir")
    print("-"*50)

def codificar_interactivo():
    """Permite al usuario codificar texto paso a paso"""
    print("\n🔧 CODIFICADOR RADIX-50 INTERACTIVO")
    print("="*40)
    
    while True:
        texto = input("\nIngresa texto para codificar (máximo 3 chars, o 'q' para salir): ").strip()
        
        if texto.lower() == 'q':
            break
            
        if len(texto) == 0:
            print("⚠️  Debes ingresar al menos un carácter")
            continue
            
        # Verificar caracteres válidos
        texto_upper = texto.upper()
        caracteres_invalidos = []
        for char in texto_upper:
            if char not in CARACTERES_RADIX50:
                caracteres_invalidos.append(char)
        
        if caracteres_invalidos:
            print(f"⚠️  Caracteres inválidos: {', '.join(caracteres_invalidos)}")
            print(f"Caracteres válidos: {CARACTERES_RADIX50}")
            continue
        
        resultado = radix50_codificar_paso_a_paso(texto)
        print(f"\n📋 RESUMEN: '{texto}' → {resultado}")
        
        # Verificar decodificando
        print("\n🔍 VERIFICACIÓN (decodificando el resultado):")
        verificacion = radix50_decodificar_paso_a_paso(resultado)
        if verificacion.strip() == texto_upper:
            print("✅ ¡Verificación exitosa!")
        else:
            print(f"❌ Error en verificación: esperaba '{texto_upper}', obtuvo '{verificacion.strip()}'")

def decodificar_interactivo():
    """Permite al usuario decodificar números paso a paso"""
    print("\n🔍 DECODIFICADOR RADIX-50 INTERACTIVO")
    print("="*40)
    
    while True:
        entrada = input("\nIngresa número para decodificar (0-63999, o 'q' para salir): ").strip()
        
        if entrada.lower() == 'q':
            break
            
        try:
            # Permitir entrada en decimal, hex (0x) u octal (0o)
            if entrada.startswith('0x') or entrada.startswith('0X'):
                numero = int(entrada, 16)
            elif entrada.startswith('0o') or entrada.startswith('0O'):
                numero = int(entrada, 8)
            else:
                numero = int(entrada)
                
            if numero < 0 or numero >= 40**3:
                print(f"⚠️  Número fuera de rango: debe estar entre 0 y {40**3-1}")
                continue
                
            resultado = radix50_decodificar_paso_a_paso(numero)
            print(f"\n📋 RESUMEN: {numero} → '{resultado}'")
            
            # Verificar codificando
            print("\n🔧 VERIFICACIÓN (codificando el resultado):")
            verificacion = radix50_codificar_paso_a_paso(resultado.strip())
            if verificacion == numero:
                print("✅ ¡Verificación exitosa!")
            else:
                print(f"❌ Error en verificación: esperaba {numero}, obtuvo {verificacion}")
                
        except ValueError:
            print("⚠️  Entrada inválida. Usa números decimales, hex (0x1234) u octales (0o1234)")

def nombres_archivo_interactivo():
    """Permite trabajar con nombres de archivo RT-11"""
    print("\n📁 NOMBRES DE ARCHIVO RT-11 INTERACTIVOS")
    print("="*45)
    
    while True:
        print("\nOpciones:")
        print("1. Codificar nombre de archivo")
        print("2. Decodificar desde 3 palabras")
        print("3. Volver al menú principal")
        
        opcion = input("\nElige opción (1-3): ").strip()
        
        if opcion == '3':
            break
        elif opcion == '1':
            nombre = input("Ingresa nombre de archivo (ej: HELLO.TXT): ").strip().upper()
            
            if '.' in nombre:
                archivo, extension = nombre.split('.', 1)
            else:
                archivo = nombre
                extension = ""
            
            if len(archivo) > 6:
                print("⚠️  Nombre muy largo (máximo 6 caracteres)")
                continue
            if len(extension) > 3:
                print("⚠️  Extensión muy larga (máximo 3 caracteres)")
                continue
                
            # Dividir nombre en dos partes de 3 caracteres
            parte1 = archivo[:3].ljust(3)
            parte2 = archivo[3:6].ljust(3)
            parte3 = extension.ljust(3)
            
            print(f"\nDivisión:")
            print(f"  Nombre parte 1: '{parte1}'")
            print(f"  Nombre parte 2: '{parte2}'")
            print(f"  Extensión:      '{parte3}'")
            
            palabra1 = radix50_codificar_paso_a_paso(parte1)
            palabra2 = radix50_codificar_paso_a_paso(parte2)
            palabra3 = radix50_codificar_paso_a_paso(parte3)
            
            print(f"\nResultado:")
            print(f"  Palabra 1: {palabra1:5d} (0x{palabra1:04X})")
            print(f"  Palabra 2: {palabra2:5d} (0x{palabra2:04X})")
            print(f"  Palabra 3: {palabra3:5d} (0x{palabra3:04X})")
            
        elif opcion == '2':
            try:
                palabra1 = int(input("Palabra 1: "))
                palabra2 = int(input("Palabra 2: "))
                palabra3 = int(input("Palabra 3: "))
                
                nombre, extension = decodificar_nombre_archivo_rt11(palabra1, palabra2, palabra3)
                if nombre:
                    if extension:
                        print(f"\n✅ Archivo: '{nombre}.{extension}'")
                    else:
                        print(f"\n✅ Archivo: '{nombre}' (sin extensión)")
                        
            except ValueError:
                print("⚠️  Ingresa números válidos")

def ejercicios_automaticos():
    """Genera ejercicios automáticos para el estudiante"""
    print("\n🎯 EJERCICIOS AUTOMÁTICOS")
    print("="*30)
    
    ejercicios = [
        ("Codifica 'PDP'", lambda: radix50_codificar_texto_simple("PDP")),
        ("Decodifica 12345", lambda: radix50_decodificar_texto_simple(12345)),
        ("Codifica 'RT11'", lambda: radix50_codificar_texto_simple("RT11")),  # Se truncará a RT1
        ("Decodifica 1600", lambda: radix50_decodificar_texto_simple(1600)),
        ("Codifica '123'", lambda: radix50_codificar_texto_simple("123")),
    ]
    
    puntos = 0
    total = len(ejercicios)
    
    for i, (pregunta, solucion_func) in enumerate(ejercicios, 1):
        print(f"\n--- Ejercicio {i}/{total} ---")
        print(f"Pregunta: {pregunta}")
        
        respuesta_usuario = input("Tu respuesta: ").strip()
        respuesta_correcta = solucion_func()
        
        if respuesta_usuario.upper() == str(respuesta_correcta).upper():
            print("✅ ¡Correcto!")
            puntos += 1
        else:
            print(f"❌ Incorrecto. La respuesta correcta es: {respuesta_correcta}")
            
        input("Presiona Enter para continuar...")
    
    print(f"\n🏆 RESULTADO FINAL: {puntos}/{total} ({puntos/total*100:.1f}%)")
    
    if puntos == total:
        print("🎉 ¡Perfecto! Dominas el RADIX-50")
    elif puntos >= total * 0.8:
        print("👍 ¡Muy bien! Casi perfecto")
    elif puntos >= total * 0.6:
        print("👌 Bien, pero puedes mejorar")
    else:
        print("📚 Necesitas practicar más")

def radix50_codificar_texto_simple(texto):
    """Codifica texto sin mostrar pasos (para ejercicios)"""
    texto = texto.upper().ljust(3)[:3]
    resultado = 0
    for i, char in enumerate(texto):
        try:
            posicion = CARACTERES_RADIX50.index(char)
        except ValueError:
            posicion = 0
        resultado += posicion * (40 ** (2 - i))
    return resultado

def radix50_decodificar_texto_simple(numero):
    """Decodifica número sin mostrar pasos (para ejercicios)"""
    if numero == 0:
        return "   "
    if numero >= 40**3:
        return "???"
    
    resultado = ""
    temp = numero
    for i in range(3):
        pos = temp % 40
        temp //= 40
        if pos < len(CARACTERES_RADIX50):
            resultado = CARACTERES_RADIX50[pos] + resultado
        else:
            resultado = "?" + resultado
    return resultado.strip()

def mostrar_tabla():
    """Muestra la tabla de caracteres RADIX-50"""
    print("\n📚 TABLA DE CARACTERES RADIX-50")
    print("="*40)
    print("Pos | Char | Dec | Hex | Oct | Bin")
    print("-"*40)
    
    for i, char in enumerate(CARACTERES_RADIX50):
        char_display = "SPC" if char == ' ' else f" {char} "
        print(f"{i:2d}  | {char_display} | {i:2d}  | {i:2X}  | {i:2o}  | {i:06b}")

def calculadora_radix50():
    """Calculadora simple para RADIX-50"""
    print("\n🧮 CALCULADORA RADIX-50")
    print("="*30)
    print("Convierte entre texto y números rápidamente")
    print("(sin mostrar pasos detallados)")
    
    while True:
        print("\nOpciones:")
        print("1. Texto → Número")
        print("2. Número → Texto") 
        print("3. Volver")
        
        opcion = input("\nOpción: ").strip()
        
        if opcion == '3':
            break
        elif opcion == '1':
            texto = input("Texto (máx 3 chars): ").strip()
            if texto:
                resultado = radix50_codificar_texto_simple(texto)
                print(f"'{texto}' → {resultado} (0x{resultado:04X})")
        elif opcion == '2':
            try:
                numero = int(input("Número: "))
                resultado = radix50_decodificar_texto_simple(numero)
                print(f"{numero} → '{resultado}'")
            except ValueError:
                print("⚠️  Número inválido")

def quiz_practica():
    """Quiz de práctica con preguntas aleatorias"""
    print("\n🏆 QUIZ DE PRÁCTICA RADIX-50")
    print("="*35)
    
    preguntas = 5
    puntos = 0
    
    for i in range(preguntas):
        print(f"\n--- Pregunta {i+1}/{preguntas} ---")
        
        if random.choice([True, False]):
            # Pregunta de codificación
            textos = ['A', 'AB', 'XYZ', '123', 'RT', 'PDP', '$.$', 'END']
            texto = random.choice(textos)
            respuesta_correcta = radix50_codificar_texto_simple(texto)
            
            print(f"¿Cuál es el valor RADIX-50 de '{texto}'?")
            try:
                respuesta = int(input("Respuesta: "))
                if respuesta == respuesta_correcta:
                    print("✅ ¡Correcto!")
                    puntos += 1
                else:
                    print(f"❌ Incorrecto. Respuesta: {respuesta_correcta}")
            except ValueError:
                print(f"❌ Respuesta inválida. Respuesta: {respuesta_correcta}")
        else:
            # Pregunta de decodificación
            numero = random.randint(1, 10000)
            respuesta_correcta = radix50_decodificar_texto_simple(numero)
            
            print(f"¿Qué texto representa el número {numero}?")
            respuesta = input("Respuesta: ").strip().upper()
            if respuesta == respuesta_correcta.strip():
                print("✅ ¡Correcto!")
                puntos += 1
            else:
                print(f"❌ Incorrecto. Respuesta: '{respuesta_correcta.strip()}'")
    
    print(f"\n🎯 PUNTUACIÓN FINAL: {puntos}/{preguntas}")
    porcentaje = puntos / preguntas * 100
    
    if porcentaje >= 90:
        print("🏆 ¡Excelente! Eres un experto en RADIX-50")
    elif porcentaje >= 70:
        print("👍 ¡Muy bien! Buen dominio del tema")
    elif porcentaje >= 50:
        print("👌 Regular, sigue practicando")
    else:
        print("📚 Necesitas estudiar más el RADIX-50")

def main():
    """Función principal del programa interactivo"""
    print("🎓 BIENVENIDO AL LABORATORIO INTERACTIVO RADIX-50")
    print("Perfecto para estudiantes de Organización de Computadoras")
    
    while True:
        mostrar_menu()
        opcion = input("Elige una opción (1-8): ").strip()
        
        if opcion == '1':
            codificar_interactivo()
        elif opcion == '2':
            decodificar_interactivo()
        elif opcion == '3':
            nombres_archivo_interactivo()
        elif opcion == '4':
            ejercicios_automaticos()
        elif opcion == '5':
            mostrar_tabla()
        elif opcion == '6':
            calculadora_radix50()
        elif opcion == '7':
            quiz_practica()
        elif opcion == '8':
            print("\n👋 ¡Gracias por usar el laboratorio RADIX-50!")
            print("¡Sigue practicando y aprendiendo!")
            break
        else:
            print("⚠️  Opción inválida, elige entre 1-8")

if __name__ == '__main__':
    main()
