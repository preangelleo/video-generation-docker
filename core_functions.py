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
    根据运行环境和语言返回合适的字体名称
    
    Args:
        language (str): 语言类型，'chinese'（默认）或 'english'
    
    Returns:
        str: 字体名称或字体文件路径
    """
    import subprocess
    if language.lower() == 'english':
        # 英文使用Ubuntu字体
        font_name = "Ubuntu"
    else:
        # 中文优先使用霞鹜文楷 Bold
        # 所有系统都优先检查霞鹜文楷
        if which_ubuntu in ['TB', 'AWS', 'RunPod']:
            # Linux系统 - 先检查系统是否安装了霞鹜文楷
            
            try:
                result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True)
                if 'LXGW WenKai' in result.stdout:
                    # 系统已安装，返回字体名称（不是路径）
                    return "LXGW WenKai Bold"
            except:
                pass
            
            # 检查字体文件是否存在
            font_paths = [
                # 最优先：霞鹜文楷 Bold
                "/usr/share/fonts/truetype/lxgw/LXGWWenKai-Bold.ttf",
                "/usr/local/share/fonts/LXGWWenKai-Bold.ttf",
                "/home/ubuntu/.local/share/fonts/LXGWWenKai-Bold.ttf",
                # 备选：思源黑体
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Bold.ttc",
                "/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-zenhei.ttc",
                "/usr/share/fonts/truetype/wqy/wqy-microhei.ttc"
            ]
            for path in font_paths:
                if os.path.exists(path):
                    # 如果是霞鹜文楷，返回字体名称而不是路径
                    if 'lxgw' in path.lower() or 'LXGWWenKai' in path:
                        return "LXGW WenKai Bold"
                    else:
                        # 其他字体返回路径
                        return path
            # 如果没找到中文字体，返回Ubuntu作为后备
            font_name = "Ubuntu"
        else:
            # Mac系统 - 也优先使用霞鹜文楷
            # 先检查系统是否安装了霞鹜文楷
            try:
                result = subprocess.run(['fc-list', ':family'], capture_output=True, text=True)
                if 'LXGW WenKai' in result.stdout or '霞鹜文楷' in result.stdout:
                    # 系统已安装，直接使用字体名称
                    font_name = "LXGW WenKai"
                    return font_name
            except:
                pass
            
            # 如果系统没有安装，检查本地字体文件
            mac_font_paths = [
                "/Library/Fonts/LXGWWenKai-Bold.ttf",
                os.path.expanduser("~/Library/Fonts/LXGWWenKai-Bold.ttf")
            ]
            
            for path in mac_font_paths:
                if os.path.exists(path):
                    # 如果是系统字体目录，返回字体名称而不是路径
                    if path.startswith("/Library/Fonts/") or path.startswith(os.path.expanduser("~/Library/Fonts/")):
                        font_name = "LXGW WenKai"
                        return font_name
                    else:
                        # 项目内的字体文件，返回路径
                        return path
            
            # 如果没找到霞鹜文楷，使用默认的思源黑体
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
                # 移除冗余的特效选择日志
                # if progress_callback:
                #     progress_callback(f"Selected '{chosen_effect}' from effects list: {effects}")
            elif effect and effect != "random":
                # Priority 2: Use specified single effect
                chosen_effect = effect
            else:
                # Priority 3: Random from all available effects
                chosen_effect = random.choice([e for e in EFFECTS if e != "random"])
            # 移除冗余的特效应用日志
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
                    # if progress_callback:  # 清理冗余日志
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
                    # if progress_callback:  # 清理冗余日志
                    #     progress_callback("Audio restored from original video")
            w, h = clip.size
            
            # Auto-detect orientation and set appropriate aspect ratio
            if w > h:
                # Landscape: use 16:9 aspect ratio
                aspect = 16 / 9
                # 移除冗余的格式检测日志
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
                # 移除冗余的aspect ratio日志
                # if progress_callback:
                #     progress_callback(f"Video already has correct aspect ratio ({current_aspect:.3f}), no cropping needed")
                pass  # 需要pass语句来满足Python语法要求
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
            
            # 写入视频文件，确保音频为48kHz
            clip.write_videofile(output_path, 
                                codec='libx264', 
                                audio_codec='aac', 
                                audio_fps=48000,  # 48kHz采样率
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
            # if progress_callback:  # 清理冗余日志
            #     progress_callback(f"Loading image: {os.path.basename(input_image)}")
            
            # Load audio to get duration
            audio_clip = AudioFileClip(input_audio)
            # 强制重采样到48kHz以符合YouTube标准
            if audio_clip.fps != 48000:
                # if progress_callback:  # 清理冗余日志
                #     progress_callback(f"Resampling audio from {audio_clip.fps}Hz to 48000Hz...")
                audio_clip = audio_clip.with_fps(48000)
            audio_duration = audio_clip.duration
            
            # if progress_callback:  # 清理冗余日志
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
            
            # 🎯 GPU编码器检测和选择 - 使用直接FFmpeg调用而非MoviePy
            if progress_callback:
                progress_callback("Detecting optimal video encoder (GPU/CPU)...")
            
            # 测试h264_nvenc编码器是否可用
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
                # 使用直接FFmpeg调用进行GPU编码
                if progress_callback:
                    progress_callback("Creating video with direct FFmpeg GPU encoding...")
                
                # 构建FFmpeg命令
                ffmpeg_cmd = [
                    'ffmpeg', '-y', '-loglevel', 'quiet',
                    '-loop', '1', '-i', input_image,
                    '-i', input_audio,
                    '-c:v', 'h264_nvenc',           # GPU编码器
                    '-preset', 'p4',                # NVENC预设
                    '-cq:v', '19',                  # 质量因子
                    '-c:a', 'aac',                  # 音频编码器
                    '-af', 'aresample=48000',       # 音频重采样滤镜
                    '-ar', '48000',                 # 48kHz采样率
                    '-ac', '2',                     # 立体声
                    '-b:a', '128k',                 # 音频比特率
                    '-pix_fmt', 'yuv420p',          # 像素格式
                    '-r', '30',                     # 帧率
                    '-shortest',                    # 以最短流为准
                    '-vsync', 'cfr',                # 固定帧率
                    temp_video_path
                ]
                
                result = subprocess.run(ffmpeg_cmd, capture_output=True, text=True)
                if result.returncode != 0:
                    raise Exception(f"FFmpeg GPU encoding failed: {result.stderr}")
                    
                if progress_callback:
                    progress_callback("✅ Direct FFmpeg GPU encoding completed")
            else:
                # 回退到MoviePy的CPU编码
                if progress_callback:
                    progress_callback("Using MoviePy CPU encoding fallback...")
                
                # MoviePy write_videofile with compatible parameters
                write_params = {
                    'codec': 'libx264',
                    'audio_codec': 'aac',
                    'audio_bitrate': '128k',
                    'audio_fps': 48000,  # 48kHz采样率（YouTube标准）
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
            # 移除冗余的zoom进度日志，已经很稳定了
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
            # 只在开始、中间和结束时打印进度
            if progress_callback and (i == 0 or i == total_frames // 2 or i == total_frames - 1):
                progress_callback(f"Pan progress: {int((i+1) * 100 / total_frames)}%")
        cap.release()
        writer.release() 


def merge_audio_image_to_video_with_effects(input_mp3, input_image, output_video=None, effects: list = ["zoom_in", "zoom_out"], watermark_path=None) -> tuple[bool, str]:
    """
    Merges an MP3 audio file and a static image into a video file with effects and watermark.
    Uses the tested AfterEffectsProcess class for all processing.
    
    Args:
        input_mp3 (str): Path to the input MP3 file.
        input_image (str): Path to the input image file (e.g., JPG, PNG).
        output_video (str): Path for the output video file (e.g., MP4).
        effects (list, optional): List of effects to randomly choose from. Default: ["zoom_in", "zoom_out"]
        watermark_path (str, optional): Path to watermark image file.

    Returns:
        tuple[bool, str]: (success_status, output_path_or_error_message)
    """
    try:
        # 首先将所有路径转换为绝对路径
        input_mp3 = os.path.abspath(input_mp3)
        input_image = os.path.abspath(input_image)
        
        if not output_video: output_video = input_mp3.replace('.mp3', '.mp4')
        output_video = os.path.abspath(output_video)
        
        # 确保输出目录存在
        output_dir = os.path.dirname(output_video)
        if not os.path.exists(output_dir): os.makedirs(output_dir, exist_ok=True)
        
        # 检查是否已经存在输出文件
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
            progress_callback=print  # 使用print函数作为progress_callback以显示GPU/CPU信息
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
        
        # 获取字体信息
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        # 如果返回的是文件路径，提取字体目录和字体名称
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            # 如果是字体名称（如 "Ubuntu"），直接使用
            font_name = font_info
        
        # 获取视频信息
        video_info = {}
        try:
            cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_video_path}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if result and 'x' in result:
                video_width, video_height = map(int, result.split('x'))
                video_info['width'] = video_width
                video_info['height'] = video_height
                
                # 根据视频分辨率计算合适的字体大小，如果没有提供
                if not font_size:
                    # 根据1080p视频20号字体为基准进行等比例计算，然后减小20%
                    base_height = 1080
                    base_font_size = 16  # 原来20，减小20%后为16
                    calculated_font_size = int(video_height / base_height * base_font_size)
                    # 设置最小和最大字体大小限制，调整为更小的字体
                    font_size = max(18, min(32, calculated_font_size))  # 最小18，最大32
            
            # 根据视频高度调整字幕位置
            margin_v = 30  # 使用固定像素值，距离底部30像素
        except Exception as e:
            # 默认值
            font_size = font_size or 20
            margin_v = 60
        
        # 使用ass过滤器添加字幕 (ass格式比srt有更好的格式控制)
        # 先将SRT转换为ASS格式
        ass_path = subtitle_path.replace('.srt', '.ass')
        convert_cmd = f'ffmpeg -y -loglevel quiet -i "{subtitle_path}" "{ass_path}"'
        try:
            # 执行SRT到ASS的转换
            subprocess.run(convert_cmd, shell=True, check=True)
            
            # 修改ASS文件，自定义样式
            if os.path.exists(ass_path):
                try:
                    # 读取文件内容
                    with open(ass_path, 'r', encoding='utf-8') as f:
                        ass_content = f.read()
                    
                    # 使用更精确的方式修改样式
                    # 查找样式部分的行
                    lines = ass_content.split('\n')
                    new_lines = []
                    
                    # 添加一个标志来跟踪我们是否已修改样式部分
                    modified_style = False
                    
                    # 找到[V4+ Styles]部分并添加我们的自定义样式
                    in_style_section = False
                    
                    for i, line in enumerate(lines):
                        # 检查是否进入样式部分
                        if '[V4+ Styles]' in line:
                            in_style_section = True
                            new_lines.append(line)
                            continue
                            
                        # 检查是否离开样式部分
                        if in_style_section and line.strip().startswith('['):
                            in_style_section = False
                            
                        # 在样式部分中，如果进入了Format行（样式定义行）
                        if in_style_section and line.strip().startswith('Format:'):
                            new_lines.append(line)
                            continue
                            
                        # 如果在样式部分中遇到Style:行，替换它
                        if in_style_section and line.strip().startswith('Style:'):
                            # 提取样式名称
                            style_name = line.split(',')[0].strip().replace('Style:', '').strip()
                            
                            # 根据参数设置背景框
                            if background_box:
                                # ASS颜色格式测试：直接使用透明度值
                                # 0x00 = 完全不透明, 0xFF = 完全透明
                                alpha_value = int(background_opacity * 255)  # 直接使用透明度
                                alpha_hex = format(alpha_value, '02X')
                                back_colour = f"&H{alpha_hex}000000"  # 透明度+黑色背景
                                border_style = 4  # BorderStyle=4 (opaque box)
                                outline_width = 0  # 去掉描边，只保留背景框
                                shadow_width = 0   # 阴影宽度
                            else:
                                back_colour = f"&H000000FF"  # 不透明红色背景，用于测试
                                border_style = 1  # 只有描边，无背景框
                                outline_width = 2  # 正常描边宽度
                                shadow_width = 0   # 阴影宽度
                            
                            # 创建新的样式行，完全替换原有样式
                            # 对齐值使用2表示底部对齐（ASS规范中）
                            # 如果有字体文件路径，直接使用完整路径
                            font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
                            # 中文字体需要加粗
                            bold_value = 1 if language.lower() == 'chinese' else 0
                            new_style = f"Style: {style_name},{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},{bold_value},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_width},2,10,10,{margin_v}"
                            new_lines.append(new_style)
                            modified_style = True
                            continue
                        
                        # 对于其他行，保持不变
                        new_lines.append(line)
                    
                    # 如果没有修改任何样式（异常情况）
                    if not modified_style:
                        # 尝试直接在头部添加字体定义信息
                        if '[Script Info]' in ass_content:
                            # 根据参数设置背景框
                            if background_box:
                                alpha_hex = format(int(background_opacity * 255), '02X')
                                back_colour = f"&H{alpha_hex}000000"
                                border_style = 4
                                outline_width = 0  # 去掉描边，只保留背景框
                                shadow_width = 0   # 阴影宽度
                            else:
                                back_colour = f"&H000000FF"  # 不透明红色背景，用于测试
                                border_style = 1
                                outline_width = 2  # 正常描边宽度
                                shadow_width = 0   # 阴影宽度
                            
                            # 在Script Info后添加字体声明
                            # 如果有字体文件路径，直接使用完整路径
                            font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
                            # 中文字体需要加粗
                            bold_value = 1 if language.lower() == 'chinese' else 0
                            style_section = f"\n[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\nStyle: Default,{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},{bold_value},0,0,0,100,100,0,0,{border_style},{outline_width},{shadow_width},2,10,10,{margin_v}\n"
                            ass_content = ass_content.replace('[Script Info]', f'[Script Info]{style_section}')
                    
                    # 重新组合文件内容
                    ass_content = '\n'.join(new_lines)
                    
                    # 写回文件
                    with open(ass_path, 'w', encoding='utf-8') as f: f.write(ass_content)
                except Exception as e: print(f"Failed to modify ASS file, will use original: {str(e)}")
        except: ass_path = subtitle_path
        
        # 构建ffmpeg命令，使用字体和样式设置美化字幕
        # 使用hwaccel尝试启用GPU加速
        if os.path.exists(ass_path) and ass_path.endswith('.ass'):
            # 使用ASS字幕
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\":fontsdir={font_dir}" -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\"" -c:a copy "{output_video_path}"'
        else:
            # 回退到SRT字幕，指定字体大小和位置
            # Alignment=2表示底部对齐（ASS规范中）
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10\':fontsdir={font_dir}" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10\'" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
        
        # 执行命令
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        
        # 验证输出文件
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
        # 获取字体信息
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        # 如果返回的是文件路径，提取字体目录和字体名称
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            # 如果是字体名称（如 "Ubuntu"），直接使用
            font_name = font_info
        print(f"Testing with font: {font_name}, font_dir: {font_dir}")
        
        # 获取视频信息
        video_info = {}
        try:
            cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_video_path}"'
            result = subprocess.check_output(cmd, shell=True).decode('utf-8').strip()
            if result and 'x' in result:
                video_width, video_height = map(int, result.split('x'))
                video_info['width'] = video_width
                video_info['height'] = video_height
                print(f"Video dimensions: {video_width}x{video_height}")
                
                # 检测视频是否为竖屏（宽高比小于1表示竖屏）
                is_portrait = video_width / video_height < 1
                print(f"Video orientation: {'Portrait (9:16)' if is_portrait else 'Landscape'} ({video_width}x{video_height})")
                
                # 根据视频分辨率计算合适的字体大小，如果没有提供
                # 字体大小计算 - 根据视频高度缩放
                if not font_size:
                    base_height = 1080
                    # 对于竖屏，字体大小调整为适合的值，恢复原来的大小
                    if is_portrait:
                        base_font_size = 33  # 恢复原来的33
                        min_font = 22  # 从27调整为22，适应横屏的调整
                        max_font = 39  # 恢复原来的39
                    else:
                        base_font_size = 30  # 恢复原来的30
                        min_font = 24  # 恢复原来的24
                        max_font = 48  # 恢复原来的48
                    
                    calculated_font_size = int(video_height / base_height * base_font_size)
                    font_size = max(min_font, min(max_font, calculated_font_size))
                    print(f"Calculated font size for subtitles: {font_size} (for {'portrait' if is_portrait else 'landscape'} video)")
                else:
                    print(f"Using provided font size for subtitles: {font_size}")
                
                # 根据视频方向调整字幕位置 - 放在底部25%位置
                if is_portrait:
                    # 竖屏视频使用更合适的底部边距，对应于视频25%高度的位置
                    margin_v = int(video_height * 0.25)  # 视频高度的25%
                    margin_v = max(100, min(350, margin_v))  # 保证边距在合理范围内
                else:
                    margin_v = 60  # 横屏使用较小的固定边距
                print(f"Using margin_v: {margin_v} for {'portrait' if is_portrait else 'landscape'} video - positioned at bottom 25%")
            
                # 设置描边宽度
                outline_width = 3.0 if is_portrait else 2.0
                print(f"Using outline width: {outline_width} for {'portrait' if is_portrait else 'landscape'} video")
            
        except Exception as e:
            print(f"Failed to get video info: {str(e)}")
            # 默认值，针对竖屏设置更小的默认值，也减小20%
            font_size = font_size or 16  # 原来20，减小20%后为16
            margin_v = 80
            outline_width = 2.5
        
        # 使用ass过滤器添加字幕 (ass格式比srt有更好的格式控制)
        # 先将SRT转换为ASS格式
        ass_path = subtitle_path.replace('.srt', '.ass')
        if ass_path == subtitle_path:  # 如果文件已经是.ass后缀，避免覆盖
            ass_path = subtitle_path + '.ass'
            
        # 先删除现有的ASS文件，确保每次生成新的
        if os.path.exists(ass_path):
            os.remove(ass_path)
            print(f"Removed existing ASS file: {ass_path}")
            
        # 转换SRT为ASS基础文件
        convert_cmd = f'ffmpeg -y -loglevel quiet -i "{subtitle_path}" "{ass_path}"'
        subprocess.run(convert_cmd, shell=True, check=True)
        
        # 读取ASS内容
        with open(ass_path, 'r', encoding='utf-8') as f:
            ass_content = f.read()
        
        # 添加自动换行设置到Script Info部分
        play_res_x = int(video_width * 0.9)  # 设置为视频宽度的90%，碰到边缘自动换行
        
        # 创建新的Script Info部分，包含自动换行设置
        new_script_info = """[Script Info]\nScriptType: v4.00+\nWrapStyle: 2\nPlayResX: {}\nPlayResY: {}\nScaledBorderAndShadow: yes\n\n""".format(play_res_x, video_height)
        
        # 找到并替换[Script Info]部分
        if '[Script Info]' in ass_content:
            import re
            ass_content = re.sub(r'\[Script Info\][^\[]*', new_script_info, ass_content)
        
        # 根据参数设置背景框
        if background_box:
            # ASS颜色格式：直接使用透明度值
            alpha_value = int(background_opacity * 255)  # 直接使用透明度
            alpha_hex = format(alpha_value, '02X')
            back_colour = f"&H{alpha_hex}000000"  # 透明度+黑色背景
            border_style = 4  # BorderStyle=4 (opaque box)
            outline_width_final = 0  # 去掉描边，只保留背景框
            shadow_width = 0   # 阴影宽度
            print(f"Portrait background opacity: {background_opacity}, alpha_value: {alpha_value}, alpha_hex: {alpha_hex}")
        else:
            back_colour = "&H80000000"  # 默认背景色
            border_style = 1  # 只有描边，无背景框
            outline_width_final = outline_width  # 使用原来的描边宽度
            shadow_width = 1   # 阴影宽度
        
        # 创建自定义样式
        # 如果有字体文件路径，直接使用完整路径
        font_for_ass = font_info if (isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf')) else font_name
        custom_style = f"Style: Default,{font_for_ass},{font_size},&H00FFFFFF,&H00000000,{outline_color},{back_colour},1,0,0,0,100,100,0,0,{border_style},{outline_width_final},{shadow_width},2,10,10,{margin_v}"
        
        # 替换样式部分
        if '[V4+ Styles]' in ass_content:
            # 如果有样式部分，找到Style:行并替换
            style_pattern = r'Style: [^\n]*'
            if re.search(style_pattern, ass_content):
                ass_content = re.sub(style_pattern, custom_style, ass_content)
            else:
                # 如果没有Style行但有样式部分，添加我们的样式
                format_line = ass_content.find('Format:', ass_content.find('[V4+ Styles]'))
                if format_line > 0:
                    insert_pos = ass_content.find('\n', format_line) + 1
                    ass_content = ass_content[:insert_pos] + custom_style + '\n' + ass_content[insert_pos:]
        else:
            # 如果没有样式部分，添加完整的样式部分
            style_section = f"[V4+ Styles]\nFormat: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Italic, Underline, StrikeOut, ScaleX, ScaleY, Spacing, Angle, BorderStyle, Outline, Shadow, Alignment, MarginL, MarginR, MarginV, Encoding\n{custom_style}\n\n"
            events_pos = ass_content.find('[Events]')
            if events_pos > 0:
                ass_content = ass_content[:events_pos] + style_section + ass_content[events_pos:]
            else:
                ass_content += '\n' + style_section
        
        # 写回更新的ASS文件
        with open(ass_path, 'w', encoding='utf-8') as f:
            f.write(ass_content)
        print(f"Created custom ASS file with auto line-wrap (PlayResX: {play_res_x}) and positioned at bottom 25% (margin_v={margin_v})")
        
        
        # 构建ffmpeg命令，使用字体和样式设置美化字幕
        # 使用hwaccel尝试启用GPU加速
        if os.path.exists(ass_path) and ass_path.endswith('.ass'):
            # 使用ASS字幕
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\":fontsdir={font_dir}" -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "ass=\"{ass_path}\"" -c:a copy "{output_video_path}"'
        else:
            # 回退到SRT字幕，指定字体大小和位置，并增强描边以提高可读性
            if font_dir:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10,Outline=3\':fontsdir={font_dir}" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
            else:
                ffmpeg_cmd = f'ffmpeg -y -loglevel quiet -hwaccel auto -i "{input_video_path}" -vf "subtitles=\"{subtitle_path}\":force_style=\'FontSize={font_size},FontName={font_name},MarginV={margin_v},PrimaryColour=&H00FFFFFF,OutlineColour={outline_color},BackColour=&H80000000,Bold=1,Italic=0,Alignment=2,MarginL=10,MarginR=10,Outline=3\'" -c:v libx264 -preset medium -crf 23 -c:a copy "{output_video_path}"'
        
        # 执行命令
        subprocess.run(ffmpeg_cmd, shell=True, check=True)
        
        # 验证输出文件
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
    一步完成图片+音频+字幕的视频生成
    
    参数:
        input_image: 输入图片路径
        input_audio: 输入音频路径
        subtitle_path: 字幕文件路径 (SRT格式)
        output_video: 输出视频路径
        font_size: 字体大小 (可选，不提供则自动计算)
        outline_color: 描边颜色
        background_box: 是否显示背景框
        background_opacity: 背景框透明度
        language: 语言 (english/chinese)
        is_portrait: 是否为竖屏视频
        effects: 特效列表 (保留参数，暂不实现)
        watermark_path: 水印图片路径
        progress_callback: 进度回调函数
    
    返回:
        bool: 成功返回True，失败返回False
    """
    
    try:
        if progress_callback:
            progress_callback("Starting one-step video creation with subtitles...")
        
        # 验证输入文件
        if not os.path.exists(input_image):
            if progress_callback:
                progress_callback(f"Error: Image file not found: {input_image}")
            return False
            
        if not os.path.exists(input_audio):
            if progress_callback:
                progress_callback(f"Error: Audio file not found: {input_audio}")
            return False
            
        # 检查字幕文件（如果需要字幕）
        has_subtitles = subtitle_path is not None and os.path.exists(subtitle_path)
        if subtitle_path is not None and not has_subtitles:
            if progress_callback:
                progress_callback(f"Error: Subtitle file not found: {subtitle_path}")
            return False
        
        # 获取字体信息
        font_info = get_local_font(language)
        font_dir = ""
        font_name = font_info
        
        if isinstance(font_info, str) and os.path.exists(font_info) and font_info.endswith('.ttf'):
            font_dir = os.path.dirname(font_info)
            font_name = os.path.basename(font_info).replace('.ttf', '')
        elif isinstance(font_info, str) and '/' not in font_info:
            font_name = font_info
        
        # 获取视频分辨率（从图片）
        probe_cmd = f'ffprobe -v error -select_streams v:0 -show_entries stream=width,height -of csv=p=0:s=x "{input_image}"'
        result = subprocess.check_output(probe_cmd, shell=True).decode('utf-8').strip()
        
        if result and 'x' in result:
            video_width, video_height = map(int, result.split('x'))
        else:
            # 默认分辨率
            video_width = 1920 if not is_portrait else 1080
            video_height = 1080 if not is_portrait else 1920
        
        if progress_callback:
            progress_callback(f"Video dimensions: {video_width}x{video_height}")
        
        # 计算字体大小（如果未提供）
        if not font_size:
            base_height = 1080
            if is_portrait:
                # 竖屏视频的字体计算
                if language.lower() == 'chinese':
                    base_font_size = 21  # 中文竖屏基础字体
                    min_font = 18
                    max_font = 39
                else:
                    base_font_size = 30  # 英文竖屏基础字体
                    min_font = 24
                    max_font = 48
            else:
                # 横屏视频的字体计算
                base_font_size = 16  # 减小20%后的基础字体
                min_font = 18
                max_font = 32
            
            calculated_font_size = int(video_height / base_height * base_font_size)
            font_size = max(min_font, min(max_font, calculated_font_size))
        
        # 计算字幕边距
        if is_portrait:
            margin_v = int(video_height * 0.25)  # 竖屏：底部25%位置
            margin_v = max(100, min(350, margin_v))
        else:
            margin_v = 30  # 横屏：固定30像素
        
        # 设置描边宽度
        outline_width = 3.0 if is_portrait else 2.0
        
        # 检测GPU编码器
        use_gpu_encoding = False
        gpu_encoder = 'libx264'
        
        # 在RunPod环境检测GPU
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
        
        # 构建FFmpeg命令
        cmd = [
            'ffmpeg', '-y', '-loglevel', 'error',
            '-loop', '1', '-i', input_image,  # 图片输入
            '-i', input_audio,                # 音频输入
        ]
        
        # 添加视频滤镜
        video_filters = []
        
        # 缩放到目标分辨率
        video_filters.append(f"scale={video_width}:{video_height}:force_original_aspect_ratio=decrease")
        video_filters.append(f"pad={video_width}:{video_height}:(ow-iw)/2:(oh-ih)/2")
        video_filters.append("setsar=1")
        
        # 只有在有字幕文件时才添加字幕滤镜
        if has_subtitles:
            # 根据背景框设置样式
            if background_box:
                alpha_value = int(background_opacity * 255)
                alpha_hex = format(alpha_value, '02X')
                # ASS格式：BorderStyle=4表示背景框，Outline=0去掉描边
                border_style = "BorderStyle=4,Outline=0"
                back_colour = f"BackColour=&H{alpha_hex}000000"
            else:
                # BorderStyle=1表示只有描边
                border_style = f"BorderStyle=1,Outline={outline_width}"
                back_colour = "BackColour=&H80000000"
            
            # 中文需要加粗
            bold_value = 1 if language.lower() == 'chinese' else 0
            
            # 构建字幕样式字符串
            subtitle_style = (
                f"FontName={font_name},"
                f"FontSize={font_size},"
                f"PrimaryColour=&H00FFFFFF,"
                f"OutlineColour={outline_color},"
                f"{back_colour},"
                f"Bold={bold_value},"
                f"{border_style},"
                f"Alignment=2,"  # 底部居中
                f"MarginV={margin_v}"
            )
            
            # 如果有字体目录，添加fontsdir参数
            if font_dir:
                subtitle_filter = f"subtitles='{subtitle_path}':force_style='{subtitle_style}':fontsdir='{font_dir}'"
            else:
                subtitle_filter = f"subtitles='{subtitle_path}':force_style='{subtitle_style}'"
            
            # 添加字幕滤镜
            video_filters.append(subtitle_filter)
        
        # 处理滤镜组合
        if watermark_path and os.path.exists(watermark_path):
            # 有水印的情况，使用 -filter_complex
            watermark_width = int(video_width / 8)  # 水印宽度为视频宽度的 1/8
            
            if video_filters:
                # 有字幕和水印
                video_filters_str = ",".join(video_filters)
                # 使用 filter_complex 组合字幕和水印
                filter_complex = f"[0:v]{video_filters_str}[v];movie={watermark_path},scale={watermark_width}:-1[watermark];[v][watermark]overlay=10:10"
                cmd.extend([
                    '-filter_complex', filter_complex,
                ])
            else:
                # 只有水印，没有字幕
                filter_complex = f"movie={watermark_path},scale={watermark_width}:-1[watermark];[0:v][watermark]overlay=10:10"
                cmd.extend([
                    '-filter_complex', filter_complex,
                ])
            
            if progress_callback:
                progress_callback(f"Adding watermark from: {watermark_path}")
        else:
            # 没有水印的情况
            if video_filters:
                # 只有字幕，使用 -vf
                video_filters_str = ",".join(video_filters)
                cmd.extend([
                    '-vf', video_filters_str,
                ])
        
        cmd.extend([
            '-c:v', gpu_encoder,              # 视频编码器
        ])
        
        # GPU编码参数
        if use_gpu_encoding:
            cmd.extend([
                '-preset', 'p4',              # NVENC预设
                '-cq:v', '19',                # 质量因子
            ])
        else:
            cmd.extend([
                '-preset', 'medium',
                '-crf', '23',
            ])
        
        # 音频参数 - 确保48kHz输出
        cmd.extend([
            '-c:a', 'aac',                    # 音频编码器
            '-af', 'aresample=48000',         # 音频重采样滤镜
            '-ar', '48000',                   # 48kHz采样率
            '-ac', '2',                       # 立体声
            '-b:a', '128k',                   # 音频比特率
            '-pix_fmt', 'yuv420p',            # 像素格式
            '-r', '30',                       # 帧率
            '-shortest',                      # 以最短流为准
            '-vsync', 'cfr',                  # 固定帧率
            '-movflags', '+faststart',        # 优化流媒体播放
            output_video
        ])
        
        if progress_callback:
            progress_callback(f"Executing FFmpeg command with {gpu_encoder} encoder...")
        
        # 执行命令
        result = subprocess.run(cmd, capture_output=True, text=True)
        
        if result.returncode != 0:
            if progress_callback:
                progress_callback(f"FFmpeg error: {result.stderr}")
            return False
        
        # 验证输出文件
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
