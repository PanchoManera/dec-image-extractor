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
from imd2raw import IMDConverter, DiskImageValidator

# Global variables
current_operations = {}
script_dir = Path(__file__).parent
rt11extract_path = script_dir / "rt11extract"

# HTML Template
HTML_TEMPLATE = '''<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>RT-11 Extract GUI</title>
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
        <h1><img src="https://www.logo.wine/a/logo/Digital_Equipment_Corporation/Digital_Equipment_Corporation-Logo.wine.svg" alt="DEC" style="height: 2.5em; vertical-align: middle; margin-right: 12px;"> RT-11 Extract GUI</h1>
        
        <!-- Upload Section -->
        <div class="upload-section">
            <h3>Select RT-11 Disk Image (.dsk, .imd, .raw, .img)</h3>
            <form id="uploadForm">
                <input type="file" id="fileInput" accept=".dsk,.imd,.raw,.img" required>
                <br>
                <button type="submit">📁 Upload & Scan</button>
                <button type="button" onclick="clearAll()">🗑️ Clear</button>
            </form>
        </div>

        <!-- Status Section -->
        <div id="statusSection"></div>
        
        <!-- Progress Bar -->
        <div class="progress-bar" id="progressBar">
            <div class="progress-fill" id="progressFill"></div>
        </div>

        <!-- File Info -->
        <div id="fileInfo" class="file-info hidden">
            <h4>📂 Current File: <span id="currentFileName"></span></h4>
            <p>💾 Size: <span id="currentFileSize"></span></p>
        </div>

        <!-- Files Table -->
        <div id="filesSection" class="hidden">
            <h3>📋 Files in RT-11 Image</h3>
            
            <!-- Action Buttons - Top -->
            <div style="margin-bottom: 15px;">
                <button onclick="extractFiles()" id="extractBtnTop" class="success">
                    📦 Extract All Files
                </button>
                <button onclick="downloadFiles()" id="downloadBtnTop" class="success hidden">
                    ⬇️ Download Extracted Files
                </button>
            </div>
            
            <table class="files-table">
                <thead>
                    <tr>
                        <th>Filename</th>
                        <th>Size (Blocks)</th>
                        <th>Size (Bytes)</th>
                        <th>Type</th>
                        <th>Date</th>
                        <th>Download</th>
                    </tr>
                </thead>
                <tbody id="filesTableBody">
                </tbody>
            </table>
            
            <!-- Action Buttons - Bottom -->
            <div style="margin-top: 15px;">
                <button onclick="extractFiles()" id="extractBtn" class="success">
                    📦 Extract All Files
                </button>
                <button onclick="downloadFiles()" id="downloadBtn" class="success hidden">
                    ⬇️ Download Extracted Files
                </button>
            </div>
        </div>

        <!-- Log Section -->
        <div class="log-section" id="logSection">
            <div id="logContent"></div>
        </div>
        
        <button onclick="toggleLog()" id="logToggle" class="hidden">📋 Toggle Log</button>
    </div>

    <script>
        let currentOperationId = null;
        let currentExtractOperationId = null;
        let files = [];

        function showStatus(message, type = 'info') {
            const statusSection = document.getElementById('statusSection');
            statusSection.innerHTML = `<div class="status ${type}">${message}</div>`;
        }

        function showProgress(show = true) {
            const progressBar = document.getElementById('progressBar');
            if (show) {
                progressBar.classList.add('show');
            } else {
                progressBar.classList.remove('show');
            }
        }

        function updateProgress(percent) {
            const progressFill = document.getElementById('progressFill');
            progressFill.style.width = percent + '%';
        }

        function addLog(message) {
            const logContent = document.getElementById('logContent');
            const logSection = document.getElementById('logSection');
            const logToggle = document.getElementById('logToggle');
            
            logContent.innerHTML += message + '\\n';
            logContent.scrollTop = logContent.scrollHeight;
            
            logSection.classList.add('show');
            logToggle.classList.remove('hidden');
        }

        function toggleLog() {
            const logSection = document.getElementById('logSection');
            logSection.style.display = logSection.style.display === 'none' ? 'block' : 'none';
        }

        function clearAll() {
            document.getElementById('fileInput').value = '';
            document.getElementById('statusSection').innerHTML = '';
            document.getElementById('filesSection').classList.add('hidden');
            document.getElementById('fileInfo').classList.add('hidden');
            document.getElementById('logSection').classList.remove('show');
            document.getElementById('logToggle').classList.add('hidden');
            document.getElementById('downloadBtn').classList.add('hidden');
            document.getElementById('downloadBtnTop').classList.add('hidden');
            document.getElementById('logContent').innerHTML = '';
            showProgress(false);
            files = [];
            currentOperationId = null;
            currentExtractOperationId = null;
        }

        function updateFileInfo(filename, size) {
            document.getElementById('currentFileName').textContent = filename;
            document.getElementById('currentFileSize').textContent = formatFileSize(size);
            document.getElementById('fileInfo').classList.remove('hidden');
        }

        function formatFileSize(bytes) {
            if (bytes === 0) return '0 Bytes';
            const k = 1024;
            const sizes = ['Bytes', 'KB', 'MB', 'GB'];
            const i = Math.floor(Math.log(bytes) / Math.log(k));
            return parseFloat((bytes / Math.pow(k, i)).toFixed(2)) + ' ' + sizes[i];
        }

        function fileToBase64(file) {
            return new Promise((resolve, reject) => {
                const reader = new FileReader();
                reader.readAsDataURL(file);
                reader.onload = () => resolve(reader.result.split(',')[1]);
                reader.onerror = error => reject(error);
            });
        }

        document.getElementById('uploadForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            
            const fileInput = document.getElementById('fileInput');
            const file = fileInput.files[0];
            
            if (!file) {
                showStatus('Please select a file', 'error');
                return;
            }

            const validExtensions = ['.dsk', '.imd', '.raw', '.img'];
            const fileExt = file.name.toLowerCase();
            const isValidFile = validExtensions.some(ext => fileExt.endsWith(ext));
            
            if (!isValidFile) {
                showStatus('Please select a disk image file (.dsk, .imd, .raw, .img)', 'error');
                return;
            }

            try {
                const isIMD = fileExt.endsWith('.imd');
                if (isIMD) {
                    showStatus('<span class="spinner"></span>Uploading IMD file and converting to DSK...', 'info');
                } else {
                    showStatus('<span class="spinner"></span>Uploading and scanning file...', 'info');
                }
                showProgress(true);
                updateProgress(0);
                updateFileInfo(file.name, file.size);

                // Convert file to base64
                const base64Data = await fileToBase64(file);

                const response = await fetch('/scan', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        filename: file.name,
                        data: base64Data
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    currentOperationId = result.operation_id;
                    pollOperation(currentOperationId, 'scan');
                } else {
                    showStatus('Error: ' + result.error, 'error');
                    showProgress(false);
                }
            } catch (error) {
                showStatus('Upload failed: ' + error.message, 'error');
                showProgress(false);
            }
        });

        async function pollOperation(operationId, operationType) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/status?operation_id=${operationId}`);
                    const status = await response.json();
                    
                    if (status.logs) {
                        status.logs.forEach(log => addLog(log));
                    }
                    
                    updateProgress(status.progress || 0);
                    
                    if (status.completed) {
                        clearInterval(interval);
                        showProgress(false);
                        
                        if (status.success) {
                            if (operationType === 'scan') {
                                showStatus(`Scan completed! Found ${status.files.length} files`, 'success');
                                displayFiles(status.files);
                            } else if (operationType === 'extract') {
                                showStatus('Extraction completed successfully!', 'success');
                                document.getElementById('downloadBtn').classList.remove('hidden');
                                document.getElementById('downloadBtnTop').classList.remove('hidden');
                            }
                        } else {
                            showStatus('Operation failed: ' + status.error, 'error');
                        }
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 1000);
        }

        function displayFiles(filesData) {
            files = filesData;
            const tbody = document.getElementById('filesTableBody');
            tbody.innerHTML = '';
            
            files.forEach((file, index) => {
                const row = tbody.insertRow();
                row.insertCell(0).textContent = file.filename;
                row.insertCell(1).textContent = file.size_blocks;
                row.insertCell(2).textContent = file.size_bytes.toLocaleString();
                row.insertCell(3).textContent = file.file_type;
                row.insertCell(4).textContent = file.creation_date || 'N/A';
                
                // Add download button cell
                const downloadCell = row.insertCell(5);
                const downloadBtn = document.createElement('button');
                downloadBtn.innerHTML = '⬇️';
                downloadBtn.title = `Download ${file.filename}`;
                downloadBtn.style.cssText = 'padding: 5px 10px; background: #28a745; color: white; border: none; border-radius: 3px; cursor: pointer; font-size: 16px;';
                downloadBtn.onclick = () => downloadIndividualFile(index, file.filename);
                downloadCell.appendChild(downloadBtn);
            });
            
            document.getElementById('filesSection').classList.remove('hidden');
        }
        
        async function downloadIndividualFile(fileIndex, filename) {
            // If files haven't been extracted yet, do it automatically
            if (!currentExtractOperationId) {
                showStatus(`⚡ Auto-extracting files to download ${filename}...`, 'info');
                
                try {
                    // Start extraction first
                    const response = await fetch('/extract', {
                        method: 'POST',
                        headers: {
                            'Content-Type': 'application/json'
                        },
                        body: JSON.stringify({
                            operation_id: currentOperationId
                        })
                    });
                    
                    const result = await response.json();
                    
                    if (result.success) {
                        currentExtractOperationId = result.operation_id;
                        
                        // Wait for extraction to complete, then download
                        waitForExtractionThenDownload(result.operation_id, filename);
                    } else {
                        showStatus('Auto-extraction failed: ' + result.error, 'error');
                    }
                } catch (error) {
                    showStatus('Auto-extraction failed: ' + error.message, 'error');
                }
                return;
            }
            
            // Files already extracted, download directly
            try {
                // Use browser download for all cases
                window.location.href = `/download_single?operation_id=${currentExtractOperationId}&filename=${encodeURIComponent(filename)}`;
                showStatus(`Downloading ${filename} - check your downloads folder`, 'success');
            } catch (error) {
                showStatus(`Download failed: ${error.message}`, 'error');
            }
        }
        
        async function waitForExtractionThenDownload(operationId, filename) {
            const interval = setInterval(async () => {
                try {
                    const response = await fetch(`/status?operation_id=${operationId}`);
                    const status = await response.json();
                    
                    if (status.completed) {
                        clearInterval(interval);
                        
                        if (status.success) {
                            // Update UI to show extraction completed
                            document.getElementById('downloadBtn').classList.remove('hidden');
                            document.getElementById('downloadBtnTop').classList.remove('hidden');
                            
                            // Now download the individual file
                            window.location.href = `/download_single?operation_id=${operationId}&filename=${encodeURIComponent(filename)}`;
                            showStatus(`✅ Files extracted! Downloading ${filename} - check your downloads folder`, 'success');
                        } else {
                            showStatus('Auto-extraction failed: ' + status.error, 'error');
                        }
                    }
                } catch (error) {
                    console.error('Polling error:', error);
                }
            }, 1000);
        }

        async function extractFiles() {
            if (!currentOperationId) {
                showStatus('No file scanned yet', 'error');
                return;
            }

            try {
                showStatus('<span class="spinner"></span>Extracting files...', 'info');
                showProgress(true);
                updateProgress(0);

                const response = await fetch('/extract', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json'
                    },
                    body: JSON.stringify({
                        operation_id: currentOperationId
                    })
                });

                const result = await response.json();
                
                if (result.success) {
                    currentExtractOperationId = result.operation_id;
                    pollOperation(result.operation_id, 'extract');
                } else {
                    showStatus('Extraction failed: ' + result.error, 'error');
                    showProgress(false);
                }
            } catch (error) {
                showStatus('Extraction failed: ' + error.message, 'error');
                showProgress(false);
            }
        }

        async function downloadFiles() {
            if (!currentExtractOperationId) {
                showStatus('No files to download', 'error');
                return;
            }

            try {
                // Use browser download for all cases
                window.location.href = `/download?operation_id=${currentExtractOperationId}`;
                showStatus('Download started - check your downloads folder', 'success');
            } catch (error) {
                showStatus('Download failed: ' + error.message, 'error');
            }
        }
    </script>
</body>
</html>'''

class RT11ExtractHandler(http.server.SimpleHTTPRequestHandler):
    def do_GET(self):
        if self.path == '/':
            self.send_response(200)
            self.send_header('Content-type', 'text/html')
            self.end_headers()
            
            # Check if rt11extract exists
            if not rt11extract_path.exists():
                error_html = f'''
                <div style="text-align: center; padding: 50px; font-family: Arial;">
                    <h1 style="color: red;">❌ Error</h1>
                    <p><strong>rt11extract not found at:</strong> {rt11extract_path}</p>
                    <p>Please ensure rt11extract is in the same directory as this script.</p>
                </div>
                '''
                self.wfile.write(error_html.encode())
            else:
                self.wfile.write(HTML_TEMPLATE.encode())
                
        elif self.path.startswith('/status?'):
            # Parse query parameters
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            operation_id = query.get('operation_id', [None])[0]
            
            if operation_id and operation_id in current_operations:
                operation = current_operations[operation_id]
                logs = operation['logs'][-10:]  # Get last 10 log entries
                
                response_data = {
                    'status': operation['status'],
                    'progress': operation['progress'],
                    'logs': logs,
                    'files': operation['files'],
                    'completed': operation['completed'],
                    'success': operation['success'],
                    'error': operation['error']
                }
                
                self.send_response(200)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps(response_data).encode())
            else:
                self.send_response(404)
                self.send_header('Content-type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({'error': 'Operation not found'}).encode())
                
        elif self.path.startswith('/download_single?'):
            # Parse query parameters for single file download
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            operation_id = query.get('operation_id', [None])[0]
            filename = query.get('filename', [None])[0]
            
            if operation_id and operation_id in current_operations and filename:
                operation = current_operations[operation_id]
                
                if operation.get('success') and 'output_dir' in operation:
                    # Find the requested file
                    file_path = operation['output_dir'] / filename
                    
                    if file_path.exists() and file_path.is_file():
                        # Send individual file
                        self.send_response(200)
                        self.send_header('Content-type', 'application/octet-stream')
                        self.send_header('Content-Disposition', f'attachment; filename="{filename}"')
                        self.end_headers()
                        
                        with open(file_path, 'rb') as f:
                            self.wfile.write(f.read())
                    else:
                        self.send_response(404)
                        self.send_header('Content-type', 'text/plain')
                        self.end_headers()
                        self.wfile.write(b'File not found')
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'No files extracted')
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Invalid request')
                
        elif self.path.startswith('/download?'):
            # Parse query parameters
            query = urllib.parse.parse_qs(self.path.split('?')[1])
            operation_id = query.get('operation_id', [None])[0]
            
            if operation_id and operation_id in current_operations:
                operation = current_operations[operation_id]
                
                if operation.get('success') and 'output_dir' in operation:
                    # Create ZIP file
                    zip_path = operation['temp_dir'] / 'extracted_files.zip'
                    
                    with zipfile.ZipFile(zip_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        for file_path in operation['output_dir'].rglob('*'):
                            if file_path.is_file():
                                arcname = file_path.relative_to(operation['output_dir'])
                                zipf.write(file_path, arcname)
                    
                    # Send file
                    self.send_response(200)
                    self.send_header('Content-type', 'application/zip')
                    self.send_header('Content-Disposition', 'attachment; filename="extracted_rt11_files.zip"')
                    self.end_headers()
                    
                    with open(zip_path, 'rb') as f:
                        self.wfile.write(f.read())
                else:
                    self.send_response(404)
                    self.send_header('Content-type', 'text/plain')
                    self.end_headers()
                    self.wfile.write(b'No files to download')
            else:
                self.send_response(404)
                self.send_header('Content-type', 'text/plain')
                self.end_headers()
                self.wfile.write(b'Operation not found')
        else:
            self.send_response(404)
            self.send_header('Content-type', 'text/plain')
            self.end_headers()
            self.wfile.write(b'Not found')

    def do_POST(self):
        content_length = int(self.headers['Content-Length'])
        post_data = self.rfile.read(content_length)
        
        if self.path == '/scan':
            try:
                data = json.loads(post_data.decode())
                filename = data['filename']
                file_data = base64.b64decode(data['data'])
                
                # Create operation ID
                operation_id = str(uuid.uuid4())
                
                # Create temporary directory for this operation
                temp_dir = Path(tempfile.gettempdir()) / f"rt11extract_{operation_id}"
                temp_dir.mkdir(exist_ok=True)
                
                # Save uploaded file
                dsk_path = temp_dir / filename
                with open(dsk_path, 'wb') as f:
                    f.write(file_data)
                
                # Create operation data
                current_operations[operation_id] = {
                    'status': 'running',
                    'progress': 0,
                    'logs': [],
                    'files': [],
                    'temp_dir': temp_dir,
                    'dsk_path': dsk_path,
                    'completed': False,
                    'success': False,
                    'error': None
                }
                
                # Start scanning in background thread
                threading.Thread(target=scan_files_thread, args=(operation_id,), daemon=True).start()
                
                response_data = {'success': True, 'operation_id': operation_id}
                
            except Exception as e:
                response_data = {'success': False, 'error': str(e)}
                
        elif self.path == '/extract':
            try:
                data = json.loads(post_data.decode())
                operation_id = data.get('operation_id')
                
                if operation_id not in current_operations:
                    response_data = {'success': False, 'error': 'Invalid operation ID'}
                else:
                    # Create new operation for extraction
                    extract_operation_id = str(uuid.uuid4())
                    
                    # Copy operation data
                    original_op = current_operations[operation_id]
                    current_operations[extract_operation_id] = {
                        'status': 'running',
                        'progress': 0,
                        'logs': [],
                        'files': original_op['files'],
                        'temp_dir': original_op['temp_dir'],
                        'dsk_path': original_op['dsk_path'],
                        'completed': False,
                        'success': False,
                        'error': None
                    }
                    
                    # Start extraction in background thread
                    threading.Thread(target=extract_files_thread, args=(extract_operation_id,), daemon=True).start()
                    
                    response_data = {'success': True, 'operation_id': extract_operation_id}
                    
            except Exception as e:
                response_data = {'success': False, 'error': str(e)}
        else:
            response_data = {'success': False, 'error': 'Invalid endpoint'}
        
        self.send_response(200)
        self.send_header('Content-type', 'application/json')
        self.end_headers()
        self.wfile.write(json.dumps(response_data).encode())

def scan_files_thread(operation_id):
    """Background thread for scanning files"""
    try:
        operation = current_operations[operation_id]
        
        # Check if we need to convert IMD first
        dsk_path = operation['dsk_path']
        original_path = dsk_path
        
        format_type = DiskImageValidator.get_disk_format(str(dsk_path))
        
        if format_type == "IMD":
            operation['logs'].append("Detected ImageDisk (IMD) format - converting to DSK...")
            operation['progress'] = 5
            
            # Create converted DSK filename
            converted_dsk = operation['temp_dir'] / (dsk_path.stem + "_converted.dsk")
            
            # Perform IMD conversion
            converter = IMDConverter(str(dsk_path), str(converted_dsk), verbose=False)
            success = converter.convert()
            
            if not success:
                operation['error'] = "Failed to convert IMD file to DSK format"
                operation['logs'].append(f"Error: {operation['error']}")
                operation['completed'] = True
                operation['progress'] = 100
                return
                
            operation['logs'].append("IMD conversion completed successfully!")
            operation['logs'].append(f"Converted: {dsk_path.name} -> {converted_dsk.name}")
            
            # Update the path to use converted file
            dsk_path = converted_dsk
            operation['dsk_path'] = dsk_path
            operation['progress'] = 10
        
        operation['logs'].append("Starting RT-11 scan...")
        operation['progress'] = 15
        
        # Create output directory for scanning
        scan_dir = operation['temp_dir'] / 'scan_output'
        scan_dir.mkdir(exist_ok=True)
        
        # First run rt11extract in list mode to get file info with dates
        cmd_list = [str(rt11extract_path), str(operation['dsk_path']), '-l']
        operation['logs'].append(f"Running list command: {' '.join(cmd_list)}")
        operation['progress'] = 20
        
        list_result = subprocess.run(
            cmd_list,
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        operation['progress'] = 40
        
        # Then run rt11extract to actually extract files (for size verification)
        cmd = [str(rt11extract_path), str(operation['dsk_path']), '-o', str(scan_dir), '-v']
        operation['logs'].append(f"Running extract command: {' '.join(cmd)}")
        operation['progress'] = 50
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        operation['progress'] = 60
        
        if result.stdout:
            operation['logs'].append("STDOUT:")
            operation['logs'].extend(result.stdout.split('\n'))
        
        if result.stderr:
            operation['logs'].append("STDERR:")
            operation['logs'].extend(result.stderr.split('\n'))
        
        operation['progress'] = 80
        
        if result.returncode == 0:
            # Parse extracted files (use list output for dates)
            files = parse_extracted_files(scan_dir, result.stdout, list_result.stdout)
            operation['files'] = files
            operation['success'] = True
            operation['logs'].append(f"Scan completed successfully! Found {len(files)} files.")
        else:
            operation['error'] = f"rt11extract failed with return code {result.returncode}"
            operation['logs'].append(f"Error: {operation['error']}")
        
        operation['progress'] = 100
        operation['completed'] = True
        
    except Exception as e:
        operation = current_operations[operation_id]
        operation['error'] = str(e)
        operation['logs'].append(f"Exception: {str(e)}")
        operation['completed'] = True
        operation['progress'] = 100

def extract_files_thread(operation_id):
    """Background thread for extracting files"""
    try:
        operation = current_operations[operation_id]
        operation['logs'].append("Starting file extraction...")
        operation['progress'] = 10
        
        # Create final output directory
        output_dir = operation['temp_dir'] / 'extracted_files'
        output_dir.mkdir(exist_ok=True)
        
        # Run rt11extract for final extraction with new syntax
        cmd = [str(rt11extract_path), str(operation['dsk_path']), '-o', str(output_dir), '-v']
        operation['logs'].append(f"Running: {' '.join(cmd)}")
        operation['progress'] = 20
        
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            cwd=script_dir
        )
        
        operation['progress'] = 80
        
        if result.stdout:
            operation['logs'].append("STDOUT:")
            operation['logs'].extend(result.stdout.split('\n'))
        
        if result.stderr:
            operation['logs'].append("STDERR:")
            operation['logs'].extend(result.stderr.split('\n'))
        
        if result.returncode == 0:
            operation['success'] = True
            operation['logs'].append("Extraction completed successfully!")
            operation['output_dir'] = output_dir
            
            # Apply original RT-11 dates to extracted files
            apply_rt11_dates(operation)
        else:
            operation['error'] = f"rt11extract failed with return code {result.returncode}"
            operation['logs'].append(f"Error: {operation['error']}")
        
        operation['progress'] = 100
        operation['completed'] = True
        
    except Exception as e:
        operation = current_operations[operation_id]
        operation['error'] = str(e)
        operation['logs'].append(f"Exception: {str(e)}")
        operation['completed'] = True
        operation['progress'] = 100

def parse_extracted_files(scan_dir, output, list_output=None):
    """Parse extracted files to get file information with dates from list output"""
    files = []
    
    # First parse the list output to get dates
    date_map = {}
    if list_output:
        lines = list_output.split('\n')
        for line in lines:
            line = line.strip()
            # Look for lines with filename, type, size, status, date
            # Example: "CAT.SAV              permanent 25         permanent       1993-02-26"
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
            file_type = get_file_description(file_path.name)
            
            # Get creation date from list output
            creation_date = date_map.get(file_path.name, 'N/A')
            
            files.append({
                'filename': file_path.name,
                'size_blocks': size_blocks,
                'size_bytes': size_bytes,
                'file_type': file_type,
                'creation_date': creation_date
            })
    
    # Also try to parse from output for additional info
    lines = output.split('\n')
    for line in lines:
        line = line.strip()
        if "File:" in line and "blks" in line:
            try:
                parts = line.split("File:")
                if len(parts) >= 2:
                    file_part = parts[1].strip()
                    if "(" in file_part:
                        filename = file_part.split("(")[0].strip()
                        details = file_part.split("(")[1].split(")")[0]
                        
                        if "blks" in details:
                            blocks_str = details.split("blks")[0].strip()
                            size_blocks = int(blocks_str)
                            size_bytes = size_blocks * 512
                            
                            file_type = get_file_description(filename)
                            if "tentative" in details:
                                file_type = "Tentative " + file_type
                            elif "protected" in details:
                                file_type = "Protected " + file_type
                            
                            # Update existing file or add new one
                            existing_file = next((f for f in files if f['filename'] == filename), None)
                            if existing_file:
                                existing_file['size_blocks'] = size_blocks
                                existing_file['size_bytes'] = size_bytes
                                existing_file['file_type'] = file_type
                            else:
                                files.append({
                                    'filename': filename,
                                    'size_blocks': size_blocks,
                                    'size_bytes': size_bytes,
                                    'file_type': file_type,
                                    'creation_date': 'N/A'
                                })
            except (ValueError, IndexError):
                pass
    
    return files

def parse_rt11_listing(output):
    """Parse rt11extract output to extract file information"""
    lines = output.split('\n')
    files = []
    in_file_listing = False
    
    # Look for the formatted table output from the enhanced rt11extract
    for i, line in enumerate(lines):
        line = line.strip()
        
        # Detect start of file listing table (after a header line with dashes)
        if line.startswith('----------') and i > 0:
            # Check if previous line looks like a header
            prev_line = lines[i-1].strip() if i > 0 else ""
            if "Filename" in prev_line or "Name" in prev_line:
                in_file_listing = True
                continue
        
        # Detect end of file listing
        elif (line.startswith('----------') or line.startswith('Summary:') or 
              line.startswith('Total Files:') or line.startswith('By File Type:')) and in_file_listing:
            in_file_listing = False
            break
        
        # Parse file listing lines from the table
        elif in_file_listing and line and not line.startswith('-'):
            try:
                # Enhanced rt11extract produces lines like:
                # "FILENAME.EXT        TYPE     Size(KB)   STATUS         Category Description"
                # We need to parse this carefully as fields can have spaces
                
                parts = line.split()
                if len(parts) >= 4:
                    filename = parts[0]
                    file_ext = parts[1]
                    size_kb = int(parts[2])
                    status = parts[3]
                    
                    # The rest is file type description (may have spaces)
                    file_description = " ".join(parts[4:]) if len(parts) > 4 else get_file_description(filename)
                    
                    # Map RT-11 status to readable type
                    file_type = map_rt11_status(status)
                    
                    # Convert KB to blocks and bytes
                    if size_kb == 0:
                        size_blocks = 0
                        size_bytes = 0
                    else:
                        # Convert KB to bytes and blocks
                        size_bytes = size_kb * 1024
                        size_blocks = (size_bytes + 511) // 512  # Round up to nearest block
                    
                    creation_date = "N/A"  # RT-11 doesn't typically store creation dates
                    
                    file_info = {
                        'filename': filename,
                        'size_blocks': size_blocks,
                        'size_bytes': size_bytes,
                        'file_type': file_description,  # Use description as the type
                        'creation_date': creation_date,
                        'description': file_description
                    }
                    
                    # Check if we already have this file
                    if not any(f['filename'] == filename for f in files):
                        files.append(file_info)
                    
            except (ValueError, IndexError) as e:
                # Log parsing errors but continue
                pass
    
    return files

def map_rt11_status(status):
    """Map RT-11 status flags to readable types"""
    status_map = {
        'NORMAL': 'Normal',
        'TENTATIVE': 'Tentative', 
        'PERMANENT': 'Permanent',
        'PROTECTED': 'Protected',
        'EMPTY': 'Empty'
    }
    return status_map.get(status.upper(), status)

def get_file_description(filename):
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

def apply_rt11_dates(operation):
    """Apply original RT-11 creation dates to extracted files"""
    try:
        from datetime import datetime
        import os
        
        output_dir = operation.get('output_dir')
        files_info = operation.get('files', [])
        
        if not output_dir or not files_info:
            return
            
        operation['logs'].append("Applying original RT-11 dates to extracted files...")
        
        # Create a mapping of filename to date
        date_map = {}
        for file_info in files_info:
            filename = file_info.get('filename')
            creation_date = file_info.get('creation_date')
            
            if filename and creation_date and creation_date != 'N/A':
                try:
                    # Parse date string (format: YYYY-MM-DD)
                    date_obj = datetime.strptime(creation_date, '%Y-%m-%d')
                    # Convert to timestamp
                    timestamp = date_obj.timestamp()
                    date_map[filename] = timestamp
                except ValueError:
                    # Skip invalid dates
                    continue
        
        # Apply dates to extracted files
        applied_count = 0
        for file_path in output_dir.rglob('*'):
            if file_path.is_file() and not file_path.name.endswith('.rt11info'):
                filename = file_path.name
                
                if filename in date_map:
                    try:
                        timestamp = date_map[filename]
                        # Set both access and modification times
                        os.utime(file_path, (timestamp, timestamp))
                        applied_count += 1
                        operation['logs'].append(f"  Applied date {datetime.fromtimestamp(timestamp).strftime('%Y-%m-%d')} to {filename}")
                    except Exception as e:
                        operation['logs'].append(f"  Warning: Could not set date for {filename}: {e}")
        
        operation['logs'].append(f"Applied original dates to {applied_count} files")
        
    except Exception as e:
        operation['logs'].append(f"Error applying RT-11 dates: {e}")

def cleanup_old_operations():
    """Clean up old operations periodically"""
    while True:
        time.sleep(300)  # Check every 5 minutes
        cutoff_time = time.time() - 3600  # 1 hour ago
        
        to_remove = []
        for op_id, operation in current_operations.items():
            if operation.get('completed'):
                # Simple cleanup after 1 hour
                if len(current_operations) > 10:  # Keep max 10 operations
                    if 'temp_dir' in operation:
                        try:
                            shutil.rmtree(operation['temp_dir'])
                        except:
                            pass
                    to_remove.append(op_id)
        
        # Remove oldest operations if too many
        if len(to_remove) > 0:
            for op_id in to_remove[:5]:  # Remove up to 5 old operations
                if op_id in current_operations:
                    del current_operations[op_id]

def main():
    # Check if rt11extract exists
    if not rt11extract_path.exists():
        print(f"Error: rt11extract not found at: {rt11extract_path}")
        print("Please ensure rt11extract is in the same directory as this script.")
        sys.exit(1)
    
    # Start cleanup thread
    threading.Thread(target=cleanup_old_operations, daemon=True).start()
    
    # Get port from environment (for hosting platforms) or default
    PORT = int(os.environ.get('PORT', 8000))
    HOST = os.environ.get('HOST', '0.0.0.0')  # Listen on all interfaces for hosting
    
    print("🚀 Starting RT-11 Extract Web Interface...")
    print(f"📱 Server running on: http://{HOST}:{PORT}")
    if HOST == '0.0.0.0':
        print(f"📱 Local access: http://localhost:{PORT}")
    print("🛑 Press Ctrl+C to stop the server")
    
    try:
        with socketserver.TCPServer((HOST, PORT), RT11ExtractHandler) as httpd:
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n🛑 Server stopped")
    except OSError as e:
        if 'Address already in use' in str(e):
            print(f"❌ Port {PORT} is already in use")
            print("Try setting a different PORT environment variable")
        else:
            raise

if __name__ == '__main__':
    main()
