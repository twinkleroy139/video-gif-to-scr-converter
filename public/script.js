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
        const files = e.dataTransfer.files;
        if (files.length > 0) {
            handleFile(files[0]);
        }
    });
    
    dropZone.addEventListener('click', () => {
        fileInput.click();
    });

    fileInput.addEventListener('change', (e) => {
        if (e.target.files.length > 0) {
            handleFile(e.target.files[0]);
        }
    });
    
    function handleFile(file) {
        const allowed = ['image/gif', 'video/mp4', 'video/webm', 'video/x-msvideo', 'video/quicktime'];
        const ext = file.name.split('.').pop().toLowerCase();
        const allowedExt = ['gif', 'mp4', 'webm', 'avi', 'mov'];
        
        if (!allowed.includes(file.type) && !allowedExt.includes(ext)) {
            alert('Please upload a GIF or MP4 file');
            return;
        }
        
        if (file.size > 50 * 1024 * 1024) {
            alert('File too large. Maximum size is 50MB');
            return;
        }
        
        selectedFile = file;
        convertBtn.disabled = false;
        document.querySelector('.drop-zone p').textContent = `✅ ${file.name}`;
        document.querySelector('.sub-text').textContent = `Size: ${(file.size / 1024 / 1024).toFixed(2)} MB`;
        
        resultSection.style.display = 'none';
        statusSection.style.display = 'none';
    }
    
    convertBtn.addEventListener('click', async () => {
        if (!selectedFile) return;
        
        statusSection.style.display = 'block';
        statusMessage.textContent = '⏳ Uploading and converting...';
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
            statusMessage.textContent = '⏳ Generating screensaver...';
            
            const result = await response.json();
            
            if (result.success) {
                progressBar.style.width = '100%';
                statusMessage.textContent = '✅ Conversion complete!';
                
                directDownloadUrl = result.download_url;
                fileName.textContent = `📄 ${result.file}`;
                fileSize.textContent = `Size: ${(result.size / 1024 / 1024).toFixed(2)} MB`;
                resultSection.style.display = 'block';
                
                setTimeout(() => {
                    if (directDownloadUrl) {
                        window.location.href = directDownloadUrl;
                    }
                }, 1500);
            } else {
                throw new Error(result.error || 'Conversion failed');
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
            '📖 How to Test & Use Your Screensaver:\n\n' +
            '1️⃣ Double-click the downloaded .scr file to test run immediately.\n' +
            '2️⃣ Right-click > "Install" to configure it inside Windows.\n' +
            '3️⃣ Press any key or click the screen to exit.'
        );
    });
});