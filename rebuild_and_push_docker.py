#!/usr/bin/env python3
"""
Rebuild and push Docker image with the fixed app.py
This ensures the scenario detection fix is included in the Docker image
"""

import os
import subprocess
import sys
from datetime import datetime

def run_command(cmd, description=None):
    """Run a shell command and handle output"""
    if description:
        print(f"\n{description}")
    
    print(f"Running: {cmd}")
    
    try:
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode == 0:
            print("✓ Success")
            if result.stdout:
                print(result.stdout)
            return True
        else:
            print("✗ Failed")
            if result.stderr:
                print(f"Error: {result.stderr}")
            return False
            
    except Exception as e:
        print(f"✗ Exception: {str(e)}")
        return False


def main():
    """Main function to rebuild and push Docker image"""
    
    print("Docker Image Rebuild with Fix")
    print("============================")
    print(f"Start time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    
    # Change to the video_generation directory
    video_gen_dir = "/Users/lgg/coding/sumatman/runpod/video_generation"
    os.chdir(video_gen_dir)
    print(f"\nWorking directory: {os.getcwd()}")
    
    # Verify app.py has the fix
    print("\n1. Verifying app.py has the fix...")
    with open("app.py", "r") as f:
        app_content = f.read()
    
    if "# Recalculate for scenario detection" in app_content:
        print("✓ Fix confirmed in app.py (line 328)")
    else:
        print("✗ Fix NOT found in app.py!")
        print("Please ensure app.py has the scenario detection fix before proceeding.")
        return
    
    # Build the Docker image
    print("\n2. Building Docker image...")
    build_cmd = "docker build -t betashow/video-generation-api:latest -t betashow/video-generation-api:v2.0-fixed ."
    
    if not run_command(build_cmd, "Building image with fix..."):
        print("\n❌ Docker build failed!")
        return
    
    # Verify the image was built
    print("\n3. Verifying image was built...")
    verify_cmd = "docker images | grep betashow/video-generation-api"
    run_command(verify_cmd)
    
    # Login to Docker Hub
    print("\n4. Logging in to Docker Hub...")
    print("Please enter your Docker Hub credentials:")
    
    login_cmd = "docker login"
    if not run_command(login_cmd):
        print("\n❌ Docker login failed!")
        return
    
    # Push the images
    print("\n5. Pushing images to Docker Hub...")
    
    # Push latest tag
    if run_command("docker push betashow/video-generation-api:latest", "Pushing :latest tag..."):
        print("✓ Successfully pushed :latest tag")
    else:
        print("✗ Failed to push :latest tag")
        return
    
    # Push v2.0-fixed tag
    if run_command("docker push betashow/video-generation-api:v2.0-fixed", "Pushing :v2.0-fixed tag..."):
        print("✓ Successfully pushed :v2.0-fixed tag")
    else:
        print("✗ Failed to push :v2.0-fixed tag")
    
    print("\n✅ Docker image successfully rebuilt and pushed with fix!")
    print("\nImage tags:")
    print("- betashow/video-generation-api:latest")
    print("- betashow/video-generation-api:v2.0-fixed")
    print("\nYou can now run the test_docker_full_featured.py script to verify the fix.")
    
    # Create a quick test script
    print("\n6. Creating quick local test script...")
    
    test_script = """#!/bin/bash
# Quick local test of the fixed Docker image

echo "Starting local Docker test..."
docker run -d -p 5000:5000 --name test-video-api betashow/video-generation-api:latest

echo "Waiting for container to start..."
sleep 5

echo "Testing health endpoint..."
curl -s http://localhost:5000/health | python3 -m json.tool

echo ""
echo "Container logs:"
docker logs test-video-api

echo ""
echo "Cleaning up..."
docker stop test-video-api
docker rm test-video-api

echo "Local test complete!"
"""
    
    with open("test_local_docker.sh", "w") as f:
        f.write(test_script)
    os.chmod("test_local_docker.sh", 0o755)
    
    print("✓ Created test_local_docker.sh for quick local testing")
    
    print(f"\n🎉 All done! Completed at: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")


if __name__ == "__main__":
    main()