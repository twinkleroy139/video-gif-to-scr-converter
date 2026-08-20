import os
import io
import zipfile
import shutil

class ScreenSaverGenerator:
    """Generates portable screensaver package within low-memory limits"""
    
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
        
        # Package frames and config into executable ZIP-embedded wrapper
        with open(final_scr, 'wb') as f_out:
            # Write batch bootstrap header so Windows executes directly
            bootstrap = f"""@echo off
setlocal
set "TEMP_DIR=%TEMP%\\SS_{base_name}"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"
powershell -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%~f0', '%TEMP_DIR%')" 2>nul
powershell -Command "$w=New-Object Windows.Forms.Form;$w.WindowState='Maximized';$w.FormBorderStyle='None';$w.BackColor='Black';$p=New-Object Windows.Forms.PictureBox;$p.Dock='Fill';$p.SizeMode='CenterImage';$w.Controls.Add($p);$f=Get-ChildItem '%TEMP_DIR%\\*.jpg'|Sort-Object Name;$i=0;$t=New-Object Windows.Forms.Timer;$t.Interval={self.metadata.get('frame_delay', 60)};$t.add_Tick({{$p.ImageLocation=$f[$i].FullName;$i=($i+1)%%$f.Count}});$t.Start();$w.add_KeyDown({{$w.Close();$t.Stop()}});$w.add_Click({{$w.Close();$t.Stop()}});$p.add_Click({{$w.Close();$t.Stop()}});[Windows.Forms.Application]::Run($w)"
exit /b
""".encode('ascii')
            f_out.write(bootstrap)
            
            # Append zipped frames
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, frame_bytes in enumerate(self.frames):
                    zf.writestr(f"frame_{idx:04d}.jpg", frame_bytes)
            
            f_out.write(zip_buffer.getvalue())
            
        return final_scr