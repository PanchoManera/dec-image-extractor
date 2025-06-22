# RT-11 Extractor

Complete toolkit for extracting files from RT-11 disk images (.dsk files) with multiple interfaces.

## 🖥️ **What is RT-11?**

RT-11 was a real-time operating system developed by Digital Equipment Corporation (DEC) for the PDP-11 family of computers. This tool helps extract files from RT-11 disk images.

## 📦 **Project Components**

### Core Engine
- **`rt11extract`** - Command-line RT-11 extraction engine (Python script)

### User Interfaces
- **`rt11extract_gui.py`** - Desktop GUI application (Tkinter)
- **`rt11extract_simple.py`** - Web-based interface (standalone web server)

### Assets
- **`images.png`** - DEC logo for the applications

## 🚀 **Quick Start**

### Option 1: Desktop GUI (Recommended)
```bash
python3 rt11extract_gui.py
```

### Option 2: Web Interface
```bash
python3 rt11extract_simple.py
```
Then open http://localhost:8000 in your browser.

### Option 3: Command Line
```bash
./rt11extract disk_image.dsk -l          # List files
./rt11extract disk_image.dsk -o output/  # Extract all files
```

## 📱 **Pre-built Applications**

### macOS
- **`binaries/macOS/RT11ExtractGUI.app`** - Native macOS application
- **`binaries/macOS/RT11ExtractGUI-macOS.exe`** - Single-file executable

### Windows
- **`binaries/windows/`** - Build kit for Windows 32-bit executable
  - Run `build_windows.bat` on any Windows machine to create the .exe

## 📚 **Technical Documentation**

🎯 **Want to understand how RT-11 works internally?** We have complete technical documentation:

- **[RT11_Technical_Guide.pdf](RT11_Technical_Guide.pdf)** - Professional PDF guide (40+ pages)
- **[RT11_Technical_Guide.md](RT11_Technical_Guide.md)** - Markdown version
- **[TECHNICAL_DOCUMENTATION.md](TECHNICAL_DOCUMENTATION.md)** - How to use and generate docs

### 🔬 What you'll learn:
- **Physical disk structure** - How RT-11 organizes data on disk
- **RADIX-50 encoding** - The alphabet RT-11 uses for filenames
- **16-bit date format** - How RT-11 stores dates in just 2 bytes
- **Complete extraction process** - Step-by-step breakdown
- **Error recovery** - How to handle damaged disk images
- **Practical examples** - Real code for decoding structures
- **Reference tables** - Complete lookup tables and constants

The documentation includes diagrams, Python code examples, and explanations that anyone can understand - from curious users to developers building their own extractors.

## 🔧 **Features**

✅ **Complete RT-11 filesystem support**
✅ **Multiple file extraction modes** (individual, batch)
✅ **Modern GUI with vintage DEC branding**
✅ **Web interface for remote access**
✅ **Cross-platform compatibility**
✅ **No external dependencies** (pure Python)
✅ **Original file dates preservation**
✅ **Error recovery and validation**

## 📋 **Supported File Types**

- `.SAV` - Executable Programs
- `.DAT` - Data Files
- `.TXT` - Text Files
- `.BAS` - BASIC Programs
- `.FOR` - FORTRAN Source
- `.MAC` - MACRO Source
- `.OBJ` - Object Files
- And many more RT-11 file types

## 💻 **System Requirements**

- **Python 3.6+** (for source code)
- **macOS 10.14+** (for macOS app)
- **Windows 7+** (for Windows executable)
- **Any modern web browser** (for web interface)

## 🛠️ **Development**

All components are written in pure Python with no external dependencies beyond the standard library.

### Architecture
- **rt11extract** - Core extraction engine with RT-11 filesystem parser
- **GUI wrapper** - Tkinter-based desktop interface
- **Web wrapper** - HTTP server with HTML5 interface

## 📄 **License**

This project maintains the DEC heritage spirit - built for preservation and accessibility of historical computing systems.

## 🏛️ **About DEC**

Digital Equipment Corporation (DEC) was a major American computer company from 1957-1998, known for the PDP and VAX series of computers. RT-11 was one of their real-time operating systems.

---

*"The nice thing about standards is that you have so many to choose from."* - Andrew S. Tanenbaum

Built with ❤️ for retro computing enthusiasts and digital preservation.
