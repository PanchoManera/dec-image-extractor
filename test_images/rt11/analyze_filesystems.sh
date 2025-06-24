#!/bin/bash

# Analyze filesystem types of failed images to detect potential DEC systems
# that the RT-11 parser might be missing

echo "=== ANÁLISIS DE FILESYSTEMS - IMÁGENES FALLIDAS ==="
echo "Verificando si hay sistemas DEC que el parser no detecta..."
echo ""

FAILED_IMAGES=(
    "altcpm.dsk"
    "altdos.dsk" 
    "app.dsk"
    "cpm2.dsk"
    "cpm3.dsk"
    "deep_dms32k25011403.dsk"
    "deep_dms8k25011403.dsk"
    "deep_realdiskcopy_from_carl.dsk"
    "dms.dsk"
    "dos_rk.dsk"
    "iu6_dp0.dsk"
    "iu7_dp0.dsk"
    "iu7_dp1.dsk"
    "mbasic.dsk"
    "mpm.dsk"
    "rt11_rxdp_01.dsk"
    "rt11_rxdp_02.dsk"
)

echo "🔍 ANÁLISIS DETALLADO DE SISTEMAS DEC POTENCIALES:"
echo "=================================================="
echo ""

for img in "${FAILED_IMAGES[@]}"; do
    if [ ! -f "$img" ]; then
        continue
    fi
    
    echo "📀 Analizando: $img"
    echo "   Tamaño: $(ls -lh "$img" | awk '{print $5}')"
    
    # Check for DEC signatures
    echo "   🔍 Buscando firmas DEC..."
    
    # Look for RT-11 signatures
    rt11_sigs=$(strings "$img" | grep -i -E "(rt.?11|digital.*equipment|dec)" | head -3)
    if [ ! -z "$rt11_sigs" ]; then
        echo "   ✅ POSIBLES FIRMAS RT-11/DEC encontradas:"
        echo "$rt11_sigs" | sed 's/^/      /'
    fi
    
    # Look for other DEC OS signatures
    dec_os=$(strings "$img" | grep -i -E "(rsx.?11|rsts|tops|pdp.?11|vax|vms)" | head -2)
    if [ ! -z "$dec_os" ]; then
        echo "   🎯 OTROS SISTEMAS DEC encontrados:"
        echo "$dec_os" | sed 's/^/      /'
    fi
    
    # Check filesystem structure at common RT-11 locations
    echo "   📂 Verificando estructura de directorio RT-11..."
    
    # RT-11 directory usually starts at block 6 (offset 0x1800 = 6144 bytes)
    # Look for RT-11 directory patterns
    hexdump -C "$img" -s 6144 -n 512 2>/dev/null | grep -E "[0-9a-fA-F]{8}" | head -3 | while read line; do
        echo "      Bloque 6: $line"
    done
    
    # Check for RT-11 filename patterns (10-char names, specific extensions)
    rt11_files=$(strings "$img" | grep -E "\.SAV|\.BAS|\.MAC|\.FOR|\.DAT" | head -3)
    if [ ! -z "$rt11_files" ]; then
        echo "   📄 EXTENSIONES RT-11 encontradas:"
        echo "$rt11_files" | sed 's/^/      /'
    fi
    
    # Check boot sector for RT-11 boot patterns
    boot_check=$(hexdump -C "$img" -n 512 2>/dev/null | grep -E "(240|040|020)" | head -1)
    if [ ! -z "$boot_check" ]; then
        echo "   🚀 Posible sector de boot RT-11: $boot_check"
    fi
    
    echo ""
done

echo "🔍 ANÁLISIS ESPECÍFICO DE IMÁGENES RXDP (Posibles RT-11):"
echo "========================================================="
echo ""

# These might be RT-11 but with different filesystem layouts
for img in rt11_rxdp_01.dsk rt11_rxdp_02.dsk; do
    if [ -f "$img" ]; then
        echo "📀 $img (RXDP = RX02 Dual Density - podría ser RT-11)"
        
        # Try different directory block locations for RXDP
        for block in 1 2 3 6 10; do
            offset=$((block * 512))
            echo "   Probando directorio en bloque $block (offset $offset):"
            hexdump -C "$img" -s $offset -n 64 | head -2 | sed 's/^/      /'
        done
        
        # Look for RT-11 volume label or system files
        echo "   Buscando archivos de sistema RT-11:"
        strings "$img" | grep -E "(RT11|SWAP|DIR|SYS)" | head -3 | sed 's/^/      /'
        echo ""
    fi
done

echo "🎯 RECOMENDACIONES:"
echo "==================="
echo ""
echo "1. Imágenes que podrían ser RT-11 con diferentes layouts:"
for img in rt11_rxdp_01.dsk rt11_rxdp_02.dsk; do
    if [ -f "$img" ]; then
        echo "   - $img (RXDP format)"
    fi
done

echo ""
echo "2. Imágenes que definitivamente NO son RT-11:"
echo "   - altcpm.dsk, cpm*.dsk (CP/M)"
echo "   - dos_rk.dsk, altdos.dsk (DOS)"
echo "   - iu6_dp0.dsk, iu7_*.dsk (Unix)"
echo "   - dms*.dsk (IBM 1130)"

echo ""
echo "3. Imágenes que necesitan análisis manual:"
echo "   - Cualquiera que muestre firmas DEC pero falle en extracción"

echo ""
echo "✅ ANÁLISIS COMPLETADO"
