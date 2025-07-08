#!/usr/bin/env python3

import tkinter as tk
from tkinter import ttk, filedialog, messagebox, scrolledtext
import subprocess
import os
import sys
import tempfile
import shutil
from pathlib import Path
import threading
import time
from datetime import datetime

# Setup backend path for imports
from pathlib import Path

def setup_backend_path():
    """Setup the backend path and return it"""
    if getattr(sys, 'frozen', False):
        # We're running in a PyInstaller bundle
        script_dir = Path(sys.executable).parent
    else:
        # We're running in a normal Python environment
        script_dir = Path(__file__).parent.parent.parent
    
    backend_path = script_dir / "backend"
    if backend_path.exists() and str(backend_path) not in sys.path:
        sys.path.insert(0, str(backend_path))
    return backend_path

def get_rt11extract_cli_path():
    """Get path to rt11extract CLI tool"""
    if getattr(sys, 'frozen', False):
        # Running from frozen/bundled mode
        exe_dir = Path(sys.executable).parent
        
        if sys.platform.startswith('win'):
            # Windows: Try all possible CLI executables
            cli_options = [
                "RT11Extract.exe",              # Main CLI name
                "rt11extract_universal.exe",     # Universal extractor
                "rt11extract_cli.exe",          # Alternative name
                "rt11extract.exe",              # Basic name with .exe
                "universal_extractor.exe"       # Another possible name
            ]
            
            for cli in cli_options:
                cli_path = exe_dir / cli
                if cli_path.exists():
                    return cli_path
                    
        elif sys.platform == 'darwin':
            # macOS: Check bundled CLI tools directory
            bundle_cli_dir = exe_dir.parent / "Frameworks" / "cli"
            if bundle_cli_dir.exists():
                cli_options = [
                    "rt11extract",           # Universal wrapper (detects ODS-1, RT-11, Unix)
                    "rt11extract_universal", # Universal extractor
                    "universal_extractor",   # Another universal option
                    "rt11extract_cli",       # RT-11 only (fallback)
                    "RT11Extract"           # Alternative name
                ]
                
                for cli in cli_options:
                    cli_path = bundle_cli_dir / cli
                    if cli_path.exists():
                        # Make it executable
                        cli_path.chmod(cli_path.stat().st_mode | 0o755)
                        return cli_path
                        
            # If not found in bundle, that's an error in frozen mode
            print(f"ERROR: CLI not found in bundle at {bundle_cli_dir}")
            return None
            
        else:
            # Linux: Check same directory as GUI executable
            cli_options = [
                "rt11extract_universal", # Universal extractor (preferred)
                "rt11extract",           # Universal wrapper 
                "universal_extractor",   # Another universal option
                "RT11Extract"           # Alternative name
            ]
            
            for cli in cli_options:
                cli_path = exe_dir / cli
                if cli_path.exists():
                    # Make it executable
                    cli_path.chmod(cli_path.stat().st_mode | 0o755)
                    return cli_path
                    
            # If not found in same directory, that's an error in frozen mode
            print(f"ERROR: CLI not found in same directory as GUI at {exe_dir}")
            return None
            
    # Default: Try relative to script location
    script_paths = [
        Path(__file__).parent.parent.parent / "backend" / "extractors" / "rt11extract",
        Path.cwd() / "backend" / "extractors" / "rt11extract"
    ]
    
    for path in script_paths:
        if path.exists():
            return path
            
    # Last resort: Try current directory
    return Path.cwd() / "rt11extract"

def get_imd2raw_path():
    """Get path to imd2raw tool"""
    if getattr(sys, 'frozen', False):
        exe_dir = Path(sys.executable).parent
        
        if sys.platform == 'win32':
            # Windows: imd2raw.exe en mismo directorio que GUI
            imd_path = exe_dir / "imd2raw.exe"
            if imd_path.exists():
                return imd_path
        elif sys.platform == 'darwin':
            # macOS: imd2raw debe estar en Contents/Frameworks/cli/
            bundle_cli_dir = exe_dir.parent / "Frameworks" / "cli"
            if bundle_cli_dir.exists():
                cli_options = [
                    "imd2raw",    # Nombre principal
                    "IMD2RAW",    # Alternativo
                    "imd2dsk"     # Alternativo
                ]
                
                for cli in cli_options:
                    cli_path = bundle_cli_dir / cli
                    if cli_path.exists():
                        # Asegurar que sea ejecutable
                        cli_path.chmod(cli_path.stat().st_mode | 0o755)
                        return cli_path
                        
            # Si no está en el bundle, es un error en macOS frozen
            print(f"ERROR: IMD2RAW not found in bundle at {bundle_cli_dir}")
            return None
        else:
            # Linux: imd2raw en mismo directorio que GUI
            cli_options = [
                "imd2raw",    # Nombre principal
                "IMD2RAW",    # Alternativo
                "imd2dsk"     # Alternativo
            ]
            
            for cli in cli_options:
                cli_path = exe_dir / cli
                if cli_path.exists():
                    # Asegurar que sea ejecutable
                    cli_path.chmod(cli_path.stat().st_mode | 0o755)
                    return cli_path
                    
            # Si no está en el mismo directorio, es un error en Linux frozen
            print(f"ERROR: IMD2RAW not found in same directory as GUI at {exe_dir}")
            return None
    else:
        # En modo desarrollo
        imd_path = Path(__file__).parent.parent.parent / "backend" / "image_converters" / "imd2raw.py"
        if imd_path.exists():
            return imd_path
    
    return None  # No encontrado

# Initialize paths
backend_path = setup_backend_path()
rt11extract_path = get_rt11extract_cli_path()
imd2raw_path = get_imd2raw_path()

# Set script directory
if getattr(sys, 'frozen', False):
    script_dir = Path(sys.executable).parent
else:
    script_dir = Path(__file__).parent.parent.parent

class RT11ExtractGUI:
    def __init__(self, root):
        self.root = root
        self.root.title("RT-11 Extract GUI")
        self.root.geometry("900x700")
        self.root.minsize(800, 600)
        
        # Variables
        self.current_file = None
        self.current_files = []
        self.temp_dir = None
        self.output_dir = None
        self.is_extracting = False
        self.fuse_mount_point = None  # FUSE mount point
        self.fuse_process = None      # FUSE process
        self.fuse_mounted = False     # Track if FUSE is successfully mounted
        self.startup_warning_shown = False  # Track if startup warning was shown
        
        # Windows-specific variables
        if sys.platform == "win32":
            self.CREATE_NO_WINDOW = 0x08000000
        else:
            self.CREATE_NO_WINDOW = 0
        
        self.setup_ui()
        
        # Show startup warning about filesystem mounting (after UI is ready)
        self.root.after(500, self.show_startup_warning)
        
        # Check rt11extract
        self.check_rt11extract()
        
        # Debug output
        self.log(f"DEBUG: Running in {'frozen' if getattr(sys, 'frozen', False) else 'script'} mode")
        self.log(f"DEBUG: Platform: {sys.platform}")
        self.log(f"DEBUG: Executable: {sys.executable}")
        self.log(f"DEBUG: RT11Extract: {rt11extract_path}")
        self.log(f"DEBUG: IMD2RAW: {imd2raw_path}")
    
    def setup_ui(self):
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # File selection
        file_frame = ttk.LabelFrame(main_frame, text="Select RT-11 Disk Image", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        self.file_var = tk.StringVar()
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))
        self.scan_btn = ttk.Button(file_frame, text="Scan Image", command=self.scan_image, state="disabled")
        self.scan_btn.grid(row=0, column=3, padx=(5, 0))
        
        # Progress
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        ttk.Label(progress_frame, textvariable=self.progress_var).grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Files list
        files_frame = ttk.LabelFrame(main_frame, text="Files", padding="10")
        files_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(1, weight=1)
        
        # Treeview for files
        columns = ('Filename', 'Size', 'Date')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings')
        self.files_tree.heading('Filename', text='Filename')
        self.files_tree.heading('Size', text='Size')
        self.files_tree.heading('Date', text='Date')
        
        self.files_tree.column('Filename', width=350)  # Aumentar ancho para rutas más largas
        self.files_tree.column('Size', width=100)
        self.files_tree.column('Date', width=150)
        
        self.files_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons
        buttons_frame = ttk.Frame(files_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.extract_all_btn = ttk.Button(buttons_frame, text="Extract All", command=self.extract_all, state="disabled")
        self.extract_all_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.extract_selected_btn = ttk.Button(buttons_frame, text="Extract Selected", command=self.extract_selected, state="disabled")
        self.extract_selected_btn.grid(row=0, column=1, padx=(0, 5))
        
        # FUSE Mount button (works on all platforms with proper drivers)
        self.mount_btn = ttk.Button(buttons_frame, text="Mount as Filesystem", 
                                   command=self.mount_fuse, state="disabled")
        self.mount_btn.grid(row=0, column=2, padx=(0, 5))

        self.open_folder_btn = ttk.Button(buttons_frame, text="Open Output Folder", 
                                         command=self.open_output_folder, state="disabled")
        self.open_folder_btn.grid(row=0, column=3, padx=(0, 5))
        
        # Log
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8)
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E))
    
    def _get_subprocess_kwargs(self):
        """Get subprocess kwargs for running commands"""
        kwargs = {
            'capture_output': True,
            'text': True,
            'cwd': str(script_dir)
        }
        
        # On Windows, hide console window
        if sys.platform == "win32":
            kwargs['creationflags'] = self.CREATE_NO_WINDOW
        
        # In compiled mode, set proper working directory
        if getattr(sys, 'frozen', False):
            if sys.platform == 'darwin':
                # For macOS bundle, CLIs are in Contents/Frameworks/cli/
                exe_path = Path(sys.executable)
                cli_dir = exe_path.parent.parent / "Frameworks" / "cli"
                if cli_dir.exists():
                    kwargs['cwd'] = str(cli_dir)
            elif sys.platform == 'win32':
                # For Windows, use executable directory
                kwargs['cwd'] = str(Path(sys.executable).parent)
            else:
                # For Linux, CLI tools are in same directory as GUI executable
                kwargs['cwd'] = str(Path(sys.executable).parent)
        
        return kwargs
    
    def check_rt11extract(self):
        """Check if rt11extract is available"""
        if not rt11extract_path or not rt11extract_path.exists():
            self.log("ERROR: rt11extract not found")
            messagebox.showerror("Error", 
                f"rt11extract not found at: {rt11extract_path}\n\n" +
                "Please ensure rt11extract is in the correct location.")
        else:
            self.log("rt11extract found and ready")
    
    def check_winfsp_availability(self):
        """Check if WinFsp is available on Windows"""
        if sys.platform != "win32":
            return True  # Not needed on non-Windows
        
        try:
            # Try to find WinFsp installation
            import winreg
            try:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\WOW6432Node\WinFsp") as key:
                    return True
            except FileNotFoundError:
                with winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE, 
                                   r"SOFTWARE\WinFsp") as key:
                    return True
        except (ImportError, FileNotFoundError, OSError):
            # Check for WinFsp files directly
            winfsp_paths = [
                "C:\\Program Files\\WinFsp\\bin\\winfsp-x64.dll",
                "C:\\Program Files (x86)\\WinFsp\\bin\\winfsp-x86.dll"
            ]
            return any(os.path.exists(path) for path in winfsp_paths)
        
        return False
    
    def log(self, message):
        """Add message to log"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
    
    def browse_file(self):
        """Browse for disk image file"""
        filename = filedialog.askopenfilename(
            title="Select RT-11 Disk Image",
            filetypes=[
                ("All Supported", "*.dsk *.img *.raw *.imd"),
                ("DSK Files", "*.dsk"),
                ("IMG Files", "*.img"),
                ("RAW Files", "*.raw"),
                ("IMD Files", "*.imd"),
                ("All Files", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            self.file_var.set(filename)
            self.scan_btn.config(state="normal")
    
    def scan_image(self):
        """Scan the disk image for files"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "Please select a valid disk image file.")
            return
            
        if not rt11extract_path.exists():
            messagebox.showerror("Error", "rt11extract not found.")
            return
        
        # Reset UI
        self.progress_var.set("Scanning...")
        self.progress_bar.config(mode='indeterminate')
        self.progress_bar.start()
        
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        
        # Start scan in background
        threading.Thread(target=self._scan_thread, daemon=True).start()
    
    def _scan_thread(self):
        """Background thread for scanning"""
        try:
            # Create temp directory
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = Path(tempfile.mkdtemp())
            
            # Get subprocess kwargs early
            kwargs = self._get_subprocess_kwargs()
            
            # Convert IMD to RAW if necessary on Linux
            if sys.platform.startswith('linux'):
                if self.current_file.lower().endswith('.imd'):
                    if not imd2raw_path or not imd2raw_path.exists():
                        raise FileNotFoundError(f"IMD2RAW tool not found at: {imd2raw_path}")
                    raw_output = self.temp_dir / (Path(self.current_file).stem + '.raw')
                    convert_cmd = [str(imd2raw_path), self.current_file, str(raw_output)]
                    convert_result = subprocess.run(convert_cmd, **kwargs)
                    if convert_result.returncode != 0:
                        raise Exception(f"Conversion failed for IMD file: {self.current_file}")
                    working_file = str(raw_output)
                else:
                    working_file = self.current_file
            else:
                working_file = self.current_file

            # Use the rt11extract_path that was already configured correctly
            if not rt11extract_path or not rt11extract_path.exists():
                raise FileNotFoundError(f"RT11 extractor not found at: {rt11extract_path}")
            extractor = rt11extract_path
                
            # Build command for executable
            cmd = [str(extractor), '-o', str(self.temp_dir), '-v', working_file]
            
            # Run command
            result = subprocess.run(cmd, **kwargs)
            
            # Log output for debugging
            if result.stdout:
                self.log("Command output:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log(f"  {line.strip()}")
            if result.stderr:
                self.log("Command error output:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.log(f"  {line.strip()}")
            
            if result.returncode == 0:
                # Buscar archivos y directorios en el output
                self._parse_extracted_files()
            else:
                error_msg = "\n".join([
                    f"Failed to scan file (exit code {result.returncode})",
                    "",
                    "Command:",
                    " ".join(cmd),
                    "",
                    "Working directory:",
                    kwargs.get('cwd', os.getcwd())
                ])
                self.root.after(0, lambda: messagebox.showerror("Error", error_msg))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            # Reset progress
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def _parse_extracted_files(self):
        """Parse the extracted files preserving directory structure"""
        if not self.temp_dir or not self.temp_dir.exists():
            return

        files = []
        # Primero procesar archivos
        for path in self.temp_dir.rglob('*'):
            if path.is_file():
                # Calcular ruta relativa desde temp_dir para preservar estructura
                rel_path = path.relative_to(self.temp_dir)
                display_name = str(rel_path)  # Mostrar ruta completa para preservar estructura
                
                size = path.stat().st_size
                date = datetime.fromtimestamp(path.stat().st_mtime)
                
                files.append({
                    'name': display_name,
                    'size': f"{size:,} bytes",
                    'date': date.strftime("%Y-%m-%d %H:%M:%S"),
                    'path': path,
                    'type': 'file'
                })
        
        # Luego procesar directorios para mantenerlos al final
        for path in self.temp_dir.rglob('*'):
            if path.is_dir():
                rel_path = path.relative_to(self.temp_dir)
                display_name = str(rel_path) + '/'  # Agregar / para indicar directorio
                
                files.append({
                    'name': display_name,
                    'size': '',  # Los directorios no tienen tamaño
                    'date': '',   # Fecha vacía para directorios
                    'path': path,
                    'type': 'directory'
                })
        
        # Update UI
        self.current_files = files
        self.root.after(0, self._update_files_ui)
    
    def _update_files_ui(self):
        """Update files list in UI"""
        for file in self.current_files:
            self.files_tree.insert('', 'end', values=(
                file['name'],
                file['size'],
                file['date']
            ))
        
        if self.current_files:
            self.extract_all_btn.config(state="normal")
            self.extract_selected_btn.config(state="normal")
    
    def extract_all(self):
        """Extract all files"""
        if not self.current_files:
            return
        
        # Get output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
        
        self.output_dir = Path(output_dir)
        threading.Thread(target=self._extract_thread, daemon=True).start()
    
    def extract_selected(self):
        """Extract selected file"""
        selection = self.files_tree.selection()
        if not selection:
            return
        
        # Get selected file info
        item = self.files_tree.item(selection[0])
        filename = item['values'][0]
        
        # Find file in current_files
        file_info = next((f for f in self.current_files if f['name'] == filename), None)
        if not file_info:
            return
        
        # Get output file
        output_file = filedialog.asksaveasfilename(
            title="Save As",
            initialfile=filename
        )
        if not output_file:
            return
        
        # Copy file
        try:
            shutil.copy2(file_info['path'], output_file)
            messagebox.showinfo("Success", f"File extracted to:\n{output_file}")
        except Exception as e:
            messagebox.showerror("Error", f"Failed to extract file:\n{e}")
    
    def _extract_thread(self):
        """Background thread for extraction"""
        try:
            self.is_extracting = True
            self.progress_var.set("Extracting...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            
            # Use the rt11extract_path that was already configured correctly
            if not rt11extract_path or not rt11extract_path.exists():
                raise FileNotFoundError(f"RT11 extractor not found at: {rt11extract_path}")
            extractor = rt11extract_path
                
            # Get subprocess kwargs early
            kwargs = self._get_subprocess_kwargs()

            # Convert IMD to RAW if necessary on Linux
            if sys.platform.startswith('linux'):
                if self.current_file.lower().endswith('.imd'):
                    if not imd2raw_path or not imd2raw_path.exists():
                        raise FileNotFoundError(f"IMD2RAW tool not found at: {imd2raw_path}")
                    raw_output = self.output_dir / (Path(self.current_file).stem + '.raw')
                    convert_cmd = [str(imd2raw_path), self.current_file, str(raw_output)]
                    convert_result = subprocess.run(convert_cmd, **kwargs)
                    if convert_result.returncode != 0:
                        raise Exception(f"Conversion failed for IMD file: {self.current_file}")
                    working_file = str(raw_output)
                else:
                    working_file = self.current_file
            else:
                working_file = self.current_file

            # Build command for executable
            cmd = [str(extractor), '-o', str(self.output_dir), '-v', working_file]
            
            result = subprocess.run(cmd, **kwargs)
            
            if result.returncode == 0:
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"Files extracted to:\n{self.output_dir}"))
            else:
                self.root.after(0, lambda: messagebox.showerror("Error",
                    f"Extraction failed (exit code {result.returncode})"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            self.is_extracting = False
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_var.set("Ready"))

    def show_startup_warning(self):
        """Show startup warning about filesystem mounting development status"""
        # Only show once per session
        if self.startup_warning_shown:
            return
            
        self.startup_warning_shown = True
        
        warning_text = """RT-11 Extract GUI - Filesystem Mounting Status

⚠️  FILESYSTEM MOUNTING IN DEVELOPMENT  ⚠️

The "Mount as Filesystem" feature is currently under active development:

• May not work reliably on all systems
• Requires additional drivers (macFUSE on macOS, WinFsp on Windows)
• Some disk images may not mount correctly
• Unmounting may occasionally require manual intervention

✅ STABLE FEATURES:
• File scanning and browsing
• Individual and batch file extraction
• IMD to DSK conversion
• All extraction functionality

These core features are fully tested and reliable for production use.

Click OK to continue..."""
        
        messagebox.showinfo("Development Notice", warning_text)

    def mount_fuse(self):
        """Mount the RT-11 image as a filesystem using FUSE"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select and scan a disk image first.")
            return
        
        # Check platform support and available drivers
        if sys.platform == "win32":
            if not self.check_winfsp_availability():
                messagebox.showerror("WinFsp Not Installed",
                    "WinFsp is not installed on this system.\n\n" +
                    "WinFsp is required for filesystem mounting on Windows.\n\n" +
                    "Please download and install WinFsp from:\n" +
                    "  https://winfsp.dev/\n\n" +
                    "After installation, restart this application.")
                return
        else:
            # macOS/Linux: Check for FUSE
            if not os.path.exists('/usr/local/lib/libfuse.dylib') and \
               not os.path.exists('/usr/local/lib/libfuse.2.dylib') and \
               not os.path.exists('/opt/homebrew/lib/libfuse.dylib'):
                if sys.platform == "darwin":
                    messagebox.showerror("macFUSE Not Installed", 
                        "macFUSE is not installed on this system.\n\n" +
                        "Please install macFUSE from:\n" +
                        "https://osxfuse.github.io/\n\n" +
                        "After installation, restart this application.")
                else:
                    messagebox.showerror("FUSE Not Installed", 
                        "FUSE is not installed on this system.\n\n" +
                        "Please install FUSE using:\n" +
                        "Ubuntu/Debian: sudo apt install fuse libfuse-dev\n" +
                        "RHEL/CentOS: sudo yum install fuse fuse-devel\n" +
                        "After installation, restart this application.")
                return

        # Create mount point
        if sys.platform == "win32":
            # Windows: Find available drive letter
            import string
            for letter in reversed(string.ascii_uppercase):
                if letter in ['A', 'B', 'C']:  # Skip system drives
                    continue
                drive = f"{letter}:"
                try:
                    if not os.path.exists(drive):
                        mount_dir = drive
                        break
                except OSError:
                    mount_dir = drive
                    break
            else:
                messagebox.showerror("Error", "No available drive letters found")
                return
        else:
            # Unix: Create directory mount point
            mount_dir = Path.home() / "rt11_mounted"
            try:
                if mount_dir.exists():
                    if sys.platform == "darwin":
                        subprocess.run(["umount", str(mount_dir)], capture_output=True)
                    elif sys.platform.startswith('linux'):
                        subprocess.run(["fusermount", "-u", str(mount_dir)], capture_output=True)
                    shutil.rmtree(mount_dir)
                mount_dir.mkdir(exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create mount directory:\n{e}")
                return

        # Start FUSE mount
        self.progress_var.set("Mounting filesystem...")
        self.mount_btn.config(state="disabled")
        threading.Thread(target=self._mount_fuse_thread, args=(mount_dir,), daemon=True).start()

    def _mount_fuse_thread(self, mount_dir):
        """Background thread for FUSE mounting"""
        try:
            self.log(f"Mounting {os.path.basename(self.current_file)} at {mount_dir}...")
            
            # Get FUSE script path
            if sys.platform == "win32":
                fuse_script = script_dir / "rt11_mount.bat"
            else:
                fuse_script = script_dir / "backend" / "filesystem_mount" / "rt11_fuse_universal.py"
            
            if not fuse_script.exists():
                raise FileNotFoundError(f"FUSE script not found: {fuse_script}")
            
            # Run mount command
            cmd = [str(fuse_script), self.current_file, str(mount_dir)]
            kwargs = self._get_subprocess_kwargs()
            kwargs.update({
                'stdout': subprocess.PIPE,
                'stderr': subprocess.PIPE,
                'text': True
            })
            
            self.fuse_process = subprocess.Popen(cmd, **kwargs)
            self.fuse_mount_point = mount_dir
            
            # Wait for mount to be ready
            time.sleep(2)
            
            try:
                # Check if mount point has files
                if isinstance(mount_dir, Path):
                    files = list(mount_dir.iterdir())
                else:  # Windows drive letter
                    files = os.listdir(mount_dir + "\\")
                
                if files:
                    self.log(f"Filesystem mounted successfully! Found {len(files)} files")
                    self.fuse_mounted = True
                    
                    # Update mount button
                    self.root.after(0, lambda: self.mount_btn.config(
                        text="Unmount Filesystem",
                        command=self.unmount_fuse,
                        state="normal"
                    ))
                    
                    # Open file manager
                    if sys.platform == "win32":
                        os.startfile(mount_dir)
                    elif sys.platform == "darwin":
                        subprocess.run(["open", str(mount_dir)])
                    else:
                        subprocess.run(["xdg-open", str(mount_dir)])
                    
                    messagebox.showinfo("Mount Success",
                        f"RT-11 filesystem mounted at:\n{mount_dir}\n\n" +
                        f"Files available: {len(files)}")
                else:
                    raise Exception("Mount point appears empty")
                    
            except Exception as e:
                self.log(f"Error checking mount: {e}")
                raise
                
        except Exception as e:
            self.log(f"Error mounting filesystem: {e}")
            messagebox.showerror("Mount Error", f"Failed to mount filesystem:\n{e}")
            # Clean up
            if hasattr(self, 'fuse_process') and self.fuse_process:
                self.fuse_process.terminate()
            if isinstance(mount_dir, Path) and mount_dir.exists():
                mount_dir.rmdir()
            self.fuse_process = None
            self.fuse_mount_point = None
        finally:
            self.progress_var.set("Ready")
            if not self.fuse_mounted:
                self.mount_btn.config(
                    text="Mount as Filesystem",
                    command=self.mount_fuse,
                    state="normal"
                )

    def unmount_fuse(self):
        """Unmount FUSE filesystem"""
        if not self.fuse_mount_point:
            return
            
        try:
            self.log(f"Unmounting filesystem from {self.fuse_mount_point}...")
            
            # Platform-specific unmounting
            if sys.platform == "win32":
                if self.fuse_process:
                    self.fuse_process.terminate()
                # Also try net use command
                subprocess.run(["net", "use", str(self.fuse_mount_point), "/delete"], 
                             capture_output=True)
            else:
                if self.fuse_process:
                    self.fuse_process.terminate()
                if sys.platform == "darwin":
                    subprocess.run(["umount", str(self.fuse_mount_point)], 
                                 capture_output=True)
                elif sys.platform.startswith('linux'):
                    subprocess.run(["fusermount", "-u", str(self.fuse_mount_point)], 
                                 capture_output=True)
                
                # Remove mount point directory
                if isinstance(self.fuse_mount_point, Path):
                    self.fuse_mount_point.rmdir()
            
            self.log("Filesystem unmounted successfully")
            
        except Exception as e:
            self.log(f"Error unmounting filesystem: {e}")
            messagebox.showerror("Unmount Error", f"Failed to unmount filesystem:\n{e}")
        finally:
            # Reset state
            self.fuse_process = None
            self.fuse_mount_point = None
            self.fuse_mounted = False
            self.mount_btn.config(
                text="Mount as Filesystem",
                command=self.mount_fuse,
                state="normal"
            )

    def open_output_folder(self):
        """Open output folder in file manager"""
        if not self.output_dir or not self.output_dir.exists():
            messagebox.showwarning("Warning", "No output folder available")
            return
        
        try:
            if sys.platform == "win32":
                os.startfile(self.output_dir)
            elif sys.platform == "darwin":
                subprocess.run(["open", str(self.output_dir)])
            else:
                subprocess.run(["xdg-open", str(self.output_dir)])
        except Exception as e:
            messagebox.showerror("Error", f"Failed to open folder:\n{e}")

def main():
    root = tk.Tk()
    app = RT11ExtractGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
