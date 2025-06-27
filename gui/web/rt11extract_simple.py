#!/usr/bin/env python3

import http.server
import socketserver
import urllib.parse
import json
import subprocess
import os
import sys
import tempfile
import shutil
from pathlib import Path
import threading
import time
import uuid
import zipfile
import base64
from datetime import datetime
import hashlib

# Add backend path to Python path for imports
script_dir = Path(__file__).parent.parent.parent  # Go up to root from gui/web/
backend_path = script_dir / "backend"
sys.path.insert(0, str(backend_path))

from image_converters.imd2raw import IMDConverter, DiskImageValidator

# Global variables
current_operations = {}

# Use same rt11extract path as GUI desktop
if sys.platform.startswith('win'):
    rt11extract_path = script_dir / "backend" / "extractors" / "RT11Extract.exe"
else:
    rt11extract_path = script_dir / "backend" / "extractors" / "rt11extract"

# HTML Template (same as before but updated)
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>DEC Disk Image Extractor - Web Interface</title>
    <style>
        body {
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            margin: 0;
            padding: 20px;
            background-color: #f5f5f5;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 8px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            padding: 20px;
        }
        h1 {
            color: #333;
            text-align: center;
            border-bottom: 2px solid #007bff;
            padding-bottom: 10px;
        }
        .upload-section {
            border: 2px dashed #007bff;
            border-radius: 8px;
            padding: 20px;
            text-align: center;
            margin-bottom: 20px;
            background-color: #f8f9fa;
        }
        input[type="file"] {
            margin: 10px 0;
            padding: 10px;
            border: 1px solid #ddd;
            border-radius: 4px;
            width: 300px;
        }
        button {
            background-color: #007bff;
            color: white;
            padding: 10px 20px;
            border: none;
            border-radius: 4px;
            cursor: pointer;
            margin: 5px;
            font-size: 14px;
        }
        button:hover {
            background-color: #0056b3;
        }
        button:disabled {
            background-color: #6c757d;
            cursor: not-allowed;
        }
        .success {
            background-color: #28a745;
        }
        .success:hover {
            background-color: #218838;
        }
        .files-table {
            width: 100%;
            border-collapse: collapse;
            margin: 20px 0;
        }
        .files-table th, .files-table td {
            border: 1px solid #ddd;
            padding: 8px;
            text-align: left;
        }
        .files-table th {
            background-color: #007bff;
            color: white;
        }
        .files-table tr:nth-child(even) {
            background-color: #f2f2f2;
        }
        .files-table tr:hover {
            background-color: #e3f2fd;
        }
        .log-section {
            background-color: #000;
            color: #00ff00;
            padding: 15px;
            border-radius: 4px;
            font-family: 'Courier New', monospace;
            font-size: 12px;
            height: 300px;
            overflow-y: auto;
            margin: 20px 0;
            display: none;
        }
        .log-section.show {
            display: block;
        }
        .status {
            padding: 10px;
            margin: 10px 0;
            border-radius: 4px;
            font-weight: bold;
        }
        .status.info {
            background-color: #d1ecf1;
            color: #0c5460;
            border: 1px solid #bee5eb;
        }
        .status.success {
            background-color: #d4edda;
            color: #155724;
            border: 1px solid #c3e6cb;
        }
        .status.error {
            background-color: #f8d7da;
            color: #721c24;
            border: 1px solid #f5c6cb;
        }
        .progress-bar {
            width: 100%;
            height: 20px;
            background-color: #e0e0e0;
            border-radius: 10px;
            overflow: hidden;
            margin: 10px 0;
            display: none;
        }
        .progress-bar.show {
            display: block;
        }
        .progress-fill {
            height: 100%;
            background-color: #007bff;
            width: 0%;
            transition: width 0.3s ease;
        }
        .hidden {
            display: none;
        }
        .file-info {
            background-color: #e9ecef;
            padding: 10px;
            border-radius: 4px;
            margin: 10px 0;
        }
        .spinner {
            border: 3px solid #f3f3f3;
            border-top: 3px solid #007bff;
            border-radius: 50%;
            width: 20px;
            height: 20px;
            animation: spin 1s linear infinite;
            display: inline-block;
            margin-right: 10px;
        }
        @keyframes spin {
            0% { transform: rotate(0deg); }
            100% { transform: rotate(360deg); }
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🖥️ DEC Disk Image Extractor</h1>
        <p style="text-align: center; color: #666;">Extract files from RT-11, RSX-11 (ODS-1), and Unix PDP-11 disk images</p>
        
        <div class="upload-section">
            <h3>Select Disk Image</h3>
            <input type="file" id="fileInput" accept=".dsk,.img,.imd,.raw" />
            <br>
            <button id="uploadBtn" onclick="uploadFile()">📁 Upload & Scan</button>
            <button id="toggleLogsBtn" onclick="toggleLogs()" style="display:none;">📋 Show/Hide Logs</button>
        </div>
        
        <div id="status" class="status info hidden">Ready to process disk images...</div>
        <div id="progressBar" class="progress-bar">
            <div id="progressFill" class="progress-fill"></div>
        </div>
        
        <div id="fileInfo" class="file-info hidden"></div>
        
        <div id="filesSection" class="hidden">
            <h3>📂 Extracted Files</h3>
            <button id="downloadAllBtn" onclick="downloadAll()" class="success">💾 Download All Files (ZIP)</button>
            <table class="files-table" id="filesTable">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Type</th>
                        <th>Size (blocks)</th>
                        <th>Size (bytes)</th>
                        <th>Date</th>
                        <th>Actions</th>
                    </tr>
                </thead>
                <tbody id="filesTableBody">
                </tbody>
            </table>
        </div>
        
        <div id="logSection" class="log-section">
            <div id="logContent"></div>
        </div>
    </div>

    <script>
        let currentOperationId = null;
        
        function log(message) {
            const logContent = document.getElementById('logContent');
            const timestamp = new Date().toLocaleTimeString();
            logContent.innerHTML += `[${timestamp}] ${message}\n`;
            logContent.scrollTop = logContent.scrollHeight;
        }
        
        function updateStatus(message, type = 'info') {
            const status = document.getElementById('status');
            status.textContent = message;
            status.className = `status ${type}`;
            status.classList.remove('hidden');
            log(message);
        }
        
        function updateProgress(percent) {
            const progressBar = document.getElementById('progressBar');
            const progressFill = document.getElementById('progressFill');
            
            if (percent >= 0) {
                progressBar.classList.add('show');
                progressFill.style.width = percent + '%';
            } else {
                progressBar.classList.remove('show');
            }
        }
        
        function toggleLogs() {
            const logSection = document.getElementById('logSection');
            logSection.classList.toggle('show');
        }
        
        async function uploadFile() {
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                updateStatus('Please select a file first', 'error');
                return;
            }
            
            updateStatus('Uploading file...', 'info');
            updateProgress(0);
            
            const formData = new FormData();
            formData.append('file', file);
            
            try {
                const response = await fetch('/upload', {
                    method: 'POST',
                    body: formData
                });
                
                const result = await response.json();
                
                if (result.success) {
                    currentOperationId = result.operation_id;
                    updateStatus('File uploaded successfully, starting scan...', 'success');
                    document.getElementById('toggleLogsBtn').style.display = 'inline-block';
                    pollOperation();
                } else {
                    updateStatus('Upload failed: ' + result.error, 'error');
                    updateProgress(-1);
                }
            } catch (error) {
                updateStatus('Upload error: ' + error.message, 'error');
                updateProgress(-1);
            }
        }
        
        async function pollOperation() {
            if (!currentOperationId) return;
            
            try {
                const response = await fetch(`/status/${currentOperationId}`);
                const result = await response.json();
                
                updateStatus(result.status, result.type || 'info');
                updateProgress(result.progress);
                
                // Update logs
                if (result.logs) {
                    result.logs.forEach(logMessage => {
                        if (logMessage) log(logMessage);
                    });
                }
                
                // Update file info
                if (result.file_info) {
                    displayFileInfo(result.file_info);
                }
                
                // Update files list
                if (result.files) {
                    displayFiles(result.files);
                }
                
                if (result.completed) {
                    updateProgress(-1);
                    if (result.success) {
                        updateStatus('Scan completed successfully!', 'success');
                        document.getElementById('filesSection').classList.remove('hidden');
                    } else {
                        updateStatus('Scan failed: ' + (result.error || 'Unknown error'), 'error');
                    }
                } else {
                    // Continue polling
                    setTimeout(pollOperation, 1000);
                }
            } catch (error) {
                updateStatus('Status check error: ' + error.message, 'error');
                updateProgress(-1);
            }
        }
        
        function displayFileInfo(info) {
            const fileInfo = document.getElementById('fileInfo');
            fileInfo.innerHTML = `
                <h4>📊 Disk Image Information</h4>
                <p><strong>Filesystem:</strong> ${info.filesystem || 'Unknown'}</p>
                <p><strong>Files Found:</strong> ${info.file_count || 0}</p>
                <p><strong>Total Size:</strong> ${info.total_size || 'Unknown'}</p>
            `;
            fileInfo.classList.remove('hidden');
        }
        
        function displayFiles(files) {
            const tbody = document.getElementById('filesTableBody');
            tbody.innerHTML = '';
            
            files.forEach(file => {
                const row = tbody.insertRow();
                row.innerHTML = `
                    <td>${file.filename}</td>
                    <td>${file.file_type}</td>
                    <td>${file.size_blocks}</td>
                    <td>${file.size_bytes.toLocaleString()}</td>
                    <td>${file.creation_date}</td>
                    <td>
                        <button onclick="downloadFile('${file.filename}')" style="font-size: 12px; padding: 5px 10px;">💾 Download</button>
                    </td>
                `;
            });
        }
        
        async function downloadFile(filename) {
            if (!currentOperationId) {
                updateStatus('No active operation', 'error');
                return;
            }
            
            try {
                const response = await fetch(`/download/${currentOperationId}/${encodeURIComponent(filename)}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = filename;
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                } else {
                    updateStatus('Download failed', 'error');
                }
            } catch (error) {
                updateStatus('Download error: ' + error.message, 'error');
            }
        }
        
        async function downloadAll() {
            if (!currentOperationId) {
                updateStatus('No active operation', 'error');
                return;
            }
            
            try {
                updateStatus('Creating ZIP archive...', 'info');
                const response = await fetch(`/download_all/${currentOperationId}`);
                
                if (response.ok) {
                    const blob = await response.blob();
                    const url = window.URL.createObjectURL(blob);
                    const a = document.createElement('a');
                    a.href = url;
                    a.download = 'extracted_files.zip';
                    document.body.appendChild(a);
                    a.click();
                    window.URL.revokeObjectURL(url);
                    document.body.removeChild(a);
                    updateStatus('All files downloaded successfully!', 'success');
                } else {
                    updateStatus('Download failed', 'error');
                }
            } catch (error) {
                updateStatus('Download error: ' + error.message, 'error');
            }
        }
    </script>
</body>
</html>
'''


def get_subprocess_kwargs():
    """Get subprocess kwargs for platform compatibility (same as GUI)"""
    kwargs = {
        'capture_output': True,
        'text': True,
        'cwd': str(script_dir)
    }
    
    # Windows-specific: hide console
    if sys.platform == "win32":
        kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW
    
    return kwargs


def get_file_description_with_path(filename, rel_path):
    """Get file type description based on extension and path (for Unix files)"""
    # Check if it's in a Unix system directory
    path_lower = rel_path.lower()
    
    # Unix system directories
    if path_lower.startswith('bin/'):
        return 'Executable (bin)'
    elif path_lower.startswith('etc/'):
        return 'Configuration File'
    elif path_lower.startswith('dev/'):
        return 'Device File'
    elif path_lower.startswith('lib/'):
        return 'Library File'
    elif path_lower.startswith('usr/'):
        return 'User Program'
    elif path_lower.startswith('tmp/'):
        return 'Temporary File'
    elif path_lower.startswith('man/'):
        return 'Manual Page'
    elif path_lower.startswith('doc/'):
        return 'Documentation'
    
    # Extension-based descriptions
    ext = filename.split('.')[-1].upper() if '.' in filename else ''
    descriptions = {
        'SAV': 'Executable Program',
        'SYS': 'System File',
        'TSK': 'Task Image',
        'MAC': 'Macro Source',
        'FOR': 'FORTRAN Source',
        'BAS': 'BASIC Program',
        'TXT': 'Text File',
        'DAT': 'Data File',
        'OBJ': 'Object File',
        'REL': 'Relocatable Object',
        'COM': 'Command File',
        'CMD': 'Command File',
        'OLB': 'Object Library',
        'MLB': 'Macro Library',
        'MAP': 'Map File',
        'LST': 'Listing File',
        'DIR': 'Directory',
        'EXE': 'Executable',
        'SML': 'SML File',
        'FNT': 'Font File',
        'ANS': 'Answer File',
        'BOT': 'Boot File',
        'KED': 'KED File',
        'MM': 'MM File',
        'MS': 'MS File',
        'MT': 'MT File'
    }
    return descriptions.get(ext, f'{ext} File' if ext else 'Unknown Type')


def parse_extracted_files(scan_dir, output, list_result=None):
    """Parse extracted files - exact copy of GUI logic"""
    files = []
    
    # Parse the extraction output to get dates (RT-11 style)
    date_map = {}
    # Parse FILE_INFO lines for ODS-1 format
    ods1_info_map = {}
    
    if output:
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Parse ODS-1 FILE_INFO lines: "FILE_INFO: filename|size_blocks|size_bytes|file_type|creation_date|display_path"
            if "FILE_INFO:" in line:
                try:
                    parts = line.split("FILE_INFO:", 1)
                    if len(parts) == 2:
                        info_str = parts[1].strip()
                        info_parts = info_str.split('|')
                        
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
                            
                except (ValueError, IndexError) as e:
                    continue
            
            # Look for lines that show "Applied date YYYY-MM-DD to FILENAME" (RT-11 style)
            elif "Applied date" in line and " to " in line:
                try:
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
    
    # Parse Unix detailed listing if available (same as GUI)
    unix_info_map = {}
    if list_result and list_result.stdout:
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
            if not parsing_directory_data:
                if 'Full Path' in line and 'Type' in line and 'Size' in line and 'ModTime' in line:
                    parsing_directory_data = True
                continue
            
            if parsing_directory_data and line and not line.startswith('-'):
                try:
                    # Check if this is a valid data line (starts with /)
                    if not line.startswith('/'):
                        continue
                        
                    # Use regex-like parsing for the fixed-width format
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
                        
                except Exception as e:
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
                        break
            
            if ods1_info:
                # Use ODS-1 detailed information
                file_type = ods1_info['file_type']
                creation_date = ods1_info['creation_date']
                # Use ODS-1 reported size ONLY if it's greater than 0, otherwise use actual file size
                # This is critical for TSK files which show size 0 in FILE_INFO but have actual content
                if ods1_info['size_bytes'] > 0:
                    size_blocks = ods1_info['size_blocks']
                    size_bytes = ods1_info['size_bytes']
            else:
                # Check if we have Unix detailed info by trying multiple matches
                parent_dir = rel_path.parent.name if rel_path.parent != Path('.') else ''
                
                unix_info = None
                # Try different matching strategies
                if simple_name in unix_info_map:
                    unix_info = unix_info_map[simple_name]
                elif parent_dir and parent_dir in unix_info_map:
                    # Use parent directory info but mark as file in directory
                    parent_info = unix_info_map[parent_dir]
                    if parent_info['type'] == 'Directory':
                        unix_info = {
                            'type': get_file_description_with_path(simple_name, str(rel_path)),
                            'date': parent_info['date'],
                            'size': size_bytes,
                            'permissions': 'inherited'
                        }
                elif display_name in unix_info_map:
                    unix_info = unix_info_map[display_name]
                
                if unix_info:
                    file_type = unix_info['type']
                    creation_date = unix_info['date']
                else:
                    # Fallback to path-based detection and RT-11 date map
                    file_type = get_file_description_with_path(file_path.name, str(rel_path))
                    creation_date = date_map.get(file_path.name, 'N/A')
            
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
                        break
            
            if ods1_info:
                # Use ODS-1 detailed information for directories
                dir_type = ods1_info['file_type']
                creation_date = ods1_info['creation_date']
            
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
    
    return files


def perform_scan(disk_file: str, operation):
    """Perform the actual scan operation - exact copy of GUI logic"""
    try:
        # Create temporary directory
        temp_dir = Path(tempfile.mkdtemp(prefix="rt11extract_"))
        operation['temp_dir'] = temp_dir
        operation['logs'].append(f"Created temporary directory: {temp_dir}")
        
        # Create temporary directory for list operation
        list_dir = temp_dir / 'list_output'
        list_dir.mkdir(exist_ok=True)
        
        # First, try to get detailed listing for Unix files (using -l -d flags)
        list_result = None
        try:
            if getattr(sys, 'frozen', False):
                # Running as bundled executable
                list_cmd = [str(rt11extract_path), disk_file, '-l', '-d', '-r', '-v']
            else:
                # Running as script
                list_cmd = [sys.executable, str(rt11extract_path), disk_file, '-l', '-d', '-r', '-v']
            
            operation['logs'].append(f"Getting detailed file list: {' '.join(list_cmd)}")
            list_result = subprocess.run(list_cmd, **get_subprocess_kwargs())
            
            if list_result.stdout:
                operation['logs'].append("List output received")
                
        except Exception as e:
            operation['logs'].append(f"Warning: Could not get detailed listing: {e}")
        
        # Then run rt11extract to actually extract files for verification
        scan_dir = temp_dir / 'scan_output'
        scan_dir.mkdir(exist_ok=True)
        operation['output_dir'] = scan_dir
        
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - run rt11extract directly
            cmd = [str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
        else:
            # Running as script - run rt11extract with python
            cmd = [sys.executable, str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
        
        operation['logs'].append(f"Running: {' '.join(cmd)}")
        operation['status'] = "Extracting files..."
        operation['progress'] = 50
        
        result = subprocess.run(cmd, **get_subprocess_kwargs())
        
        if result.stdout:
            operation['logs'].append("Extraction output received")
        
        if result.stderr:
            operation['logs'].append(f"Stderr: {result.stderr}")
        
        if result.returncode == 0:
            operation['status'] = "Parsing extracted files..."
            operation['progress'] = 75
            
            # Parse extracted files with detailed listing info
            files = parse_extracted_files(scan_dir, result.stdout, list_result)
            operation['files'] = files
            operation['logs'].append(f"Found {len(files)} files")
            
            # Detect filesystem type from output
            filesystem_type = "Unknown"
            if "RT-11" in (result.stdout or ""):
                filesystem_type = "RT-11"
            elif "ODS-1" in (result.stdout or "") or "Files-11" in (result.stdout or ""):
                filesystem_type = "RSX-11 (ODS-1)"
            elif "Unix" in (result.stdout or ""):
                filesystem_type = "Unix PDP-11"
            
            # Calculate total size
            total_size = sum(f['size_bytes'] for f in files if f['size_bytes'] > 0)
            
            operation['file_info'] = {
                'filesystem': filesystem_type,
                'file_count': len(files),
                'total_size': f"{total_size:,} bytes"
            }
            
            operation['status'] = f"Scan completed successfully! Found {len(files)} files."
            operation['progress'] = 100
            operation['success'] = True
            operation['completed'] = True
            
        else:
            operation['status'] = f"Extraction failed with return code {result.returncode}"
            operation['error'] = f"rt11extract failed with return code {result.returncode}"
            operation['success'] = False
            operation['completed'] = True
            
    except Exception as e:
        operation['status'] = f"Exception during scan: {str(e)}"
        operation['error'] = str(e)
        operation['success'] = False
        operation['completed'] = True
        operation['logs'].append(f"Exception: {str(e)}")


def create_zip_archive(operation):
    """Create a ZIP archive of all extracted files"""
    if 'output_dir' not in operation or 'files' not in operation:
        return None
    
    output_dir = operation['output_dir']
    zip_path = operation['temp_dir'] / 'extracted_files.zip'
    
    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
        for file_info in operation['files']:
            file_path = file_info['full_path']
            if file_path.is_file():
                # Add file to ZIP with relative path
                arcname = file_info['filename']
                zipf.write(file_path, arcname)
    
    return zip_path


class RequestHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            self.wfile.write(HTML_TEMPLATE.encode())
        elif self.path.startswith('/status/'):
            operation_id = self.path.split('/')[-1]
            self.handle_status(operation_id)
        elif self.path.startswith('/download_all/'):
            operation_id = self.path.split('/')[-1]
            self.handle_download_all(operation_id)
        elif self.path.startswith('/download/'):
            parts = self.path.split('/')
            if len(parts) >= 4:
                operation_id = parts[2]
                filename = urllib.parse.unquote(parts[3])
                self.handle_download_file(operation_id, filename)
            else:
                self.send_error(400, "Invalid download path")
        else:
            self.send_error(404, "File not found")
    
    def do_POST(self):
        if self.path == '/upload':
            self.handle_upload()
        else:
            self.send_error(404, "Endpoint not found")
    
    def handle_upload(self):
        try:
            content_type = self.headers['content-type']
            if not content_type.startswith('multipart/form-data'):
                self.send_error(400, "Invalid content type")
                return
            
            # Parse multipart data
            content_length = int(self.headers['Content-Length'])
            post_data = self.rfile.read(content_length)
            
            # Simple multipart parsing (basic implementation)
            boundary = content_type.split('boundary=')[1].encode()
            parts = post_data.split(b'--' + boundary)
            
            file_data = None
            filename = None
            
            for part in parts:
                if b'Content-Disposition' in part and b'filename=' in part:
                    # Extract filename
                    lines = part.split(b'\r\n')
                    for line in lines:
                        if b'Content-Disposition' in line:
                            filename_part = line.decode().split('filename="')[1].split('"')[0]
                            filename = filename_part
                            break
                    
                    # Extract file data
                    data_start = part.find(b'\r\n\r\n') + 4
                    file_data = part[data_start:]
                    if file_data.endswith(b'\r\n'):
                        file_data = file_data[:-2]
                    break
            
            if not file_data or not filename:
                self.send_error(400, "No file uploaded")
                return
            
            # Create operation
            operation_id = str(uuid.uuid4())
            operation = {
                'id': operation_id,
                'status': 'Uploaded, starting scan...',
                'progress': 25,
                'logs': [f'Uploaded file: {filename}'],
                'completed': False,
                'success': False
            }
            
            current_operations[operation_id] = operation
            
            # Save uploaded file
            temp_dir = Path(tempfile.mkdtemp(prefix="upload_"))
            uploaded_file_path = temp_dir / filename
            
            with open(uploaded_file_path, 'wb') as f:
                f.write(file_data)
            
            operation['uploaded_file'] = uploaded_file_path
            operation['logs'].append(f'File saved to: {uploaded_file_path}')
            
            # Start scanning in background thread
            threading.Thread(target=perform_scan, args=(str(uploaded_file_path), operation), daemon=True).start()
            
            # Return success response
            response = {
                'success': True,
                'operation_id': operation_id,
                'message': 'File uploaded successfully'
            }
            
            self.send_response(200)
            self.send_header('Content-type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response).encode())
            
        except Exception as e:
            self.send_error(500, f"Upload error: {str(e)}")
    
    def handle_status(self, operation_id):
        if operation_id not in current_operations:
            self.send_error(404, "Operation not found")
            return
        
        operation = current_operations[operation_id]
        
        response = {
            'status': operation.get('status', 'Unknown'),
            'progress': operation.get('progress', 0),
            'completed': operation.get('completed', False),
            'success': operation.get('success', False),
            'logs': operation.get('logs', []),
            'error': operation.get('error'),
            'file_info': operation.get('file_info'),
            'files': [{
                'filename': f['filename'],
                'size_blocks': f['size_blocks'],
                'size_bytes': f['size_bytes'],
                'file_type': f['file_type'],
                'creation_date': f['creation_date'],
                'full_path': str(f['full_path'])  # Convert PosixPath to string
            } for f in operation.get('files', [])]
        }
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response).encode())
    
    def handle_download_file(self, operation_id, filename):
        if operation_id not in current_operations:
            self.send_error(404, "Operation not found")
            return
        
        operation = current_operations[operation_id]
        if 'output_dir' not in operation:
            self.send_error(404, "No files available")
            return
        
        # Find the file
        file_path = None
        for file_info in operation.get('files', []):
            if file_info['filename'] == filename:
                file_path = file_info['full_path']
                break
        
        if not file_path or not file_path.exists():
            self.send_error(404, "File not found")
            return
        
        try:
            with open(file_path, 'rb') as f:
                file_data = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/octet-stream')
            self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
            self.send_header('Content-Length', str(len(file_data)))
            self.end_headers()
            self.wfile.write(file_data)
            
        except Exception as e:
            self.send_error(500, f"Download error: {str(e)}")
    
    def handle_download_all(self, operation_id):
        if operation_id not in current_operations:
            self.send_error(404, "Operation not found")
            return
        
        operation = current_operations[operation_id]
        
        try:
            zip_path = create_zip_archive(operation)
            if not zip_path or not zip_path.exists():
                self.send_error(500, "Failed to create ZIP archive")
                return
            
            with open(zip_path, 'rb') as f:
                zip_data = f.read()
            
            self.send_response(200)
            self.send_header('Content-type', 'application/zip')
            self.send_header('Content-Disposition', 'attachment; filename="extracted_files.zip"')
            self.send_header('Content-Length', str(len(zip_data)))
            self.end_headers()
            self.wfile.write(zip_data)
            
        except Exception as e:
            self.send_error(500, f"ZIP creation error: {str(e)}")


def main():
    PORT = 8000
    
    print(f"🖥️ DEC Disk Image Extractor - Web Interface")
    print(f"📊 Supports: RT-11, RSX-11 (ODS-1), Unix PDP-11")
    print(f"🌐 Server starting on http://localhost:{PORT}")
    print(f"🔧 Using extractor: {rt11extract_path}")
    print(f"\n🚀 Open your browser and navigate to: http://localhost:{PORT}")
    print(f"📝 Press Ctrl+C to stop the server\n")
    
    with socketserver.TCPServer(("", PORT), RequestHandler) as httpd:
        try:
            httpd.serve_forever()
        except KeyboardInterrupt:
            print("\n🛑 Server stopped")


if __name__ == "__main__":
    main()

#!/usr/bin/env python3
"""
RT-11 Extract Simple - Replicates GUI logic without FUSE

This script replicates the exact same logic as the GUI rt11extract_gui.py
for scanning disk images and parsing file information, but without FUSE support.
"""

import sys
import os
import tempfile
import subprocess
from pathlib import Path
import shutil
from datetime import datetime

# Add backend path to Python path for imports
script_dir = Path(__file__).parent.parent.parent  # Go up to root from gui/web/
backend_path = script_dir / "backend"
sys.path.insert(0, str(backend_path))

# Use same rt11extract path as GUI
if sys.platform.startswith('win'):
    rt11extract_path = script_dir / "backend" / "extractors" / "RT11Extract.exe"
else:
    rt11extract_path = script_dir / "backend" / "extractors" / "rt11extract"


def get_subprocess_kwargs():
    """Get subprocess kwargs for platform compatibility (same as GUI)"""
    kwargs = {
        'capture_output': True,
        'text': True,
        'cwd': str(script_dir)
    }
    
    # Windows-specific: hide console
    if sys.platform == "win32":
        kwargs['creationflags'] = 0x08000000  # CREATE_NO_WINDOW
    
    return kwargs


def get_file_description_with_path(filename, rel_path):
    """Get file type description based on extension and path (for Unix files)"""
    # Check if it's in a Unix system directory
    path_lower = rel_path.lower()
    
    # Unix system directories
    if path_lower.startswith('bin/'):
        return 'Executable (bin)'
    elif path_lower.startswith('etc/'):
        return 'Configuration File'
    elif path_lower.startswith('dev/'):
        return 'Device File'
    elif path_lower.startswith('lib/'):
        return 'Library File'
    elif path_lower.startswith('usr/'):
        return 'User Program'
    elif path_lower.startswith('tmp/'):
        return 'Temporary File'
    elif path_lower.startswith('man/'):
        return 'Manual Page'
    elif path_lower.startswith('doc/'):
        return 'Documentation'
    
    # Extension-based descriptions
    ext = filename.split('.')[-1].upper() if '.' in filename else ''
    descriptions = {
        'SAV': 'Executable Program',
        'SYS': 'System File',
        'TSK': 'Task Image',
        'MAC': 'Macro Source',
        'FOR': 'FORTRAN Source',
        'BAS': 'BASIC Program',
        'TXT': 'Text File',
        'DAT': 'Data File',
        'OBJ': 'Object File',
        'REL': 'Relocatable Object',
        'COM': 'Command File',
        'CMD': 'Command File',
        'OLB': 'Object Library',
        'MLB': 'Macro Library',
        'MAP': 'Map File',
        'LST': 'Listing File',
        'DIR': 'Directory'
    }
    return descriptions.get(ext, f'{ext} File' if ext else 'Unknown Type')


def parse_extracted_files(scan_dir, output, list_result=None):
    """Parse extracted files - exact copy of GUI logic"""
    files = []
    
    # Parse the extraction output to get dates (RT-11 style)
    date_map = {}
    # Parse FILE_INFO lines for ODS-1 format
    ods1_info_map = {}
    
    if output:
        lines = output.split('\n')
        for line in lines:
            line = line.strip()
            
            # Parse ODS-1 FILE_INFO lines: "FILE_INFO: filename|size_blocks|size_bytes|file_type|creation_date|display_path"
            if "FILE_INFO:" in line:
                try:
                    parts = line.split("FILE_INFO:", 1)
                    if len(parts) == 2:
                        info_str = parts[1].strip()
                        info_parts = info_str.split('|')
                        
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
                            
                            print(f"Parsed ODS-1 info for {filename}: {file_type}, {creation_date}")
                            
                except (ValueError, IndexError) as e:
                    print(f"Could not parse FILE_INFO line: '{line}' - {e}")
                    continue
            
            # Look for lines that show "Applied date YYYY-MM-DD to FILENAME" (RT-11 style)
            elif "Applied date" in line and " to " in line:
                try:
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
                                print(f"Parsed RT-11 date for {filename}: {date_str}")
                except (ValueError, IndexError):
                    continue
    
    # Parse Unix detailed listing if available (same as GUI)
    unix_info_map = {}
    if list_result and list_result.stdout:
        print("Parsing Unix detailed listing...")
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
            if not parsing_directory_data:
                if 'Full Path' in line and 'Type' in line and 'Size' in line and 'ModTime' in line:
                    parsing_directory_data = True
                continue
            
            if parsing_directory_data and line and not line.startswith('-'):
                try:
                    # Check if this is a valid data line (starts with /)
                    if not line.startswith('/'):
                        continue
                        
                    # Use regex-like parsing for the fixed-width format
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
                        
                        print(f"Parsed Unix file: {full_path} ({file_type}, {date_str}, {unix_size} bytes)")
                        
                except Exception as e:
                    print(f"Could not parse Unix listing line: '{line}' - {e}")
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
                        print(f"Matched {simple_name} to ODS-1 file {ods1_filename} (version removed)")
                        break
            
            if ods1_info:
                # Use ODS-1 detailed information
                file_type = ods1_info['file_type']
                creation_date = ods1_info['creation_date']
                # Use ODS-1 reported size ONLY if it's greater than 0, otherwise use actual file size
                # This is critical for TSK files which show size 0 in FILE_INFO but have actual content
                if ods1_info['size_bytes'] > 0:
                    size_blocks = ods1_info['size_blocks']
                    size_bytes = ods1_info['size_bytes']
                print(f"Using ODS-1 info for {display_name}: {file_type}, {creation_date}")
            else:
                # Check if we have Unix detailed info by trying multiple matches
                parent_dir = rel_path.parent.name if rel_path.parent != Path('.') else ''
                
                unix_info = None
                # Try different matching strategies
                if simple_name in unix_info_map:
                    unix_info = unix_info_map[simple_name]
                elif parent_dir and parent_dir in unix_info_map:
                    # Use parent directory info but mark as file in directory
                    parent_info = unix_info_map[parent_dir]
                    if parent_info['type'] == 'Directory':
                        unix_info = {
                            'type': get_file_description_with_path(simple_name, str(rel_path)),
                            'date': parent_info['date'],
                            'size': size_bytes,
                            'permissions': 'inherited'
                        }
                elif display_name in unix_info_map:
                    unix_info = unix_info_map[display_name]
                
                if unix_info:
                    file_type = unix_info['type']
                    creation_date = unix_info['date']
                    print(f"Using Unix info for {display_name}: {file_type}, {creation_date}")
                else:
                    # Fallback to path-based detection and RT-11 date map
                    file_type = get_file_description_with_path(file_path.name, str(rel_path))
                    creation_date = date_map.get(file_path.name, 'N/A')
                    print(f"Using fallback info for {display_name}: {file_type}, {creation_date}")
            
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
                        print(f"Matched directory {simple_name} to ODS-1 directory {ods1_filename}")
                        break
            
            if ods1_info:
                # Use ODS-1 detailed information for directories
                dir_type = ods1_info['file_type']
                creation_date = ods1_info['creation_date']
                print(f"Using ODS-1 info for directory {display_name}: {dir_type}, {creation_date}")
            
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
    
    print(f"Final files count: {len(files)}")
    return files


def perform_scan(disk_file: str):
    """Perform the actual scan operation - exact copy of GUI logic"""
    # Create temporary directory
    temp_dir = Path(tempfile.mkdtemp(prefix="rt11extract_"))
    
    try:
        # Create temporary directory for list operation
        list_dir = temp_dir / 'list_output'
        list_dir.mkdir(exist_ok=True)
        
        # First, try to get detailed listing for Unix files (using -l -d flags)
        list_result = None
        try:
            if getattr(sys, 'frozen', False):
                # Running as bundled executable
                list_cmd = [str(rt11extract_path), disk_file, '-l', '-d', '-r', '-v']
            else:
                # Running as script
                list_cmd = [sys.executable, str(rt11extract_path), disk_file, '-l', '-d', '-r', '-v']
            
            print(f"Getting detailed file list: {' '.join(list_cmd)}")
            list_result = subprocess.run(list_cmd, **get_subprocess_kwargs())
            
            if list_result.stdout:
                print("List STDOUT:")
                for line in list_result.stdout.split('\n'):
                    if line.strip():
                        print(f"  {line}")
        except Exception as e:
            print(f"Warning: Could not get detailed listing: {e}")
        
        # Then run rt11extract to actually extract files for verification
        scan_dir = temp_dir / 'scan_output'
        scan_dir.mkdir(exist_ok=True)
        
        if getattr(sys, 'frozen', False):
            # Running as bundled executable - run rt11extract directly
            cmd = [str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
        else:
            # Running as script - run rt11extract with python
            cmd = [sys.executable, str(rt11extract_path), disk_file, '-o', str(scan_dir), '-v']
        print(f"Running: {' '.join(cmd)}")
        
        result = subprocess.run(cmd, **get_subprocess_kwargs())
        
        if result.stdout:
            print("STDOUT:")
            for line in result.stdout.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.stderr:
            print("STDERR:")
            for line in result.stderr.split('\n'):
                if line.strip():
                    print(f"  {line}")
        
        if result.returncode == 0:
            # Parse extracted files with detailed listing info
            files = parse_extracted_files(scan_dir, result.stdout, list_result)
            print(f"\nScan completed successfully! Found {len(files)} files.")
            
            # Display files in a nice table
            print("\n" + "="*100)
            print(f"{'Filename':<40} {'Type':<25} {'Size (bytes)':<12} {'Date':<12}")
            print("="*100)
            
            for file_info in files:
                filename = file_info['filename'][:39]  # Truncate if too long
                file_type = file_info['file_type'][:24]  # Truncate if too long
                size_bytes = f"{file_info['size_bytes']:,}"
                date = file_info['creation_date']
                print(f"{filename:<40} {file_type:<25} {size_bytes:<12} {date:<12}")
            
            print("="*100)
            print(f"Total: {len(files)} files")
            
            return temp_dir, files
        else:
            print(f"Error: rt11extract failed with return code {result.returncode}")
            return None, None
        
    except Exception as e:
        print(f"Exception during scan: {str(e)}")
        # Cleanup on error
        if temp_dir.exists():
            shutil.rmtree(temp_dir, ignore_errors=True)
        return None, None


def main():
    if len(sys.argv) < 2:
        print("Usage: rt11extract_simple.py <disk_image_path>")
        print("\nSupported formats: RT-11, RSX-11 (ODS-1), Unix PDP-11")
        print("This script replicates the exact logic of the GUI without FUSE support.")
        sys.exit(1)

    disk_image_path = sys.argv[1]

    if not os.path.exists(disk_image_path):
        print(f"Error: File '{disk_image_path}' not found")
        sys.exit(1)
    
    print(f"RT-11 Extract Simple - Processing: {disk_image_path}")
    print(f"Using extractor: {rt11extract_path}")
    print("\nStarting scan...")
    
    temp_dir, files = perform_scan(disk_image_path)
    
    if temp_dir and files:
        print(f"\nAll operations completed. Temporary files are located in: {temp_dir}")
        print("Note: Temporary files contain extracted files for verification.")
    else:
        print("\nScan failed.")
        sys.exit(1)


if __name__ == "__main__":
    main()
