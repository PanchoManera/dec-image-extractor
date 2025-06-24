#!/bin/bash

# Process ALL disk images with RT-11 extractor
# Extract each image to IMAGENAME_extracted folder

echo "=== RT-11 EXTRACTOR - MASS PROCESSING ==="
echo "Processing ALL disk images in directory..."
echo ""

SCRIPT_DIR="/Users/pancho/git/rt11_Extractor"
RT11_EXTRACTOR="$SCRIPT_DIR/rt11extract"
IMD_CONVERTER="$SCRIPT_DIR/imd2raw.py"
CURRENT_DIR="/Users/pancho/git/rt11_Extractor/test_images/rt11"

cd "$CURRENT_DIR"

# Counters
TOTAL_IMAGES=0
SUCCESS_COUNT=0
FAILED_COUNT=0
IMD_CONVERTED=0
TOTAL_FILES_EXTRACTED=0

# Arrays to store results
SUCCESS_IMAGES=()
FAILED_IMAGES=()
SUCCESS_FILES=()

echo "=== PROCESSING IMAGES ==="
echo ""

# Process all image files
for image in *.dsk *.img *.raw *.imd; do
    if [ ! -f "$image" ]; then
        continue
    fi
    
    TOTAL_IMAGES=$((TOTAL_IMAGES + 1))
    basename_no_ext="${image%.*}"
    extract_dir="${basename_no_ext}_extracted"
    
    echo "[$TOTAL_IMAGES] Processing: $image"
    echo "    Extract dir: $extract_dir"
    
    # Create extraction directory
    rm -rf "$extract_dir"
    mkdir -p "$extract_dir"
    
    # Handle IMD files - convert to DSK first
    working_image="$image"
    if [[ "$image" == *.imd ]]; then
        echo "    IMD detected - converting to DSK..."
        converted_dsk="${basename_no_ext}_converted.dsk"
        if python3 "$IMD_CONVERTER" "$image" "$converted_dsk" >/dev/null 2>&1; then
            working_image="$converted_dsk"
            IMD_CONVERTED=$((IMD_CONVERTED + 1))
            echo "    ✅ IMD converted successfully"
        else
            echo "    ❌ IMD conversion FAILED"
            FAILED_COUNT=$((FAILED_COUNT + 1))
            FAILED_IMAGES+=("$image (IMD conversion failed)")
            continue
        fi
    fi
    
    # Extract files using RT-11 extractor
    echo "    Extracting files..."
    if "$RT11_EXTRACTOR" "$working_image" -o "$extract_dir" >/dev/null 2>&1; then
        # Count extracted files
        file_count=$(find "$extract_dir" -type f -name "*" ! -name "*.rt11info" | wc -l | tr -d ' ')
        
        if [ "$file_count" -gt 0 ]; then
            echo "    ✅ SUCCESS - $file_count files extracted"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            SUCCESS_IMAGES+=("$image")
            SUCCESS_FILES+=("$file_count")
            TOTAL_FILES_EXTRACTED=$((TOTAL_FILES_EXTRACTED + file_count))
        else
            echo "    ⚠️  NO FILES - extraction succeeded but no files found"
            SUCCESS_COUNT=$((SUCCESS_COUNT + 1))
            SUCCESS_IMAGES+=("$image")
            SUCCESS_FILES+=("0")
        fi
    else
        echo "    ❌ EXTRACTION FAILED - not a valid RT-11 image"
        FAILED_COUNT=$((FAILED_COUNT + 1))
        FAILED_IMAGES+=("$image")
        rm -rf "$extract_dir"
    fi
    
    # Clean up converted IMD files
    if [[ "$image" == *.imd ]] && [ -f "${basename_no_ext}_converted.dsk" ]; then
        rm -f "${basename_no_ext}_converted.dsk"
    fi
    
    echo ""
done

echo "=== PROCESSING COMPLETE ==="
echo ""

# Generate final report
echo "=== FINAL REPORT ==="
echo "===================="
echo "Total images processed: $TOTAL_IMAGES"
echo "Successful extractions: $SUCCESS_COUNT"
echo "Failed extractions: $FAILED_COUNT"
echo "IMD files converted: $IMD_CONVERTED"
echo "Total files extracted: $TOTAL_FILES_EXTRACTED"
echo ""

if [ ${#SUCCESS_IMAGES[@]} -gt 0 ]; then
    echo "✅ SUCCESSFUL IMAGES ($SUCCESS_COUNT):"
    echo "======================================"
    for i in "${!SUCCESS_IMAGES[@]}"; do
        printf "  %2d. %-40s - %s files\n" $((i+1)) "${SUCCESS_IMAGES[$i]}" "${SUCCESS_FILES[$i]}"
    done
    echo ""
fi

if [ ${#FAILED_IMAGES[@]} -gt 0 ]; then
    echo "❌ FAILED IMAGES ($FAILED_COUNT):"
    echo "================================="
    for i in "${!FAILED_IMAGES[@]}"; do
        printf "  %2d. %s\n" $((i+1)) "${FAILED_IMAGES[$i]}"
    done
    echo ""
fi

echo "=== EXTRACTION DIRECTORIES CREATED ==="
echo "======================================"
ls -la *_extracted/ 2>/dev/null | head -10
if [ $(ls -d *_extracted/ 2>/dev/null | wc -l) -gt 10 ]; then
    echo "... and $(($(ls -d *_extracted/ 2>/dev/null | wc -l) - 10)) more directories"
fi

echo ""
echo "=== SUMMARY STATISTICS ==="
echo "=========================="
echo "Success rate: $(( (SUCCESS_COUNT * 100) / TOTAL_IMAGES ))%"
echo "Average files per successful image: $(( TOTAL_FILES_EXTRACTED / (SUCCESS_COUNT > 0 ? SUCCESS_COUNT : 1) ))"
echo ""
echo "🎉 MASS PROCESSING COMPLETED!"
echo "All extraction directories are ready for inspection."
