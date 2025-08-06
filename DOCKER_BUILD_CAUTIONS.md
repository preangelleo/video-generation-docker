# Docker Build Cautions for Video Generation API

## Critical Issues to Avoid

### 1. NumPy Version Compatibility (Critical)
**Issue**: NumPy 2.x causes compatibility issues with OpenCV
**Error**: `AttributeError: _ARRAY_API not found` and `numpy.core.multiarray failed to import`
**Solution**: Pin NumPy to version 1.26.4 in requirements.txt
```
numpy==1.26.4  # DO NOT use numpy>=2.0 - breaks OpenCV compatibility
```

### 2. Lexend Font Installation (Non-Critical)
**Issue**: Google Fonts URLs for Lexend are broken/404
**Solution**: Remove Lexend font installation from Dockerfile - not essential for functionality
```dockerfile
# REMOVE THIS BLOCK - URLs are broken
# RUN mkdir -p /usr/share/fonts/truetype/lexend && \
#     wget -O /usr/share/fonts/truetype/lexend/Lexend-Regular.ttf \
#     "https://fonts.gstatic.com/s/lexend/v18/wlptgwvFAVdoq2_v9KSe2A.ttf" && \
#     wget -O /usr/share/fonts/truetype/lexend/Lexend-Bold.ttf \
#     "https://fonts.gstatic.com/s/lexend/v18/wlpvgwvFAVdoq2_v9KKm-tXY.ttf" && \
#     fc-cache -fv
```

### 3. Docker Build Performance
**Issue**: Building from scratch is extremely slow on restored AWS snapshots
**Observation**: Layer caching doesn't work properly after snapshot restore
**Solution**: Use existing images when possible, or expect 15+ minute builds

### 4. Quick Update Method
Instead of rebuilding, update existing images:
```bash
# Create temporary container
docker create --name temp_update betashow/video-generation-api:latest

# Copy updated files
docker cp app.py temp_update:/workspace/video_generation/
docker cp core_functions.py temp_update:/workspace/video_generation/
docker cp README.md temp_update:/workspace/video_generation/

# Commit to new image
docker commit temp_update betashow/video-generation-api:v2.1

# Clean up
docker rm temp_update
```

## Verified Working Configuration
- Base: Ubuntu 22.04
- Python: 3.10
- NumPy: 1.26.4
- OpenCV: 4.8.1.78
- Flask: 3.0.0
- Chinese Font: LXGW WenKai Bold (working)
- Lexend Font: Removed (broken URLs)

## Testing After Build
Always test the Flask API starts correctly:
```bash
docker run -d --name test-api -p 5001:5000 your-image:tag
sleep 5
docker logs test-api
curl http://localhost:5001/health
```

Last updated: 2025-08-06