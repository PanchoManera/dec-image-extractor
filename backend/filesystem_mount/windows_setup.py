#!/usr/bin/env python3
"""
Windows Setup Script for RT-11 Extractor
========================================

This script ensures that all required files exist for Windows execution
without relying on symbolic links that don't work on Windows.
"""

import os
import sys
import shutil
from pathlib import Path

def ensure_windows_compatibility():
    """Ensure all required files exist for Windows without symbolic links"""
    script_dir = Path(__file__).parent
    extractors_dir = script_dir.parent / "extractors"
    
    # Files that need to exist in filesystem_mount directory
    required_files = [
        (extractors_dir / "universal_extractor.py", script_dir / "pdp11_smart_extractor.py"),
        (extractors_dir / "rt11extract", script_dir / "rt11extract_cli"),
    ]
    
    for source, target in required_files:
        if source.exists() and not target.exists():
            try:
                # Copy file instead of creating symlink
                shutil.copy2(source, target)
                print(f"Created {target.name} -> {source.name}")
            except Exception as e:
                print(f"Warning: Could not create {target.name}: {e}")
                # Create a Python wrapper instead
                if target.name.endswith('.py') or 'extractor' in target.name:
                    create_python_wrapper(source, target)

def create_python_wrapper(source_file: Path, target_file: Path):
    """Create a Python wrapper that imports and runs the source file"""
    try:
        wrapper_content = f'''#!/usr/bin/env python3
"""
Windows-compatible wrapper for {source_file.name}
Generated automatically to replace symbolic link functionality.
"""

import sys
import os
from pathlib import Path

# Add the source directory to Python path
source_dir = Path(__file__).parent.parent / "extractors"
sys.path.insert(0, str(source_dir))

# Import and run the source module
try:
    if "{source_file.name}" == "universal_extractor.py":
        from universal_extractor import main
        if __name__ == "__main__":
            main()
    elif "{source_file.name}" == "rt11extract":
        # For rt11extract, execute it as a script
        import subprocess
        result = subprocess.run([sys.executable, str(source_dir / "rt11extract")] + sys.argv[1:])
        sys.exit(result.returncode)
    else:
        # Generic handler
        exec(open(str(source_dir / "{source_file.name}")).read())
except ImportError as e:
    print(f"Error importing {{source_file.name}}: {{e}}")
    sys.exit(1)
except Exception as e:
    print(f"Error executing {{source_file.name}}: {{e}}")
    sys.exit(1)
'''
        
        with open(target_file, 'w', encoding='utf-8') as f:
            f.write(wrapper_content)
        
        # Make it executable on Unix systems
        if hasattr(os, 'chmod'):
            os.chmod(target_file, 0o755)
            
        print(f"Created Python wrapper: {target_file.name}")
        
    except Exception as e:
        print(f"Error creating wrapper for {target_file.name}: {e}")

if __name__ == "__main__":
    ensure_windows_compatibility()
