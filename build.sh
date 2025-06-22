#!/bin/bash

# RT-11 Extractor Quick Build Script
echo "🚀 RT-11 Extractor Quick Build"
echo "=============================="

# Run the master build script
python3 build_all.py

# Show what was built
echo ""
echo "📁 Build Results:"
echo "=================="
ls -la builds/

echo ""
echo "✅ Build complete! Check the builds/ directory for all executables and scripts."
