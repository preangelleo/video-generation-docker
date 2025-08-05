# Security and Environment Variables

## Environment Variables Used

This Docker image uses the following environment variables:

### Automatically Set by RunPod
- `RUNPOD_POD_ID` - The Pod ID, used to generate download URLs

### Optional Configuration
- `OUTPUT_DIR` - Directory for output files (default: `/workspace/video_generation/outputs`)
- `TEMP_DIR` - Directory for temporary files (default: `/tmp/video_processing`)
- `API_PORT` - API port (default: 5000)

## Security Measures

1. **No Hardcoded Credentials** - All sensitive information must be passed via environment variables
2. **No Default POD_ID** - The app will fail gracefully if RUNPOD_POD_ID is not set
3. **Dockerignore** - Ensures no sensitive files are included in the image
4. **Directory Isolation** - Uses specific directories for outputs and temp files

## Running the Container

### On RunPod
RunPod automatically sets `RUNPOD_POD_ID`, so you just need to run the container normally.

### Local Testing
```bash
docker run -e RUNPOD_POD_ID=test-pod-id \
           -e OUTPUT_DIR=/tmp/outputs \
           -e TEMP_DIR=/tmp/processing \
           -p 5000:5000 \
           video-merger-api:latest
```

## Important Notes

1. Never commit `.env` files to version control
2. Always use `.env.example` as a template
3. RunPod automatically provides `RUNPOD_POD_ID` - don't hardcode it
4. The image contains no sensitive data and can be safely shared