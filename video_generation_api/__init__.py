"""
Video Generation API
A powerful API for intelligent video generation with professional effects and subtitles.
"""

__version__ = "1.0.1"
__author__ = "Leo Wang"
__email__ = "preangelleo@gmail.com"

from .core_functions import (
    create_video_with_subtitles_onestep,
    merge_audio_image_to_video_with_effects,
    add_subtitles_to_video,
    add_subtitles_to_video_portrait,
    AfterEffectsProcess,
    get_local_font,
    get_output_filename,
    EFFECTS
)

from .api_client import VideoGenerationClient

__all__ = [
    "create_video_with_subtitles_onestep",
    "merge_audio_image_to_video_with_effects", 
    "add_subtitles_to_video",
    "add_subtitles_to_video_portrait",
    "AfterEffectsProcess",
    "get_local_font",
    "get_output_filename",
    "EFFECTS",
    "VideoGenerationClient"
]