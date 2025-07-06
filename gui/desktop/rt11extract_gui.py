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
        if sys.platform == 'win32':
            # Windows: use RT11Extract.exe in same directory
            return Path(sys.executable).parent / "RT11Extract.exe"
        elif sys.platform == 'darwin':
            # macOS: Check bundle/cli/ directory
            exe_path = Path(sys.executable)
            cli_dir = exe_path.parent.parent / "cli"
            if cli_dir.exists():
                return cli_dir / "rt11extract_cli"
    # Default: Use rt11extract in backend
    return Path(__file__).parent.parent.parent / "backend" / "extractors" / "rt11extract"

def get_imd2raw_path():
    """Get path to imd2raw tool"""
    if getattr(sys, 'frozen', False):
        if sys.platform == 'win32':
            # Windows: use imd2raw.exe in same directory
            return Path(sys.executable).parent / "imd2raw.exe"
        elif sys.platform == 'darwin':
            # macOS: Check bundle/cli/ directory
            exe_path = Path(sys.executable)
            cli_dir = exe_path.parent.parent / "cli"
            if cli_dir.exists():
                return cli_dir / "imd2raw"
    # Default: Use imd2raw.py in backend
    return Path(__file__).parent.parent.parent / "backend" / "image_converters" / "imd2raw.py"

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
        
        # Windows-specific variables
        if sys.platform == "win32":
            self.CREATE_NO_WINDOW = 0x08000000
        else:
            self.CREATE_NO_WINDOW = 0
        
        self.setup_ui()
        
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
        file_frame = ttk.LabelFrame(main_frame, text="RT-11 Disk Image", padding="10")
        file_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
        file_frame.columnconfigure(1, weight=1)
        
        self.file_var = tk.StringVar()
        ttk.Label(file_frame, text="File:").grid(row=0, column=0, sticky=tk.W, padx=(0, 5))
        ttk.Entry(file_frame, textvariable=self.file_var, state="readonly").grid(row=0, column=1, sticky=(tk.W, tk.E))
        ttk.Button(file_frame, text="Browse...", command=self.browse_file).grid(row=0, column=2, padx=(5, 0))
        
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
        
        self.files_tree.column('Filename', width=250)
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
        self.extract_selected_btn.grid(row=0, column=1)
        
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
                # For macOS bundle, CLIs are in Contents/cli/
                exe_path = Path(sys.executable)
                cli_dir = exe_path.parent.parent / "cli"
                if cli_dir.exists():
                    kwargs['cwd'] = str(cli_dir)
            else:
                # For Windows, use executable directory
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
            self.scan_file()
    
    def scan_file(self):
        """Scan the selected file"""
        if not self.current_file:
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
            
            # Build command
            cmd = [str(rt11extract_path), self.current_file, '-o', str(self.temp_dir), '-v']
            
            # Run command
            kwargs = self._get_subprocess_kwargs()
            result = subprocess.run(cmd, **kwargs)
            
            if result.returncode == 0:
                # Parse output directory
                self._parse_output()
            else:
                self.root.after(0, lambda: messagebox.showerror("Error", 
                    f"Failed to scan file (exit code {result.returncode})"))
        except Exception as e:
            self.root.after(0, lambda: messagebox.showerror("Error", str(e)))
        finally:
            # Reset progress
            self.root.after(0, lambda: self.progress_bar.stop())
            self.root.after(0, lambda: self.progress_var.set("Ready"))
    
    def _parse_output(self):
        """Parse scan output directory"""
        if not self.temp_dir or not self.temp_dir.exists():
            return
        
        files = []
        for path in self.temp_dir.rglob('*'):
            if path.is_file():
                size = path.stat().st_size
                date = datetime.fromtimestamp(path.stat().st_mtime)
                files.append({
                    'name': path.name,
                    'size': f"{size:,} bytes",
                    'date': date.strftime("%Y-%m-%d %H:%M:%S"),
                    'path': path
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
            
            # Use rt11extract for extraction
            cmd = [str(rt11extract_path), self.current_file, '-o', str(self.output_dir), '-v']
            kwargs = self._get_subprocess_kwargs()
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

def main():
    root = tk.Tk()
    app = RT11ExtractGUI(root)
    root.mainloop()

if __name__ == '__main__':
    main()
