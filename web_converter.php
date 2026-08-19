<?php
// Web-based GIF/MP4 to SCR converter using PHP + JavaScript

// Check if file was uploaded
if ($_SERVER['REQUEST_METHOD'] === 'POST' && isset($_FILES['video_file'])) {
    $upload_dir = 'uploads/';
    if (!file_exists($upload_dir)) {
        mkdir($upload_dir, 0777, true);
    }
    
    $file = $_FILES['video_file'];
    $ext = pathinfo($file['name'], PATHINFO_EXTENSION);
    $input_path = $upload_dir . uniqid() . '.' . $ext;
    
    if (move_uploaded_file($file['tmp_name'], $input_path)) {
        // Process video using Python script
        $output_name = 'screensaver_' . uniqid();
        $command = "python main.py \"$input_path\" -o \"$output_name\" 2>&1";
        $output = shell_exec($command);
        
        // Check if .scr was created
        $scr_file = $output_name . '.scr';
        if (file_exists($scr_file)) {
            // Serve the file
            header('Content-Type: application/octet-stream');
            header('Content-Disposition: attachment; filename="' . $scr_file . '"');
            readfile($scr_file);
            
            // Clean up
            unlink($input_path);
            unlink($scr_file);
            exit;
        } else {
            echo "<pre>Error: $output</pre>";
        }
    }
}
?>

<!DOCTYPE html>
<html>
<head>
    <title>ScreenSaverForge - Web Converter</title>
    <style>
        body {
            font-family: Arial, sans-serif;
            max-width: 600px;
            margin: 50px auto;
            padding: 20px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
        }
        .container {
            background: rgba(255,255,255,0.1);
            padding: 30px;
            border-radius: 10px;
            backdrop-filter: blur(10px);
        }
        h1 { text-align: center; }
        .upload-area {
            border: 2px dashed rgba(255,255,255,0.5);
            padding: 40px;
            text-align: center;
            border-radius: 10px;
            cursor: pointer;
            transition: all 0.3s;
        }
        .upload-area:hover {
            border-color: white;
            background: rgba(255,255,255,0.1);
        }
        input[type="file"] {
            display: none;
        }
        button {
            background: #ff6b6b;
            border: none;
            color: white;
            padding: 15px 30px;
            border-radius: 5px;
            font-size: 18px;
            cursor: pointer;
            margin-top: 20px;
            width: 100%;
            transition: transform 0.2s;
        }
        button:hover {
            transform: scale(1.02);
        }
        #status {
            text-align: center;
            margin-top: 20px;
            padding: 10px;
        }
        .progress-bar {
            width: 0%;
            height: 5px;
            background: #ff6b6b;
            border-radius: 3px;
            transition: width 0.3s;
        }
        .features {
            margin-top: 30px;
            display: grid;
            grid-template-columns: 1fr 1fr;
            gap: 10px;
        }
        .feature-item {
            background: rgba(255,255,255,0.1);
            padding: 10px;
            border-radius: 5px;
            text-align: center;
            font-size: 14px;
        }
    </style>
</head>
<body>
    <div class="container">
        <h1>🎬 ScreenSaverForge</h1>
        <p style="text-align: center;">Convert GIF/MP4 to Windows Screensaver (.scr)</p>
        
        <form id="uploadForm" method="post" enctype="multipart/form-data">
            <div class="upload-area" id="dropZone">
                <div style="font-size: 48px;">📁</div>
                <p>Drop your GIF or MP4 here</p>
                <p style="font-size: 12px;">or click to browse</p>
                <input type="file" name="video_file" id="fileInput" accept=".gif,.mp4,.webm">
            </div>
            
            <div style="margin-top: 20px;">
                <label>FPS: 
                    <input type="number" name="fps" value="10" min="1" max="30" style="width: 60px; padding: 5px;">
                </label>
                <label style="margin-left: 20px;">
                    Max Frames: 
                    <input type="number" name="max_frames" value="200" min="10" max="500" style="width: 70px; padding: 5px;">
                </label>
            </div>
            
            <button type="submit" id="convertBtn">⚡ Convert to .SCR</button>
        </form>
        
        <div id="status">
            <div class="progress-bar" id="progressBar"></div>
            <p id="statusText">Ready to convert!</p>
        </div>
        
        <div class="features">
            <div class="feature-item">🎨 Supports GIF</div>
            <div class="feature-item">🎥 Supports MP4</div>
            <div class="feature-item">⚡ Fast processing</div>
            <div class="feature-item">🖼️ Full screen mode</div>
        </div>
    </div>
    
    <script>
        const dropZone = document.getElementById('dropZone');
        const fileInput = document.getElementById('fileInput');
        const form = document.getElementById('uploadForm');
        const statusText = document.getElementById('statusText');
        const progressBar = document.getElementById('progressBar');
        
        // Drag and drop
        dropZone.addEventListener('dragover', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = '#ff6b6b';
        });
        
        dropZone.addEventListener('dragleave', () => {
            dropZone.style.borderColor = 'rgba(255,255,255,0.5)';
        });
        
        dropZone.addEventListener('drop', (e) => {
            e.preventDefault();
            dropZone.style.borderColor = 'rgba(255,255,255,0.5)';
            const files = e.dataTransfer.files;
            if (files.length > 0) {
                fileInput.files = files;
                statusText.textContent = `Selected: ${files[0].name}`;
            }
        });
        
        dropZone.addEventListener('click', () => {
            fileInput.click();
        });
        
        fileInput.addEventListener('change', () => {
            if (fileInput.files.length > 0) {
                statusText.textContent = `Selected: ${fileInput.files[0].name}`;
            }
        });
        
        form.addEventListener('submit', (e) => {
            // Show progress
            progressBar.style.width = '50%';
            statusText.textContent = 'Processing... This may take a moment.';
            
            // Auto download will happen via PHP
        });
        
        // Check for conversion status
        const urlParams = new URLSearchParams(window.location.search);
        if (urlParams.get('status') === 'success') {
            statusText.textContent = '✅ Conversion complete! File downloading...';
            progressBar.style.width = '100%';
        } else if (urlParams.get('status') === 'error') {
            statusText.textContent = '❌ Error during conversion. Please try again.';
            progressBar.style.width = '0%';
        }
    </script>
</body>
</html>