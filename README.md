# Video Generation API v1.0

[中文版](./README_CN.md)

🎬 A powerful Docker-based API for intelligent video generation with professional effects and subtitles.

## 🚀 Quick Start

### Pull and Run

```bash
# Pull the Docker image
docker pull betashow/video-generation-api:latest

# Run the container
docker run -d \
  --name video-api \
  -p 5000:5000 \
  betashow/video-generation-api:latest
```

The API will be available at `http://localhost:5000`

## 🚀 Want to Deploy This on AWS?

Check out my second open source project: **[CloudBurst](https://github.com/preangelleo/cloudburst)**

CloudBurst helps you deploy this Video Generation API on AWS with:
- ⚡ **On-demand instances** - Pay only when you need it
- 💰 **96% cost savings** - Compared to 24/7 GPU instances
- 🔄 **Fully automated** - Create → Deploy → Process → Terminate
- 📊 **Real-time cost tracking** - Know exactly what you're paying

Perfect for production use cases where you need to generate videos occasionally but don't want to maintain expensive infrastructure.

## 📖 API Documentation

### Core Endpoint: `/create_video_onestep`

A single intelligent endpoint that automatically handles all video creation scenarios based on your input parameters.

#### Request Format

**URL**: `POST http://your-server:5000/create_video_onestep`

**Headers**:
```json
{
  "Content-Type": "application/json",
  "X-Authentication-Key": "your-key-if-required"
}
```

**Body Parameters**:

| Parameter | Type | Required | Description |
|-----------|------|----------|-------------|
| `input_image` | string | Yes | Base64 encoded image (JPG/PNG) |
| `input_audio` | string | Yes | Base64 encoded audio (MP3/WAV) |
| `subtitle` | string | No | Base64 encoded SRT subtitle file |
| `effects` | array | No | Effects to apply. Available: `"zoom_in"`, `"zoom_out"`, `"pan_left"`, `"pan_right"`, `"random"` |
| `language` | string | No | Subtitle language: `"chinese"` or `"english"` (default: chinese) |
| `background_box` | boolean | No | Show subtitle background (default: true) |
| `background_opacity` | float | No | Subtitle background transparency 0-1 (default: 0.2) **[See important note below](#subtitle-background-transparency)** |
| `font_size` | integer | No | Subtitle font size in pixels (default: auto-calculated based on video size) |
| `outline_color` | string | No | Subtitle outline color in ASS format (default: "&H00000000" - black) |
| `is_portrait` | boolean | No | Force portrait orientation (default: auto-detect) |
| `watermark` | string | No | Base64 encoded watermark image |
| `output_filename` | string | No | Preferred output filename |

#### Processing Scenarios

The API automatically detects and optimizes for 4 scenarios:

| Scenario | Effects | Subtitles | Description |
|----------|---------|-----------|-------------|
| **Baseline** | ❌ | ❌ | Simple image + audio merge (fastest) |
| **Subtitles Only** | ❌ | ✅ | Basic video with professional subtitles |
| **Effects Only** | ✅ | ❌ | Cinematic zoom/pan effects |
| **Full Featured** | ✅ | ✅ | Effects + professional subtitles |

#### Response Format

```json
{
  "success": true,
  "file_id": "f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "download_endpoint": "/download/f47ac10b-58cc-4372-a567-0e02b2c3d479",
  "filename": "output.mp4",
  "size": 15728640,
  "scenario": "full_featured"
}
```

#### Complete Examples

**1. Baseline (Simplest)**
```python
import requests
import base64

def encode_file(filepath):
    with open(filepath, 'rb') as f:
        return base64.b64encode(f.read()).decode('utf-8')

# Prepare inputs
image_b64 = encode_file('image.jpg')
audio_b64 = encode_file('audio.mp3')

# Make request
response = requests.post('http://localhost:5000/create_video_onestep', 
    json={
        'input_image': image_b64,
        'input_audio': audio_b64
    }
)

result = response.json()
if result['success']:
    # Download the video
    download_url = f"http://localhost:5000{result['download_endpoint']}"
    video = requests.get(download_url)
    with open('output.mp4', 'wb') as f:
        f.write(video.content)
```

**2. With Chinese Subtitles**
```python
subtitle_b64 = encode_file('subtitles.srt')

response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'subtitle': subtitle_b64,
        'language': 'chinese',
        'background_box': True,
        'background_opacity': 0.2
    }
)
```

**3. With Effects**
```python
# Zoom effects (randomly picks one)
response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'effects': ['zoom_in', 'zoom_out']  # Randomly chooses zoom_in OR zoom_out
    }
)

# Pan effects
response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'effects': ['pan_left']  # Pan from right to center
    }
)

# Let system choose randomly from all effects
response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'effects': ['random']  # System picks any available effect
    }
)
```

**4. Full Featured (Effects + Subtitles)**
```python
response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'subtitle': subtitle_b64,
        'effects': ['zoom_in', 'zoom_out'],
        'language': 'chinese'
    }
)
```

**5. Advanced Subtitle Customization**
```python
response = requests.post('http://localhost:5000/create_video_onestep',
    json={
        'input_image': image_b64,
        'input_audio': audio_b64,
        'subtitle': subtitle_b64,
        'language': 'chinese',
        'font_size': 48,                    # Custom font size
        'outline_color': '&H00FF0000',      # Blue outline
        'background_box': True,             # Show background
        'background_opacity': 0.3           # 30% transparent (dark background)
    }
)
```

### Other Endpoints

#### Health Check
```bash
GET /health
```

Returns API status, FFmpeg version, and available endpoints.

#### Download Video
```bash
GET /download/{file_id}
```

Download the generated video file. Files expire after 1 hour.

#### Cleanup Expired Files
```bash
GET /cleanup
```

Manually trigger cleanup of expired files.

## 🔧 Authentication

The API supports two modes:

### Default Mode (No Authentication)
By default, the API is open and requires no authentication.

### Secure Mode
Set the `AUTHENTICATION_KEY` environment variable to enable authentication:

```bash
docker run -d \
  -e AUTHENTICATION_KEY=your-secure-uuid-here \
  -p 5000:5000 \
  betashow/video-generation-api:latest
```

Then include the key in your requests:
```python
headers = {
    'Content-Type': 'application/json',
    'X-Authentication-Key': 'your-secure-uuid-here'
}
```

## 🎯 Features

- **Intelligent Processing**: Automatically optimizes based on input parameters
- **Professional Subtitles**: High-quality subtitle rendering (not FFmpeg filters)
- **Auto-Orientation**: Detects portrait/landscape videos automatically
- **Cinematic Effects**: Hollywood-style zoom and pan effects
- **Multi-Language**: Supports Chinese and English with proper fonts
- **GPU Acceleration**: Automatic GPU detection and usage when available

## 🎨 Advanced Subtitle Styling

### Subtitle Background Transparency

⚠️ **IMPORTANT**: The `background_opacity` parameter controls **transparency**, not opacity!

| Value | Visual Result | Description |
|-------|--------------|-------------|
| **0.0** | Solid black | Completely opaque background |
| **0.2** | Dark background | **Default** - Good readability |
| **0.5** | Semi-transparent | 50% see-through |
| **0.7** | Very transparent | Old default - quite see-through |
| **1.0** | No background | Completely transparent |

**Examples**:
- For **darker, more readable** subtitles: Use **lower** values (0.0 - 0.3)
- For **more transparent** subtitles: Use **higher** values (0.5 - 1.0)
- Recommended: **0.2** (the new default) provides excellent readability

```python
# Dark, readable background (recommended)
'background_opacity': 0.2

# Solid black background
'background_opacity': 0.0

# Very transparent (hard to read)
'background_opacity': 0.8
```

### Color Format (ASS/SSA Style)
The `outline_color` parameter uses ASS subtitle format: `&HAABBGGRR` where:
- AA = Alpha (transparency): 00 = opaque, FF = transparent
- BB = Blue component (00-FF)
- GG = Green component (00-FF)  
- RR = Red component (00-FF)

**Common Colors**:
- `&H00000000` - Black (default)
- `&H00FFFFFF` - White
- `&H000000FF` - Red
- `&H0000FF00` - Green
- `&H00FF0000` - Blue
- `&H0000FFFF` - Yellow
- `&H00FF00FF` - Magenta

### Font Size Guidelines
If not specified, font size is auto-calculated based on video resolution:
- **1080p Landscape**: ~45px for Chinese, ~60px for English
- **1080p Portrait**: ~21px for Chinese, ~30px for English
- **4K Videos**: Proportionally larger

## 📋 Requirements

- Docker
- 2GB+ RAM (4GB recommended)
- 10GB+ free disk space
- GPU (optional, for faster processing)

## 🎬 Output Examples

See what this API can generate:

**English Example**:
[![English Video Example](https://img.youtube.com/vi/JiWsyuyw1ao/maxresdefault.jpg)](https://www.youtube.com/watch?v=JiWsyuyw1ao)

**Chinese Example**:
[![Chinese Video Example](https://img.youtube.com/vi/WYFyUAk9F6k/maxresdefault.jpg)](https://www.youtube.com/watch?v=WYFyUAk9F6k)

**Features Demonstrated**:
- ✅ Professional subtitles with semi-transparent background
- ✅ Smooth zoom effects (Ken Burns effect)
- ✅ Perfect audio-visual synchronization
- ✅ High-quality 1080p video output
- ✅ Support for both English and Chinese

Both examples were generated using the "Full Featured" mode with subtitles and effects enabled.

## 🐳 Docker Image Details

The image includes:
- Ubuntu 22.04 base
- FFmpeg with GPU support
- Python 3.10
- Chinese fonts (LXGW WenKai Bold)
- All required video processing libraries

## 📝 Notes

- All file inputs must be Base64 encoded
- Generated videos expire after 1 hour
- The API returns relative download paths, not full URLs
- This is designed for on-demand, disposable container usage

## 🚨 Important

This Docker image is designed for temporary, on-demand usage. The container can be destroyed and recreated as needed - all paths are relative and no persistent storage is required.

---

**Ready to generate amazing videos? Start the container and make your first request!**