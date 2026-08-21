document.addEventListener('DOMContentLoaded', function() {
    const dropZone = document.getElementById('dropZone');
    const fileInput = document.getElementById('fileInput');
    const convertBtn = document.getElementById('convertBtn');
    const statusSection = document.getElementById('statusSection');
    const statusMessage = document.getElementById('statusMessage');
    const progressBar = document.getElementById('progressBar');
    const resultSection = document.getElementById('resultSection');
    const fileName = document.getElementById('fileName');
    const fileSize = document.getElementById('fileSize');
    const downloadBtn = document.getElementById('downloadBtn');
    const installInstructions = document.getElementById('installInstructions');
    
    let selectedFile = null;
    let directDownloadUrl = null;

    // Trigger file selection dialog safely
    dropZone.addEventListener('click', (e) => {
        if (e.target !== fileInput) {
            fileInput.click();
        }
    });
    
    // Drag & Drop handlers
    dropZone.addEventListener('dragover', (e) => {
        e.preventDefault();
        dropZone.classList.add('dragover');
    });
    
    dropZone.addEventListener('dragleave', () => {
        dropZone.classList.remove('dragover');
    });
    
    dropZone.addEventListener('drop', (e) => {
        e.preventDefault();
        dropZone.classList.remove('dragover');
        if (e.dataTransfer.files && e.dataTransfer.files.length > 0) {
            handleFile(e.dataTransfer.files[0]);
        }
    });
    
    fileInput.addEventListener('change', (e) => {
        if (e.target.files && e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    function handleFile(file) {
        const ext = file.name.split('.').pop().toLowerCase();
        const allowedExt = ['gif', 'mp4', 'webm', 'avi', 'mov'];
        
        if (!allowedExt.includes(ext)) {
            alert('Please upload a valid GIF or MP4/video file.');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            alert('File is too large. Maximum allowed size is 50MB.');
            return;
        }
        
        selectedFile = file;
        convertBtn.disabled = false;
        
        const titleText = dropZone.querySelector('p');
        const subText = dropZone.querySelector('.sub-text');
        if (titleText) titleText.textContent = `✅ ${file.name}`;
        if (subText) subText.textContent = `Size: ${(file.size / (1024 * 1024)).toFixed(2)} MB`;
        
        resultSection.style.display = 'none';
        statusSection.style.display = 'none';
    }
    
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        statusSection.style.display = 'block';
        statusMessage.textContent = '⏳ Uploading and processing...';
        progressBar.style.width = '30%';
        convertBtn.disabled = true;
        resultSection.style.display = 'none';
        
        const formData = new FormData();
        formData.append('video_file', selectedFile);
        formData.append('fps', document.getElementById('fps').value);
        formData.append('max_frames', document.getElementById('maxFrames').value);
        
        try {
            const response = await fetch('/api/convert.php', {
                method: 'POST',
                body: formData
            });
            
            progressBar.style.width = '80%';
            statusMessage.textContent = '⏳ Generating screensaver file...';
            
            const result = await response.json();
            
            if (result.success) {
                progressBar.style.width = '100%';
                statusMessage.textContent = '✅ Conversion complete!';
                
                directDownloadUrl = result.download_url;
                fileName.textContent = `📄 ${result.file}`;
                fileSize.textContent = `Size: ${(result.size / (1024 * 1024)).toFixed(2)} MB`;
                resultSection.style.display = 'block';
                
                setTimeout(() => {
                    if (directDownloadUrl) {
                        window.location.href = directDownloadUrl;
                    }
                }, 1200);
            } else {
                throw new Error(result.error || 'Conversion failed on server.');
            }
        } catch (error) {
            statusMessage.textContent = `❌ Error: ${error.message}`;
            progressBar.style.width = '0%';
        } finally {
            convertBtn.disabled = false;
        }
    });
    
    downloadBtn.addEventListener('click', () => {
        if (directDownloadUrl) {
            window.location.href = directDownloadUrl;
        }
    });
    
    installInstructions.addEventListener('click', () => {
        alert(
            '📖 How to Use Your Screensaver:\n\n' +
            '1️⃣ Double-click the downloaded file to run fullscreen immediately.\n' +
            '2️⃣ Move the mouse or press any key to exit.\n' +
            '3️⃣ To run on PC startup, place a shortcut in your Startup folder (Win + R -> shell:startup).'
        );
    });
});