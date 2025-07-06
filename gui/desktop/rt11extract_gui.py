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
import zipfile
import uuid
from datetime import datetime
import webbrowser
import sys
from pathlib import Path

# Import PyInstaller helper for path resolution
try:
    from pyinstaller_helper import setup_backend_path, get_rt11extract_cli_path, get_imd2raw_path, is_frozen, get_script_dir
except ImportError:
    # Fallback: create minimal helper functions if file not found
    def setup_backend_path():
        script_dir = Path(__file__).parent.parent.parent if not getattr(sys, 'frozen', False) else Path(sys.executable).parent
        backend_path = script_dir / "backend"
        if backend_path.exists() and str(backend_path) not in sys.path:
            sys.path.insert(0, str(backend_path))
        return backend_path
    
    def get_rt11extract_cli_path():
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
            if sys.platform.startswith('win'):
                return exe_dir / "RT11Extract.exe"
            elif sys.platform == 'darwin':
                return exe_dir / "rt11extract_cli"
            else:
                return exe_dir / "RT11Extract"
        else:
            return Path(__file__).parent.parent.parent / "backend" / "extractors" / "rt11extract"
    
    def get_imd2raw_path():
        if getattr(sys, 'frozen', False):
            exe_dir = Path(sys.executable).parent
            if sys.platform.startswith('win'):
                return exe_dir / "imd2raw.exe"
            else:
                return exe_dir / "imd2raw"
        else:
            return Path(__file__).parent.parent.parent / "backend" / "image_converters" / "imd2raw.py"
    
    def is_frozen():
        return getattr(sys, 'frozen', False)
    
    def get_script_dir():
        if is_frozen():
            return Path(sys.executable).parent
        else:
            return Path(__file__).parent.parent.parent

# Setup backend path for imports
backend_path = setup_backend_path()

# Windows-specific setup to ensure files exist without symlinks
if sys.platform == "win32" and backend_path:
    try:
        windows_setup_script = backend_path / "filesystem_mount" / "windows_setup.py"
        if windows_setup_script.exists():
            import subprocess
            subprocess.run([sys.executable, str(windows_setup_script)], 
                         capture_output=True, text=True, timeout=10)
    except Exception:
        pass  # Fail silently if setup can't run

# Try to import backend modules
try:
    from image_converters.imd2raw import IMDConverter, DiskImageValidator
except ImportError:
    # Fallback if direct import fails
    IMDConverter = None
    DiskImageValidator = None

# Windows-specific imports for hiding console
if sys.platform == "win32":
    # Constants for Windows subprocess creation flags
    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008
else:
    CREATE_NO_WINDOW = 0
    DETACHED_PROCESS = 0

# Global variables - use PyInstaller helper for path resolution
rt11extract_path = get_rt11extract_cli_path()
imd2raw_path = get_imd2raw_path()
script_dir = get_script_dir()

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
        self.converted_dsk_file = None  # For IMD->DSK conversion
        self.fuse_mount_point = None  # FUSE mount point
        self.fuse_process = None      # FUSE process
        self.fuse_mounted = False     # Track if FUSE is successfully mounted
        
        self.setup_ui()
        self.setup_menu()
        
        # Set custom RT-11/DEC icon (after UI setup so log function is available)
        self.set_application_icon()
        
        self.check_rt11extract()
        
        # Debug CLI path resolution
        self.log(f"DEBUG: Resolved CLI path: {rt11extract_path}")
        self.log(f"DEBUG: CLI exists: {rt11extract_path.exists() if rt11extract_path else False}")
        self.log(f"DEBUG: Running as frozen: {getattr(sys, 'frozen', False)}")
        self.log(f"DEBUG: Script directory: {script_dir}")
    
    def set_application_icon(self):
        """Set custom application icon for main window and all dialogs"""
        try:
            # Try different icon formats based on platform
            icon_paths = [
                script_dir / "icon.png",       # Original icon
                script_dir / "rt11_icon.ico",  # Windows ICO format (fallback)
                script_dir / "rt11_icon.png",  # PNG format (fallback)
                script_dir / "rt11_icon.icns"  # macOS ICNS format (fallback)
            ]
            
            icon_set = False
            self.icon_photo = None  # Store icon reference
            
            for icon_path in icon_paths:
                if icon_path.exists():
                    try:
                        # Try to set the icon
                        if sys.platform == "win32" and icon_path.suffix == '.ico':
                            self.root.iconbitmap(str(icon_path))
                            icon_set = True
                            self.log(f"Set application icon: {icon_path.name}")
                            break
                        elif icon_path.suffix in ['.png', '.ico']:
                            # For PNG/ICO, load with PIL if available
                            try:
                                try:
                                    from PIL import Image, ImageTk
                                    img = Image.open(icon_path)
                                    # Resize to appropriate icon size for better display
                                    img = img.resize((32, 32), Image.Resampling.LANCZOS)
                                    self.icon_photo = ImageTk.PhotoImage(img)
                                    # Set as default icon for all windows
                                    self.root.iconphoto(True, self.icon_photo)
                                    icon_set = True
                                    self.log(f"Set application icon: {icon_path.name}")
                                    break
                                except ImportError:
                                    # Fall back to tk.PhotoImage for PNG only
                                    if icon_path.suffix == '.png':
                                        self.icon_photo = tk.PhotoImage(file=str(icon_path))
                                        self.root.iconphoto(True, self.icon_photo)
                                        icon_set = True
                                        self.log(f"Set application icon: {icon_path.name} (fallback)")
                                        break
                            except Exception as e:
                                self.log(f"Could not load icon {icon_path.name}: {e}")
                                continue
                    except Exception as e:
                        self.log(f"Could not set icon {icon_path.name}: {e}")
                        continue
            
            if not icon_set:
                self.log("Using default application icon (custom icon not found)")
                
        except Exception as e:
            self.log(f"Error setting application icon: {e}")
        
    def setup_menu(self):
        """Setup menu bar"""
        menubar = tk.Menu(self.root)
        self.root.config(menu=menubar)
        
        # Tools menu
        tools_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Tools", menu=tools_menu)
        tools_menu.add_command(label="Convert IMD to DSK/RAW...", command=self.convert_imd_to_dsk)
        tools_menu.add_separator()
        tools_menu.add_command(label="About", command=self.show_about)
        
    def setup_ui(self):
        # Configure style
        style = ttk.Style()
        style.theme_use('clam' if 'clam' in style.theme_names() else 'default')
        
        # Main frame
        main_frame = ttk.Frame(self.root, padding="10")
        main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        main_frame.columnconfigure(1, weight=1)
        
        # Title with DEC reference
        title_frame = ttk.Frame(main_frame)
        title_frame.grid(row=0, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 20))
        title_frame.columnconfigure(1, weight=1)
        
        # DEC logo placeholder (text)
        dec_label = ttk.Label(title_frame, text="DEC", font=("Arial", 14, "bold"), 
                             foreground="navy", background="white", relief="solid", 
                             padding="5")
        dec_label.grid(row=0, column=0, padx=(0, 10))
        
        title_label = ttk.Label(title_frame, text="RT-11 Extract GUI", 
                               font=("Arial", 16, "bold"))
        title_label.grid(row=0, column=1, sticky=tk.W)
        
        # File selection section
        file_frame = ttk.LabelFrame(main_frame, text="Select RT-11 Disk Image", padding="10")
        file_frame.grid(row=1, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        
        self.file_var = tk.StringVar()
        self.file_entry = ttk.Entry(file_frame, textvariable=self.file_var, state="readonly")
        self.file_entry.grid(row=0, column=1, sticky=(tk.W, tk.E), padx=(0, 5))
        
        self.browse_btn = ttk.Button(file_frame, text="Browse...", command=self.browse_file)
        self.browse_btn.grid(row=0, column=2)
        
        self.scan_btn = ttk.Button(file_frame, text="Scan Image", command=self.scan_image, 
                                  state="disabled")
        self.scan_btn.grid(row=0, column=3, padx=(5, 0))
        
        # Progress section
        progress_frame = ttk.Frame(main_frame)
        progress_frame.grid(row=2, column=0, columnspan=3, sticky=(tk.W, tk.E), pady=(0, 10))
        progress_frame.columnconfigure(0, weight=1)
        
        self.progress_var = tk.StringVar(value="Ready")
        self.status_label = ttk.Label(progress_frame, textvariable=self.progress_var)
        self.status_label.grid(row=0, column=0, sticky=tk.W)
        
        self.progress_bar = ttk.Progressbar(progress_frame, mode='determinate')
        self.progress_bar.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(5, 0))
        
        # Files section
        files_frame = ttk.LabelFrame(main_frame, text="Files in RT-11 Image", padding="10")
        files_frame.grid(row=3, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        files_frame.columnconfigure(0, weight=1)
        files_frame.rowconfigure(1, weight=1)
        
        # Treeview for files
        columns = ('Filename', 'Size (Blocks)', 'Size (Bytes)', 'Type', 'Date')
        self.files_tree = ttk.Treeview(files_frame, columns=columns, show='headings', height=10)
        
        # Configure columns
        self.files_tree.heading('Filename', text='Filename')
        self.files_tree.heading('Size (Blocks)', text='Size (Blocks)')
        self.files_tree.heading('Size (Bytes)', text='Size (Bytes)')
        self.files_tree.heading('Type', text='Type')
        self.files_tree.heading('Date', text='Date')
        
        self.files_tree.column('Filename', width=150, minwidth=100)
        self.files_tree.column('Size (Blocks)', width=100, minwidth=80)
        self.files_tree.column('Size (Bytes)', width=100, minwidth=80)
        self.files_tree.column('Type', width=150, minwidth=100)
        self.files_tree.column('Date', width=100, minwidth=80)
        
        self.files_tree.grid(row=1, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Scrollbar for treeview
        scrollbar = ttk.Scrollbar(files_frame, orient=tk.VERTICAL, command=self.files_tree.yview)
        scrollbar.grid(row=1, column=1, sticky=(tk.N, tk.S))
        self.files_tree.configure(yscrollcommand=scrollbar.set)
        
        # Buttons frame
        buttons_frame = ttk.Frame(files_frame)
        buttons_frame.grid(row=2, column=0, columnspan=2, pady=(10, 0))
        
        self.extract_all_btn = ttk.Button(buttons_frame, text="Extract All Files", 
                                         command=self.extract_all_files, state="disabled")
        self.extract_all_btn.grid(row=0, column=0, padx=(0, 5))
        
        self.extract_selected_btn = ttk.Button(buttons_frame, text="Extract Selected", 
                                              command=self.extract_selected_file, state="disabled")
        self.extract_selected_btn.grid(row=0, column=1, padx=(0, 5))
        
        # FUSE Mount button (works on all platforms with proper drivers)
        self.mount_btn = ttk.Button(buttons_frame, text="Mount as Filesystem", 
                                   command=self.mount_fuse, state="disabled")
        self.mount_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.open_folder_btn = ttk.Button(buttons_frame, text="Open Output Folder", 
                                         command=self.open_output_folder, state="disabled")
        self.open_folder_btn.grid(row=0, column=3, padx=(0, 5))
        
        self.clear_btn = ttk.Button(buttons_frame, text="Clear", command=self.clear_all)
        self.clear_btn.grid(row=0, column=4, padx=(5, 0))
        
        # Log section
        log_frame = ttk.LabelFrame(main_frame, text="Log", padding="10")
        log_frame.grid(row=4, column=0, columnspan=3, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
        log_frame.columnconfigure(0, weight=1)
        log_frame.rowconfigure(0, weight=1)
        
        self.log_text = scrolledtext.ScrolledText(log_frame, height=8, state="disabled")
        self.log_text.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
        
        # Configure grid weights for resizing
        main_frame.rowconfigure(3, weight=2)  # Files section gets more space
        main_frame.rowconfigure(4, weight=1)  # Log section gets some space
        
        # Bind double-click on treeview
        self.files_tree.bind('<Double-1>', self.on_file_double_click)
        
    def _get_subprocess_kwargs(self):
        """Get subprocess kwargs that hide console window on Windows"""
        kwargs = {
            'capture_output': True,
            'text': True,
            'cwd': script_dir
        }
        
        # On Windows, hide the console window
        if sys.platform == "win32":
            kwargs['creationflags'] = CREATE_NO_WINDOW
        
        return kwargs
    
    def check_rt11extract(self):
        """Check if rt11extract is available"""
        if not rt11extract_path.exists():
            self.log(f"ERROR: rt11extract not found at: {rt11extract_path}")
            self.log("Please ensure rt11extract is in the same directory as this script.")
            messagebox.showerror("RT-11 Extract Not Found", 
                               f"rt11extract not found at:\n{rt11extract_path}\n\n"
                               "Please ensure rt11extract is in the same directory as this script.")
        else:
            self.log("RT-11 Extract found and ready.")
            
    def log(self, message):
        """Add message to log"""
        self.log_text.config(state="normal")
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.log_text.insert(tk.END, f"[{timestamp}] {message}\n")
        self.log_text.see(tk.END)
        self.log_text.config(state="disabled")
        self.root.update_idletasks()
        
    def browse_file(self):
        """Browse for DSK file"""
        filename = filedialog.askopenfilename(
            title="Select RT-11 Disk Image",
            filetypes=[("Disk Image Files", "*.dsk *.raw *.img *.imd"), ("DSK Files", "*.dsk"), ("RAW Files", "*.raw"), ("IMG Files", "*.img"), ("ImageDisk Files", "*.imd"), ("All Files", "*.*")]
        )
        
        if filename:
            # Validate the selected file
            format_type = DiskImageValidator.get_disk_format(filename)
            
            if format_type == "IMD":
                self.log(f"Detected ImageDisk (IMD) format: {filename}")
            elif format_type == "RT11_DSK":
                self.log(f"Detected disk image format: {filename}")
            else:
                # Only show warning, don't prevent usage
                self.log(f"Warning: Could not identify disk format, will attempt to process: {filename}")
                
            self.file_var.set(filename)
            self.current_file = filename
            self.scan_btn.config(state="normal")
            self.log(f"Selected file: {filename}")
            
    def scan_image(self):
        """Scan the disk image for files"""
        if not self.current_file or not os.path.exists(self.current_file):
            messagebox.showerror("Error", "Please select a valid disk image file.")
            return
            
        if not rt11extract_path.exists():
            messagebox.showerror("Error", "rt11extract not found.")
            return
        
        # Check if FUSE is mounted and ask user if they want to unmount
        if not self._check_and_unmount_if_needed("scan this new image"):
            return  # User cancelled
            
        # Disable buttons during scan
        self.scan_btn.config(state="disabled")
        self.extract_all_btn.config(state="disabled")
        self.extract_selected_btn.config(state="disabled")
        
        # Check if we need to convert IMD first
        format_type = DiskImageValidator.get_disk_format(self.current_file)
        
        if format_type == "IMD":
            # Start IMD conversion + scan in background thread
            threading.Thread(target=self._scan_with_imd_conversion_thread, daemon=True).start()
        else:
            # Start regular scan in background thread
            threading.Thread(target=self._scan_thread, daemon=True).start()
        
    def _scan_with_imd_conversion_thread(self):
        """Background thread for IMD conversion + scanning"""
        try:
            self.root.after(0, lambda: self.progress_var.set("Converting IMD to DSK..."))
            self.root.after(0, lambda: self.progress_bar.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress_bar.start())
            
            # Create temporary DSK file
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = Path(tempfile.mkdtemp(prefix="rt11extract_"))
            
            # Generate temporary DSK filename
            dsk_filename = self.temp_dir / (Path(self.current_file).stem + "_converted.dsk")
            self.converted_dsk_file = str(dsk_filename)
            
            self.log(f"Converting IMD to DSK: {os.path.basename(self.current_file)} -> {dsk_filename.name}")
            
            # Perform IMD conversion
            converter = IMDConverter(self.current_file, str(dsk_filename), verbose=False)
            success = converter.convert()
            
            if not success:
                self.log("IMD conversion failed")
                self.root.after(0, lambda: self._scan_error("Failed to convert IMD file to DSK format"))
                return
                
            self.log("IMD conversion completed, starting scan...")
            
            # Now scan the converted DSK file
            self.root.after(0, lambda: self.progress_var.set("Scanning converted disk image..."))
            
            # Continue with regular scan using converted file
            self._perform_scan(str(dsk_filename))
            
        except Exception as e:
            self.log(f"Exception during IMD conversion + scan: {str(e)}")
            self.root.after(0, lambda: self._scan_error(str(e)))
        finally:
            # Re-enable UI
            self.root.after(0, self._scan_finished)
        
    def _scan_thread(self):
        """Background thread for scanning"""
        try:
            self.progress_var.set("Scanning disk image...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            
            # Create temporary directory
            if self.temp_dir:
                shutil.rmtree(self.temp_dir, ignore_errors=True)
            self.temp_dir = Path(tempfile.mkdtemp(prefix="rt11extract_"))
            
            self.log("Starting scan...")
            
            # Perform scan
            self._perform_scan(self.current_file)
            
        except Exception as e:
            self.log(f"Exception during scan: {str(e)}")
            self.root.after(0, self._scan_error, str(e))
        finally:
            # Re-enable UI
            self.root.after(0, self._scan_finished)
            
    def _perform_scan(self, disk_file: str):
        """Perform the actual scan operation using backend directly"""
        # Create a temporary directory for scan operation
        scan_dir = self.temp_dir / 'scan_output'
        scan_dir.mkdir(exist_ok=True)
        
        try:
            # Use backend directly instead of calling external CLI
            self.log(f"Scanning disk image: {disk_file}")
            
            # Import backend modules directly
            sys.path.insert(0, str(backend_path)) if backend_path else None
            
            # Try to import and use the universal extractor directly
            try:
                from extractors.universal_extractor import UniversalExtractor
                extractor = UniversalExtractor(disk_file, str(scan_dir), verbose=True)
                
                # First get file list
                files_info = extractor.list_files()
                if files_info:
                    self.log(f"Found {len(files_info)} files in image")
                    
                    # Convert to our format
                    files = []
                    for file_info in files_info:
                        files.append({
                            'filename': file_info.get('name', 'Unknown'),
                            'size_blocks': file_info.get('blocks', 0),
                            'size_bytes': file_info.get('size', 0),
                            'file_type': file_info.get('type', 'Unknown'),
                            'creation_date': file_info.get('date', 'Unknown'),
                            'path': file_info.get('path', '')
                        })
                    
                    self.current_files = files
                    self.root.after(0, self._update_files_ui, files)
                    self.log(f"Scan completed successfully! Found {len(files)} files.")
                    return
                    
            except ImportError as e:
                self.log(f"Could not import smart extractor: {e}, trying RT-11 extractor")
            
            # Fallback: try RT-11 extractor directly
            try:
                from extractors.rt11extract_smart import RT11Extractor
                extractor = RT11Extractor()
                
                # Extract to temp directory to get file list
                result = extractor.extract_disk(disk_file, str(scan_dir), list_only=True)
                
                if result and 'files' in result:
                    files = []
                    for file_info in result['files']:
                        files.append({
                            'filename': file_info.get('name', 'Unknown'),
                            'size_blocks': file_info.get('blocks', 0),
                            'size_bytes': file_info.get('size', 0),
                            'file_type': file_info.get('type', 'File'),
                            'creation_date': file_info.get('date', 'Unknown'),
                            'path': file_info.get('path', '')
                        })
                    
                    self.current_files = files
                    self.root.after(0, self._update_files_ui, files)
                    self.log(f"Scan completed successfully! Found {len(files)} files.")
                    return
                    
            except ImportError as e:
                self.log(f"Could not import RT-11 extractor: {e}, falling back to CLI")
            
            # Last resort: use CLI but redirect output properly
            self._perform_scan_via_cli(disk_file, scan_dir)
            
        except Exception as e:
            self.log(f"Exception during backend scan: {str(e)}")
            # Fallback to CLI method
            self._perform_scan_via_cli(disk_file, scan_dir)
    
    def _perform_scan_via_cli(self, disk_file: str, scan_dir: Path):
        """Fallback method using CLI when backend import fails"""
        self.log("Using CLI fallback method")
        
        # DEBUG: Log detailed execution context
        self.log(f"DEBUG SCAN CLI: sys.frozen = {getattr(sys, 'frozen', False)}")
        self.log(f"DEBUG SCAN CLI: sys.executable = {sys.executable}")
        self.log(f"DEBUG SCAN CLI: backend_path = {backend_path}")
        self.log(f"DEBUG SCAN CLI: script_dir = {script_dir}")
        
        # Build command - but ensure we don't open GUI
        # When frozen, NEVER use external CLI as it might open another GUI
        # Always use the backend script directly
        backend_script = backend_path / 'extractors' / 'rt11extract' if backend_path else None
        self.log(f"DEBUG SCAN CLI: backend_script path = {backend_script}")
        self.log(f"DEBUG SCAN CLI: backend_script exists = {backend_script.exists() if backend_script else False}")
        
        if backend_script and backend_script.exists():
            # CRITICAL FIX: When frozen, sys.executable points to GUI executable, not Python!
            # We need to use python3 directly to avoid opening another GUI
            if getattr(sys, 'frozen', False):
                # When packaged, use system python instead of GUI executable
                python_cmd = 'python3'
                # Verify python3 is available
                import shutil
                if not shutil.which('python3'):
                    # Fallback to 'python'
                    python_cmd = 'python' if shutil.which('python') else sys.executable
                    self.log(f"DEBUG SCAN CLI: python3 not found, using fallback: {python_cmd}")
                else:
                    self.log(f"DEBUG SCAN CLI: Using system python3")
                cmd = [python_cmd, str(backend_script), disk_file, '-o', str(scan_dir), '-v']
            else:
                # When running as script, sys.executable is correct
                cmd = [sys.executable, str(backend_script), disk_file, '-o', str(scan_dir), '-v']
            self.log(f"DEBUG SCAN CLI: Using backend_script command")
        else:
            # Last resort: try to find universal extractor
            universal_script = backend_path / 'extractors' / 'universal_extractor.py' if backend_path else None
            self.log(f"DEBUG SCAN CLI: universal_script path = {universal_script}")
            self.log(f"DEBUG SCAN CLI: universal_script exists = {universal_script.exists() if universal_script else False}")
            if universal_script and universal_script.exists():
                # Same fix for universal extractor
                if getattr(sys, 'frozen', False):
                    python_cmd = 'python3'
                    import shutil
                    if not shutil.which('python3'):
                        python_cmd = 'python' if shutil.which('python') else sys.executable
                    cmd = [python_cmd, str(universal_script), disk_file, '-o', str(scan_dir), '-v']
                else:
                    cmd = [sys.executable, str(universal_script), disk_file, '-o', str(scan_dir), '-v']
                self.log(f"DEBUG SCAN CLI: Using universal_script command")
            else:
                self.log(f"DEBUG SCAN CLI: No extractor found!")
                raise FileNotFoundError("No extractor available")
        
        self.log(f"DEBUG SCAN CLI: Final command = {cmd}")
        self.log(f"DEBUG SCAN CLI: Command length = {len(cmd)}")
        for i, part in enumerate(cmd):
            self.log(f"DEBUG SCAN CLI: cmd[{i}] = '{part}'")
        
        subprocess_kwargs = self._get_subprocess_kwargs()
        self.log(f"DEBUG SCAN CLI: subprocess kwargs = {subprocess_kwargs}")
        
        self.log(f"Running CLI: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, **subprocess_kwargs)
        
        if result.stdout:
            self.log("CLI STDOUT:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    self.log(f"  {line}")
        
        if result.stderr:
            self.log("CLI STDERR:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    self.log(f"  {line}")
        
        if result.returncode == 0:
            # Parse extracted files
            files = self._parse_extracted_files(scan_dir, result.stdout, None)
            self.current_files = files
            
            # Update UI in main thread
            self.root.after(0, self._update_files_ui, files)
            self.log(f"CLI scan completed successfully! Found {len(files)} files.")
        else:
            self.log(f"Error: CLI failed with return code {result.returncode}")
            self.root.after(0, self._scan_error, f"Extractor failed with return code {result.returncode}")
            
    def _scan_finished(self):
        """Re-enable UI after scan"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set("Ready")
        self.scan_btn.config(state="normal")
        
    def _scan_error(self, error_msg):
        """Handle scan error"""
        messagebox.showerror("Scan Error", f"Failed to scan disk image:\n{error_msg}")
        
    def _update_files_ui(self, files):
        """Update files treeview"""
        # Clear existing items
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
            
        # Add files
        for file_info in files:
            self.files_tree.insert('', 'end', values=(
                file_info['filename'],
                file_info['size_blocks'],
                f"{file_info['size_bytes']:,}",
                file_info['file_type'],
                file_info['creation_date']
            ))
            
        # Enable buttons
        self.extract_all_btn.config(state="normal")
        
        # Enable mount button if we have files (works on all platforms with proper drivers)
        if files and hasattr(self, 'mount_btn') and self.mount_btn is not None:
            self.mount_btn.config(state="normal")
        
        # Enable extract selected button if there are files
        if files:
            # Bind selection change event to enable/disable extract selected button
            self.files_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
    def _parse_extracted_files(self, scan_dir, output, list_result=None):
        """Parse extracted files to get file information"""
        files = []
        
        # Parse the extraction output to get dates (RT-11 style)
        date_map = {}
        # Parse FILE_INFO lines for ODS-1 format
        ods1_info_map = {}
        
        if output:
            lines = output.split('\n')
            for line in lines:
                line = line.strip()
                
                # Debug: Log all lines for troubleshooting
                if "FILE_INFO:" in line or "Extracted:" in line:
                    self.log(f"DEBUG: Processing line: '{line}'")
                
                # Parse ODS-1 FILE_INFO lines: "FILE_INFO: filename|size_blocks|size_bytes|file_type|creation_date"
                if "FILE_INFO:" in line:
                    try:
                        # Extract info from "FILE_INFO: RSX11.SYS;1|50|25600|System File|1985-12-20"
                        parts = line.split("FILE_INFO:", 1)
                        if len(parts) == 2:
                            info_str = parts[1].strip()
                            self.log(f"DEBUG: Info string: '{info_str}'")
                            info_parts = info_str.split('|')
                            self.log(f"DEBUG: Info parts: {info_parts}")
                            
                            if len(info_parts) >= 5:
                                filename = info_parts[0]
                                size_blocks = int(info_parts[1]) if info_parts[1].isdigit() else 0
                                size_bytes = int(info_parts[2]) if info_parts[2].isdigit() else 0
                                file_type = info_parts[3]
                                creation_date = info_parts[4]
                                
                                ods1_info_map[filename] = {
                                    'size_blocks': size_blocks,
                                    'size_bytes': size_bytes,
                                    'file_type': file_type,
                                    'creation_date': creation_date,
                                    'display_path': info_parts[5] if len(info_parts) > 5 else filename
                                }
                                
                                self.log(f"DEBUG: Successfully parsed ODS-1 info for {filename}: {file_type}, {creation_date}")
                            else:
                                self.log(f"DEBUG: Not enough parts in FILE_INFO: got {len(info_parts)}, need 5")
                    except (ValueError, IndexError) as e:
                        self.log(f"Could not parse FILE_INFO line: '{line}' - {e}")
                        continue
                
                # Look for lines that show "Applied date YYYY-MM-DD to FILENAME" (RT-11 style)
                elif "Applied date" in line and " to " in line:
                    try:
                        # Extract date and filename from "Applied date 1985-12-20 to SWAP.SYS"
                        parts = line.split()
                        if len(parts) >= 5 and parts[0] == "Applied" and parts[1] == "date":
                            date_str = parts[2]  # Should be YYYY-MM-DD format
                            filename = parts[4]  # Should be the filename
                            
                            # Validate date format
                            if '-' in date_str and len(date_str.split('-')) == 3:
                                year, month, day = date_str.split('-')
                                if (len(year) == 4 and len(month) == 2 and len(day) == 2 and
                                    year.isdigit() and month.isdigit() and day.isdigit()):
                                    date_map[filename] = date_str
                    except (ValueError, IndexError):
                        continue
        
        # Parse Unix detailed listing if available
        unix_info_map = {}
        if list_result and list_result.stdout:
            self.log("Parsing Unix detailed listing...")
            lines = list_result.stdout.split('\n')
            parsing_directory_data = False
            
            for line in lines:
                line = line.strip()
                
                # Skip header and separator lines
                if ('Directory Listing:' in line or 
                    '================' in line or 
                    '----------------' in line or
                    'Permissions  Links' in line or
                    'Summary:' in line or
                    'Total size:' in line or
                    'Superblock info:' in line or
                    not line):
                    if 'Permissions  Links' in line:
                        parsing_directory_data = True
                    continue
                
                # Look for actual file/directory entries in Unix format
                # Skip header lines and look for actual data
                if not parsing_directory_data:
                    if 'Full Path' in line and 'Type' in line and 'Size' in line and 'ModTime' in line:
                        parsing_directory_data = True
                    continue
                
                if parsing_directory_data and line and not line.startswith('-'):
                    try:
                        # New recursive format: "/bin/cat                                 File       152       1988-11-28 05:07:21 aF...rwxr-xr-x"
                        # The format is fixed-width, so we need to be careful with spacing
                        
                        # Check if this is a valid data line (starts with /)
                        if not line.startswith('/'):
                            continue
                            
                        # Use regex-like parsing for the fixed-width format
                        # Format: path (40 chars) + type (10 chars) + size (9 chars) + date (19 chars) + permissions (rest)
                        if len(line) >= 79:  # Minimum length for all fields
                            full_path = line[:40].strip()      # e.g., "/bin/cat"
                            file_type_raw = line[40:50].strip() # e.g., "File" or "Directory"
                            size_str = line[50:59].strip()     # e.g., "152"
                            modtime_str = line[59:78].strip()  # e.g., "1988-11-28 05:07:21"
                            permissions = line[78:].strip()    # e.g., "aF...rwxr-xr-x"
                            
                            # Extract date and time from modtime_str
                            if ' ' in modtime_str:
                                date_part, time_part = modtime_str.split(' ', 1)
                            else:
                                date_part = modtime_str
                                time_part = '00:00:00'
                            
                            # Extract just the filename from full path
                            filename = full_path.split('/')[-1]
                            
                            # Parse size
                            try:
                                unix_size = int(size_str.replace(',', ''))
                            except ValueError:
                                unix_size = 0
                            
                            # Map file type
                            if file_type_raw == 'Directory':
                                file_type = 'Directory'
                            elif file_type_raw == 'File':
                                if 'x' in permissions:
                                    file_type = 'Executable'
                                else:
                                    file_type = 'Regular File'
                            else:
                                file_type = file_type_raw
                            
                            # Parse date - already in good format (YYYY-MM-DD)
                            date_str = date_part if date_part else 'N/A'
                            
                            # Store both simple filename and full path
                            unix_info_map[filename] = {
                                'type': file_type,
                                'date': date_str,
                                'size': unix_size,
                                'permissions': permissions,
                                'time': time_part,
                                'full_path': full_path
                            }
                            
                            # Also store by full path for better matching
                            unix_info_map[full_path] = unix_info_map[filename]
                            
                            self.log(f"Parsed Unix file: {full_path} ({file_type}, {date_str}, {unix_size} bytes)")
                            
                    except Exception as e:
                        self.log(f"Could not parse Unix listing line: '{line}' - {e}")
                        continue
        
        # Get files AND directories from directory - preserve directory structure for Unix filesystems
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.endswith('.rt11info'):
                size_bytes = file_path.stat().st_size
                size_blocks = (size_bytes + 511) // 512
                
                # Calculate relative path from scan_dir to preserve directory structure
                rel_path = file_path.relative_to(scan_dir)
                display_name = str(rel_path)  # Show full path for Unix files
                simple_name = file_path.name
                
                # Check if we have ODS-1 info first (highest priority)
                file_type = 'Unknown Type'
                creation_date = 'N/A'
                ods1_info = None
                
                # Try multiple matching strategies for ODS-1
                if simple_name in ods1_info_map:
                    ods1_info = ods1_info_map[simple_name]
                elif display_name in ods1_info_map:
                    ods1_info = ods1_info_map[display_name]
                else:
                    # Try matching without version (ODS-1 files have versions like FILENAME.EXT;1)
                    for ods1_filename in ods1_info_map.keys():
                        # Remove version from ODS-1 filename (everything after ';')
                        ods1_name_no_version = ods1_filename.split(';')[0]
                        if simple_name == ods1_name_no_version or display_name == ods1_name_no_version:
                            ods1_info = ods1_info_map[ods1_filename]
                            self.log(f"Matched {simple_name} to ODS-1 file {ods1_filename} (version removed)")
                            break
                
                if ods1_info:
                    # Use ODS-1 detailed information
                    file_type = ods1_info['file_type']
                    creation_date = ods1_info['creation_date']
                    size_blocks = ods1_info['size_blocks']  # Use ODS-1 reported size
                    size_bytes = ods1_info['size_bytes']
                    self.log(f"Using ODS-1 info for {display_name}: {file_type}, {creation_date}")
                    
                else:
                    # Check if we have Unix detailed info by trying multiple matches
                    parent_dir = rel_path.parent.name if rel_path.parent != Path('.') else ''
                    
                    unix_info = None
                    # Try different matching strategies
                    # First try exact filename match
                    if simple_name in unix_info_map:
                        unix_info = unix_info_map[simple_name]
                    # Then try parent directory name (for files inside directories)
                    elif parent_dir and parent_dir in unix_info_map:
                        # Use parent directory info but mark as file in directory
                        parent_info = unix_info_map[parent_dir]
                        if parent_info['type'] == 'Directory':
                            # Create appropriate file type for files inside Unix directories
                            unix_info = {
                                'type': self._get_file_description_with_path(simple_name, str(rel_path)),
                                'date': parent_info['date'],  # Use parent directory date as fallback
                                'size': size_bytes,
                                'permissions': 'inherited'
                            }
                    # Finally try full path
                    elif display_name in unix_info_map:
                        unix_info = unix_info_map[display_name]
                    
                    if unix_info:
                        file_type = unix_info['type']
                        creation_date = unix_info['date']
                        self.log(f"Using Unix info for {display_name}: {file_type}, {creation_date}")
                    else:
                        # Fallback to path-based detection and RT-11 date map
                        file_type = self._get_file_description_with_path(file_path.name, str(rel_path))
                        creation_date = date_map.get(file_path.name, 'N/A')
                        self.log(f"Using fallback info for {display_name}: {file_type}, {creation_date}")
                
                files.append({
                    'filename': display_name,  # Use full relative path
                    'size_blocks': size_blocks,
                    'size_bytes': size_bytes,
                    'file_type': file_type,
                    'creation_date': creation_date,
                    'full_path': file_path  # Store full path for extraction
                })
            
        
        # After processing files, also process directories for ODS-1
        for dir_path in scan_dir.rglob('*'):
            if dir_path.is_dir():
                # Handle directories (especially ODS-1 user directories)
                rel_path = dir_path.relative_to(scan_dir)
                display_name = str(rel_path)  # Show full path for directories
                simple_name = dir_path.name
                
                # Check if we have ODS-1 directory info
                dir_type = 'Directory'
                creation_date = 'N/A'
                ods1_info = None
                
                # Try multiple matching strategies for ODS-1 directories
                if simple_name in ods1_info_map:
                    ods1_info = ods1_info_map[simple_name]
                elif display_name in ods1_info_map:
                    ods1_info = ods1_info_map[display_name]
                else:
                    # Check for directory entries with DIR extension or ;1 version
                    for ods1_filename in ods1_info_map.keys():
                        # Remove version from ODS-1 filename and check for .DIR extension
                        ods1_name_no_version = ods1_filename.split(';')[0]
                        ods1_base_name = ods1_name_no_version.replace('.DIR', '')
                        
                        if (simple_name == ods1_name_no_version or 
                            simple_name == ods1_base_name or
                            display_name == ods1_name_no_version or 
                            display_name == ods1_base_name):
                            ods1_info = ods1_info_map[ods1_filename]
                            self.log(f"Matched directory {simple_name} to ODS-1 directory {ods1_filename}")
                            break
                
                if ods1_info:
                    # Use ODS-1 detailed information for directories
                    dir_type = ods1_info['file_type']
                    creation_date = ods1_info['creation_date']
                    self.log(f"Using ODS-1 info for directory {display_name}: {dir_type}, {creation_date}")
                
                # For ODS-1, numeric directory names are UIC (User Identification Code) directories
                if simple_name.isdigit() and len(simple_name) == 6:
                    # Format like 001054 is UIC group 1, user 54 in octal
                    group = int(simple_name[:3], 8)  # First 3 digits are group (octal)
                    user = int(simple_name[3:], 8)   # Last 3 digits are user (octal)
                    dir_type = f'User Directory [UIC {group},{user}]'
                elif simple_name == '000000':
                    dir_type = 'Root Directory [UIC 0,0]'
                
                files.append({
                    'filename': display_name + '/',  # Add slash to indicate directory
                    'size_blocks': 0,  # Directories don't have size
                    'size_bytes': 0,
                    'file_type': dir_type,
                    'creation_date': creation_date,
                    'full_path': dir_path  # Store full path for browsing
                })
        
        self.log(f"Final files count: {len(files)}")
        self.log(f"Unix info map keys: {list(unix_info_map.keys())}")
        return files
        
    def _get_file_description(self, filename):
        """Get file type description based on extension"""
        ext = filename.split('.')[-1].upper() if '.' in filename else ''
        descriptions = {
            'SAV': 'Executable Program',
            'DAT': 'Data File',
            'TXT': 'Text File',
            'BAS': 'BASIC Program',
            'FOR': 'FORTRAN Source',
            'OUX': 'Unknown Type',
            'FIL': 'Unknown Type'
        }
        return descriptions.get(ext, 'Unknown Type')
        
    def _get_file_description_with_path(self, filename, rel_path):
        """Get file type description based on extension and path (for Unix files)"""
        # Check if it's in a Unix system directory
        path_lower = rel_path.lower()
        
        # Unix system directories
        if path_lower.startswith('bin/'):
            return 'Executable (bin)'
        elif path_lower.startswith('etc/'):
            return 'Configuration File'
        elif path_lower.startswith('usr/bin/'):
            return 'User Executable'
        elif path_lower.startswith('usr/lib/'):
            return 'Library File'
        elif path_lower.startswith('dev/'):
            return 'Device File'
        elif path_lower.startswith('tmp/'):
            return 'Temporary File'
        elif path_lower.startswith('lib/'):
            return 'Library File'
        
        # Check for known Unix file patterns
        if filename.lower() in ['makefile', 'readme', 'changelog', 'license']:
            return 'Unix System File'
        
        # Fall back to extension-based detection
        return self._get_file_description(filename)
        
    def extract_all_files(self):
        """Extract all files"""
        if not self.current_files:
            messagebox.showwarning("Warning", "No files to extract.")
            return
            
        # Ask for output directory
        output_dir = filedialog.askdirectory(title="Select Output Directory")
        if not output_dir:
            return
            
        self.output_dir = Path(output_dir)
        
        # Start extraction in background thread
        threading.Thread(target=self._extract_all_thread, daemon=True).start()
        
    def _extract_all_thread(self):
        """Background thread for extraction"""
        try:
            self.is_extracting = True
            self.root.after(0, self._disable_extract_buttons)
            
            self.progress_var.set("Extracting files...")
            self.progress_bar.config(mode='indeterminate')
            self.progress_bar.start()
            
            self.log("Starting extraction...")
            
            # Run rt11extract for extraction
            if getattr(sys, 'frozen', False):
                # Running as bundled executable - run rt11extract directly (it's included in bundle)
                cmd = [str(rt11extract_path), self.current_file, '-o', str(self.output_dir), '-v']
            else:
                # Running as script - run rt11extract with python (it's a python script)
                cmd = [sys.executable, str(rt11extract_path), self.current_file, '-o', str(self.output_dir), '-v']
            self.log(f"Running: {' '.join(cmd)}")
            
            result = subprocess.run(cmd, **self._get_subprocess_kwargs())
            
            if result.stdout:
                self.log("STDOUT:")
                for line in result.stdout.split('\n'):
                    if line.strip():
                        self.log(f"  {line}")
            
            if result.stderr:
                self.log("STDERR:")
                for line in result.stderr.split('\n'):
                    if line.strip():
                        self.log(f"  {line}")
            
            if result.returncode == 0:
                self.log("Extraction completed successfully!")
                self.root.after(0, self._extraction_success)
            else:
                self.log(f"Error: rt11extract failed with return code {result.returncode}")
                self.root.after(0, self._extraction_error, f"rt11extract failed with return code {result.returncode}")
                
        except Exception as e:
            self.log(f"Exception during extraction: {str(e)}")
            self.root.after(0, self._extraction_error, str(e))
        finally:
            self.is_extracting = False
            self.root.after(0, self._enable_extract_buttons)
            self.root.after(0, self._extraction_finished)
            
    def _disable_extract_buttons(self):
        """Disable extract buttons"""
        self.extract_all_btn.config(state="disabled")
        self.extract_selected_btn.config(state="disabled")
        
    def _enable_extract_buttons(self):
        """Enable extract buttons"""
        self.extract_all_btn.config(state="normal")
        if self.files_tree.selection():
            self.extract_selected_btn.config(state="normal")
            
    def _extraction_finished(self):
        """Clean up after extraction"""
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        self.progress_var.set("Ready")
        
    def _extraction_success(self):
        """Handle successful extraction"""
        self.open_folder_btn.config(state="normal")
        messagebox.showinfo("Success", f"Files extracted successfully to:\n{self.output_dir}")
        
    def _extraction_error(self, error_msg):
        """Handle extraction error"""
        messagebox.showerror("Extraction Error", f"Failed to extract files:\n{error_msg}")
        
    def extract_selected_file(self):
        """Extract selected file"""
        selection = self.files_tree.selection()
        if not selection:
            messagebox.showwarning("Warning", "Please select a file to extract.")
            return
            
        # Get selected filename
        item = self.files_tree.item(selection[0])
        filename = item['values'][0]  # This includes the full path for Unix files
        
        # For Unix files, suggest just the base filename for saving
        suggested_name = Path(filename).name
        
        # Ask for output file location
        output_file = filedialog.asksaveasfilename(
            title="Save extracted file as...",
            initialfile=suggested_name,
            defaultextension="",
            filetypes=[("All Files", "*.*")]
        )
        
        if not output_file:
            return
            
        # Extract single file (we'll copy from temp scan directory if available)
        if self.temp_dir:
            scan_dir = self.temp_dir / 'scan_output'
            source_file = scan_dir / filename  # filename includes full path for Unix
            
            if source_file.exists():
                try:
                    # Create parent directories if needed
                    output_path = Path(output_file)
                    output_path.parent.mkdir(parents=True, exist_ok=True)
                    
                    shutil.copy2(source_file, output_file)
                    self.log(f"File '{filename}' extracted to: {output_file}")
                    messagebox.showinfo("Success", f"File extracted successfully:\n{output_file}")
                except Exception as e:
                    self.log(f"Error copying file: {str(e)}")
                    messagebox.showerror("Error", f"Failed to extract file:\n{str(e)}")
            else:
                messagebox.showerror("Error", "Source file not found. Please scan the image again.")
        else:
            messagebox.showerror("Error", "No files available. Please scan the image first.")
            
    def on_file_double_click(self, event):
        """Handle double-click on file"""
        self.extract_selected_file()
        
    def on_file_select(self, event):
        """Handle file selection"""
        selection = self.files_tree.selection()
        if selection:
            self.extract_selected_btn.config(state="normal")
            selected_item = self.files_tree.item(selection[0])
            filename = selected_item['values'][0]
            self.log(f"Selected file: {filename}")
        else:
            self.extract_selected_btn.config(state="disabled")
            
    def open_output_folder(self):
        """Open output folder in file manager"""
        if self.output_dir and self.output_dir.exists():
            try:
                if sys.platform == "win32":
                    os.startfile(self.output_dir)
                elif sys.platform == "darwin":  # macOS
                    subprocess.run(["open", str(self.output_dir)], **self._get_subprocess_kwargs())
                else:  # Linux and others
                    subprocess.run(["xdg-open", str(self.output_dir)], **self._get_subprocess_kwargs())
            except Exception as e:
                self.log(f"Error opening folder: {str(e)}")
                messagebox.showerror("Error", f"Failed to open folder:\n{str(e)}")
        else:
            messagebox.showwarning("Warning", "No output folder available.")
            
    def clear_all(self):
        """Clear all data"""
        # Check if FUSE is mounted and ask user if they want to unmount
        if not self._check_and_unmount_if_needed("clear all data"):
            return  # User cancelled
        
        # Clear file selection
        self.file_var.set("")
        self.current_file = None
        
        # Clear files list
        for item in self.files_tree.get_children():
            self.files_tree.delete(item)
        self.current_files = []
        
        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        self.temp_dir = None
        self.output_dir = None
        self.converted_dsk_file = None
        
        # Reset UI
        self.scan_btn.config(state="disabled")
        self.extract_all_btn.config(state="disabled")
        self.extract_selected_btn.config(state="disabled")
        self.open_folder_btn.config(state="disabled")
        
        self.progress_var.set("Ready")
        self.progress_bar.stop()
        self.progress_bar.config(mode='determinate')
        
        # Clear log
        self.log_text.config(state="normal")
        self.log_text.delete(1.0, tk.END)
        self.log_text.config(state="disabled")
        
        self.log("Cleared all data.")
        
    def convert_imd_to_dsk(self):
        """Convert IMD file to DSK/RAW format"""
        # Select input IMD file
        input_file = filedialog.askopenfilename(
            title="Select IMD Image File",
            filetypes=[("ImageDisk Files", "*.imd"), ("All Files", "*.*")]
        )
        
        if not input_file:
            return
            
        # Select output DSK file
        output_file = filedialog.asksaveasfilename(
            title="Save DSK/RAW File As...",
            initialfile=os.path.splitext(os.path.basename(input_file))[0] + ".dsk",
            defaultextension=".dsk",
            filetypes=[("DSK Files", "*.dsk"), ("RAW Files", "*.raw"), ("All Files", "*.*")]
        )
        
        if not output_file:
            return
            
        # Start conversion in background thread
        threading.Thread(target=self._convert_imd_thread, args=(input_file, output_file), daemon=True).start()
        
    def _convert_imd_thread(self, input_file, output_file):
        """Background thread for IMD conversion"""
        try:
            self.root.after(0, lambda: self.progress_var.set("Converting IMD to DSK..."))
            self.root.after(0, lambda: self.progress_bar.config(mode='indeterminate'))
            self.root.after(0, lambda: self.progress_bar.start())
            
            self.log(f"Starting IMD conversion: {os.path.basename(input_file)} -> {os.path.basename(output_file)}")
            
            # Create converter instance
            converter = IMDConverter(input_file, output_file, verbose=False)
            
            # Perform conversion
            success = converter.convert()
            
            if success:
                self.log("IMD conversion completed successfully!")
                self.root.after(0, lambda: messagebox.showinfo("Success", 
                    f"IMD file converted successfully!\n\nInput: {os.path.basename(input_file)}\nOutput: {os.path.basename(output_file)}"))
            else:
                self.log("IMD conversion failed.")
                self.root.after(0, lambda: messagebox.showerror("Error", "IMD conversion failed. Check the log for details."))
                
        except Exception as e:
            self.log(f"Exception during IMD conversion: {str(e)}")
            self.root.after(0, lambda: messagebox.showerror("Error", f"IMD conversion failed:\n{str(e)}"))
        finally:
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_bar.config(mode='determinate'))
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            
    def show_about(self):
        """Show about dialog"""
        about_text = """RT-11 Extract GUI
        
A graphical interface for extracting files from RT-11 disk images.

Features:
• Extract files from RT-11 disk images (.dsk, .raw, .img)
• Convert ImageDisk (.imd) files to DSK/RAW format
• Browse and preview file contents
• Batch extraction capabilities

Based on the RT-11 file system used by
Digital Equipment Corporation (DEC) computers."""
        
        messagebox.showinfo("About RT-11 Extract GUI", about_text)
        
    def check_fuse_availability(self):
        """Check if FUSE is available on this system"""
        # Check if FUSE system is available
        if sys.platform == 'darwin':  # macOS
            # Check for macFUSE (more lenient check)
            return os.path.exists('/usr/local/lib/libfuse.dylib') or \
                   os.path.exists('/usr/local/lib/libfuse.2.dylib') or \
                   os.path.exists('/opt/homebrew/lib/libfuse.dylib')
        elif sys.platform.startswith('linux'):  # Linux
            # Check for FUSE utilities
            try:
                subprocess.run(['fusermount', '--version'], 
                             capture_output=True, check=True)
                return True
            except (subprocess.CalledProcessError, FileNotFoundError):
                return False
        else:
            return False
    
    def check_winfsp_availability(self):
        """Check if WinFsp is available on Windows"""
        if sys.platform != "win32":
            return False
        
        # Check if WinFsp is installed
        winfsp_paths = [
            "C:\\Program Files (x86)\\WinFsp\\bin\\winfsp-x64.dll",
            "C:\\Program Files\\WinFsp\\bin\\winfsp-x64.dll",
            "C:\\Program Files (x86)\\WinFsp\\bin\\winfsp-x86.dll"
        ]
        
        winfsp_found = any(os.path.exists(path) for path in winfsp_paths)
        
        if not winfsp_found:
            messagebox.showerror("WinFsp Not Installed",
                "WinFsp is not installed on this system.\n\n" +
                "WinFsp is required for filesystem mounting on Windows.\n\n" +
                "Please download and install WinFsp from:\n" +
                "  https://winfsp.dev/\n" +
                "  https://github.com/winfsp/winfsp/releases\n\n" +
                "After installation, restart this application.")
            return False
        
        # Check if rt11_mount.bat script exists
        winfsp_script = script_dir / "rt11_mount.bat"
        if not winfsp_script.exists():
            messagebox.showerror("WinFsp Driver Not Found",
                f"WinFsp mount script not found: {winfsp_script}\n\n" +
                "Please ensure rt11_mount.bat is in the same directory.")
            return False
        
        return True
    
    def mount_fuse(self):
        """Mount the RT-11 image as a filesystem using FUSE"""
        if not self.current_file:
            messagebox.showwarning("Warning", "Please select and scan a disk image first.")
            return
        
        # Check platform support and available drivers
        if sys.platform == "win32":
            # Windows: Check for WinFsp
            if not self.check_winfsp_availability():
                return  # Error already shown
        else:
            # macOS/Linux: Check for FUSE
            if not self.check_fuse_availability():
                if sys.platform == "darwin":
                    messagebox.showerror("macFUSE Not Installed", 
                        "macFUSE is not installed on this system.\n\n" +
                        "Please install macFUSE from:\n" +
                        "https://osxfuse.github.io/\n\n" +
                        "After installation, restart this application.")
                elif sys.platform.startswith('linux'):
                    messagebox.showerror("FUSE Not Installed", 
                        "FUSE is not installed on this system.\n\n" +
                        "Please install FUSE using:\n" +
                        "Ubuntu/Debian: sudo apt install fuse libfuse-dev\n" +
                        "RHEL/CentOS: sudo yum install fuse fuse-devel\n" +
                        "Arch Linux: sudo pacman -S fuse2\n\n" +
                        "After installation, restart this application.")
                else:
                    messagebox.showerror("FUSE Not Available", 
                        "FUSE is not available on this platform.")
                return
        
        # Determine which FUSE script to use based on platform
        if sys.platform == "win32":
            fuse_script_name = "rt11_mount.bat"
        else:
            # Use the universal FUSE script that supports both RT-11 and Unix
            fuse_script_name = "rt11_fuse_universal.py"
        
        # Find FUSE script using robust path detection (similar to scan fix)
        fuse_script = None
        
        # Try multiple locations for FUSE script
        possible_locations = []
        
        # Add detailed debugging for path resolution
        self.log(f"DEBUG MOUNT: backend_path = {backend_path}")
        self.log(f"DEBUG MOUNT: script_dir = {script_dir}")
        self.log(f"DEBUG MOUNT: sys.executable = {sys.executable}")
        self.log(f"DEBUG MOUNT: sys.frozen = {getattr(sys, 'frozen', False)}")
        self.log(f"DEBUG MOUNT: fuse_script_name = {fuse_script_name}")
        
        if backend_path:
            # Primary location: backend/filesystem_mount
            primary_location = backend_path / "filesystem_mount" / fuse_script_name
            possible_locations.append(primary_location)
            self.log(f"DEBUG MOUNT: Primary location: {primary_location}")
        else:
            self.log(f"DEBUG MOUNT: WARNING - backend_path is None!")
            # If backend_path is None, try to calculate it manually
            if getattr(sys, 'frozen', False):
                # For packaged apps, backend should be relative to executable
                exe_dir = Path(sys.executable).parent
                manual_backend = exe_dir / "backend"
                if not manual_backend.exists():
                    manual_backend = exe_dir.parent / "backend"
                if not manual_backend.exists():
                    manual_backend = exe_dir.parent / "Resources" / "backend"
                self.log(f"DEBUG MOUNT: Trying manual backend path: {manual_backend}")
                if manual_backend.exists():
                    possible_locations.append(manual_backend / "filesystem_mount" / fuse_script_name)
            else:
                # For scripts, backend should be relative to script directory
                manual_backend = script_dir.parent.parent / "backend"
                self.log(f"DEBUG MOUNT: Trying manual backend path for script: {manual_backend}")
                if manual_backend.exists():
                    possible_locations.append(manual_backend / "filesystem_mount" / fuse_script_name)
        
        if getattr(sys, 'frozen', False):
            # When packaged, also try relative to executable
            exe_dir = Path(sys.executable).parent
            possible_locations.extend([
                exe_dir / fuse_script_name,
                exe_dir / "backend" / "filesystem_mount" / fuse_script_name,
                exe_dir.parent / "Resources" / fuse_script_name,  # macOS bundle
            ])
        
        # Also try relative to script directory
        possible_locations.extend([
            script_dir / fuse_script_name,
            script_dir / "backend" / "filesystem_mount" / fuse_script_name,
            script_dir.parent.parent / "backend" / "filesystem_mount" / fuse_script_name,
        ])
        
        # Find the first existing script
        for location in possible_locations:
            if location.exists():
                fuse_script = location
                self.log(f"DEBUG MOUNT: Found FUSE script at: {fuse_script}")
                break
        
        if not fuse_script:
            self.log(f"DEBUG MOUNT: FUSE script not found. Tried locations:")
            for i, loc in enumerate(possible_locations):
                self.log(f"DEBUG MOUNT: [{i}] {loc} (exists: {loc.exists()})")
            
            messagebox.showerror("FUSE Driver Not Found", 
                f"FUSE driver script not found: {fuse_script_name}\n\n" +
                f"Searched in multiple locations but could not find the script.\n" +
                f"Please ensure the backend files are properly installed.")
            return
        
        # Create mount point - different approach for Windows vs Unix
        if sys.platform == "win32":
            # Windows: Find available drive letter
            mount_dir = self._find_available_drive_letter()
            if not mount_dir:
                messagebox.showerror("Error", "No available drive letters found. Please free up a drive letter and try again.")
                return
        else:
            # Unix: Create directory mount point in user's home directory
            # This avoids App Translocation read-only issues on macOS
            if getattr(sys, 'frozen', False) and sys.platform == 'darwin':
                # For bundled macOS apps, use ~/rt11_mounted to avoid App Translocation issues
                mount_dir = Path.home() / "rt11_mounted"
            else:
                # For scripts or other platforms, use script directory
                mount_dir = script_dir / "rt11_mounted"
                
            try:
                # Clean up any existing mount first
                if mount_dir.exists():
                    # Try to unmount if it's mounted
                    if sys.platform == "darwin":
                        subprocess.run(["umount", str(mount_dir)], 
                                     capture_output=True, check=False)
                    elif sys.platform.startswith('linux'):
                        subprocess.run(["fusermount", "-u", str(mount_dir)], 
                                     capture_output=True, check=False)
                    
                    # Remove and recreate directory
                    shutil.rmtree(mount_dir, ignore_errors=True)
                
                mount_dir.mkdir(exist_ok=True)
            except Exception as e:
                messagebox.showerror("Error", f"Failed to create mount directory:\n{e}")
                return
        
        # Use converted DSK file if available, otherwise use original
        image_file = self.converted_dsk_file if self.converted_dsk_file else self.current_file
        
        # Start FUSE mounting in background thread
        self.log(f"Starting to mount {os.path.basename(image_file)} as filesystem...")
        self.progress_var.set("Mounting filesystem...")
        self.mount_btn.config(state="disabled")
        
        # Start mounting in background thread
        threading.Thread(target=self._mount_fuse_thread, 
                        args=(fuse_script, image_file, mount_dir), 
                        daemon=True).start()
    
    def _mount_fuse_thread(self, fuse_script, image_file, mount_dir):
        """Background thread for FUSE mounting"""
        try:
            self.log(f"Mounting {os.path.basename(image_file)} as filesystem...")
            
            # Debug: Log all parameters
            self.log(f"DEBUG: Script path: {fuse_script}")
            self.log(f"DEBUG: Image file: {image_file}")
            self.log(f"DEBUG: Mount directory: {mount_dir}")
            self.log(f"DEBUG: Script exists: {fuse_script.exists()}")
            self.log(f"DEBUG: Image exists: {os.path.exists(image_file)}")
            # Fix: Handle both Path objects and strings for mount_dir
            if isinstance(mount_dir, Path):
                self.log(f"DEBUG: Mount dir exists: {mount_dir.exists()}")
            else:
                # For Windows drive letters, just check if it's a valid format
                self.log(f"DEBUG: Mount dir (drive letter): {mount_dir}")
            self.log(f"DEBUG: Working directory: {script_dir}")
            
            # Start FUSE mount
            cmd = [str(fuse_script), image_file, str(mount_dir)]
            self.log(f"Running: {' '.join(cmd)}")
            
            # Start the FUSE process (runs in foreground but in our thread)
            kwargs = {
                'stdout': subprocess.PIPE,
                'stderr': subprocess.STDOUT,  # Redirect stderr to stdout for better capture
                'text': True,
                'cwd': script_dir,
                'bufsize': 1,  # Line buffered
                'universal_newlines': True
            }
            
            # On Windows, hide console window but allow output capture
            if sys.platform == "win32":
                kwargs['creationflags'] = CREATE_NO_WINDOW
            
            self.log(f"DEBUG: subprocess.Popen kwargs: {kwargs}")
            
            self.fuse_process = subprocess.Popen(cmd, **kwargs)
            
            self.fuse_mount_point = mount_dir
            self.fuse_mounted = False  # Track if mount was successful
            
            # Give it a moment to start mounting
            time.sleep(2)
            
            # Check mount success after a delay
            self.root.after(0, self._check_mount_success)
            
            # Now wait for the FUSE process to finish with timeout
            try:
                stdout, stderr = self.fuse_process.communicate(timeout=30)
                self.log(f"DEBUG: Process completed with returncode: {self.fuse_process.returncode}")
                if stdout:
                    self.log(f"DEBUG: Process output: {stdout}")
            except subprocess.TimeoutExpired:
                self.log("DEBUG: Process timeout after 30 seconds - process may be running in background")
                # Don't kill the process if it's a successful mount that's running in background
                stdout, stderr = "", ""
            
            # Process ended - filesystem was unmounted
            self.log("FUSE filesystem unmounted")
            self.root.after(0, lambda: self._reset_mount_button())
            
            # If there were errors, show them
            if stderr and "destroyed" not in stderr.lower():
                self.log(f"FUSE stderr: {stderr}")
            
        except Exception as e:
            self.log(f"Error mounting filesystem: {e}")
            self.root.after(0, lambda: messagebox.showerror("Mount Error", f"Failed to mount filesystem:\n{e}"))
            self.root.after(0, lambda: self._reset_mount_button())
        finally:
            # Reset progress and clean up
            self.root.after(0, lambda: self.progress_var.set("Ready"))
            self.fuse_process = None
            self.fuse_mount_point = None
            self.fuse_mounted = False
    
    def _check_mount_success(self):
        """Check if FUSE mount was successful and open file manager"""
        # Handle both Path objects (Unix) and strings (Windows drive letters)
        mount_point_exists = False
        if self.fuse_mount_point:
            if isinstance(self.fuse_mount_point, Path):
                mount_point_exists = self.fuse_mount_point.exists()
            else:
                # For Windows drive letters, check if accessible
                try:
                    mount_point_exists = os.path.exists(self.fuse_mount_point + "\\")
                except:
                    mount_point_exists = False
        
        if mount_point_exists:
            try:
                # Check if mount point has files (indicates successful mount)
                if isinstance(self.fuse_mount_point, Path):
                    files = list(self.fuse_mount_point.iterdir())
                else:
                    # For Windows drive letters, list files in root
                    try:
                        files = os.listdir(self.fuse_mount_point + "\\")
                    except OSError:
                        files = []
                
                if files:
                    self.log(f"Filesystem mounted successfully! Found {len(files)} files.")
                    self.fuse_mounted = True
                    
                    # Update button to show unmount option
                    self.mount_btn.config(
                        text="Unmount Filesystem", 
                        command=self.unmount_fuse,
                        state="normal"
                    )
                    
                    # Open the mount point in file manager
                    self._open_file_manager(self.fuse_mount_point)
                    
                    messagebox.showinfo("Mount Success", 
                        f"RT-11 filesystem mounted successfully!\n\n" +
                        f"Mount point: {self.fuse_mount_point}\n" +
                        f"Files available: {len(files)}\n\n" +
                        "The folder has been opened in your file manager.")
                else:
                    # Check if FUSE process is still running
                    if self.fuse_process and self.fuse_process.poll() is None:
                        self.log("Mount appears empty, checking again...")
                        self.root.after(2000, self._check_mount_success)
                    else:
                        self._handle_mount_failure()
            except Exception as e:
                self.log(f"Error checking mount: {e}")
                self._handle_mount_failure()
        else:
            self._handle_mount_failure()
    
    def _handle_mount_failure(self):
        """Handle FUSE mount failure"""
        error_msg = "Failed to mount filesystem."
        
        if self.fuse_process and self.fuse_process.poll() is None:
            # Process is still running, try to get stderr
            try:
                self.fuse_process.terminate()
                stdout, stderr = self.fuse_process.communicate(timeout=2)
                if stderr:
                    error_msg += f"\n\nError output:\n{stderr}"
            except (subprocess.TimeoutExpired, OSError, AttributeError):
                # Force kill if terminate doesn't work or other errors
                try:
                    self.fuse_process.kill()
                except (OSError, AttributeError):
                    pass
        elif self.fuse_process and hasattr(self.fuse_process, 'stderr') and self.fuse_process.stderr:
            # Process already ended, try to read stderr if available
            try:
                stderr = self.fuse_process.stderr.read()
                if stderr:
                    error_msg += f"\n\nError output:\n{stderr}"
            except (OSError, AttributeError):
                pass
        
        self.log(error_msg)
        messagebox.showerror("Mount Failed", error_msg)
        
        # Reset button
        self._reset_mount_button()
        
        # Clean up
        self.fuse_mount_point = None
        self.fuse_process = None
    
    def _open_file_manager(self, path):
        """Open file manager at the specified path"""
        try:
            if sys.platform == "win32":
                os.startfile(path)
            elif sys.platform == "darwin":  # macOS
                subprocess.run(["open", str(path)])
            else:  # Linux and others
                subprocess.run(["xdg-open", str(path)])
        except Exception as e:
            self.log(f"Error opening file manager: {e}")
    
    def unmount_fuse(self):
        """Unmount the FUSE/WinFsp filesystem"""
        if not self.fuse_mount_point:
            self.log("No mount point to unmount")
            return
        
        unmount_success = False
        
        try:
            self.log(f"Attempting to unmount filesystem at: {self.fuse_mount_point}")
            
            # Platform-specific unmounting
            if sys.platform == "win32":
                self.log("Windows: Attempting WinFsp unmount...")
                
                # Method 1: Try to terminate the WinFsp process first (most reliable)
                if hasattr(self, 'fuse_process') and self.fuse_process and self.fuse_process.poll() is None:
                    self.log("Terminating WinFsp process...")
                    try:
                        self.fuse_process.terminate()
                        self.fuse_process.wait(timeout=5)
                        self.log("WinFsp process terminated successfully")
                        unmount_success = True
                    except subprocess.TimeoutExpired:
                        self.log("Process termination timeout, force killing...")
                        self.fuse_process.kill()
                        try:
                            self.fuse_process.wait(timeout=2)
                            self.log("WinFsp process force-killed")
                            unmount_success = True
                        except subprocess.TimeoutExpired:
                            self.log("ERROR: Could not kill WinFsp process")
                    except Exception as e:
                        self.log(f"Error terminating WinFsp process: {e}")
                
                # Method 2: Try net use command as backup
                if not unmount_success:
                    self.log("Trying net use disconnect command...")
                    try:
                        cmd = ["net", "use", str(self.fuse_mount_point), "/delete", "/y"]
                        self.log(f"Running: {' '.join(cmd)}")
                        result = subprocess.run(cmd, capture_output=True, text=True, 
                                              creationflags=CREATE_NO_WINDOW, timeout=10)
                        
                        self.log(f"net use exit code: {result.returncode}")
                        if result.stdout:
                            self.log(f"net use stdout: {result.stdout.strip()}")
                        if result.stderr:
                            self.log(f"net use stderr: {result.stderr.strip()}")
                        
                        if result.returncode == 0:
                            self.log(f"Successfully disconnected drive {self.fuse_mount_point}")
                            unmount_success = True
                        else:
                            # Try alternative disconnect command
                            self.log("Trying alternative disconnect command...")
                            alt_cmd = ["net", "use", str(self.fuse_mount_point), "/delete"]
                            alt_result = subprocess.run(alt_cmd, capture_output=True, text=True,
                                                      creationflags=CREATE_NO_WINDOW, timeout=10)
                            if alt_result.returncode == 0:
                                self.log(f"Alternative disconnect succeeded for {self.fuse_mount_point}")
                                unmount_success = True
                            else:
                                self.log(f"Both net use commands failed")
                                
                    except subprocess.TimeoutExpired:
                        self.log("net use command timed out")
                    except Exception as e:
                        self.log(f"Error with net use command: {e}")
                
                # Method 3: Try direct file system check (verify unmount)
                if not unmount_success:
                    self.log("Checking if drive is still accessible...")
                    try:
                        test_path = str(self.fuse_mount_point) + "\\"
                        if not os.path.exists(test_path):
                            self.log("Drive is no longer accessible, assuming unmounted")
                            unmount_success = True
                        else:
                            try:
                                # Try to list files - if this fails, drive might be unmounted
                                os.listdir(test_path)
                                self.log("Drive is still accessible - unmount may have failed")
                            except OSError:
                                self.log("Drive exists but not accessible - assuming unmounted")
                                unmount_success = True
                    except Exception as e:
                        self.log(f"Error checking drive accessibility: {e}")
                        # Assume it's unmounted if we can't check
                        unmount_success = True
                        
            else:
                # Unix systems (macOS/Linux): Terminate FUSE process first
                self.log("Unix: Attempting FUSE unmount...")
                if hasattr(self, 'fuse_process') and self.fuse_process and self.fuse_process.poll() is None:
                    self.log("Terminating FUSE process...")
                    try:
                        self.fuse_process.terminate()
                        self.fuse_process.wait(timeout=5)
                        self.log("FUSE process terminated successfully")
                        unmount_success = True
                    except subprocess.TimeoutExpired:
                        self.log("FUSE process termination timeout, force killing...")
                        self.fuse_process.kill()
                        self.log("FUSE process force-killed")
                        unmount_success = True
                    except Exception as e:
                        self.log(f"Error terminating FUSE process: {e}")
                
                # Try platform-specific unmount commands as backup
                if sys.platform == "darwin":
                    try:
                        result = subprocess.run(["umount", str(self.fuse_mount_point)], 
                                               check=True, capture_output=True, timeout=5)
                        self.log("macOS umount command succeeded")
                        unmount_success = True
                    except subprocess.CalledProcessError as e:
                        self.log(f"umount command failed: {e}")
                        # Process termination may have already unmounted
                    except subprocess.TimeoutExpired:
                        self.log("umount command timed out")
                elif sys.platform.startswith('linux'):
                    try:
                        result = subprocess.run(["fusermount", "-u", str(self.fuse_mount_point)], 
                                               check=True, capture_output=True, timeout=5)
                        self.log("Linux fusermount command succeeded")
                        unmount_success = True
                    except subprocess.CalledProcessError as e:
                        self.log(f"fusermount command failed: {e}")
                        # Process termination may have already unmounted
                    except subprocess.TimeoutExpired:
                        self.log("fusermount command timed out")
            
            if unmount_success:
                self.log("Filesystem unmounted successfully!")
            else:
                self.log("WARNING: Unmount may have failed or was only partially successful")
            
        except Exception as e:
            self.log(f"ERROR during unmount: {e}")
            # Continue with cleanup even if unmount failed
        finally:
            # Always reset state regardless of unmount success
            self.log("Resetting mount state...")
            if hasattr(self, 'mount_btn') and self.mount_btn is not None:
                self.mount_btn.config(text="Mount as Filesystem", command=self.mount_fuse, state="normal")
            self.fuse_mount_point = None
            self.fuse_process = None
            self.fuse_mounted = False
            self.log("Mount state reset complete")
    
    def _find_available_drive_letter(self):
        """Find an available drive letter on Windows"""
        import string
        
        # Check for available drive letters (starting from Z: and going backwards)
        for letter in reversed(string.ascii_uppercase):
            drive = f"{letter}:"
            # Skip common system drives
            if letter in ['A', 'B', 'C']:
                continue
                
            # Check if drive is available
            try:
                if not os.path.exists(drive + "\\"):
                    self.log(f"Found available drive letter: {drive}")
                    return drive
            except OSError:
                # Drive letter is available if we get an OSError
                self.log(f"Found available drive letter: {drive}")
                return drive
        
        # If no drive letter found, try some common ones
        for letter in ['Z', 'Y', 'X', 'W', 'V', 'U', 'T', 'S', 'R']:
            drive = f"{letter}:"
            try:
                if not os.path.exists(drive + "\\"):
                    self.log(f"Using drive letter: {drive}")
                    return drive
            except OSError:
                self.log(f"Using drive letter: {drive}")
                return drive
        
        return None  # No available drive letter found
    
    def _get_winfsp_mounted_drives(self):
        """Get list of WinFsp mounted drives on Windows using multiple detection methods"""
        if sys.platform != "win32":
            return []
        
        mounted_drives = []
        self.log("Checking for active WinFsp mounts...")
        
        # Method 1: Check net use output (WinFsp may appear as network drives)
        try:
            self.log("Method 1: Checking 'net use' output...")
            result = subprocess.run(["net", "use"], capture_output=True, text=True, 
                                  creationflags=CREATE_NO_WINDOW, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                self.log(f"net use output: {result.stdout}")
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for lines that indicate WinFsp mounts
                    if ':' in line and ('WinFsp' in line or 'rt11' in line.lower() or 'fuse' in line.lower()):
                        # Extract drive letter from the line
                        parts = line.split()
                        for part in parts:
                            if len(part) == 2 and part[1] == ':' and part[0].isalpha():
                                self.log(f"Found WinFsp drive via net use: {part}")
                                mounted_drives.append(part)
                                break
        except Exception as e:
            self.log(f"Error checking net use: {e}")
        
        # Method 2: Check all drive letters for WinFsp characteristics (more specific criteria)
        try:
            self.log("Method 2: Scanning all drive letters for WinFsp...")
            import string
            for letter in string.ascii_uppercase:
                drive = f"{letter}:"
                # Skip common system drives
                if letter in ['A', 'B', 'C']:
                    continue
                
                try:
                    drive_path = drive + "\\"
                    # Check if drive exists and is accessible
                    if os.path.exists(drive_path):
                        # Try to detect if it's a WinFsp mount by checking multiple criteria
                        try:
                            files = os.listdir(drive_path)
                            
                            # More specific RT-11 detection criteria
                            rt11_extensions = ['.SAV', '.DAT', '.TXT', '.BAS', '.FOR', '.MAC', '.OBJ', '.REL']
                            rt11_like_files = [f for f in files if any(f.upper().endswith(ext) for ext in rt11_extensions)]
                            
                            # Check for typical RT-11 filenames (uppercase, short names)
                            typical_rt11_names = any(
                                len(f.split('.')[0]) <= 6 and f.isupper() and '.' in f
                                for f in files if '.' in f
                            )
                            
                            # Exclude known non-WinFsp drives
                            is_network_drive = any(keyword in drive_path.lower() for keyword in ['icloud', 'onedrive', 'dropbox', 'google'])
                            
                            # Only consider it WinFsp if:
                            # 1. Has RT-11-like files AND typical RT-11 naming pattern
                            # 2. Not a known cloud/network drive
                            # 3. Small number of files (RT-11 disks typically have < 30 files)
                            if (len(rt11_like_files) >= 2 and typical_rt11_names and 
                                not is_network_drive and len(files) <= 30):
                                self.log(f"Found WinFsp drive via scan: {drive} (files: {len(files)}, RT-11 files: {len(rt11_like_files)}, typical names: {typical_rt11_names})")
                                if drive not in mounted_drives:
                                    mounted_drives.append(drive)
                            else:
                                # Log why it was rejected
                                rejection_reasons = []
                                if len(rt11_like_files) < 2:
                                    rejection_reasons.append(f"insufficient RT-11 files ({len(rt11_like_files)})")
                                if not typical_rt11_names:
                                    rejection_reasons.append("no typical RT-11 naming pattern")
                                if is_network_drive:
                                    rejection_reasons.append("appears to be network/cloud drive")
                                if len(files) > 30:
                                    rejection_reasons.append(f"too many files ({len(files)})")
                                
                                self.log(f"Skipping {drive}: {', '.join(rejection_reasons)}")
                                
                        except (OSError, PermissionError):
                            # Can't list files, might not be a WinFsp mount
                            pass
                except OSError:
                    # Drive doesn't exist or not accessible
                    pass
        except Exception as e:
            self.log(f"Error scanning drive letters: {e}")
        
        # Method 3: Check using wmic (Windows Management Instrumentation)
        try:
            self.log("Method 3: Checking via wmic...")
            result = subprocess.run(["wmic", "logicaldisk", "get", "size,freespace,caption,description,filesystem"], 
                                  capture_output=True, text=True, 
                                  creationflags=CREATE_NO_WINDOW, timeout=10)
            
            if result.returncode == 0 and result.stdout:
                lines = result.stdout.split('\n')
                for line in lines:
                    line = line.strip()
                    # Look for drives with unusual filesystems that might be WinFsp
                    if ':' in line and ('fuse' in line.lower() or line.count(' ') > 5):
                        parts = line.split()
                        for part in parts:
                            if len(part) == 2 and part[1] == ':' and part[0].isalpha():
                                self.log(f"Found potential WinFsp drive via wmic: {part}")
                                if part not in mounted_drives:
                                    mounted_drives.append(part)
                                break
        except Exception as e:
            self.log(f"Error checking wmic: {e}")
        
        self.log(f"Total WinFsp drives detected: {mounted_drives}")
        return mounted_drives
    
    def _is_winfsp_drive_mounted(self, drive_letter):
        """Check if a specific drive is a WinFsp mount"""
        if sys.platform != "win32":
            return False
        
        try:
            # Check if the drive exists and is accessible
            test_path = drive_letter + "\\"
            if os.path.exists(test_path):
                # Try to list files to see if it's a working WinFsp mount
                try:
                    files = os.listdir(test_path)
                    return True  # If we can list files, it's likely mounted
                except OSError:
                    return False
        except Exception:
            pass
        
        return False
    
    def _reset_mount_button(self):
        """Reset mount button to initial state"""
        if hasattr(self, 'mount_btn') and self.mount_btn is not None:
            self.mount_btn.config(
                text="Mount as Filesystem", 
                command=self.mount_fuse,
                state="normal" if self.current_files else "disabled"
            )
        self.fuse_mounted = False
    
    def _check_and_unmount_if_needed(self, action_name="proceed"):
        """Check if FUSE/WinFsp is mounted and ask user if they want to unmount"""
        # Only check our internal state for now (disable external WinFsp detection to avoid false positives)
        if hasattr(self, 'fuse_mounted') and self.fuse_mounted and self.fuse_mount_point:
            mounted_location = self.fuse_mount_point
        else:
            # TODO: Re-enable automatic WinFsp detection after improving accuracy
            # External WinFsp detection temporarily disabled due to false positives with network drives
            # if sys.platform == "win32":
            #     mounted_drives = self._get_winfsp_mounted_drives()
            #     if mounted_drives:
            #         mounted_location = mounted_drives[0]
            #         self.fuse_mount_point = mounted_location
            #         self.fuse_mounted = True
            #     else:
            #         return True
            # else:
            return True  # No mount state to check
        
        # We have an active mount, ask user what to do
        if sys.platform == "win32":
            dialog_title = "WinFsp Filesystem Mounted"
            mount_type = "drive"
        else:
            dialog_title = "FUSE Filesystem Mounted"
            mount_type = "directory"
            
        response = messagebox.askyesno(
            dialog_title,
            f"A filesystem is currently mounted at {mount_type}:\n{mounted_location}\n\n" +
            f"Do you want to unmount it and {action_name}?"
        )
        if response:
            self.unmount_fuse()
            return True
        else:
            return False
    
    def on_closing(self):
        """Handle application closing"""
        # Check if FUSE/WinFsp filesystem is mounted (both internal state and external detection)
        mounted_location = None
        
        if hasattr(self, 'fuse_mounted') and self.fuse_mounted and self.fuse_mount_point:
            mounted_location = self.fuse_mount_point
        elif sys.platform == "win32":
            # Also check for any active WinFsp mounts we might not know about
            mounted_drives = self._get_winfsp_mounted_drives()
            if mounted_drives:
                mounted_location = mounted_drives[0]
                self.fuse_mount_point = mounted_location  # Update our state
                self.fuse_mounted = True
        
        if mounted_location:
            # Choose appropriate dialog title and instructions based on platform
            if sys.platform == "win32":
                dialog_title = "WinFsp Filesystem Mounted"
                unmount_instructions = f"You can eject it from File Explorer or using:\n  net use {mounted_location} /delete"
            else:
                dialog_title = "FUSE Filesystem Mounted"
                if sys.platform == "darwin":
                    unmount_instructions = f"umount {mounted_location}"
                elif sys.platform.startswith('linux'):
                    unmount_instructions = f"fusermount -u {mounted_location}"
                else:
                    unmount_instructions = "Check your system documentation for unmount commands"
            
            response = messagebox.askyesnocancel(
                dialog_title,
                f"A filesystem is currently mounted at:\n{mounted_location}\n\n" +
                "Do you want to keep it mounted after closing the application?\n\n" +
                "• Yes: Keep mounted and close application\n" +
                "• No: Unmount and close application\n" +
                "• Cancel: Don't close application"
            )
            
            if response is None:  # Cancel
                return  # Don't close
            elif response is False:  # No - unmount and close
                self.log("User chose to unmount filesystem before closing...")
                self.unmount_fuse()
                self.log("Filesystem unmounted successfully.")
            else:  # Yes - keep mounted and close
                self.log("User chose to keep filesystem mounted.")
                self.log("Leaving filesystem mounted. You can unmount it manually with:")
                self.log(f"  {unmount_instructions}")
                
                # Detach the process so it continues running
                if hasattr(self, 'fuse_process') and self.fuse_process:
                    self.fuse_process = None  # Don't terminate it
        
        # Clean up temp directory
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        
        self.root.destroy()

def main():
    # Create main window
    root = tk.Tk()
    
    # Create application
    app = RT11ExtractGUI(root)
    
    # Handle window closing
    root.protocol("WM_DELETE_WINDOW", app.on_closing)
    
    # Start application
    root.mainloop()

if __name__ == '__main__':
    main()
