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
        
        # Set icon (DEC logo text as fallback)
        try:
            # You can add an icon file here if you have one
            pass
        except:
            pass
        
        self.setup_ui()
        self.setup_menu()
        self.check_rt11extract()
        
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
        
        self.open_folder_btn = ttk.Button(buttons_frame, text="Open Output Folder", 
                                         command=self.open_output_folder, state="disabled")
        self.open_folder_btn.grid(row=0, column=2, padx=(0, 5))
        
        self.clear_btn = ttk.Button(buttons_frame, text="Clear", command=self.clear_all)
        self.clear_btn.grid(row=0, column=3, padx=(5, 0))
        
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
                # Look for lines with filename, type, size, status, date
                if line and not line.startswith('-') and len(line.split()) >= 5:
                    parts = line.split()
                    if len(parts) >= 5 and parts[-1] != 'Date':
                        filename = parts[0]
                        date_str = parts[-1]
                        # Validate date format
                        if '-' in date_str and len(date_str.split('-')) == 3:
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
        
    def on_closing(self):
        """Handle application closing"""
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
