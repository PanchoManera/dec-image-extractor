
import sys
from cx_Freeze import setup, Executable

build_exe_options = {
    "packages": ["tkinter", "PIL"],
    "include_files": [("rt11extract", "rt11extract"), ("images.png", "images.png")],
    "excludes": ["unittest"]
}

setup(
    name="RT11ExtractGUI",
    version="1.0",
    description="RT-11 Disk Extractor",
    options={"build_exe": build_exe_options},
    executables=[Executable("rt11extract_gui.py", base="Win32GUI", icon="icon.ico")]
)
