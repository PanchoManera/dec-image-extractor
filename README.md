# RT-11 Extractor

Complete toolkit for extracting files from RT-11 disk images and converting ImageDisk (IMD) files with modern GUI and command-line interfaces.

## 🖥️ **What is RT-11?**

RT-11 was a real-time operating system developed by Digital Equipment Corporation (DEC) for the PDP-11 family of computers. This tool helps extract files from RT-11 disk images.

## 📦 **Project Components**

### Core Tools
- **`rt11extract`** - Command-line RT-11 extraction engine
- **`imd2raw.py`** - ImageDisk (IMD) to DSK/RAW converter
- **`rt11extract_gui.py`** - Desktop GUI application with IMD support
- **`rt11extract_simple.py`** - Web-based interface

## 🚀 **Quick Start**

### Option 1: Desktop GUI (Recommended)
```bash
python3 rt11extract_gui.py
```
*Supports both DSK and IMD files with automatic conversion*

### Option 2: Command Line Extraction
```bash
./rt11extract disk_image.dsk -l          # List files
./rt11extract disk_image.dsk -o output/  # Extract all files
```

### Option 3: IMD Conversion
```bash
./imd2raw input.imd output.dsk           # Convert ImageDisk to DSK
```

### Option 4: Web Interface
```bash
python3 rt11extract_simple.py
```
Then open http://localhost:8000 in your browser.

## 📱 **Download Pre-built Executables**

Pre-built executables are automatically generated for all platforms and available in the [Releases](../../releases) section.

### Available Platforms
- **Windows** (x86, x64, ARM64) - `.exe` files
- **macOS** (Intel x64, Apple Silicon ARM64) - Native executables
- **Linux** (x64) - Standalone executables

*Each release includes both GUI and command-line versions.*


## 🔧 **Features**

✅ **Complete RT-11 filesystem support**
✅ **ImageDisk (IMD) to DSK/RAW conversion**
✅ **Automatic IMD detection and conversion in GUI**
✅ **Multiple file extraction modes** (individual, batch)
✅ **Modern GUI with file format validation**
✅ **Web interface for remote access**
✅ **Cross-platform compatibility**
✅ **No external dependencies** (pure Python)
✅ **Original file dates preservation**
✅ **Error recovery and validation**

## 📋 **Supported Formats**

### Disk Image Formats
- **`.dsk`** - Standard RT-11 disk images
- **`.raw`** - Raw disk images
- **`.img`** - Generic disk images
- **`.imd`** - ImageDisk format (auto-converted)

### RT-11 File Types
- `.SAV` - Executable Programs
- `.DAT` - Data Files
- `.TXT` - Text Files
- `.BAS` - BASIC Programs
- `.FOR` - FORTRAN Source
- `.MAC` - MACRO Source
- `.OBJ` - Object Files
- And many more RT-11 file types

## 💻 **System Requirements**

### For Source Code
- **Python 3.6+** with Tkinter support
- **Any modern web browser** (for web interface)

### For Pre-built Executables
- **Windows 7+** (Windows executables)
- **macOS 10.14+** (macOS executables)
- **Linux** with glibc 2.17+ (Linux executables)

## 🛠️ **Development**

All components are written in pure Python with no external dependencies beyond the standard library.

### Architecture
- **rt11extract** - Core extraction engine with RT-11 filesystem parser
- **imd2raw** - ImageDisk format converter (Python port of imd2raw.c)
- **GUI application** - Tkinter-based desktop interface with IMD support
- **Web interface** - HTTP server with HTML5 interface

## 📚 **Technical References**

This project builds upon extensive research and documentation:

### Primary Sources
1. **[putr.asm by D-Bit](http://www.dbit.com/putr/putr.asm)** - Original ASM implementation that served as the foundation for this project's RT-11 filesystem parsing logic

2. **[RT-11 Technical Documentation from DEC](https://ia802804.us.archive.org/31/items/DIGITAL_Guide_to_RT-11_Documentation/DIGITAL_Guide_to_RT-11_Documentation.pdf)** - Official Digital Equipment Corporation guide to RT-11 documentation

3. **[RT-11 Volume and File Formats Manual](http://www.bitsavers.org/pdf/dec/pdp11/rt11/v5.6_Aug91/AA-PD6PA-TC_RT-11_Volume_and_File_Formats_Manual_Aug91.pdf)** - Comprehensive technical specification of RT-11 filesystem structures (v5.6, August 1991)

4. **[The Open SIMH Project](https://github.com/open-simh/simh)** - Historical computer simulation project that provides invaluable context for understanding vintage computing systems

### Additional Resources
- **Bitsavers.org** - Digital preservation of computer documentation
- **Archive.org** - Historical computing documentation archive
- **PDP-11 Community** - Ongoing preservation and documentation efforts

## 📄 **License**

This project maintains the DEC heritage spirit - built for preservation and accessibility of historical computing systems.

## 🏛️ **About RT-11**

RT-11 was a real-time operating system developed by Digital Equipment Corporation (DEC) for the PDP-11 family of computers. This project helps preserve and access historical software by extracting files from RT-11 disk images.

---

Built with ❤️ for retro computing enthusiasts and digital preservation.
