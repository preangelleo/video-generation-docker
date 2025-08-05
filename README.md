# Video Generation API for RunPod

A standalone video generation API service that creates single scene videos with 4 core video processing functions for parallel processing on RunPod.

## Features

- **Create video with subtitles in one step** - Combines image, audio, and subtitles with zoom/pan effects
- **Merge audio and image to video** - Creates video from static image and audio with visual effects
- **Add subtitles to video** - Adds styled subtitles to existing videos (landscape)
- **Add subtitles to portrait video** - Specialized subtitle positioning for vertical videos

## Key Components

- `app.py` - Flask API server with 4 endpoints
- `core_functions.py` - Core video processing functions
- `pm2_config.json` - PM2 process manager configuration
- `start_with_pm2.sh` - PM2 startup script
- `Dockerfile` - Docker container definition
- `requirements.txt` - Python dependencies

## API Endpoints

All endpoints accept POST requests with JSON data:

1. **POST /create_video_onestep**
   - Combines image + audio + subtitles with effects
   - Required: `input_image`, `input_audio`
   - Optional: `subtitle_path`, `zoom_factor`, `pan_direction`, `language`

2. **POST /merge_audio_image**
   - Creates video from image + audio
   - Required: `input_image`, `input_audio`
   - Optional: `zoom_factor`, `pan_direction`

3. **POST /add_subtitles**
   - Adds subtitles to landscape video
   - Required: `input_video`, `subtitle_path`
   - Optional: `language` (important for Chinese: use `"chinese"`)

4. **POST /add_subtitles_portrait**
   - Adds subtitles to portrait video
   - Required: `input_video`, `subtitle_path`
   - Optional: `language`

## Important Notes

1. **Chinese Font Support**: When processing Chinese subtitles, always pass `"language": "chinese"` in the request, otherwise English fonts will be used.

2. **Font Configuration**: The system only installs LXGW WenKai Bold font. Do not install the Regular version as fontconfig will default to Regular instead of Bold.

3. **File Downloads**: API returns download URLs for processed videos. Files are stored temporarily and should be downloaded promptly.

## Deployment

1. Build Docker image: `./build_and_push.sh`
2. Deploy to RunPod: `./deploy_to_pod.sh`
3. Or create multiple pods: `python3 create_runpod.py`

## Process Management

The API runs under PM2 for reliability:
- Check status: `pm2 status`
- View logs: `pm2 logs video-generation-api`
- Restart: `pm2 restart video-generation-api`