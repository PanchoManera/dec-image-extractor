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

