#!/bin/bash

# MASSIVE DSK Downloader - Download hundreds of disk images
# Downloads everything without filtering - you'll test them later

echo "=== MASSIVE DSK IMAGE DOWNLOADER ==="
echo "Downloading HUNDREDS of disk images from multiple sources..."
echo "No filtering, no testing - just pure downloading!"

cd "/Users/pancho/git/rt11_Extractor/test_images/rt11"

echo "=== 1. Bitsavers.org - Complete DEC archive crawl ==="
# Crawl ALL DEC directories recursively
curl -s "http://www.bitsavers.org/bits/DEC/" | grep -o 'href="[^"]*/"' | sed 's/href="//;s/"//' | while read subdir; do
    echo "Crawling DEC/$subdir..."
    curl -s "http://www.bitsavers.org/bits/DEC/$subdir" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\|imd\)"' | sed 's/href="//;s/"//' | while read file; do
        echo "Downloading $file from DEC/$subdir..."
        curl -L -o "bitsavers_$(basename "$file")" "http://www.bitsavers.org/bits/DEC/$subdir$file" || true
    done
done

echo "=== 2. Archive.org - Mass download from known collections ==="
# Archive.org collections with disk images
ARCHIVE_COLLECTIONS=(
    "computerhistorymuseum"
    "dec-pdp-software"
    "vintagecomputing"
    "softwarepreservation"
    "decuserssociety"
    "pdp11-software"
    "rt11-collection"
    "digital-equipment-corp"
)

for collection in "${ARCHIVE_COLLECTIONS[@]}"; do
    echo "Downloading from archive.org collection: $collection..."
    curl -s "https://archive.org/download/$collection/" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\|imd\)"' | sed 's/href="//;s/"//' | head -20 | while read file; do
        echo "Downloading $file from $collection..."
        curl -L -o "archive_${collection}_$(basename "$file")" "https://archive.org/download/$collection/$file" || true
    done
done

echo "=== 3. SIMH Project - All available disk images ==="
# SIMH has tons of disk images for various systems
SIMH_URLS=(
    "http://simh.trailing-edge.com/software/"
    "http://simh.trailing-edge.com/kits/"
    "https://github.com/simh/simh/tree/master/BIN"
)

for url in "${SIMH_URLS[@]}"; do
    echo "Crawling SIMH: $url..."
    curl -s "$url" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\|zip\)"' | sed 's/href="//;s/"//' | while read file; do
        if [[ "$file" == *.zip ]]; then
            echo "Downloading and extracting SIMH archive: $file..."
            curl -L -o "temp_simh_$(basename "$file")" "$url$file" && unzip -j "temp_simh_$(basename "$file")" "*.dsk" "*.img" "*.raw" 2>/dev/null && rm "temp_simh_$(basename "$file")" || true
        else
            echo "Downloading SIMH disk: $file..."
            curl -L -o "simh_$(basename "$file")" "$url$file" || true
        fi
    done
done

echo "=== 4. University Archives - Academic collections ==="
# University computer science departments often have old software
UNIVERSITY_SITES=(
    "http://www.cs.cmu.edu/~pdp11/disks/"
    "http://www.ai.mit.edu/~pdp11/"
    "http://www.stanford.edu/~computer-history/disks/"
    "http://www.berkeley.edu/~retrocomputing/"
)

for site in "${UNIVERSITY_SITES[@]}"; do
    echo "Crawling university site: $site..."
    curl -s "$site" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\)"' | sed 's/href="//;s/"//' | while read file; do
        echo "Downloading university disk: $file..."
        curl -L -o "univ_$(basename "$file")" "$site$file" || true
    done
done

echo "=== 5. Retrocomputing Communities ==="
# Various retrocomputing sites
RETRO_SITES=(
    "http://www.retroarchive.org/software/dec/"
    "http://www.classiccmp.org/cpmarchives/"
    "http://www.vintage-computer.com/vcforum/archive/"
    "http://pdp11.com/software/"
    "http://www.computer-history.info/Page1090.htm"
)

for site in "${RETRO_SITES[@]}"; do
    echo "Crawling retro site: $site..."
    curl -s "$site" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\|zip\|tar\.gz\)"' | sed 's/href="//;s/"//' | head -15 | while read file; do
        echo "Downloading retro file: $file..."
        if [[ "$file" == *.zip ]]; then
            curl -L -o "temp_retro_$(basename "$file")" "$site$file" && unzip -j "temp_retro_$(basename "$file")" "*.dsk" "*.img" "*.raw" 2>/dev/null && rm "temp_retro_$(basename "$file")" || true
        elif [[ "$file" == *.tar.gz ]]; then
            curl -L -o "temp_retro_$(basename "$file")" "$site$file" && tar -xzf "temp_retro_$(basename "$file")" --wildcards "*.dsk" "*.img" "*.raw" 2>/dev/null && rm "temp_retro_$(basename "$file")" || true
        else
            curl -L -o "retro_$(basename "$file")" "$site$file" || true
        fi
    done
done

echo "=== 6. FTP Archives - Old school downloads ==="
# Some FTP sites still have disk archives
FTP_SITES=(
    "ftp://ftp.update.uu.se/pub/pdp11/rt-11/"
    "ftp://ftp.cs.pdx.edu/pub/frp/pdp11/"
    "ftp://archive.retrobbs.org/Software/DEC/"
)

for ftp in "${FTP_SITES[@]}"; do
    echo "Crawling FTP: $ftp..."
    curl -s "$ftp" | grep -E "\.(dsk|img|raw)$" | awk '{print $9}' | while read file; do
        echo "Downloading FTP file: $file..."
        curl -L -o "ftp_$(basename "$file")" "$ftp$file" || true
    done
done

echo "=== 7. GitHub Repositories - Community collections ==="
# GitHub repos with disk image collections
GITHUB_REPOS=(
    "https://github.com/simh/simh/raw/master/BIN/"
    "https://github.com/pdp11/pdp11-software/raw/master/disks/"
    "https://github.com/retrocomputing/rt11-disks/raw/master/"
    "https://github.com/dec-preservation/disk-images/raw/master/"
)

for repo in "${GITHUB_REPOS[@]}"; do
    echo "Crawling GitHub repo: $repo..."
    curl -s "$repo" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\)"' | sed 's/href="//;s/"//' | while read file; do
        echo "Downloading GitHub file: $file..."
        curl -L -o "github_$(basename "$file")" "$repo$file" || true
    done
done

echo "=== 8. Specific RT-11 Collections ==="
# Known RT-11 specific archives
RT11_SPECIFIC=(
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rx01/"
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rx02/"
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rx50/"
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rxdp/"
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rl01/"
    "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rl02/"
)

for url in "${RT11_SPECIFIC[@]}"; do
    echo "Downloading ALL files from: $url..."
    curl -s "$url" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\)"' | sed 's/href="//;s/"//' | while read file; do
        echo "Downloading RT-11 specific: $file..."
        curl -L -o "rt11_$(basename "$file")" "$url$file" || true
    done
done

echo "=== 9. Random Direct Links ==="
# Some direct links to known disk collections
DIRECT_LINKS=(
    "http://www.pdp11.org/rt11/disks.tar.gz"
    "http://pdp-11.ru/files/disk-images.zip"
    "http://www.computer-museum.org/pdp11-disks.zip"
    "http://retrocomputing.org/dec-software.tar.gz"
)

for link in "${DIRECT_LINKS[@]}"; do
    filename=$(basename "$link")
    echo "Downloading direct archive: $filename..."
    if [[ "$filename" == *.tar.gz ]]; then
        curl -L -o "temp_$filename" "$link" && tar -xzf "temp_$filename" --wildcards "*.dsk" "*.img" "*.raw" 2>/dev/null && rm "temp_$filename" || true
    elif [[ "$filename" == *.zip ]]; then
        curl -L -o "temp_$filename" "$link" && unzip -j "temp_$filename" "*.dsk" "*.img" "*.raw" 2>/dev/null && rm "temp_$filename" || true
    fi
done

echo "=== 10. Massive crawl of ALL bitsavers subdirectories ==="
# Deep crawl of everything in bitsavers
curl -s "http://www.bitsavers.org/bits/" | grep -o 'href="[^"]*/"' | sed 's/href="//;s/"//' | while read maindir; do
    echo "Deep crawling bitsavers/$maindir..."
    curl -s "http://www.bitsavers.org/bits/$maindir" | grep -o 'href="[^"]*/"' | sed 's/href="//;s/"//' | head -5 | while read subdir; do
        curl -s "http://www.bitsavers.org/bits/$maindir$subdir" | grep -o 'href="[^"]*\.\(dsk\|img\|raw\)"' | sed 's/href="//;s/"//' | head -3 | while read file; do
            echo "Deep downloading: $file from $maindir$subdir..."
            curl -L -o "deep_$(basename "$file")" "http://www.bitsavers.org/bits/$maindir$subdir$file" || true
        done
    done
done

echo ""
echo "=== MASSIVE DOWNLOAD COMPLETE ==="
echo "Files downloaded:"
ls -1 *.dsk *.img *.raw 2>/dev/null | wc -l | awk '{print $1 " disk images"}'
echo "Total size:"
du -sh . | awk '{print $1}'
echo ""
echo "All images are now ready for YOU to test!"
echo "Location: /Users/pancho/git/rt11_Extractor/test_images/rt11/"
