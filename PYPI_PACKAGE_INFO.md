# Video Generation API - PyPI Package

## 📦 Package Information

- **Package Name**: `video-generation-api`
- **Version**: 1.0.0
- **PyPI URL**: https://pypi.org/project/video-generation-api/
- **Author**: Leo Wang
- **License**: MIT

## 🚀 Installation

```bash
pip install video-generation-api
```

## 📖 Usage Examples

### 1. Python Client Usage

```python
from video_generation_api import VideoGenerationClient

# Initialize client
client = VideoGenerationClient("http://localhost:5000")

# Create a simple video
result = client.create_video(
    image_path="image.jpg",
    audio_path="audio.mp3",
    output_path="output.mp4"
)

# Create video with subtitles and effects
result = client.create_video(
    image_path="image.jpg",
    audio_path="audio.mp3",
    subtitle_path="subtitles.srt",
    effects=["zoom_in", "pan_left"],
    language="chinese",
    background_box=True,
    background_opacity=0.2,
    watermark_path="logo.png",
    output_path="full_featured.mp4"
)
```

### 2. Direct Function Usage

```python
from video_generation_api import (
    create_video_with_subtitles_onestep,
    merge_audio_image_to_video_with_effects,
    add_subtitles_to_video
)

# Create video with subtitles in one step
success = create_video_with_subtitles_onestep(
    input_image="image.jpg",
    input_audio="audio.mp3",
    subtitle_path="subtitles.srt",
    output_video="output.mp4",
    language="chinese",
    effects=["zoom_in"]
)
```

### 3. API Server Usage

```bash
# Start the API server
video-generation-api

# The server will run on http://localhost:5000
```

### 4. Docker Usage

The package is designed to work seamlessly with the Docker image:

```bash
docker pull betashow/video-generation-api:latest
docker run -d -p 5000:5000 betashow/video-generation-api:latest
```

## 🔧 Features

- **Intelligent Processing**: Automatically optimizes based on input parameters
- **Professional Subtitles**: High-quality subtitle rendering (not FFmpeg filters)
- **Cinematic Effects**: Hollywood-style zoom and pan effects
- **Multi-Language Support**: Chinese and English with proper fonts
- **GPU Acceleration**: Automatic GPU detection and usage
- **Python Client Library**: Easy integration with Python applications
- **REST API**: Full-featured HTTP API for any language
- **Docker Ready**: Containerized deployment option

## 📊 Processing Scenarios

| Scenario | Effects | Subtitles | Use Case |
|----------|---------|-----------|----------|
| Baseline | ❌ | ❌ | Simple image + audio merge |
| Subtitles Only | ❌ | ✅ | Educational content |
| Effects Only | ✅ | ❌ | Artistic videos |
| Full Featured | ✅ | ✅ | Professional production |

## 🔗 Related Resources

- **GitHub Repository**: https://github.com/preangelleo/video-generation-docker
- **Docker Hub**: https://hub.docker.com/r/betashow/video-generation-api
- **CloudBurst (AWS Deployment)**: https://github.com/preangelleo/cloudburst

## 📝 Notes

- This package requires FFmpeg to be installed on your system
- For production use, consider using the Docker image which includes all dependencies
- The package supports both standalone usage and API server mode
- GPU acceleration is automatically detected and used when available