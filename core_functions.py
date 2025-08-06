import os, subprocess, cv2, random, tempfile, shutil
from typing import Optional, List
from datetime import datetime
from moviepy import VideoFileClip, ImageClip, CompositeVideoClip, AudioFileClip
from moviepy.video.fx import Crop

which_ubuntu = 'RunPod'


def get_output_filename(prefix, input_path, output_ext=".mp4"):
    """
    Generate output filename based on prefix and input path.
    
    Args:
        prefix: String prefix for the output filename
        input_path: Path to the input file
        output_ext: Extension for the output file (default: .mp4)
    
    Returns:
        Generated output filename
    """
    # Get the base name without extension
    base_name = os.path.splitext(os.path.basename(input_path))[0]
    
    # Create timestamp for uniqueness
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    
    # Combine prefix, base name, timestamp, and extension
    output_filename = f"{prefix}_{base_name}_{timestamp}{output_ext}"
    
    # Clean up any spaces or special characters
    output_filename = output_filename.replace(" ", "_").replace("(", "").replace(")", "")
    
    return output_filename


def get_local_font(language='chinese'):
    """
    Get appropriate font name based on environment and language
    
    Args:
        language (str): Language type, 'chinese' (default) or 'english'
    
    Returns:
        str: Font name or font file path
    """
    import subprocess
    if language.lower() == 'english':
        # Use Ubuntu font for English
        font_name = "Ubuntu"
    else:
        # Chinese: prioritize LXGW WenKai Bold
        # All systems prioritize checking LXGW WenKai
        if which_ubuntu in ['TB', 'AWS', 'RunPod']:
            # Linux systems - check if LXGW WenKai is installed
            
            try:
                result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True)
                if 'LXGW WenKai' in result.stdout:
                    # System has installed font, return font name (not path)
                    return "LXGW WenKai Bold"
            except:
                pass
            
            # Check if font files exist
            font_paths = [
                # Top priority: LXGW WenKai Bold
                "/usr/share/fonts/truetype/lxgw/LXGWWenKai-Bold.ttf",
                "/usr/local/share/fonts/LXGWWenKai-Bold.ttf",
                "/home/ubuntu/.local/share/fonts/LXGWWenKai-Bold.ttf",
                # Backup: Source Han fonts
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
            ]
            for path in font_paths:
                if os.path.exists(path):
                    # If LXGW WenKai, return font name instead of path
                    if 'lxgw' in path.lower() or 'LXGWWenKai' in path:
                        return "LXGW WenKai Bold"
                    else:
                        # Other fonts return path
                        return path
            # If no Chinese font found, use Ubuntu as fallback
            font_name = "Ubuntu"
        else:
            # Mac systems - also prioritize LXGW WenKai
            # First check if system has LXGW WenKai installed
            try:
                result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True)
                if 'LXGW WenKai' in result.stdout or 'LXGW' in result.stdout:
                    # System has installed font, use font name directly
                    font_name = "LXGW WenKai"
                    return font_name
            except:
                pass
            
            # If system doesn't have it, check local font files
            mac_font_paths = [
                "/Library/Fonts/LXGWWenKai-Bold.ttf",
                os.path.expanduser("~/Library/Fonts/LXGWWenKai-Bold.ttf")
            ]
            
            for path in mac_font_paths:
                if os.path.exists(path):
                    # If in system font directory, return font name instead of path
                    if path.startswith("/Library/Fonts/") or path.startswith(os.path.expanduser("~/Library/Fonts/")):
                        font_name = "LXGW WenKai"
                        return font_name
                    else:
                        # Project font files, return path
                        return path
            
            # If LXGW WenKai not found, use default Noto Sans CJK
            font_name = "Noto Sans CJK SC"
    
    return font_name


EFFECTS = ["random", "zoom_in", "zoom_out", "pan_left", "pan_right"]

class AfterEffectsProcess:
    def __init__(self, output_folder, logger=None):
        self.output_folder = output_folder
        self.logger = logger

    def process_file(self, input_path=None, parameters=None, progress_callback=None, **kwargs):
        # Support both old and new calling methods
        if input_path and parameters:
            # Old method: backward compatibility
            skip_existed = parameters.get("skip_existed", True)
            effect = parameters.get("effect", "random")
            effects = parameters.get("effects", None)
            watermark_path = parameters.get("watermark_path", None)
            input_video = input_path
            input_image = None
            input_audio = None
        else:
            # New method: use **kwargs
            skip_existed = kwargs.get("skip_existed", True)
            effect = kwargs.get("effect", "random")
            effects = kwargs.get("effects", None)
            watermark_path = kwargs.get("watermark_path", None)
            input_video = kwargs.get("input_video", None)
            input_image = kwargs.get("input_image", None)
            input_audio = kwargs.get("input_audio", None)
            progress_callback = kwargs.get("progress_callback", progress_callback)
        
        # Input validation logic
        if input_video and os.path.exists(input_video):
            # Priority 1: Process existing video file
            if progress_callback:
                progress_callback(f"Processing video: {os.path.basename(input_video)}")
            source_path = input_video
            
        elif input_image and input_audio and os.path.exists(input_image) and os.path.exists(input_audio):
            # Priority 2: Create video from image + audio
            if progress_callback:
                progress_callback(f"Creating video from image and audio")
            source_path = self._create_video_from_image_audio(input_image, input_audio, progress_callback)
            if not source_path:
                return None
                
        else:
            # Error: Invalid input combination
            if progress_callback:
                progress_callback("Error: Must provide either input_video OR both input_image and input_audio")
            return None
        
        # Generate output path
        if input_path:
            output_name = get_output_filename("After Effects", input_path, output_ext=".mp4")
        else:
            base_name = os.path.basename(input_video) if input_video else f"{os.path.basename(input_image)}_with_audio"
            output_name = get_output_filename("After Effects", base_name, output_ext=".mp4")
        
        output_path = os.path.join(self.output_folder, output_name)
        if skip_existed and os.path.exists(output_path):
            return output_path
        try:
            clip = VideoFileClip(source_path)
            
            # Smart effect selection logic
            if effects and isinstance(effects, list) and len(effects) > 0:
                # Priority 1: Random selection from provided effects list
                chosen_effect = random.choice(effects)
                # Remove redundant effect selection logging
                # if progress_callback:
                #     progress_callback(f"Selected '{chosen_effect}' from effects list: {effects}")
            elif effect and effect != "random":
                # Priority 2: Use specified single effect
                chosen_effect = effect
            else:
                # Priority 3: Random from all available effects
                chosen_effect = random.choice([e for e in EFFECTS if e != "random"])
            # Remove redundant effect application logging
            # if progress_callback:
            #     progress_callback(f"Applying effect '{chosen_effect}' to {os.path.basename(source_path)}")
            temp_out_path = None
            original_audio = clip.audio  # Preserve original audio
            
            if chosen_effect in ("zoom_in", "zoom_out"):
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_out:
                    temp_out_path = temp_out.name
                self._opencv_smooth_zoom(
                    source_path,
                    temp_out_path,
                    chosen_effect,
                    fps=int(getattr(clip, 'fps', 30) or 30),
                    w=clip.w,
                    h=clip.h,
                    progress_callback=progress_callback
                )
                # Load the video-only clip and restore audio
                clip = VideoFileClip(temp_out_path)
                if original_audio:
                    clip = clip.with_audio(original_audio)
                    # if progress_callback:  # Clean up redundant logging
                    #     progress_callback("Audio restored from original video")
                        
            elif chosen_effect in ("pan_left", "pan_right"):
                with tempfile.NamedTemporaryFile(suffix='.mp4', delete=False) as temp_out:
                    temp_out_path = temp_out.name
                self._opencv_smooth_pan(
                    source_path,
                    temp_out_path,
                    chosen_effect,
                    fps=int(getattr(clip, 'fps', 30) or 30),
                    w=clip.w,
                    h=clip.h,
                    progress_callback=progress_callback
                )
                # Load the video-only clip and restore audio
                clip = VideoFileClip(temp_out_path)
                if original_audio:
                    clip = clip.with_audio(original_audio)
                    # if progress_callback:  # Clean up redundant logging
                    #     progress_callback("Audio restored from original video")
            w, h = clip.size
            
            # Auto-detect orientation and set appropriate aspect ratio
            if w > h:
                # Landscape: use 16:9 aspect ratio
                aspect = 16 / 9
                # Remove redundant format detection logging
                # if progress_callback:
                #     progress_callback(f"Detected landscape format ({w}x{h}), using 16:9 aspect ratio")
            else:
                # Portrait: use 9:16 aspect ratio
                aspect = 9 / 16
                if progress_callback:
                    progress_callback(f"Detected portrait format ({w}x{h}), using 9:16 aspect ratio")
            
            effects = []
            current_aspect = w / h
            
            if abs(current_aspect - aspect) > 0.01:  # Only crop if aspect ratios differ significantly
                if current_aspect > aspect:
                    # Video is wider than target aspect ratio - crop horizontally
                    new_w = int(h * aspect)
                    x1 = (w - new_w) // 2
                    x2 = x1 + new_w
                    effects.append(Crop(x1=x1, y1=0, x2=x2, y2=h))
                    if progress_callback:
                        progress_callback(f"Cropping width from {w} to {new_w} pixels")
                elif current_aspect < aspect:
                    # Video is taller than target aspect ratio - crop vertically
                    new_h = int(w / aspect)
                    y1 = (h - new_h) // 2
                    y2 = y1 + new_h
                    effects.append(Crop(x1=0, y1=y1, x2=w, y2=y2))
                    if progress_callback:
                        progress_callback(f"Cropping height from {h} to {new_h} pixels")
            else:
                # Remove redundant aspect ratio logging
                # if progress_callback:
                #     progress_callback(f"Video already has correct aspect ratio ({current_aspect:.3f}), no cropping needed")
                pass  # Need pass statement for Python syntax
            if effects:
                clip = clip.with_effects(effects)
            
            # Add watermark if provided
            if watermark_path and os.path.exists(watermark_path):
                if progress_callback:
                    progress_callback(f"Adding watermark: {os.path.basename(watermark_path)}")
                
                # Create watermark clip with same duration as video
                watermark_clip = ImageClip(watermark_path).with_duration(clip.duration)
                # Position watermark at top-left corner (10, 10) like in the original function
                watermark_clip = watermark_clip.with_position((10, 10))
                
                # Composite video with watermark
                clip = CompositeVideoClip([clip, watermark_clip])
                
                if progress_callback:
                    progress_callback("Watermark added successfully")
            
            # Write video file with 48kHz audio
            clip.write_videofile(output_path, 
                                codec='libx264', 
                                audio_codec='aac', 
                                audio_fps=48000,  # 48kHz sample rate
                                audio_bitrate='128k',
                                threads=2, 
                                logger=None)
            
            # Clean up clips and audio
            if original_audio:
                original_audio.close()
            clip.close()
            if temp_out_path and os.path.exists(temp_out_path):
                os.remove(temp_out_path)
            return output_path
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error processing {os.path.basename(source_path)}: {e}")
            return None

    def _create_video_from_image_audio(self, input_image, input_audio, progress_callback=None):
        """
        Create a video from image and audio files
        
        Args:
            input_image: Path to image file
            input_audio: Path to audio file
            progress_callback: Optional callback function
            
        Returns:
            Path to created video file or None if failed
        """
        try:
            # if progress_callback:  # Clean up redundant logging
            #     progress_callback(f"Loading image: {os.path.basename(input_image)}")
            
            # Load audio to get duration
            audio_clip = AudioFileClip(input_audio)
            # Force resample to 48kHz for YouTube standard
            if audio_clip.fps != 48000:
                # if progress_callback:  # Clean up redundant logging
                #     progress_callback(f"Resampling audio from {audio_clip.fps}Hz to 48000Hz...")
                audio_clip = audio_clip.with_fps(48000)
            audio_duration = audio_clip.duration
            
            # if progress_callback:  # Clean up redundant logging
            #     progress_callback(f"Audio duration: {audio_duration:.2f} seconds")
            
            # Create video clip from image with audio duration
            image_clip = ImageClip(input_image).with_duration(audio_duration)
            image_clip = image_clip.with_fps(30)  # Set FPS for smooth playback
            
            # Apply smart cropping to maintain aspect ratio without distortion
            image_clip = self._apply_smart_cropping(image_clip, progress_callback)
            
            # Add audio to video
            video_clip = image_clip.with_audio(audio_clip)
            
            # Create temporary video file
            temp_video = tempfile.NamedTemporaryFile(suffix='.mp4', delete=False)
            temp_video_path = temp_video.name
            temp_video.close()
            
            if progress_callback:
                progress_callback("Creating video from image and audio...")
            
            # 🎯 GPU encoder detection and selection - Use direct FFmpeg instead of MoviePy
            if progress_callback:
                progress_callback("Detecting optimal video encoder (GPU/CPU)...")
            
            # Test if h264_nvenc encoder is available
            encoder_test_cmd = ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=0.1', '-c:v', 'h264_nvenc', '-f', 'null', '-']
            use_gpu_encoding = False
            try:
                test_result = subprocess.run(encoder_test_cmd, capture_output=True, text=True, timeout=10)
                if test_result.returncode == 0:
                    use_gpu_encoding = True
                    if progress_callback:
                        progress_callback("✅ GPU encoder available - will use direct FFmpeg with h264_nvenc")
                else:
                    if progress_callback:
                        progress_callback("🖥️  GPU encoder not available - using MoviePy with libx264")
            except Exception as e:
                if progress_callback:
                    progress_callback(f"⚠️  GPU test failed - using MoviePy with libx264: {str(e)[:100]}")
            
            if use_gpu_encoding:
                # Use direct FFmpeg call for GPU encoding
                if progress_callback:
                    progress_callback("Creating video with direct FFmpeg GPU encoding...")
                
                # Build FFmpeg command
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-loglevel', 'quiet',
                    '-loop', '1', '-i', input_image,
                    '-i', input_audio,
                    '-c:v', 'h264_nvenc',           # GPU encoder
                    '-preset', 'p4',                # NVENC preset
                    '-cq:v', '19',                  # Quality factor
                    '-c:a', 'aac',                  # Audio encoder
                    '-af', 'aresample=48000',       # Audio resample filter
                    '-ar', '48000',                 # 48kHz sample rate
                    '-ac', '2',                     # Stereo
                    '-b:a', '128k',                 # Audio bitrate
                    '-pix_fmt', 'yuv420p',          # Pixel format
                    '-r', '30',                     # Frame rate
                    '-shortest',                    # Use shortest stream
                    '-vsync', 'cfr',                # Constant frame rate
                    temp_video_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg GPU encoding failed: {result.stderr}")
                    
                if progress_callback:
                    progress_callback("✅ Direct FFmpeg GPU encoding completed")
            else:
                # Fallback to MoviePy CPU encoding
                if progress_callback:
                    progress_callback("Using MoviePy CPU encoding fallback...")
                
                # MoviePy write_videofile with compatible parameters
                write_params = {
                    'codec': 'libx264',
                    'audio_codec': 'aac',
                    'audio_bitrate': '128k',
                    'audio_fps': 48000,  # 48kHz sample rate (YouTube standard)
                    'preset': 'medium',
                    'threads': 2,
                    'logger': None
                }
                
                # Try with crf parameter, fallback without it if not supported
                try:
                    video_clip.write_videofile(
                        temp_video_path,
                        crf=23,
                        **write_params
                    )
                except TypeError:
                    # Older MoviePy version without crf support
                    video_clip.write_videofile(
                        temp_video_path,
                        **write_params
                    )
            
            # Clean up clips
            audio_clip.close()
            image_clip.close()
            video_clip.close()
            
            if progress_callback:
                progress_callback("Video created successfully from image and audio")
            
            return temp_video_path
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error creating video from image and audio: {e}")
            return None

    def _apply_smart_cropping(self, clip, progress_callback=None):
        """
        Apply smart cropping to maintain proper aspect ratio without distortion
        
        Args:
            clip: VideoClip to crop
            progress_callback: Optional callback function
            
        Returns:
            Cropped clip with proper aspect ratio
        """
        try:
            w, h = clip.size
            current_aspect = w / h
            
            # Determine target aspect ratio based on orientation
            if w > h:
                # Landscape: use 16:9 aspect ratio
                target_aspect = 16 / 9
                orientation = "landscape"
            else:
                # Portrait: use 9:16 aspect ratio
                target_aspect = 9 / 16
                orientation = "portrait"
            
            if progress_callback:
                progress_callback(f"Input: {w}x{h} ({orientation}, aspect: {current_aspect:.3f})")
                progress_callback(f"Target aspect: {target_aspect:.3f}")
            
            # Check if cropping is needed
            if abs(current_aspect - target_aspect) <= 0.01:
                if progress_callback:
                    progress_callback("No cropping needed - aspect ratio already correct")
                return clip
            
            # Calculate crop dimensions (center-based cropping)
            if current_aspect > target_aspect:
                # Image is wider than target - crop width (left and right)
                new_w = int(h * target_aspect)
                new_h = h
                x_offset = (w - new_w) // 2  # Center horizontally
                y_offset = 0
                if progress_callback:
                    progress_callback(f"Cropping width: {w} → {new_w} (removing {x_offset} pixels from each side)")
            else:
                # Image is taller than target - crop height (top and bottom)
                new_w = w
                new_h = int(w / target_aspect)
                x_offset = 0
                y_offset = (h - new_h) // 2  # Center vertically
                if progress_callback:
                    progress_callback(f"Cropping height: {h} → {new_h} (removing {y_offset} pixels from top and bottom)")
            
            # Apply center-based cropping
            cropped_clip = clip.with_effects([
                Crop(x1=x_offset, y1=y_offset, x2=x_offset + new_w, y2=y_offset + new_h)
            ])
            
            if progress_callback:
                progress_callback(f"Smart cropping applied: {new_w}x{new_h} (aspect: {new_w/new_h:.3f})")
            
            return cropped_clip
            
        except Exception as e:
            if progress_callback:
                progress_callback(f"Error in smart cropping: {e}")
            return clip  # Return original clip if cropping fails

    @staticmethod
    def _opencv_smooth_zoom(input_path, output_path, effect, fps, w, h, progress_callback=None):
        """
        Generate a smooth zoom in/out video using OpenCV per-frame affine transform.
        The center remains fixed, and zoom is linearly interpolated from 1.0 to 1.1 (in) or 1.1 to 1.0 (out).
        """
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        in_fps = cap.get(cv2.CAP_PROP_FPS) or fps
        if total_frames <= 1:
            total_frames = 2
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (w, h))
        if effect == "zoom_in":
            start_zoom, end_zoom = 1.0, 1.1
        else:
            start_zoom, end_zoom = 1.1, 1.0
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            alpha = i / (total_frames - 1)
            zoom = start_zoom + alpha * (end_zoom - start_zoom)
            # Build affine transform to keep center fixed
            center = (w / 2, h / 2)
            M = cv2.getRotationMatrix2D(center, 0, zoom)
            frame_zoomed = cv2.warpAffine(frame, M, (w, h), flags=cv2.INTER_LANCZOS4)
            writer.write(frame_zoomed)
            # Remove redundant zoom progress logging - already stable
            # if progress_callback and (i == 0 or i == total_frames // 2 or i == total_frames - 1):
            #     progress_callback(f"Zoom progress: {int((i+1) * 100 / total_frames)}%")
        cap.release()
        writer.release()

    @staticmethod
    def _opencv_smooth_pan(input_path, output_path, effect, fps, w, h, progress_callback=None):
        """
        Generate a smooth pan left/right video using OpenCV per-frame crop.
        For pan left: first frame's right edge aligns with output right, last frame is centered.
        For pan right: first frame's left edge aligns with output left, last frame is centered.
        Crop window matches 9:16 aspect ratio.
        """
        # Auto-detect orientation and set appropriate aspect ratio
        if w > h:
            # Landscape: use 16:9 aspect ratio
            aspect = 16 / 9
        else:
            # Portrait: use 9:16 aspect ratio
            aspect = 9 / 16
            
        if w / h > aspect:
            crop_w = int(h * aspect)
            crop_h = h
        else:
            crop_w = w
            crop_h = int(w / aspect)
        center_x = (w - crop_w) // 2
        if effect == "pan_left":
            start_x = w - crop_w  # right edge aligns
            end_x = center_x      # center
        else:  # pan_right
            start_x = 0          # left edge aligns
            end_x = center_x     # center
        cap = cv2.VideoCapture(input_path)
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        in_fps = cap.get(cv2.CAP_PROP_FPS) or fps
        if total_frames <= 1:
            total_frames = 2
        fourcc = cv2.VideoWriter_fourcc(*"mp4v")
        writer = cv2.VideoWriter(output_path, fourcc, fps, (crop_w, crop_h))
        for i in range(total_frames):
            ret, frame = cap.read()
            if not ret:
                break
            alpha = i / (total_frames - 1)
            x = int(round(start_x + (end_x - start_x) * alpha))
            y = 0 if crop_h == h else (h - crop_h) // 2
            # Crop window
            crop = frame[y:y+crop_h, x:x+crop_w]
            # If needed, resize to output size (shouldn't be needed, but for safety)
            if crop.shape[1] != crop_w or crop.shape[0] != crop_h:
                crop = cv2.resize(crop, (crop_w, crop_h), interpolation=cv2.INTER_LANCZOS4)
            writer.write(crop)
            # Only print progress at start, middle and end
            if progress_callback and (i == 0 or i == total_frames // 2 or i == total_frames - 1):
                progress_callback(f"Pan progress: {int((i+1) * 100 / total_frames)}%")
        cap.release()
        writer.release() 


def merge_audio_image_to_video_with_effects(input_mp3, input_image, output_video=None, effects: list = ["zoom_in", "zoom_out"], watermark_path=None) -> tuple[bool, str]:
    """
    Merges an audio file and a static image into a video file with effects and watermark.
    Uses the tested AfterEffectsProcess class for all processing.
    
    Args:
        input_mp3 (str): Path to the input audio file (MP3, WAV, M4A supported).
        input_image (str): Path to the input image file (e.g., JPG, PNG).
        output_video (str): Path for the output video file (e.g., MP4).
        effects (list, optional): List of effects to randomly choose from. Default: ["zoom_in", "zoom_out"]
        watermark_path (str, optional): Path to watermark image file.

    Returns:
        tuple[bool, str]: (success_status, output_path_or_error_message)
    """
    try:
        # First convert all paths to absolute paths
        input_mp3 = os.path.abspath(input_mp3)
        input_image = os.path.abspath(input_image)
        
        if not output_video: output_video = input_mp3.replace('.mp3', '.mp4')
        output_video = os.path.abspath(output_video)
        
        # Ensure output directory exists
        output_dir = os.path.dirname(output_video)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
        
        # Check if output file already exists
        if os.path.isfile(output_video): return True, output_video

        # Check if input files exist
        if not os.path.exists(input_mp3): return False, f"Error: Input audio file not found: {input_mp3}"
        if not os.path.exists(input_image): return False, f"Error: Input image file not found: {input_image}"
        
        # Default effects if not provided or None (but preserve empty list)
        if effects is None: 
            effects = ["zoom_in", "zoom_out"]
        
        # Create temporary output directory for AfterEffectsProcess
        temp_output_dir = os.path.dirname(output_video)
        processor = AfterEffectsProcess(output_folder=temp_output_dir)
        
        # Process with effects using our tested class
        result = processor.process_file(
            input_image=input_image,
            input_audio=input_mp3,
            effects=effects,
            watermark_path=watermark_path,
            skip_existed=False,  # Always process for this function
            progress_callback=print  # Use print function as progress_callback to show GPU/CPU info
        )
        
        if result: # Move result to expected output path if different
            if result != output_video: shutil.move(result, output_video)
            return True, output_video
        else: return False, "Error: Video processing failed"
            
    except Exception as e: return False, f"Error creating video: {str(e)}"



def add_subtitles_to_video(input_video_path: str, subtitle_path: str, output_video_path: str = None, font_size: int = None, outline_color: str = "&H00000000", background_box: bool = True, background_opacity: float = 0.5, language: str = 'english', force_redo = False) -> bool:
    try:
        if not os.path.exists(input_video_path): return print(f"Input video does not exist at {input_video_path}")
        if not os.path.exists(subtitle_path): return print(f"Subtitle file does not exist at {subtitle_path}")
        if os.path.isfile(output_video_path):
            if not force_redo: return print(f"Output video already exists at {output_video_path}")
            else: os.remove(output_video_path)
        
        # Get font information
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        # If returned value is file path, extract font directory and name
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            # If it's a font name (like "Ubuntu"), use directly
            font_name = font_info
        
        # Get video information
        video_info = {}
        try:
            cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_video_path}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if result and 'x' in result:
                video_width, video_height = map(int, result.split('x'))
                video_info['width'] = video_width
                video_info['height'] = video_height
                
                # Calculate appropriate font size based on video resolution if not provided
                if not font_size:
                    # Based on 1080p video with 20pt font as reference, then reduced by 20%
                    base_height = 1080
                    base_font_size = 16  # Originally 20, reduced 20% to 16
                    calculated_font_size = int(video_height / base_height * base_font_size)
                    # Set minimum and maximum font size limits, adjusted to smaller fonts
                    font_size = max(18, min(32, calculated_font_size))  # Min 18, Max 32
            
            # Adjust subtitle position based on video height
            margin_v = 30  # Use fixed pixel value, 30 pixels from bottom
        except Exception as e:
            # Default values
            font_size = font_size or 20
            margin_v = 60
        
        # Use ass filter to add subtitles (ass format has better format control than srt)
        # First convert SRT to ASS format
        ass_path = subtitle_path.replace('.srt', '.ass')
        convert_cmd = f'ffmpeg -y -loglevel quiet -i "{subtitle_path}" "{ass_path}"'
        try:
            # Execute SRT to ASS conversion
            subprocess.run(convert_cmd, shell=True, check=True)
            
            # Modify ASS file with custom styles
            if os.path.exists(ass_path):
                try:
                    # Read file content
                    with open(ass_path, 'r', encoding='utf-8') as f:
                        ass_content = f.read()
                    
                    # Use more precise way to modify styles
                    # Find style section lines
                    lines = ass_content.split('\n')
                    new_lines = []
                    
                    # Add flag to track if we've modified the style section
                    modified_style = False
                    
                    # Find [V4+ Styles] section and add our custom styles
                    in_style_section = False
                    
                    for i, line in enumerate(lines):
                        # Check if entering style section
                        if '[V4+ Styles]' in line:
                            in_style_section = True
                            new_lines.append(line)
                            continue
                            
                        # Check if leaving style section
                        if in_style_section and line.strip().startswith('['):
                            in_style_section = False
                            
                        # In style section, if encountered Format line (style definition line)
                        if in_style_section and line.strip().startswith('Format:'):
                            new_lines.append(line)
                            continue
                            
                        # If encountered Style: line in style section, replace it
                        if in_style_section and line.strip().startswith('Style:'):
                            # Extract style name
                            style_name = line.split(',')[0].strip().replace('Style:', '').strip()
                            
                            # Set background box based on parameters
                            if background_box:
                                # ASS color format test: use transparency value directly
                                # 0x00 = completely opaque, 0xFF = completely transparent
                                alpha_value = int(background_opacity * 255)  # Use transparency directly
                                alpha_hex = format(alpha_value, '02X')
                                back_colour = f"&H{alpha_hex}000000"  # Transparency + black background
                                border_style = 4  # BorderStyle=4 (opaque box)
                                outline_width = 0  # Remove outline, keep only background box
                                shadow_width = 0   # Shadow width
                            else:
                                back_colour = f"&H000000FF"  # Opaque red background for testing
                                border_style = 1  # Only outline, no background box
                                outline_width = 2  # Normal outline width
                                shadow_width = 0   # Shadow width
                            
                            # Create new style line, completely replace original style
                            # Alignment value 2 means bottom alignment (in ASS specification)
                            # If there's font file path, use complete path directly
                            font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
                            # Chinese fonts need to be bold
                            bold_value = 1 if language.lower() == 'chinese' else 0
                            new_style = f"Style: {style_name},{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},{bold_value},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_width},2,10,10,{margin_v}"
                            new_lines.append(new_style)
                            modified_style = True
                            continue
                        
                        # For other lines, keep unchanged
                        new_lines.append(line)
                    
                    # If no style was modified (exceptional case)
                    if not modified_style:
                        # Try to add font definition info directly in header
                        if '[Script Info]' in ass_content:
                            # Set background box based on parameters
                            if background_box:
                                alpha_hex = format(int(background_opacity * 255), '02X')
                                back_colour = f"&H{alpha_hex}000000"
                                border_style = 4
                                outline_width = 0  # Remove outline, keep only background box
                                shadow_width = 0   # Shadow width
                            else:
                                back_colour = f"&H000000FF"  # Opaque red background for testing
                                border_style = 1
                                outline_width = 2  # Normal outline width
                                shadow_width = 0   # Shadow width
                            
                            # Add font declaration after Script Info
                            # If there's font file path, use complete path directly
                            font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
                            # Chinese fonts need to be bold
                            bold_value = 1 if language.lower() == 'chinese' else 0
                            style_section = f"\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},{bold_value},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_width},2,10,10,{margin_v}\n"
                            ass_content = ass_content.replace('[Script Info]', f'[Script Info]{style_section}')
                    
                    # Recombine file content
                    ass_content = '\n'.join(new_lines)
                    
                    # Write back to file
                    with open(ass_path, 'w', encoding='utf-8') as f: f.write(ass_content)
                except Exception as e: print(f"Failed to modify ASS file, will use original: {str(e)}")
        except: ass_path = subtitle_path
        
        # Build ffmpeg command with font and style settings for beautiful subtitles
        # Use hwaccel to attempt GPU acceleration
        if os.path.exists(ass_path) and ass_path.endswith('.ass'):
            # Use ASS subtitles
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\":fontsdir={font_dir}" -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\"" -c:a copy "{output_video_path}"'
        else:
            # Fallback to SRT subtitles, specify font size and position
            # Alignment=2 means bottom alignment (in ASS specification)
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10\':fontsdir={font_dir}" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10\'" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
        
        # Execute command
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        
        # Verify output file
        if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0: return True
        else: return False
            
    except Exception as e: return False




def add_subtitles_to_video_portrait(input_video_path: str, subtitle_path: str, output_video_path: str = None, font_size: int = None, outline_color: str = "&H00000000", background_box: bool = True, background_opacity: float = 0.5, language = 'english', force_redo = False) -> bool:
    try:
        if not os.path.exists(input_video_path): return False
        if not os.path.exists(subtitle_path): return False
        if os.path.isfile(output_video_path):
            if not force_redo: return False
            else: os.remove(output_video_path)
        # Get font information
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        # If returned value is file path, extract font directory and name
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            # If it's a font name (like "Ubuntu"), use directly
            font_name = font_info
        print(f"Testing with font: {font_name}, font_dir: {font_dir}")
        
        # Get video information
        video_info = {}
        try:
            cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_video_path}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if result and 'x' in result:
                video_width, video_height = map(int, result.split('x'))
                video_info['width'] = video_width
                video_info['height'] = video_height
                print(f"Video dimensions: {video_width}x{video_height}")
                
                # Detect if video is portrait (aspect ratio < 1 means portrait)
                is_portrait = video_width / video_height < 1
                print(f"Video orientation: {'Portrait (9:16)' if is_portrait else 'Landscape'} ({video_width}x{video_height})")
                
                # Calculate appropriate font size based on video resolution if not provided
                # Font size calculation - scale based on video height
                if not font_size:
                    base_height = 1080
                    # For portrait, adjust font size to appropriate value, restore original size
                    if is_portrait:
                        base_font_size = 33  # Restore original 33
                        min_font = 22  # Adjusted from 27 to 22, adapted to landscape adjustment
                        max_font = 39  # Restore original 39
                    else:
                        base_font_size = 30  # Restore original 30
                        min_font = 24  # Restore original 24
                        max_font = 48  # Restore original 48
                    
                    calculated_font_size = int(video_height / base_height * base_font_size)
                    font_size = max(min_font, min(max_font, calculated_font_size))
                    print(f"Calculated font size for subtitles: {font_size} (for {'portrait' if is_portrait else 'landscape'} video)")
                else:
                    print(f"Using provided font size for subtitles: {font_size}")
                
                # Adjust subtitle position based on video orientation - place at bottom 25% position
                if is_portrait:
                    # Portrait videos use more appropriate bottom margin, corresponding to 25% of video height position
                    margin_v = int(video_height * 0.25)  # 25% of video height
                    margin_v = max(100, min(350, margin_v))  # Ensure margin is within reasonable range
                else:
                    margin_v = 60  # Landscape uses smaller fixed margin
                print(f"Using margin_v: {margin_v} for {'portrait' if is_portrait else 'landscape'} video - positioned at bottom 25%")
            
                # Set outline width
                outline_width = 3.0 if is_portrait else 2.0
                print(f"Using outline width: {outline_width} for {'portrait' if is_portrait else 'landscape'} video")
            
        except Exception as e:
            print(f"Failed to get video info: {str(e)}")
            # Default values, set smaller default values for portrait, also reduced by 20%
            font_size = font_size or 16  # Originally 20, reduced 20% to 16
            margin_v = 80
            outline_width = 2.5
        
        # Use ass filter to add subtitles (ass format has better format control than srt)
        # First convert SRT to ASS format
        ass_path = subtitle_path.replace('.srt', '.ass')
        if ass_path == subtitle_path:  # If file already has .ass suffix, avoid overwriting
            ass_path = subtitle_path + '.ass'
            
        # Delete existing ASS file first to ensure generating new one each time
        if os.path.exists(ass_path):
            os.remove(ass_path)
            print(f"Removed existing ASS file: {ass_path}")
            
        # Convert SRT to ASS base file
        convert_cmd = f'ffmpeg -y -loglevel quiet -i "{subtitle_path}" "{ass_path}"'
        subprocess.run(convert_cmd, shell=True, check=True)
        
        # Read ASS content
        with open(ass_path, 'r', encoding='utf-8') as f:
            ass_content = f.read()
        
        # Add automatic line wrapping settings to Script Info section
        play_res_x = int(video_width * 0.9)  # Set to 90% of video width, auto wrap when hitting edges
        
        # Create new Script Info section with automatic line wrapping settings
        new_script_info = """[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nPlayResX: {}\nPlayResY: {}\nScaledBorderAndShadow: yes\n\n""".format(play_res_x, video_height)
        
        # Find and replace [Script Info] section
        if '[Script Info]' in ass_content:
            import re
            ass_content = re.sub(r'\[Script Info\][^\[]*', new_script_info, ass_content)
        
        # Set background box based on parameters
        if background_box:
            # ASS color format: use transparency value directly
            alpha_value = int(background_opacity * 255)  # Use transparency directly
            alpha_hex = format(alpha_value, '02X')
            back_colour = f"&H{alpha_hex}000000"  # Transparency + black background
            border_style = 4  # BorderStyle=4 (opaque box)
            outline_width_final = 0  # Remove outline, keep only background box
            shadow_width = 0   # Shadow width
            print(f"Portrait background opacity: {background_opacity}, alpha_value: {alpha_value}, alpha_hex: {alpha_hex}")
        else:
            back_colour = "&H80000000"  # Default background color
            border_style = 1  # Only outline, no background box
            outline_width_final = outline_width  # Use original outline width
            shadow_width = 1   # Shadow width
        
        # Create custom style
        # If there's font file path, use complete path directly
        font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
        custom_style = f"Style: Default,{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},1,0,0,0,100,100,0,0,{border_style},{outline_width_final},{shadow_width},2,10,10,{margin_v}"
        
        # Replace style section
        if '[V4+ Styles]' in ass_content:
            # If there's style section, find Style: line and replace
            style_pattern = r'Style: [^\n]*'
            if re.search(style_pattern, ass_content):
                ass_content = re.sub(style_pattern, custom_style, ass_content)
            else:
                # If no Style line but has style section, add our style
                format_line = ass_content.find('Format:', ass_content.find('[V4+ Styles]'))
                if format_line > 0:
                    insert_pos = ass_content.find('\n', format_line) + 1
                    ass_content = ass_content[:insert_pos] + custom_style + '\n' + ass_content[insert_pos:]
        else:
            # If no style section, add complete style section
            style_section = f"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n{custom_style}\n\n"
            events_pos = ass_content.find('[Events]')
            if events_pos > 0:
                ass_content = ass_content[:events_pos] + style_section + ass_content[events_pos:]
            else:
                ass_content += '\n' + style_section
        
        # Write back updated ASS file
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        print(f"Created custom ASS file with auto line-wrap (PlayResX: {play_res_x}) and positioned at bottom 25% (margin_v={margin_v})")
        
        
        # Build ffmpeg command with font and style settings for beautiful subtitles
        # Use hwaccel to attempt GPU acceleration
        if os.path.exists(ass_path) and ass_path.endswith('.ass'):
            # Use ASS subtitles
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\":fontsdir={font_dir}" -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\"" -c:a copy "{output_video_path}"'
        else:
            # Fallback to SRT subtitles, specify font size and position, enhance outline for better readability
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10,Outline=3\':fontsdir={font_dir}" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10,Outline=3\'" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
        
        # Execute command
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        
        # Verify output file
        if os.path.exists(output_video_path) and os.path.getsize(output_video_path) > 0:
            print(f"Successfully added subtitles to video: {output_video_path}")
            return True
        else:
            print(f"Failed to add subtitles: output file does not exist or is empty")
            return False
            
    except Exception as e:
        print(f"Error adding subtitles to video: {str(e)}")
        return False




def create_video_with_subtitles_onestep(
    input_image: str,
    input_audio: str,
    subtitle_path: str,
    output_video: str,
    font_size: Optional[int] = None,
    outline_color: str = "&H00000000",
    background_box: bool = True,
    background_opacity: float = 0.5,
    language: str = 'english',
    is_portrait: bool = False,
    effects: Optional[List[str]] = None,
    watermark_path: Optional[str] = None,
    progress_callback=None
) -> bool:
    """
    One-step completion of image + audio + subtitles video generation
    
    Args:
        input_image: Input image path
        input_audio: Input audio path
        subtitle_path: Subtitle file path (SRT format)
        output_video: Output video path
        font_size: Font size (optional, auto-calculated if not provided)
        outline_color: Outline color
        background_box: Whether to show background box
        background_opacity: Background box opacity
        language: Language (english/chinese)
        is_portrait: Whether it's a portrait video
        effects: Effects list (reserved parameter, not implemented yet)
        watermark_path: Watermark image path
        progress_callback: Progress callback function
    
    Returns:
        bool: True if successful, False if failed
    """
    
    try:
        if progress_callback:
            progress_callback("Starting one-step video creation with subtitles...")
        
        # Verify input files
        if not os.path.exists(input_image):
            if progress_callback:
                progress_callback(f"Error: Image file not found: {input_image}")
            return False
            
        if not os.path.exists(input_audio):
            if progress_callback:
                progress_callback(f"Error: Audio file not found: {input_audio}")
            return False
            
        # Check subtitle file (if subtitles needed)
        has_subtitles = subtitle_path is not None and os.path.exists(subtitle_path)
        if subtitle_path is not None and not has_subtitles:
            if progress_callback:
                progress_callback(f"Error: Subtitle file not found: {subtitle_path}")
            return False
        
        # Get font information
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            font_name = font_info
        
        # Get video resolution (from image)
        probe_cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_image}"'
        result = subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip()
        
        if result and 'x' in result:
            video_width, video_height = map(int, result.split('x'))
        else:
            # Default resolution
            video_width = 1920 if not is_portrait else 1080
            video_height = 1080 if not is_portrait else 1920
        
        if progress_callback:
            progress_callback(f"Video dimensions: {video_width}x{video_height}")
        
        # Calculate font size (if not provided)
        if not font_size:
            base_height = 1080
            if is_portrait:
                # Font calculation for portrait videos
                if language.lower() == 'chinese':
                    base_font_size = 21  # Chinese portrait base font
                    min_font = 18
                    max_font = 39
                else:
                    base_font_size = 30  # English portrait base font
                    min_font = 24
                    max_font = 48
            else:
                # Font calculation for landscape videos
                base_font_size = 16  # Base font after 20% reduction
                min_font = 18
                max_font = 32
            
            calculated_font_size = int(video_height / base_height * base_font_size)
            font_size = max(min_font, min(max_font, calculated_font_size))
        
        # Calculate subtitle margins
        if is_portrait:
            margin_v = int(video_height * 0.25)  # Portrait: bottom 25% position
            margin_v = max(100, min(350, margin_v))
        else:
            margin_v = 30  # Landscape: fixed 30 pixels
        
        # Set outline width
        outline_width = 3.0 if is_portrait else 2.0
        
        # Detect GPU encoder
        use_gpu_encoding = False
        gpu_encoder = 'libx264'
        
        # Detect GPU in RunPod environment
        if os.environ.get('RUNPOD_POD_ID') or which_ubuntu == 'RunPod':
            test_cmd = ['ffmpeg', '-hide_banner', '-f', 'lavfi', '-i', 'nullsrc=s=256x256:d=0.1', 
                       '-c:v', 'h264_nvenc', '-f', 'null', '-']
            try:
                test_result = subprocess.run(test_cmd, capture_output=True, text=True)
                if test_result.returncode == 0:
                    use_gpu_encoding = True
                    gpu_encoder = 'h264_nvenc'
                    if progress_callback:
                        progress_callback("✅ GPU encoder available - will use h264_nvenc")
            except:
                pass
        
        # Build FFmpeg command
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-loop', '1', '-i', input_image,  # Image input
            '-i', input_audio,                # Audio input
        ]
        
        # Add video filters
        video_filters = []
        
        # Scale to target resolution
        video_filters.append(f"scale={video_width}:{video_height}:force_original_aspect_ratio=decrease")
        video_filters.append(f"pad={video_width}:{video_height}:(ow-iw)/2:(oh-ih)/2")
        video_filters.append("setsar=1")
        
        # Only add subtitle filter when subtitle file exists
        if has_subtitles:
            # Set style based on background box parameters
            if background_box:
                alpha_value = int(background_opacity * 255)
                alpha_hex = format(alpha_value, '02X')
                # ASS format: BorderStyle=4 means background box, Outline=0 removes outline
                border_style = "BorderStyle=4,Outline=0"
                back_colour = f"BackColour=&H{alpha_hex}000000"
            else:
                # BorderStyle=1 means outline only
                border_style = f"BorderStyle=1,Outline={outline_width}"
                back_colour = "BackColour=&H80000000"
            
            # Chinese text needs bold formatting
            bold_value = 1 if language.lower() == 'chinese' else 0
            
            # Build subtitle style string
            subtitle_style = (
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour={outline_color},"
                f"{back_colour},"
                f"Bold={bold_value},"
                f"{border_style},"
                f"Alignment=2,"  # Bottom center alignment
                f"MarginV={margin_v}"
            )
            
            # Add fontsdir parameter if font directory exists
            if font_dir:
                subtitle_filter = f"subtitles='{subtitle_path}':force_style='{subtitle_style}':fontsdir='{font_dir}'"
            else:
                subtitle_filter = f"subtitles='{subtitle_path}':force_style='{subtitle_style}'"
            
            # Add subtitle filter
            video_filters.append(subtitle_filter)
        
        # Handle filter combination
        if watermark_path and os.path.exists(watermark_path):
            # Case with watermark, use -filter_complex
            watermark_width = int(video_width / 8)  # Watermark width is 1/8 of video width
            
            if video_filters:
                # With both subtitles and watermark
                video_filters_str = ",".join(video_filters)
                # Use filter_complex to combine subtitles and watermark
                filter_complex = f"[0:v]{video_filters_str}[v];movie={watermark_path},scale={watermark_width}:-1[watermark];[v][watermark]overlay=10:10"
                cmd.extend([
                    '-filter_complex', filter_complex,
                ])
            else:
                # Only watermark, no subtitles
                filter_complex = f"movie={watermark_path},scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=10:10"
                cmd.extend([
                    '-filter_complex', filter_complex,
                ])
            
            if progress_callback:
                progress_callback(f"Adding watermark from: {watermark_path}")
        else:
            # Case without watermark
            if video_filters:
                # Only subtitles, use -vf
                video_filters_str = ",".join(video_filters)
                cmd.extend([
                    '-vf', video_filters_str,
                ])
        
        cmd.extend([
            '-c:v', gpu_encoder,              # Video encoder
        ])
        
        # GPU encoding parameters
        if use_gpu_encoding:
            cmd.extend([
                '-preset', 'p4',              # NVENC preset
                '-cq:v', '19',                # Quality factor
            ])
        else:
            cmd.extend([
                '-preset', 'medium',
                '-crf', '23',
            ])
        
        # Audio parameters - ensure 48kHz output
        cmd.extend([
            '-c:a', 'aac',                    # Audio encoder
            '-af', 'aresample=48000',         # Audio resample filter
            '-ar', '48000',                   # 48kHz sample rate
            '-ac', '2',                       # Stereo
            '-b:a', '128k',                   # Audio bitrate
            '-pix_fmt', 'yuv420p',            # Pixel format
            '-r', '30',                       # Frame rate
            '-shortest',                      # Use shortest stream
            '-vsync', 'cfr',                  # Constant frame rate
            '-movflags', '+faststart',        # Optimize streaming playback
            output_video
        ])
        
        if progress_callback:
            progress_callback(f"Executing FFmpeg command with {gpu_encoder} encoder...")
        
        # Execute command
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            if progress_callback:
                progress_callback(f"FFmpeg error: {result.stderr}")
            return False
        
        # Verify output file
        if os.path.exists(output_video) and os.path.getsize(output_video) > 0:
            if progress_callback:
                progress_callback(f"✅ Video created successfully: {output_video}")
            return True
        else:
            if progress_callback:
                progress_callback("Error: Output file not created or empty")
            return False
            
    except Exception as e:
        if progress_callback:
            progress_callback(f"Exception: {str(e)}")
        return False
