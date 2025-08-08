"""
Python client for Video Generation API
"""

import os
import base64
import requests
import time
from typing import Optional, List, Dict, Union
from pathlib import Path


class VideoGenerationClient:
    """
    Client for interacting with Video Generation API
    
    Example:
        client = VideoGenerationClient("http://localhost:5000")
        result = client.create_video(
            image_path="image.jpg",
            audio_path="audio.mp3",
            subtitle_path="subtitles.srt",
            effects=["zoom_in"],
            output_path="output.mp4"
        )
    """
    
    def __init__(self, api_url: str, auth_key: Optional[str] = None):
        """
        Initialize client
        
        Args:
            api_url: Base URL of the API (e.g., "http://localhost:5000")
            auth_key: Optional authentication key for secure mode
        """
        self.api_url = api_url.rstrip('/')
        self.auth_key = auth_key
        self.headers = {"Content-Type": "application/json"}
        if auth_key:
            self.headers["X-Authentication-Key"] = auth_key
    
    def _encode_file(self, file_path: str) -> str:
        """Encode file to base64"""
        with open(file_path, 'rb') as f:
            return base64.b64encode(f.read()).decode('utf-8')
    
    def health_check(self) -> Dict:
        """Check API health status"""
        response = requests.get(f"{self.api_url}/health")
        response.raise_for_status()
        return response.json()
    
    def create_video(
        self,
        image_path: str,
        audio_path: str,
        subtitle_path: Optional[str] = None,
        effects: Optional[List[str]] = None,
        language: str = "chinese",
        background_box: bool = True,
        background_opacity: float = 0.2,
        font_size: Optional[int] = None,
        outline_color: str = "&H00000000",
        is_portrait: Optional[bool] = None,
        watermark_path: Optional[str] = None,
        output_path: str = "output.mp4",
        timeout: int = 300
    ) -> Dict:
        """
        Create video with all options
        
        Args:
            image_path: Path to input image
            audio_path: Path to input audio
            subtitle_path: Optional path to subtitle file (SRT)
            effects: List of effects ["zoom_in", "zoom_out", "pan_left", "pan_right", "random"]
            language: Subtitle language ("chinese" or "english")
            background_box: Show subtitle background
            background_opacity: Background transparency (0-1, 0=opaque, 1=transparent)
            font_size: Custom font size
            outline_color: Subtitle outline color in ASS format
            is_portrait: Force portrait orientation
            watermark_path: Optional watermark image
            output_path: Local path to save the output video
            timeout: Request timeout in seconds
            
        Returns:
            Dict with success status and file information
        """
        # Prepare request data
        data = {
            "input_image": self._encode_file(image_path),
            "input_audio": self._encode_file(audio_path),
            "language": language,
            "background_box": background_box,
            "background_opacity": background_opacity,
            "output_filename": os.path.basename(output_path)
        }
        
        # Add optional parameters
        if subtitle_path:
            data["subtitle"] = self._encode_file(subtitle_path)
        if effects:
            data["effects"] = effects
        if font_size:
            data["font_size"] = font_size
        if outline_color:
            data["outline_color"] = outline_color
        if is_portrait is not None:
            data["is_portrait"] = is_portrait
        if watermark_path:
            data["watermark"] = self._encode_file(watermark_path)
        
        # Make request
        response = requests.post(
            f"{self.api_url}/create_video_onestep",
            json=data,
            headers=self.headers,
            timeout=timeout
        )
        response.raise_for_status()
        result = response.json()
        
        if result.get("success"):
            # Download the video
            download_url = f"{self.api_url}{result['download_endpoint']}"
            video_response = requests.get(download_url, timeout=60)
            video_response.raise_for_status()
            
            # Save to file
            with open(output_path, 'wb') as f:
                f.write(video_response.content)
            
            result["local_path"] = output_path
        
        return result
    
    def create_baseline_video(
        self,
        image_path: str,
        audio_path: str,
        output_path: str = "output.mp4"
    ) -> Dict:
        """
        Create simplest video (no effects, no subtitles)
        
        Args:
            image_path: Path to input image
            audio_path: Path to input audio
            output_path: Local path to save the output video
            
        Returns:
            Dict with success status and file information
        """
        return self.create_video(
            image_path=image_path,
            audio_path=audio_path,
            output_path=output_path
        )
    
    def create_video_with_subtitles(
        self,
        image_path: str,
        audio_path: str,
        subtitle_path: str,
        language: str = "chinese",
        output_path: str = "output.mp4"
    ) -> Dict:
        """
        Create video with subtitles only (no effects)
        
        Args:
            image_path: Path to input image
            audio_path: Path to input audio
            subtitle_path: Path to subtitle file (SRT)
            language: Subtitle language ("chinese" or "english")
            output_path: Local path to save the output video
            
        Returns:
            Dict with success status and file information
        """
        return self.create_video(
            image_path=image_path,
            audio_path=audio_path,
            subtitle_path=subtitle_path,
            language=language,
            output_path=output_path
        )
    
    def create_video_with_effects(
        self,
        image_path: str,
        audio_path: str,
        effects: List[str] = ["zoom_in", "zoom_out"],
        output_path: str = "output.mp4"
    ) -> Dict:
        """
        Create video with effects only (no subtitles)
        
        Args:
            image_path: Path to input image
            audio_path: Path to input audio
            effects: List of effects to apply
            output_path: Local path to save the output video
            
        Returns:
            Dict with success status and file information
        """
        return self.create_video(
            image_path=image_path,
            audio_path=audio_path,
            effects=effects,
            output_path=output_path
        )
    
    def cleanup_expired_files(self) -> Dict:
        """
        Trigger cleanup of expired files on server
        
        Returns:
            Dict with cleanup statistics
        """
        response = requests.get(f"{self.api_url}/cleanup")
        response.raise_for_status()
        return response.json()


# Convenience functions for direct usage
def create_video_from_api(
    api_url: str,
    image_path: str,
    audio_path: str,
    subtitle_path: Optional[str] = None,
    effects: Optional[List[str]] = None,
    output_path: str = "output.mp4",
    auth_key: Optional[str] = None,
    **kwargs
) -> Dict:
    """
    Convenience function to create video using the API
    
    Args:
        api_url: Base URL of the API
        image_path: Path to input image
        audio_path: Path to input audio
        subtitle_path: Optional path to subtitle file
        effects: Optional list of effects
        output_path: Local path to save the output
        auth_key: Optional authentication key
        **kwargs: Additional parameters for video creation
        
    Returns:
        Dict with success status and file information
    """
    client = VideoGenerationClient(api_url, auth_key)
    return client.create_video(
        image_path=image_path,
        audio_path=audio_path,
        subtitle_path=subtitle_path,
        effects=effects,
        output_path=output_path,
        **kwargs
    )