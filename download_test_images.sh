#!/bin/bash

# RT-11 and DEC Disk Image Downloader
# This script downloads various RT-11 and DEC disk images for testing

set -e

echo "=== RT-11 and DEC Disk Image Downloader ==="
echo "Creating test directories..."

cd "/Users/pancho/git/rt11_Extractor"
mkdir -p test_images/rt11 test_images/dec_other test_images/imd_format test_images/simh

echo "=== Downloading RT-11 Images ==="

cd test_images/rt11

# RT-11 from various sources
echo "Downloading RT-11 v5.6..."
curl -L -o "rt11_v56.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/rt11v56.dsk" || echo "Failed to download rt11v56.dsk"

echo "Downloading RT-11 v5.7..."
curl -L -o "rt11_v57.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/rt11v57.dsk" || echo "Failed to download rt11v57.dsk"

echo "Downloading RT-11 sample disk..."
curl -L -o "rt11_sample.dsk" "https://raw.githubusercontent.com/simh/simh/master/BIN/rt11.dsk" || echo "Failed to download rt11_sample.dsk"

echo "Downloading RT-11 games disk..."
curl -L -o "rt11_games.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/games.dsk" || echo "Failed to download games.dsk"

echo "Downloading RT-11 utilities disk..."
curl -L -o "rt11_utils.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/utils.dsk" || echo "Failed to download utils.dsk"

echo "Downloading RT-11 FORTRAN disk..."
curl -L -o "rt11_fortran.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/fortran.dsk" || echo "Failed to download fortran.dsk"

echo "Downloading RT-11 BASIC disk..."
curl -L -o "rt11_basic.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rt11/basic.dsk" || echo "Failed to download basic.dsk"

echo "=== Downloading DEC ImageDisk (IMD) Files ==="

cd ../imd_format

echo "Downloading ImageDisk samples..."
curl -L -o "pdp11_boot.imd" "http://www.classiccmp.org/dunfield/img/pdp11/pdp11boot.imd" || echo "Failed to download pdp11boot.imd"

curl -L -o "rt11_sample.imd" "http://www.classiccmp.org/dunfield/img/pdp11/rt11.imd" || echo "Failed to download rt11.imd"

echo "=== Downloading SIMH Images ==="

cd ../simh

echo "Downloading SIMH RT-11 images..."
curl -L -o "simh_rt11_v4.dsk" "https://github.com/simh/simh/raw/master/BIN/rt11v4.dsk" || echo "Failed to download rt11v4.dsk"

curl -L -o "simh_rt11_v5.dsk" "https://github.com/simh/simh/raw/master/BIN/rt11v5.dsk" || echo "Failed to download rt11v5.dsk"

echo "Downloading PDP-11 UNIX v6..."
curl -L -o "unix_v6.dsk" "https://github.com/simh/simh/raw/master/BIN/unixv6.dsk" || echo "Failed to download unixv6.dsk"

echo "=== Downloading DEC Other Systems ==="

cd ../dec_other

echo "Downloading PDP-11 DOS/BATCH..."
curl -L -o "pdp11_dos.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/dos-batch/dos.dsk" || echo "Failed to download dos.dsk"

echo "Downloading RSX-11M..."
curl -L -o "rsx11m.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/rsx11m/rsx11m.dsk" || echo "Failed to download rsx11m.dsk"

echo "=== Alternative Sources ==="

cd ../rt11

echo "Downloading from retro computing archives..."
curl -L -o "retro_rt11_1.dsk" "https://winworldpc.com/download/c3919ce2-8be2-8a18-c39a-11c3a4e284a2/from/c3ae1ce2-8e99-8195-c395-11c3a4e28295" || echo "Failed from winworld"

echo "Downloading from Digital Research archives..."
curl -L -o "rt11_diag.dsk" "http://www.bitsavers.org/bits/DEC/pdp11/floppyimages/diagnostics/diag.dsk" || echo "Failed to download diag.dsk"

echo "=== Creating README ==="

cd /Users/pancho/git/rt11_Extractor/test_images

cat > README.md << 'EOF'
# RT-11 and DEC Test Images

This directory contains various RT-11 and DEC disk images for testing the RT-11 Extractor.

## Directory Structure

- `rt11/` - RT-11 operating system images (.dsk format)
- `imd_format/` - ImageDisk format files (.imd)
- `simh/` - Images from the SIMH simulator project
- `dec_other/` - Other DEC operating systems (RSX-11M, DOS/BATCH, etc.)

## Sources

Images downloaded from:
- bitsavers.org - Primary DEC archive
- SIMH project - Historical computer simulator
- ClassicCMP.org - Vintage computer preservation
- Various retro computing archives

## Usage

These images can be used to test:
1. RT-11 file extraction
2. ImageDisk (IMD) to DSK conversion
3. FUSE filesystem mounting
4. Cross-platform compatibility

## File Types Expected

- `.dsk` - Standard RT-11 disk images
- `.imd` - ImageDisk format (needs conversion)
- Various RT-11 file types: .SAV, .BAS, .FOR, .MAC, .TXT, .DAT

## Testing Commands

```bash
# Test extraction
./rt11extract_cli rt11_sample.dsk -l

# Test IMD conversion
./imd2raw rt11_sample.imd rt11_converted.dsk

# Test GUI
python3 rt11extract_gui.py
```

EOF

echo "=== Download Summary ==="
echo ""
echo "RT-11 Images:"
ls -la rt11/ 2>/dev/null || echo "No RT-11 images downloaded"
echo ""
echo "IMD Images:"
ls -la imd_format/ 2>/dev/null || echo "No IMD images downloaded"
echo ""
echo "SIMH Images:"
ls -la simh/ 2>/dev/null || echo "No SIMH images downloaded"
echo ""
echo "Other DEC Images:"
ls -la dec_other/ 2>/dev/null || echo "No other DEC images downloaded"

echo ""
echo "=== Download Complete ==="
echo "Test images ready in: /Users/pancho/git/rt11_Extractor/test_images/"
echo "You can now test the RT-11 Extractor with these images!"
