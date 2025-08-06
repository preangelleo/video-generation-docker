#!/bin/bash
# Script to rebuild and push the fixed Docker image

echo "🐳 Rebuilding Docker image with scenario detection fix..."
echo "==========================================="

# Build the image
echo "Building image..."
docker build -t betashow/video-generation-api:latest .
docker tag betashow/video-generation-api:latest betashow/video-generation-api:v2.0-fixed

# Login to Docker Hub (you'll need to enter credentials)
echo ""
echo "Please login to Docker Hub:"
docker login

# Push the image
echo ""
echo "Pushing image..."
docker push betashow/video-generation-api:latest
docker push betashow/video-generation-api:v2.0-fixed

echo ""
echo "✅ Docker image updated with scenario detection fix!"
echo "The Full Featured test should now work correctly."