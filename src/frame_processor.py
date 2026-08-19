import os
import io
import base64
from PIL import Image

class FrameProcessor:
    """Process video/GIF files and extract frames as BMP byte data"""
    
    def __init__(self, input_path):
        self.input_path = input_path
        self.frames = []
        self.metadata = {}
        
    def process_video(self, fps=10, max_frames=200, target_size=(800, 600)):
        """Extract and process frames from video/GIF"""
        
        if not os.path.exists(self.input_path):
            raise FileNotFoundError(f"Input file not found: {self.input_path}")
        
        ext = os.path.splitext(self.input_path)[1].lower()
        
        if ext == '.gif':
            return self._process_gif(fps, max_frames, target_size)
        elif ext in ['.mp4', '.webm', '.avi', '.mov']:
            return self._process_video(fps, max_frames, target_size)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    
    def _process_gif(self, fps, max_frames, target_size):
        """Process GIF file using PIL"""
        try:
            gif = Image.open(self.input_path)
            frames = []
            frame_count = 0
            
            try:
                duration = gif.info.get('duration', 100)
                if not duration or duration <= 0:
                    duration = int(1000 / fps)
                self.metadata['frame_delay'] = max(20, duration)
            except Exception:
                self.metadata['frame_delay'] = int(1000 / fps)
            
            while True:
                frame = gif.convert('RGB')
                frame = self._resize_keep_aspect(frame, target_size)
                
                # Save as standard BMP for fast direct GDI rendering
                img_byte_arr = io.BytesIO()
                frame.save(img_byte_arr, format='BMP')
                frames.append(img_byte_arr.getvalue())
                
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
        """Process video file using OpenCV"""
        try:
            import cv2
            
            cap = cv2.VideoCapture(self.input_path)
            if not cap.isOpened():
                raise Exception("Could not open video file")
            
            video_fps = cap.get(cv2.CAP_PROP_FPS)
            if video_fps <= 0:
                video_fps = 30
            
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
                    pil_img = self._resize_keep_aspect(pil_img, target_size)
                    
                    img_byte_arr = io.BytesIO()
                    pil_img.save(img_byte_arr, format='BMP')
                    frames.append(img_byte_arr.getvalue())
                
                count += 1
            
            cap.release()
            
            self.metadata['frame_delay'] = max(20, int(1000 / fps))
            self.metadata['frame_count'] = len(frames)
            self.metadata['fps'] = fps
            self.metadata['size'] = target_size
            
            self.frames = frames
            return frames
            
        except ImportError:
            raise Exception("OpenCV not installed. Please install opencv-python-headless")
        except Exception as e:
            raise Exception(f"Error processing video: {str(e)}")
    
    def _resize_keep_aspect(self, image, target_size):
        """Resize image maintaining aspect ratio with black padding"""
        target_width, target_height = target_size
        original_width, original_height = image.size
        
        target_ratio = target_width / target_height
        original_ratio = original_width / original_height
        
        if original_ratio > target_ratio:
            new_width = target_width
            new_height = int(target_width / original_ratio)
        else:
            new_height = target_height
            new_width = int(target_height * original_ratio)
        
        image = image.resize((new_width, new_height), Image.Resampling.LANCZOS)
        
        new_image = Image.new('RGB', target_size, (0, 0, 0))
        x_offset = (target_width - new_width) // 2
        y_offset = (target_height - new_height) // 2
        new_image.paste(image, (x_offset, y_offset))
        
        return new_image
    
    def get_metadata(self):
        return self.metadata