import os
import io
import base64
from PIL import Image

class FrameProcessor:
    """Process video/GIF files with low memory footprint"""
    
    def __init__(self, input_path):
        self.input_path = input_path
        self.frames = []
        self.metadata = {}
        
    def process_video(self, fps=10, max_frames=120, target_size=(1280, 720)):
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        ext = os.path.splitext(self.input_path)[1].lower()
        
        if ext == '.gif':
            return self._process_gif(fps, max_frames, target_size)
        elif ext in ['.mp4', '.webm', '.avi', '.mov']:
            return self._process_video(fps, max_frames, target_size)
        else:
            raise ValueError(f"Unsupported format: {ext}")
            
    def _process_gif(self, fps, max_frames, target_size):
        try:
            gif = Image.open(self.input_path)
            frames = []
            frame_count = 0
            
            duration = gif.info.get('duration', 100)
            if not duration or duration <= 0:
                duration = int(1000 / fps)
            self.metadata['frame_delay'] = max(30, duration)
            
            while True:
                frame = gif.convert('RGB')
                frame.thumbnail(target_size, Image.Resampling.BILINEAR)
                
                # Compress to JPEG in-memory to save RAM
                buffer = io.BytesIO()
                frame.save(buffer, format='JPEG', quality=80, optimize=True)
                frames.append(buffer.getvalue())
                
                frame_count += 1
                if frame_count >= max_frames:
                    break
                gif.seek(gif.tell() + 1)
        except EOFError:
            pass
        except Exception as e:
            raise Exception(f"Error processing GIF: {str(e)}")
            
        self.frames = frames
        self.metadata['frame_count'] = len(frames)
        self.metadata['fps'] = fps
        self.metadata['size'] = target_size
        return frames

    def _process_video(self, fps, max_frames, target_size):
        try:
            import cv2
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
                
            video_fps = cap.get(cv2.CAP_PROP_FPS) or 30
            frame_interval = max(1, int(round(video_fps / fps)))
            frames = []
            count = 0
            
            while cap.isOpened() and len(frames) < max_frames:
                ret, frame = cap.read()
                if not ret:
                    break
                if count % frame_interval == 0:
                    frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                    pil_img = Image.fromarray(frame)
                    pil_img.thumbnail(target_size, Image.Resampling.BILINEAR)
                    
                    buffer = io.BytesIO()
                    pil_img.save(buffer, format='JPEG', quality=80, optimize=True)
                    frames.append(buffer.getvalue())
                count += 1
            cap.release()
            
            self.metadata['frame_delay'] = max(30, int(1000 / fps))
            self.metadata['frame_count'] = len(frames)
            self.metadata['fps'] = fps
            self.metadata['size'] = target_size
            return frames
        except Exception as e:
            raise Exception(f"Error processing video: {str(e)}")

    def get_metadata(self):
        return self.metadata