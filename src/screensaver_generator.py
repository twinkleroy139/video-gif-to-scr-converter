import os
import io
import json
import base64

class ScreenSaverGenerator:
    """Generates portable screensaver HTML5 bundle package"""
    
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
        
        # Base64 encode all frames to embed cleanly
        encoded_frames = [base64.b64encode(f).decode('ascii') for f in self.frames]
        frames_json = json.dumps(encoded_frames)

        # Build self-contained HTA/Win32 executable bootstrap
        hta_payload = f"""<!-- ::
@echo off
setlocal
start "" mshta.exe "%~f0"
exit /b
-->
<!DOCTYPE html>
<html>
<head>
<meta http-equiv="X-UA-Compatible" content="IE=edge">
<title>Screensaver</title>
<HTA:APPLICATION 
    APPLICATIONNAME="ScreenSaverForge"
    BORDER="none"
    CAPTION="no"
    SHOWINTASKBAR="no"
    SINGLEINSTANCE="yes"
    WINDOWSTATE="maximize"
    SCROLL="no">
<style>
    * {{ margin: 0; padding: 0; box-sizing: border-box; }}
    body {{ background: black; width: 100vw; height: 100vh; overflow: hidden; display: flex; align-items: center; justify-content: center; cursor: none; }}
    img {{ max-width: 100%; max-height: 100%; object-fit: contain; }}
</style>
</head>
<body onkeydown="window.close()" onclick="window.close()" onmousemove="handleMouseMove(event)">
    <img id="ss_img" src="data:image/jpeg;base64,{encoded_frames[0]}">
    <script>
        var frames = {frames_json};
        var idx = 0;
        var imgEl = document.getElementById('ss_img');
        var moves = 0;
        
        function handleMouseMove(e) {{
            moves++;
            if (moves > 5) {{ window.close(); }}
        }}

        setInterval(function() {{
            idx = (idx + 1) % frames.length;
            imgEl.src = "data:image/jpeg;base64," + frames[idx];
        }}, {delay_ms});
    </script>
</body>
</html>
"""

        with open(final_scr, 'w', encoding='utf-8') as f:
            f.write(hta_payload)
            
        return final_scr