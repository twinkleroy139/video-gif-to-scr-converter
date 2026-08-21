import os
import io
import json
import base64

class ScreenSaverGenerator:
    """Generates a standalone Windows Screensaver package with instant launch and installation support"""
    
    def __init__(self, output_name="screensaver"):
        self.output_name = output_name
        self.frames = []
        self.metadata = {}
        
    def set_frames(self, frames, metadata=None):
        self.frames = frames
        self.metadata = metadata or {}
        
    def generate_scr(self):
        if not self.frames:
            raise Exception("No frames loaded.")
            
        output_dir = os.path.dirname(os.path.abspath(self.output_name))
        base_name = os.path.splitext(os.path.basename(self.output_name))[0]
        os.makedirs(output_dir, exist_ok=True)
        
        final_scr = os.path.join(output_dir, f"{base_name}.scr")
        delay_ms = max(20, int(self.metadata.get('frame_delay', 60)))
        
        # Base64 encode all extracted frames
        encoded_frames = [base64.b64encode(f).decode('ascii') for f in self.frames]
        frames_json = json.dumps(encoded_frames)

        # Standard Windows Scripting Host / MSHTA Screensaver Engine
        runner_content = f"""<!-- ::
@echo off
setlocal
if /i "%~1"=="/c" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Windows.Forms.MessageBox]::Show('ScreenSaverForge animation running smoothly.', 'Screensaver Info', 0, 64)"
    exit /b
)
if /i "%~1"=="/p" (
    exit /b
)
start "" mshta.exe "%~f0"
exit /b
-->
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>Screensaver</title>
<HTA:APPLICATION 
    APPLICATIONNAME="OnePieceScreenSaver"
    BORDER="none"
    CAPTION="no"
    SHOWINTASKBAR="no"
    SINGLEINSTANCE="yes"
    WINDOWSTATE="maximize"
    SCROLL="no">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: #000000; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: none; }}
    img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
</style>
</head>
<body onkeydown="window.close()" onclick="window.close()" onmousemove="detectExit(event)">
    <img id="display_frame" src="data:image/jpeg;base64,{encoded_frames[0]}">
    <script>
        var frameData = {frames_json};
        var currentIdx = 0;
        var displayImg = document.getElementById('display_frame');
        var mouseMoveCount = 0;
        
        function detectExit(e) {{
            mouseMoveCount++;
            if (mouseMoveCount > 6) {{
                window.close();
            }}
        }}

        setInterval(function() {{
            currentIdx = (currentIdx + 1) % frameData.length;
            displayImg.src = "data:image/jpeg;base64," + frameData[currentIdx];
        }}, {delay_ms});
    </script>
</body>
</html>
"""

        with open(final_scr, 'w', encoding='utf-8') as f:
            f.write(runner_content)
            
        return final_scr