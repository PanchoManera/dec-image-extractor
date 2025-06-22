# 🔨 RT-11 Extractor - Build Instructions

Complete build system for creating standalone executables across all platforms.

## 🚀 Quick Build (macOS)

```bash
# Option 1: Full automated build
./build.sh

# Option 2: Python script directly  
python3 build_all.py
```

## 📦 What Gets Built

### ✅ Immediate (macOS)
- **RT11ExtractGUI-macOS** - Native macOS app bundle
- **RT11ExtractGUI-macOS-Standalone** - Single executable file

### 🛠️ Ready-to-Build Scripts
- **Windows 32-bit/64-bit/ARM64** - Complete build kits
- **Linux x64** - Build scripts and source

## 📁 Build Output Structure

```
builds/
├── macOS/
│   ├── RT11ExtractGUI-macOS/              # Native app bundle
│   └── RT11ExtractGUI-macOS-Standalone    # Single file (8MB)
├── windows/
│   ├── build_win32.bat                    # Windows 32-bit builder
│   ├── build_win64.bat                    # Windows 64-bit builder  
│   ├── build_winarm64.bat                 # Windows ARM64 builder
│   ├── build_all_windows.bat              # All Windows versions
│   ├── build.ps1                          # PowerShell version
│   └── [source files]                     # Complete source code
└── linux/
    ├── build_linux.sh                     # Linux builder
    └── [source files]                     # Complete source code
```

## 🎯 Platform-Specific Builds

### Windows
1. **Copy** `builds/windows/` to Windows machine
2. **Run** desired build script:
   - `build_win32.bat` → RT11ExtractGUI-Win32.exe
   - `build_win64.bat` → RT11ExtractGUI-Win64.exe  
   - `build_winarm64.bat` → RT11ExtractGUI-WinARM64.exe
   - `build_all_windows.bat` → All three versions

### Linux
1. **Copy** `builds/linux/` to Linux machine
2. **Run** `./build_linux.sh`
3. **Result** → `dist/RT11ExtractGUI-Linux`

## 🔧 Build Features

### All Executables Include:
- ✅ **Standalone** - No Python required
- ✅ **DEC Logo** - Vintage branding
- ✅ **Complete RT-11 engine** - Full filesystem support
- ✅ **Modern GUI** - Cross-platform interface
- ✅ **Error recovery** - Robust extraction
- ✅ **All file types** - SAV, DAT, TXT, etc.

### Build Optimizations:
- 🔥 **Small size** - 8-15MB executables
- ⚡ **Fast startup** - Optimized loading
- 🛡️ **Secure** - No external dependencies
- 📦 **Portable** - Single file distribution

## 🏗️ Architecture Support

| Platform | 32-bit | 64-bit | ARM64 | Status |
|----------|--------|--------|-------|---------|
| **Windows** | ✅ Win32 | ✅ Win64 | ✅ ARM64 | Ready to build |
| **macOS** | ❌ | ✅ Intel | ✅ Apple Silicon | Built |
| **Linux** | ❌ | ✅ x64 | ⚠️ Manual | Ready to build |

## 🚨 Requirements

### Build Machine (macOS):
- Python 3.6+
- PyInstaller (auto-installed)
- Pillow (auto-installed)

### Target Machines:
- **Nothing!** - Executables are completely standalone

## 🎮 Testing Builds

### Quick Test:
```bash
# Test macOS build
./builds/macOS/RT11ExtractGUI-macOS-Standalone

# Test with sample DSK file
./builds/macOS/RT11ExtractGUI-macOS-Standalone sample.dsk
```

### Windows Testing:
Copy to Windows and double-click any .exe - should launch immediately.

## 📋 Troubleshooting

### macOS Build Issues:
```bash
# If PyInstaller missing
pipx install pyinstaller

# If Pillow missing  
pip3 install --user pillow --break-system-packages

# Clean build
rm -rf builds/ && python3 build_all.py
```

### Windows Build Issues:
- Ensure Python in PATH
- Run as Administrator
- Windows Defender may flag (false positive)

## 🚀 Distribution Ready

All builds are **production-ready**:
- No installation required
- No Python dependency  
- No configuration needed
- Cross-platform compatible
- Vintage DEC branding included

---

**🎯 One-liner:** `./build.sh` → Complete multi-platform build system ready!
