#!/usr/bin/env python3
import sys
import os
import argparse
from src.frame_processor import FrameProcessor
from src.screensaver_generator import ScreenSaverGenerator

def main():
    parser = argparse.ArgumentParser(
        description='Convert GIF/MP4 to Windows .SCR screensaver'
    )
    parser.add_argument('input', help='Input GIF or MP4 file')
    parser.add_argument('-o', '--output', default='screensaver', 
                       help='Output .scr filename or path (without extension)')
    parser.add_argument('-f', '--fps', type=int, default=10,
                       help='Frames per second (default: 10)')
    parser.add_argument('-m', '--max-frames', type=int, default=200,
                       help='Maximum frames to extract (default: 200)')
    parser.add_argument('-s', '--size', default='1920x1080',
                       help='Frame size (default: 1920x1080)')
    
    args = parser.parse_args()
    
    if not os.path.exists(args.input):
        print(f"[ERROR] Input file '{args.input}' not found!")
        return 1
    
    # Parse size
    try:
        width, height = map(int, args.size.split('x'))
        target_size = (width, height)
    except Exception:
        print("[ERROR] Invalid size format. Use WIDTHxHEIGHT (e.g., 800x600)")
        return 1
    
    # Normalize absolute output path
    output_path = os.path.abspath(args.output)
    output_dir = os.path.dirname(output_path)
    if output_dir and not os.path.exists(output_dir):
        os.makedirs(output_dir, exist_ok=True)
    
    print(f"[INFO] Processing: {args.input}")
    print(f"[INFO] FPS: {args.fps}, Max Frames: {args.max_frames}")
    print(f"[INFO] Target Size: {args.size}")
    print(f"[INFO] Output: {output_path}")
    
    try:
        # Step 1: Process frames
        print("[INFO] Processing frames...")
        processor = FrameProcessor(args.input)
        frames = processor.process_video(args.fps, args.max_frames, target_size)
        metadata = processor.get_metadata()
        print(f"[OK] Extracted {len(frames)} frames")
        
        # Step 2: Generate screensaver
        print("[INFO] Generating screensaver...")
        generator = ScreenSaverGenerator(output_path)
        generator.set_frames(frames, metadata)
        output_file = generator.generate_scr()
        
        if output_file and os.path.exists(output_file):
            print(f"[OK] Success! Screensaver created: {output_file}")
            print("\n[INFO] Installation Instructions:")
            print("   1. Right-click the .scr file")
            print("   2. Select 'Install' from the context menu")
            print("   3. Or copy to C:\\Windows\\System32 and set in Display Settings")
            return 0
        else:
            print("[ERROR] Failed to generate screensaver")
            return 1
        
    except Exception as e:
        print(f"[ERROR] {str(e)}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())