import os
import io
import subprocess
import shutil

class ScreenSaverGenerator:
    """Generates a standalone native Windows PE (.scr) screensaver binary"""
    
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
        
        temp_rc = os.path.join(output_dir, f"{base_name}.rc")
        temp_res = os.path.join(output_dir, f"{base_name}_res.o")
        temp_c = os.path.join(output_dir, f"{base_name}_stub.c")
        
        # 1. Write frames to disk and generate Windows Resource file (.rc)
        frame_files = []
        rc_entries = []
        for idx, frame_bytes in enumerate(self.frames):
            frame_path = os.path.join(output_dir, f"f_{idx:04d}.jpg")
            with open(frame_path, 'wb') as f:
                f.write(frame_bytes)
            frame_files.append(frame_path)
            # Resource ID format: 1000 + idx
            rc_entries.append(f"{1000 + idx} RCDATA \"{os.path.basename(frame_path)}\"")
            
        with open(temp_rc, 'w', encoding='utf-8') as f:
            f.write("\n".join(rc_entries))
            
        # 2. Native Win32 + GDI+ / Windows Forms Screensaver C stub
        c_code = f"""
#include <windows.h>
#include <gdiplus.h>
#include <stdio.h>
#include <stdlib.h>

#define TOTAL_FRAMES {len(self.frames)}
#define TIMER_ID 101

HINSTANCE hInst;
ULONG_PTR gdiplusToken;
IStream* pStreams[TOTAL_FRAMES];
void* pImages[TOTAL_FRAMES];
int currentFrame = 0;
POINT lastCursorPos;
BOOL firstMouseMove = TRUE;

// Load JPEG from binary resources into GDI+ Image
void LoadResources() {{
    for (int i = 0; i < TOTAL_FRAMES; i++) {{
        HRSRC hRes = FindResource(hInst, MAKEINTRESOURCE(1000 + i), RT_RCDATA);
        if (hRes) {{
            HGLOBAL hData = LoadResource(hInst, hRes);
            DWORD size = SizeofResource(hInst, hRes);
            void* pData = LockResource(hData);
            
            HGLOBAL hMem = GlobalAlloc(GMEM_MOVEABLE, size);
            void* pMem = GlobalLock(hMem);
            memcpy(pMem, pData, size);
            GlobalUnlock(hMem);
            
            if (CreateStreamOnHGlobal(hMem, TRUE, &pStreams[i]) == S_OK) {{
                // GdipCreateBitmapFromStream
                typedef int (WINAPI *GdipCreateBitmapFromStream_t)(IStream*, void**);
                GdipCreateBitmapFromStream_t fnCreate = (GdipCreateBitmapFromStream_t)GetProcAddress(GetModuleHandleA("gdiplus.dll"), "GdipCreateBitmapFromStream");
                if (fnCreate) {{
                    fnCreate(pStreams[i], &pImages[i]);
                }}
            }}
        }}
    }}
}}

LRESULT CALLBACK WndProc(HWND hWnd, UINT message, WPARAM wParam, LPARAM lParam) {{
    switch (message) {{
        case WM_CREATE: {{
            GetCursorPos(&lastCursorPos);
            SetTimer(hWnd, TIMER_ID, {delay_ms}, NULL);
            break;
        }}
        case WM_TIMER: {{
            currentFrame = (currentFrame + 1) % TOTAL_FRAMES;
            InvalidateRect(hWnd, NULL, FALSE);
            break;
        }}
        case WM_PAINT: {{
            PAINTSTRUCT ps;
            HDC hdc = BeginPaint(hWnd, &ps);
            RECT rect;
            GetClientRect(hWnd, &rect);
            int screenW = rect.right;
            int screenH = rect.bottom;

            // Black background
            HBRUSH blackBrush = CreateSolidBrush(RGB(0, 0, 0));
            FillRect(hdc, &rect, blackBrush);
            DeleteObject(blackBrush);

            if (pImages[currentFrame] != NULL) {{
                typedef int (WINAPI *GdipCreateFromHDC_t)(HDC, void**);
                typedef int (WINAPI *GdipDrawImageRectRectI_t)(void*, void*, int, int, int, int, int, int, int, int, int, void*, void*, void*);
                typedef int (WINAPI *GdipGetImageWidth_t)(void*, UINT*);
                typedef int (WINAPI *GdipGetImageHeight_t)(void*, UINT*);
                typedef int (WINAPI *GdipDeleteGraphics_t)(void*);

                HMODULE hGdiplus = GetModuleHandleA("gdiplus.dll");
                GdipCreateFromHDC_t fnCreateGraphics = (GdipCreateFromHDC_t)GetProcAddress(hGdiplus, "GdipCreateFromHDC");
                GdipDrawImageRectRectI_t fnDrawImage = (GdipDrawImageRectRectI_t)GetProcAddress(hGdiplus, "GdipDrawImageRectRectI");
                GdipGetImageWidth_t fnGetWidth = (GdipGetImageWidth_t)GetProcAddress(hGdiplus, "GdipGetImageWidth");
                GdipGetImageHeight_t fnGetHeight = (GdipGetImageHeight_t)GetProcAddress(hGdiplus, "GdipGetImageHeight");
                GdipDeleteGraphics_t fnDeleteGraphics = (GdipDeleteGraphics_t)GetProcAddress(hGdiplus, "GdipDeleteGraphics");

                void* graphics = NULL;
                if (fnCreateGraphics && fnCreateGraphics(hdc, &graphics) == 0) {{
                    UINT imgW = 0, imgH = 0;
                    fnGetWidth(pImages[currentFrame], &imgW);
                    fnGetHeight(pImages[currentFrame], &imgH);

                    // Aspect ratio scaling
                    float scale = min((float)screenW / imgW, (float)screenH / imgH);
                    int drawW = (int)(imgW * scale);
                    int drawH = (int)(imgH * scale);
                    int drawX = (screenW - drawW) / 2;
                    int drawY = (screenH - drawH) / 2;

                    fnDrawImage(graphics, pImages[currentFrame], drawX, drawY, drawW, drawH, 0, 0, imgW, imgH, 2, NULL, NULL, NULL);
                    fnDeleteGraphics(graphics);
                }}
            }}
            EndPaint(hWnd, &ps);
            break;
        }}
        case WM_MOUSEMOVE: {{
            POINT pt;
            GetCursorPos(&pt);
            if (firstMouseMove) {{
                lastCursorPos = pt;
                firstMouseMove = FALSE;
            }} else if (abs(pt.x - lastCursorPos.x) > 10 || abs(pt.y - lastCursorPos.y) > 10) {{
                PostMessage(hWnd, WM_CLOSE, 0, 0);
            }}
            break;
        }}
        case WM_KEYDOWN:
        case WM_LBUTTONDOWN:
        case WM_RBUTTONDOWN:
        case WM_MBUTTONDOWN:
            PostMessage(hWnd, WM_CLOSE, 0, 0);
            break;
        case WM_DESTROY:
            KillTimer(hWnd, TIMER_ID);
            PostQuitMessage(0);
            break;
        default:
            return DefWindowProc(hWnd, message, wParam, lParam);
    }}
    return 0;
}}

int WINAPI WinMain(HINSTANCE hInstance, HINSTANCE hPrevInstance, LPSTR lpCmdLine, int nCmdShow) {{
    hInst = hInstance;
    char flag[4] = {{0}};
    if (lpCmdLine != NULL && strlen(lpCmdLine) >= 2) {{
        flag[0] = lpCmdLine[0];
        flag[1] = lpCmdLine[1];
    }}

    if (_stricmp(flag, "/c") == 0 || _stricmp(flag, "-c") == 0) {{
        MessageBoxA(NULL, "One Piece ScreenSaverForge is ready and configured.", "ScreenSaver Settings", MB_OK | MB_ICONINFORMATION);
        return 0;
    }}

    // Initialize GDI+
    HMODULE hGdiplus = LoadLibraryA("gdiplus.dll");
    typedef struct {{ UINT32 GdiplusVersion; void* DebugEventCallback; BOOL SuppressBackgroundThread; BOOL SuppressExternalCodecs; }} GdiplusStartupInput;
    typedef int (WINAPI *GdiplusStartup_t)(ULONG_PTR*, GdiplusStartupInput*, void*);
    GdiplusStartup_t fnStartup = (GdiplusStartup_t)GetProcAddress(hGdiplus, "GdiplusStartup");
    GdiplusStartupInput input = {{1, NULL, FALSE, FALSE}};
    if (fnStartup) {{
        fnStartup(&gdiplusToken, &input, NULL);
    }}

    LoadResources();

    WNDCLASSEXA wcex = {{0}};
    wcex.cbSize = sizeof(WNDCLASSEXA);
    wcex.style = CS_HREDRAW | CS_VREDRAW;
    wcex.lpfnWndProc = WndProc;
    wcex.hInstance = hInstance;
    wcex.hCursor = LoadCursor(NULL, IDC_ARROW);
    wcex.hbrBackground = (HBRUSH)GetStockObject(BLACK_BRUSH);
    wcex.lpszClassName = "ScreenSaverForgeClass";
    RegisterClassExA(&wcex);

    HWND hWnd = CreateWindowExA(
        WS_EX_TOPMOST,
        "ScreenSaverForgeClass",
        "ScreenSaverForge",
        WS_POPUP | WS_VISIBLE,
        0, 0,
        GetSystemMetrics(SM_CXSCREEN),
        GetSystemMetrics(SM_CYSCREEN),
        NULL, NULL, hInstance, NULL
    );

    ShowCursor(FALSE);
    UpdateWindow(hWnd);

    MSG msg;
    while (GetMessage(&msg, NULL, 0, 0)) {{
        TranslateMessage(&msg);
        DispatchMessage(&msg);
    }}

    ShowCursor(TRUE);
    return 0;
}}
"""
        with open(temp_c, 'w', encoding='utf-8') as f:
            f.write(c_code)
            
        # 3. Compile Windows Resource (.rc -> .o) using windres
        windres = "x86_64-w64-mingw32-windres" if shutil.which("x86_64-w64-mingw32-windres") else "windres"
        rc_cmd = [windres, "-i", temp_rc, "-o", temp_res]
        res_rc = subprocess.run(rc_cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res_rc.returncode != 0:
            raise Exception(f"Resource Compiler Error: {res_rc.stderr}")

        # 4. Cross-compile full binary with embedded resources and GDI+
        compiler = "x86_64-w64-mingw32-gcc" if shutil.which("x86_64-w64-mingw32-gcc") else "gcc"
        compile_cmd = [
            compiler,
            "-O2",
            "-mwindows",
            temp_c,
            temp_res,
            "-o", final_scr,
            "-luser32",
            "-lgdi32",
            "-lole32",
            "-lkernel32"
        ]
        
        res = subprocess.run(compile_cmd, cwd=output_dir, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True)
        if res.returncode != 0:
            raise Exception(f"Compiler Error: {res.stderr}")

        # 5. Clean up temporary generation files
        for item in frame_files + [temp_rc, temp_res, temp_c]:
            if os.path.exists(item):
                os.remove(item)
                
        return final_scr