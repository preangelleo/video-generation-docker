#!/bin/bash
# Start API with PM2

cd /workspace/video_generation

# RunPod automatically sets RUNPOD_POD_ID
if [ -z "$RUNPOD_POD_ID" ]; then
    echo "Warning: RUNPOD_POD_ID not set. Download URLs may not work correctly."
fi

# Set default directories if not provided
export OUTPUT_DIR=${OUTPUT_DIR:-"/workspace/video_generation/outputs"}
export TEMP_DIR=${TEMP_DIR:-"/tmp/video_processing"}

# Create directories if they don't exist
mkdir -p $OUTPUT_DIR
mkdir -p $TEMP_DIR

# Install PM2 if not installed
which pm2 > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "Installing PM2..."
    npm install -g pm2
fi

# Kill any existing processes
pkill -f "python.*app.py"

# Stop existing PM2 process if any
pm2 stop video-generation-api 2>/dev/null
pm2 delete video-generation-api 2>/dev/null

sleep 2

# Start with PM2
pm2 start pm2_config.json

# Show status
pm2 status
echo ""
echo "API started with PM2. Use these commands:"
echo "  pm2 status          - Check status"
echo "  pm2 logs            - View logs"
echo "  pm2 restart video-generation-api - Restart API"
echo "  pm2 stop video-generation-api    - Stop API"