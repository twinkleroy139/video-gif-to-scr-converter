import os
import base64
import sys
import shutil
import tempfile

class ScreenSaverGenerator:
    """Generate Windows .SCR screensaver from BMP frames using in-memory GDI drawing"""
    
    def __init__(self, output_name="screensaver"):
        self.output_name = output_name
        self.frames = []
        self.metadata = {}
        
    def set_frames(self, frames, metadata=None):
        self.frames = frames
        self.metadata = metadata or {}
        
    def generate_scr(self):
        if not self.frames:
            raise Exception("No frames loaded! Call set_frames() first.")
        
        script_content = self._generate_python_script()
        
        temp_dir = tempfile.mkdtemp()
        script_name = "screensaver_script.py"
        script_path = os.path.join(temp_dir, script_name)
        
        with open(script_path, 'w', encoding='utf-8') as f:
            f.write(script_content)
        
        try:
            import PyInstaller.__main__
            return self._build_with_pyinstaller(script_path, temp_dir)
        except ImportError:
            print("[WARNING] PyInstaller not found. Creating fallback version.")
            return self._build_fallback(script_path, temp_dir)
    
    def _generate_python_script(self):
        encoded_frames = [base64.b64encode(f).decode('ascii') for f in self.frames]
        frame_count = len(encoded_frames)
        frame_delay = self.metadata.get('frame_delay', 60)
        
        script = f'''#!/usr/bin/env python3
import sys
import os
import base64
import ctypes
from ctypes import wintypes
import time

FRAMES = [{', '.join([f'"{f}"' for f in encoded_frames])}]
FRAME_DELAY = {frame_delay}
FRAME_COUNT = {frame_count}

WS_POPUP = 0x80000000
WS_VISIBLE = 0x10000000
WS_EX_TOPMOST = 0x00000008
WM_PAINT = 0x000F
WM_ERASEBKGND = 0x0014
WM_TIMER = 0x0113
WM_DESTROY = 0x0002
WM_KEYDOWN = 0x0100
WM_LBUTTONDOWN = 0x0201
WM_RBUTTONDOWN = 0x0204
WM_MOUSEMOVE = 0x0200
WM_CLOSE = 0x0010
WM_ACTIVATEAPP = 0x001C
WM_CREATE = 0x0001
DIB_RGB_COLORS = 0
SRCCOPY = 0x00CC0020

class BITMAPINFOHEADER(ctypes.Structure):
    _fields_ = [
        ("biSize", wintypes.DWORD),
        ("biWidth", wintypes.LONG),
        ("biHeight", wintypes.LONG),
        ("biPlanes", wintypes.WORD),
        ("biBitCount", wintypes.WORD),
        ("biCompression", wintypes.DWORD),
        ("biSizeImage", wintypes.DWORD),
        ("biXPelsPerMeter", wintypes.LONG),
        ("biYPelsPerMeter", wintypes.LONG),
        ("biClrUsed", wintypes.DWORD),
        ("biClrImportant", wintypes.DWORD)
    ]

class ScreenSaver:
    def __init__(self, preview_hwnd=None):
        self.user32 = ctypes.windll.user32
        self.gdi32 = ctypes.windll.gdi32
        self.kernel32 = ctypes.windll.kernel32
        
        self.preview_hwnd = preview_hwnd
        self.frame_index = 0
        self.running = True
        self.hwnd = None
        self.last_mouse = None
        
        # Pre-decode BMP bytes into memory buffers
        self.raw_frames = [base64.b64decode(f) for f in FRAMES]
        
        if self.preview_hwnd:
            rect = wintypes.RECT()
            self.user32.GetClientRect(self.preview_hwnd, ctypes.byref(rect))
            self.screen_width = rect.right - rect.left
            self.screen_height = rect.bottom - rect.top
        else:
            self.screen_width = self.user32.GetSystemMetrics(0)
            self.screen_height = self.user32.GetSystemMetrics(1)
        
    def create_window(self):
        class_name = f"SS_{{int(time.time() * 1000)}}"
        
        def wndproc(hwnd, msg, wparam, lparam):
            if msg == WM_CREATE:
                self.user32.SetTimer(hwnd, 1, FRAME_DELAY, None)
                return 0
            elif msg == WM_TIMER:
                self.frame_index = (self.frame_index + 1) % FRAME_COUNT
                self.user32.InvalidateRect(hwnd, None, False)
                return 0
            elif msg == WM_PAINT:
                ps = (ctypes.c_byte * 64)()
                hdc = self.user32.BeginPaint(hwnd, ps)
                self._draw_frame(hdc)
                self.user32.EndPaint(hwnd, ps)
                return 0
            elif msg in [WM_KEYDOWN, WM_LBUTTONDOWN, WM_RBUTTONDOWN]:
                if not self.preview_hwnd:
                    self.running = False
                    self.user32.PostQuitMessage(0)
                return 0
            elif msg == WM_MOUSEMOVE:
                if not self.preview_hwnd:
                    x = lparam & 0xFFFF
                    y = (lparam >> 16) & 0xFFFF
                    if self.last_mouse is None:
                        self.last_mouse = (x, y)
                    elif abs(x - self.last_mouse[0]) > 5 or abs(y - self.last_mouse[1]) > 5:
                        self.running = False
                        self.user32.PostQuitMessage(0)
                return 0
            elif msg == WM_ERASEBKGND:
                return 1
            elif msg in [WM_DESTROY, WM_CLOSE]:
                self.running = False
                self.user32.PostQuitMessage(0)
                return 0
            return self.user32.DefWindowProcW(hwnd, msg, wparam, lparam)
        
        wndclass = (ctypes.c_void_p * 10)()
        wndproc_cb = ctypes.WINFUNCTYPE(ctypes.c_longlong, ctypes.c_void_p, ctypes.c_uint, ctypes.c_void_p, ctypes.c_void_p)(wndproc)
        self._wndproc = wndproc_cb
        
        style = 0x40000000 | 0x10000000 if self.preview_hwnd else WS_POPUP | WS_VISIBLE
        parent = self.preview_hwnd if self.preview_hwnd else None
        
        self.hwnd = self.user32.CreateWindowExW(
            0 if self.preview_hwnd else WS_EX_TOPMOST,
            "Static",
            "",
            style,
            0, 0,
            self.screen_width,
            self.screen_height,
            parent,
            None,
            None,
            None
        )
        
        # Subclass standard window procedure
        self.user32.SetWindowLongPtrW(self.hwnd, -4, wndproc_cb)
        self.user32.SetTimer(self.hwnd, 1, FRAME_DELAY, None)
        return self.hwnd
    
    
    def _draw_frame(self, hdc):
        try:
            bmp_bytes = self.raw_frames[self.frame_index]
            pixel_offset = int.from_bytes(bmp_bytes[10:14], byteorder='little')
            bmi_bytes = bmp_bytes[14:pixel_offset]
            pixel_data = bmp_bytes[pixel_offset:]
            
            width = int.from_bytes(bmi_bytes[4:8], byteorder='little', signed=True)
            height = int.from_bytes(bmi_bytes[8:12], byteorder='little', signed=True)
            
            # Set stretching mode to prevent distortion
            self.gdi32.SetStretchBltMode(hdc, 3) # COLORONCOLOR
            
            self.gdi32.StretchDIBits(
                hdc,
                0, 0, self.screen_width, self.screen_height,
                0, 0, width, abs(height),
                pixel_data,
                bmi_bytes,
                DIB_RGB_COLORS,
                SRCCOPY
            )
        except Exception:
            pass




    def run(self):
        self.create_window()
        msg = wintypes.MSG()
        while self.running and self.user32.GetMessageW(ctypes.byref(msg), None, 0, 0):
            self.user32.TranslateMessage(ctypes.byref(msg))
            self.user32.DispatchMessageW(ctypes.byref(msg))

def main():
    try:
        preview_hwnd = None
        if len(sys.argv) > 1:
            mode = sys.argv[1].lower()[:2]
            if mode == '/c':
                return 0
            elif mode == '/p' and len(sys.argv) > 2:
                try:
                    preview_hwnd = int(sys.argv[2])
                except Exception:
                    return 0
        
        app = ScreenSaver(preview_hwnd)
        app.run()
    except Exception:
        pass
    return 0

if __name__ == "__main__":
    sys.exit(main())
'''
        return script
    
    def _build_with_pyinstaller(self, script_path, temp_dir):
        try:
            import PyInstaller.__main__
            
            base_name = os.path.splitext(os.path.basename(self.output_name))[0]
            base_name = ''.join(c for c in base_name if c.isalnum() or c in '._-')
            if not base_name:
                base_name = "screensaver"
            
            cmd = [
                '--onefile',
                '--noconsole',
                '--name', base_name,
                '--distpath', os.path.join(temp_dir, 'dist'),
                '--workpath', os.path.join(temp_dir, 'build'),
                '--specpath', temp_dir,
                script_path
            ]
            
            PyInstaller.__main__.run(cmd)
            
            dist_exe = os.path.join(temp_dir, 'dist', f"{base_name}.exe")
            
            if os.path.exists(dist_exe):
                output_dir = os.path.dirname(os.path.abspath(self.output_name))
                if output_dir and not os.path.exists(output_dir):
                    os.makedirs(output_dir, exist_ok=True)
                
                final_scr = os.path.join(output_dir, f"{base_name}.scr")
                shutil.copy2(dist_exe, final_scr)
                
                try:
                    shutil.rmtree(temp_dir)
                except Exception:
                    pass
                
                return final_scr
            return None
            
        except Exception as e:
            print(f"[ERROR] PyInstaller build failed: {e}")
            return None
    
    def _build_fallback(self, script_path, temp_dir):
        base_name = os.path.splitext(os.path.basename(self.output_name))[0]
        base_name = ''.join(c for c in base_name if c.isalnum() or c in '._-')
        if not base_name:
            base_name = "screensaver"
        
        output_dir = os.path.dirname(os.path.abspath(self.output_name))
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir, exist_ok=True)
        
        pyw_path = os.path.join(output_dir, f"{base_name}.pyw")
        shutil.copy2(script_path, pyw_path)
        
        scr_path = os.path.join(output_dir, f"{base_name}.scr")
        with open(scr_path, 'w') as f:
            f.write(f'@echo off\nstart /B pythonw "{pyw_path}"\n')
        
        try:
            shutil.rmtree(temp_dir)
        except Exception:
            pass
            
        return scr_path