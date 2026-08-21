import os
import io
import zipfile

class ScreenSaverGenerator:
    """Generates portable screensaver package with full screensaver argument handling"""
    
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
        
        # Batch script header handling /s, /c, /p arguments
        bootstrap = f"""@echo off
setlocal enabledelayedexpansion
set "ARG=%~1"
set "FLAG=!ARG:~0,2!"

if /i "!FLAG!"=="/c" (
    powershell -NoProfile -ExecutionPolicy Bypass -Command "[System.Windows.Forms.MessageBox]::Show('ScreenSaverForge: No extra configuration needed.', 'One Piece Screensaver', 0, 64)"
    exit /b
)

if /i "!FLAG!"=="/p" (
    exit /b
)

set "TEMP_DIR=%TEMP%\\SS_{base_name}"
if not exist "%TEMP_DIR%" mkdir "%TEMP_DIR%"

powershell -NoProfile -ExecutionPolicy Bypass -Command "Add-Type -AssemblyName System.IO.Compression.FileSystem; [System.IO.Compression.ZipFile]::ExtractToDirectory('%~f0', '%TEMP_DIR%')" 2>nul

powershell -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command "$w=New-Object Windows.Forms.Form;$w.WindowState='Maximized';$w.FormBorderStyle='None';$w.BackColor='Black';$w.TopMost=$true;$p=New-Object Windows.Forms.PictureBox;$p.Dock='Fill';$p.SizeMode='Zoom';$w.Controls.Add($p);$f=Get-ChildItem '%TEMP_DIR%\\*.jpg'|Sort-Object Name;if($f.Count -gt 0){{$i=0;$t=New-Object Windows.Forms.Timer;$t.Interval={delay_ms};$t.add_Tick({{$p.ImageLocation=$f[$i].FullName;$i=($i+1)%%$f.Count}});$t.Start()}};$closeAction={{$t.Stop();$w.Close();[Windows.Forms.Application]::Exit()}};$w.add_KeyDown($closeAction);$w.add_Click($closeAction);$p.add_Click($closeAction);[Windows.Forms.Application]::Run($w)"
exit /b
""".encode('ascii')

        with open(final_scr, 'wb') as f_out:
            f_out.write(bootstrap)
            
            zip_buffer = io.BytesIO()
            with zipfile.ZipFile(zip_buffer, 'w', zipfile.ZIP_DEFLATED) as zf:
                for idx, frame_bytes in enumerate(self.frames):
                    zf.writestr(f"frame_{idx:04d}.jpg", frame_bytes)
            
            f_out.write(zip_buffer.getvalue())
            
        return final_scr