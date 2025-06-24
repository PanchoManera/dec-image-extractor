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
from imd2raw import IMDConverter, DiskImageValidator

# Windows-specific imports for hiding console
if sys.platform == "win32":
    # Constants for Windows subprocess creation flags
    CREATE_NO_WINDOW = 0x08000000
    DETACHED_PROCESS = 0x00000008
else:
    CREATE_NO_WINDOW = 0
    DETACHED_PROCESS = 0

# Global variables
import sys

# Determine if running as script or frozen exe
if getattr(sys, 'frozen', False):
    # Running as compiled executable - look in same directory as executable
    script_dir = Path(sys.executable).parent
    # Check for different executable names based on platform
    if sys.platform.startswith('win'):
        rt11extract_path = script_dir / "RT11Extract.exe"
    elif sys.platform == 'darwin':  # macOS
        # In macOS bundle, the GUI is inside .app/Contents/MacOS/, but CLI might be in different locations
        if str(script_dir).endswith('.app/Contents/MacOS'):
            # We're inside a .app bundle, try multiple locations for CLI
            possible_cli_paths = [
                script_dir / "rt11extract_cli",  # Inside the .app bundle (preferred)
                script_dir.parent.parent.parent / "rt11extract_cli",  # In parent directory of .app
            ]
            
            # Find the first existing CLI executable
            rt11extract_path = None
            for path in possible_cli_paths:
                if path.exists():
                    rt11extract_path = path
                    break
            
            # If not found, default to the preferred location (inside bundle)
            if rt11extract_path is None:
                rt11extract_path = script_dir / "rt11extract_cli"
        else:
            # Not in .app bundle, look in same directory
            rt11extract_path = script_dir / "rt11extract_cli"
    else:
        rt11extract_path = script_dir / "RT11Extract"
else:
    # Running as script
    script_dir = Path(__file__).parent
    # Check for different executable names based on platform
    if sys.platform.startswith('win'):
        rt11extract_path = script_dir / "RT11Extract.exe"
    else:
        rt11extract_path = script_dir / "rt11extract"

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
        """Perform the actual scan operation"""
        # First run rt11extract in list mode to get file info with dates
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - run rt11extract directly (it's included in bundle)
            cmd_list = [str(rt11extract_path), disk_file, '-l']
        else:
            # Running as script - run rt11extract with python (it's a python script)
            cmd_list = [sys.executable, str(rt11extract_path), disk_file, '-l']
        self.log(f"Running: {' '.join(cmd_list)}")
        
        list_result = subprocess.run(cmd_list, **self._get_subprocess_kwargs())
        
        # Then run rt11extract to actually extract files for verification
        scan_dir = self.temp_dir / 'scan_output'
        scan_dir.mkdir(exist_ok=True)
        
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - run rt11extract directly (it's included in bundle)
            cmd = [str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
        else:
            # Running as script - run rt11extract with python (it's a python script)
            cmd = [sys.executable, str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
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
            # Parse extracted files
            files = self._parse_extracted_files(scan_dir, result.stdout, list_result.stdout)
            self.current_files = files
            
            # Update UI in main thread
            self.root.after(0, self._update_files_ui, files)
            self.log(f"Scan completed successfully! Found {len(files)} files.")
        else:
            self.log(f"Error: rt11extract failed with return code {result.returncode}")
            self.root.after(0, self._scan_error, f"rt11extract failed with return code {result.returncode}")
            
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
        
        # Enable FUSE mount button if we have files (only on non-Windows)
        if files and hasattr(self, 'mount_btn') and self.mount_btn is not None:
            self.mount_btn.config(state="normal")
        
        # Enable extract selected button if there are files
        if files:
            # Bind selection change event to enable/disable extract selected button
            self.files_tree.bind('<<TreeviewSelect>>', self.on_file_select)
        
    def _parse_extracted_files(self, scan_dir, output, list_output=None):
        """Parse extracted files to get file information"""
        files = []
        
        # First parse the list output to get dates
        date_map = {}
        if list_output:
            lines = list_output.split('\n')
            for line in lines:
                line = line.strip()
                # Look for lines with data that match the table format
                # Skip header lines, separators, and summary lines
                if (line and not line.startswith('-') and not line.startswith('=') and 
                    'Filename' not in line and 'Type' not in line and 
                    'Total files:' not in line and 'RT-11 Directory Listing:' not in line and
                    'RT-11 Extractor' not in line and 'Processing:' not in line and
                    line != '' and len(line.split()) >= 5):
                    
                    # Split the line into parts - use more flexible parsing
                    parts = line.split()
                    
                    # Look for date pattern in the line (YYYY-MM-DD)
                    date_str = None
                    filename = parts[0] if parts else None
                    
                    # Search for date pattern in all parts
                    for part in parts:
                        if '-' in part and len(part.split('-')) == 3:
                            try:
                                # Check if it looks like a date
                                year, month, day = part.split('-')
                                if (len(year) == 4 and len(month) == 2 and len(day) == 2 and
                                    year.isdigit() and month.isdigit() and day.isdigit()):
                                    date_str = part
                                    break
                            except (ValueError, IndexError):
                                continue
                    
                    # If we found both filename and date, add to map
                    if filename and date_str:
                        date_map[filename] = date_str
        
        # Get files from directory
        for file_path in scan_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.endswith('.rt11info'):
                size_bytes = file_path.stat().st_size
                size_blocks = (size_bytes + 511) // 512
                
                # Determine file type based on extension
                file_type = self._get_file_description(file_path.name)
                
                # Get creation date from list output
                creation_date = date_map.get(file_path.name, 'N/A')
                
                files.append({
                    'filename': file_path.name,
                    'size_blocks': size_blocks,
                    'size_bytes': size_bytes,
                    'file_type': file_type,
                    'creation_date': creation_date
                })
        
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
        filename = item['values'][0]
        
        # Ask for output file location
        output_file = filedialog.asksaveasfilename(
            title="Save extracted file as...",
            initialfile=filename,
            defaultextension="",
            filetypes=[("All Files", "*.*")]
        )
        
        if not output_file:
            return
            
        # Extract single file (we'll copy from temp scan directory if available)
        if self.temp_dir:
            scan_dir = self.temp_dir / 'scan_output'
            source_file = scan_dir / filename
            
            if source_file.exists():
                try:
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
            # Use the wrapper script that prefers standalone executable
            fuse_script_name = "rt11_fuse_wrapper.sh"
        
        # Find FUSE script in appropriate location
        if getattr(sys, 'frozen', False) and str(script_dir).endswith('.app/Contents/MacOS'):
            # In macOS bundle, FUSE scripts are in Resources/
            resources_dir = script_dir.parent / "Resources"
            fuse_script = resources_dir / fuse_script_name
        else:
            # Not in bundle or not macOS, look in script directory
            fuse_script = script_dir / fuse_script_name
            
        if not fuse_script.exists():
            messagebox.showerror("FUSE Driver Not Found", 
                f"FUSE driver script not found: {fuse_script}\n\n" +
                f"Please ensure {fuse_script_name} is in the same directory.")
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
        """Unmount the FUSE filesystem"""
        if not self.fuse_mount_point:
            return
        
        try:
            self.log("Unmounting filesystem...")
            
            # Terminate FUSE process
            if self.fuse_process and self.fuse_process.poll() is None:
                self.fuse_process.terminate()
                try:
                    self.fuse_process.wait(timeout=5)
                except subprocess.TimeoutExpired:
                    self.fuse_process.kill()
            
            # On macOS, try unmounting with umount
            if sys.platform == "darwin":
                try:
                    subprocess.run(["umount", str(self.fuse_mount_point)], 
                                 check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    pass  # Process termination may have already unmounted
            
            # On Linux, try fusermount
            elif sys.platform.startswith('linux'):
                try:
                    subprocess.run(["fusermount", "-u", str(self.fuse_mount_point)], 
                                 check=True, capture_output=True)
                except subprocess.CalledProcessError:
                    pass  # Process termination may have already unmounted
            
            self.log("Filesystem unmounted successfully.")
            
        except Exception as e:
            self.log(f"Error during unmount: {e}")
        finally:
            # Reset state (only if button exists - not on Windows)
            if hasattr(self, 'mount_btn') and self.mount_btn is not None:
                self.mount_btn.config(text="Mount as Filesystem", command=self.mount_fuse)
            self.fuse_mount_point = None
            self.fuse_process = None
            self.fuse_mounted = False
    
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
        if hasattr(self, 'fuse_mounted') and self.fuse_mounted and self.fuse_mount_point:
            # Choose appropriate dialog title based on platform
            if sys.platform == "win32":
                dialog_title = "WinFsp Filesystem Mounted"
            else:
                dialog_title = "FUSE Filesystem Mounted"
                
            response = messagebox.askyesno(
                dialog_title,
                f"A filesystem is currently mounted at:\n{self.fuse_mount_point}\n\n" +
                f"Do you want to unmount it and {action_name}?"
            )
            if response:
                self.unmount_fuse()
                return True
            else:
                return False
        return True
    
    def on_closing(self):
        """Handle application closing"""
        # Check if FUSE/WinFsp filesystem is mounted
        if hasattr(self, 'fuse_mounted') and self.fuse_mounted and self.fuse_mount_point:
            # Choose appropriate dialog title and instructions based on platform
            if sys.platform == "win32":
                dialog_title = "WinFsp Filesystem Mounted"
                unmount_instructions = f"You can eject it from File Explorer or using:\n  net use {self.fuse_mount_point} /delete"
            else:
                dialog_title = "FUSE Filesystem Mounted"
                if sys.platform == "darwin":
                    unmount_instructions = f"umount {self.fuse_mount_point}"
                elif sys.platform.startswith('linux'):
                    unmount_instructions = f"fusermount -u {self.fuse_mount_point}"
                else:
                    unmount_instructions = "Check your system documentation for unmount commands"
            
            response = messagebox.askyesnocancel(
                dialog_title,
                f"A filesystem is currently mounted at:\n{self.fuse_mount_point}\n\n" +
                "Do you want to keep it mounted after closing the application?\n\n" +
                "• Yes: Keep mounted and close application\n" +
                "• No: Unmount and close application\n" +
                "• Cancel: Don't close application"
            )
            
            if response is None:  # Cancel
                return  # Don't close
            elif response is False:  # No - unmount and close
                self.unmount_fuse()
                self.log("Filesystem unmounted before closing.")
            else:  # Yes - keep mounted and close
                self.log("Leaving filesystem mounted. You can unmount it manually with:")
                self.log(f"  {unmount_instructions}")
                
                # Detach the process so it continues running
                if self.fuse_process:
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
