import os
import io
import zipfile
import subprocess
import shutil

class ScreenSaverGenerator:
    """Generates a true native Windows PE (.scr) screensaver executable"""
    
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
        
        temp_zip = os.path.join(output_dir, f"{base_name}_assets.zip")
        temp_c = os.path.join(output_dir, f"{base_name}_stub.c")
        
        # 1. Write frames into a zip archive
        with zipfile.ZipFile(temp_zip, 'w', zipfile.ZIP_DEFLATED) as zf:
            for idx, frame_bytes in enumerate(self.frames):
                zf.writestr(f"frame_{idx:04d}.jpg", frame_bytes)
                
        # 2. C source code handling screensaver arguments and powershell host
        c_code = f"""
#include <windows.h>
#include <stdio.h>
#include <string.h>

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {{
    char flag[4] = {{0}};
    if (lpCmdLine != NULL && strlen(lpCmdLine) >= 2) {{
        flag[0] = lpCmdLine[0];
        flag[1] = lpCmdLine[1];
    }}

    if (_stricmp(flag, "/c") == 0 || _stricmp(flag, "-c") == 0) {{
        MessageBoxA(NULL, "ScreenSaverForge: No additional configuration needed.", "ScreenSaver Settings", MB_OK | MB_ICONINFORMATION);
        return 0;
    }}
    if (_stricmp(flag, "/p") == 0 || _stricmp(flag, "-p") == 0) {{
        return 0;
    }}

    char exePath[MAX_PATH];
    GetModuleFileNameA(NULL, exePath, MAX_PATH);

    char cmd[4096];
    snprintf(cmd, sizeof(cmd),
        "powershell.exe -NoProfile -ExecutionPolicy Bypass -WindowStyle Hidden -Command \\""
        "$t=[System.IO.Path]::Combine($env:TEMP, 'SS_%s');"
        "if(-not (Test-Path $t)){{New-Item -ItemType Directory -Path $t | Out-Null}};"
        "Add-Type -AssemblyName System.IO.Compression.FileSystem;"
        "[System.IO.Compression.ZipFile]::ExtractToDirectory('%s', $t);"
        "$w=New-Object Windows.Forms.Form;$w.WindowState='Maximized';$w.FormBorderStyle='None';$w.BackColor='Black';$w.TopMost=$true;"
        "$p=New-Object Windows.Forms.PictureBox;$p.Dock='Fill';$p.SizeMode='Zoom';$w.Controls.Add($p);"
        "$f=Get-ChildItem \\"$t\\\\*.jpg\\"|Sort-Object Name;"
        "if($f.Count -gt 0){{$i=0;$tm=New-Object Windows.Forms.Timer;$tm.Interval={delay_ms};$tm.add_Tick({{$p.ImageLocation=$f[$i].FullName;$i=($i+1)%%$f.Count}});$tm.Start()}};"
        "$c={{$tm.Stop();$w.Close();[Windows.Forms.Application]::Exit()}};"
        "$w.add_KeyDown($c);$w.add_Click($c);$p.add_Click($c);[Windows.Forms.Application]::Run($w)\\"",
        "{base_name}", exePath
    );

    STARTUPINFOA si;
    PROCESS_INFORMATION pi;
    ZeroMemory(&si, sizeof(si));
    si.cb = sizeof(si);
    si.dwFlags = STARTF_USESHOWWINDOW;
    si.wShowWindow = SW_HIDE;
    ZeroMemory(&pi, sizeof(pi));

    if (CreateProcessA(NULL, cmd, NULL, NULL, FALSE, CREATE_NO_WINDOW, NULL, NULL, &si, &pi)) {{
        WaitForSingleObject(pi.hProcess, INFINITE);
        CloseHandle(pi.hProcess);
        CloseHandle(pi.hThread);
    }}

    return 0;
}}
"""
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(c_code)
            
        # 3. Cross-compile to genuine Windows PE 64-bit Binary
        compiler = "x86_64-w64-mingw32-gcc" if shutil.which("x86_64-w64-mingw32-gcc") else "gcc"
        compile_cmd = [
            compiler,
            "-O2",
            "-mwindows",
            temp_c,
            "-o", final_scr,
            "-luser32",
            "-lkernel32"
        ]
        
        res = subprocess.run(compile_cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise Exception(f"Compiler Error: {res.stderr}")
            
        # 4. Append Zip Payload directly to PE executable
        with open(temp_zip, 'rb') as zf, open(final_scr, 'ab') as scr_out:
            scr_out.write(zf.read())
            
        # Cleanup temp source files
        if os.path.exists(temp_c):
            os.remove(temp_c)
        if os.path.exists(temp_zip):
            os.remove(temp_zip)
            
        return final_scr