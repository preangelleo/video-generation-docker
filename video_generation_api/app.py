#!/usr/bin/env python3
"""
Video Generation API with Authentication Support
Secure Flask API for video processing with optional authentication
"""

import os
import sys
import base64
import json
import tempfile
import re
import shutil
import uuid
from datetime import datetime, timedelta
from functools import wraps
from flask import Flask, request, jsonify, send_file, url_for
import subprocess

# Import core functions from same package
from .core_functions import (
    create_video_with_subtitles_onestep,
    merge_audio_image_to_video_with_effects,
    add_subtitles_to_video,
    add_subtitles_to_video_portrait
)

# Create Flask app
app = Flask(__name__)

# Authentication Configuration
DEFAULT_AUTH_KEY = "your-authentication-key-placeholder-uuid-here"

def check_authentication():
    """
    Dual-compatible authentication check
    - If AUTHENTICATION_KEY is placeholder value → Allow all requests (default mode)
    - If AUTHENTICATION_KEY is custom value → Verify header (secure mode)
    """
    config_auth_key = os.getenv('AUTHENTICATION_KEY', DEFAULT_AUTH_KEY)
    
    # Default mode: using placeholder, no authentication required
    if config_auth_key == DEFAULT_AUTH_KEY:
        return True, "Default mode - open access"
    
    # Secure mode: verify header key
    request_auth_key = request.headers.get('X-Authentication-Key')
    if request_auth_key == config_auth_key:
        return True, "Authenticated successfully"
    else:
        return False, "Invalid authentication key"

def save_input_file(data, work_dir, filename):
    """Save base64 encoded data or file path to disk"""
    if not data:
        raise ValueError(f"No data provided for {filename}")
    
    file_path = os.path.join(work_dir, filename)
    
    # If it's a file path
    if isinstance(data, str) and os.path.exists(data):
        shutil.copy(data, file_path)
    else:
        # Assume it's base64 encoded
        try:
            decoded_data = base64.b64decode(data)
            with open(file_path, 'wb') as f:
                f.write(decoded_data)
        except Exception as e:
            raise ValueError(f"Failed to decode base64 data for {filename}: {e}")
    
    return file_path


def require_auth(f):
    """Decorator: Add authentication check to API endpoints"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        is_authenticated, message = check_authentication()
        if not is_authenticated:
            return jsonify({
                "error": "Authentication failed",
                "message": message,
                "required_header": "X-Authentication-Key"
            }), 401
        return f(*args, **kwargs)
    return decorated_function

# Configure directories - simple hardcoded paths for disposable Docker containers
OUTPUT_DIR = './outputs'
TEMP_DIR = './temp'

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Store file metadata (in production, use Redis or database)
file_metadata = {}

def detect_video_orientation(video_path):
    """
    Detect if video is portrait or landscape using ffprobe
    Returns: True if portrait, False if landscape
    """
    try:
        cmd = [
            'ffprobe', '-v', 'error', 
            '-select_streams', 'v:0',
            '-show_entries', 'stream=width,height',
            '-of', 'json',
            video_path
        ]
        
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode != 0:
            app.logger.error(f"ffprobe failed: {result.stderr}")
            return False
            
        data = json.loads(result.stdout)
        if 'streams' in data and len(data['streams']) > 0:
            width = int(data['streams'][0].get('width', 1920))
            height = int(data['streams'][0].get('height', 1080))
            
            # Video is portrait if height > width
            is_portrait = height > width
            app.logger.info(f"Video dimensions: {width}x{height}, portrait: {is_portrait}")
            return is_portrait
        
        return False
        
    except Exception as e:
        app.logger.error(f"Error detecting video orientation: {e}")
        return False

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint with authentication status"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ffmpeg_version = result.stdout.split('\n')[0] if result.returncode == 0 else "Not installed"
        
        # Check GPU
        gpu_available = os.path.exists('/dev/nvidia0')
        
        # Check authentication status
        config_auth_key = os.getenv('AUTHENTICATION_KEY', DEFAULT_AUTH_KEY)
        auth_mode = "default" if config_auth_key == DEFAULT_AUTH_KEY else "secure"
        
        response = {
            "status": "healthy",
            "ffmpeg_version": ffmpeg_version,
            "gpu_available": gpu_available,
            "output_dir": OUTPUT_DIR,
            "temp_dir": TEMP_DIR,
            "authentication": {
                "mode": auth_mode,
                "description": "Open access - no authentication required" if auth_mode == "default" 
                              else "Secure mode - X-Authentication-Key header required"
            },
            "available_endpoints": [
                "/create_video_onestep",
                "/download/<file_id>",
                "/cleanup"
            ]
        }
        
        if auth_mode == "secure":
            response["authentication"]["required_header"] = "X-Authentication-Key"
            
        return jsonify(response)
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/create_video_onestep', methods=['POST'])
@require_auth
def create_video_onestep_api():
    """
    Unified intelligent video creation endpoint
    Handles all 4 scenarios based on effects and subtitle parameters:
    1. Baseline: No effects, no subtitles -> create_basic_video
    2. Subtitles Only: No effects, with subtitles -> create_basic_video + add_subtitles
    3. Effects Only: With effects, no subtitles -> merge_audio_image
    4. Full Featured: With effects and subtitles -> merge_audio_image + add_subtitles
    """
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Create work directory
        work_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        work_dir = os.path.join(TEMP_DIR, work_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # Process input files
        is_portrait = data.get('is_portrait')
        input_image = save_input_file(data.get('input_image'), work_dir, 'input.png')
        input_audio = save_input_file(data.get('input_audio'), work_dir, 'input.mp3')
        subtitle_path = save_input_file(data.get('subtitle'), work_dir, 'subtitle.srt') if data.get('subtitle') else None
        watermark_path = save_input_file(data.get('watermark'), work_dir, 'watermark.png') if data.get('watermark') else None
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mp4"
        
        # Determine processing path based on parameters
        effects = data.get('effects', [])
        has_effects = bool(effects)
        has_subtitles = bool(subtitle_path)
        
        app.logger.info(f"Processing request - Effects: {has_effects}, Subtitles: {has_subtitles}")
        
        # Step 1: Create base video (with or without effects)
        base_video_path = os.path.join(work_dir, "base_video.mp4")
        
        if has_effects:
            # Use merge_audio_image for effects
            app.logger.info("Using merge_audio_image_to_video_with_effects for zoom/pan effects")
            success, result = merge_audio_image_to_video_with_effects(
                input_mp3=input_audio,
                input_image=input_image,
                output_video=base_video_path,
                effects=effects,
                watermark_path=watermark_path
            )
            
            if not success:
                shutil.rmtree(work_dir)
                return jsonify({"error": f"Video creation with effects failed: {result}"}), 500
                
            # The result is the actual output path
            if result != base_video_path:
                base_video_path = result
                
        else:
            # Use basic video creation (no effects) - using the existing function but without effects
            app.logger.info("Creating basic video without effects")
            success = create_video_with_subtitles_onestep(
                input_image=input_image,
                input_audio=input_audio,
                subtitle_path=None,  # No subtitles in first step
                output_video=base_video_path,
                font_size=None,
                outline_color=None,
                background_box=False,
                background_opacity=0,
                language='english',
                is_portrait=is_portrait,
                effects=None,  # No effects
                watermark_path=watermark_path,
                progress_callback=lambda msg: app.logger.debug(f"Progress: {msg}")
            )
            
            if not success:
                shutil.rmtree(work_dir)
                return jsonify({"error": "Basic video creation failed"}), 500
        
        # Step 2: Add subtitles if requested
        final_output = os.path.join(OUTPUT_DIR, output_filename)
        
        if has_subtitles:
            app.logger.info("Adding subtitles to video")
            
            # Detect video orientation
            
            if is_portrait is None:
                # Auto-detect orientation
                is_portrait = detect_video_orientation(base_video_path)
                app.logger.info(f"Auto-detected video orientation - Portrait: {is_portrait}")
            
            # Choose appropriate subtitle function
            if is_portrait:
                app.logger.info("Using add_subtitles_to_video_portrait for portrait video")
                success = add_subtitles_to_video_portrait(
                    input_video_path=base_video_path,
                    subtitle_path=subtitle_path,
                    output_video_path=final_output,
                    font_size=data.get('font_size'),
                    outline_color=data.get('outline_color', "&H00000000"),
                    background_box=data.get('background_box', True),
                    background_opacity=data.get('background_opacity', 0.2),
                    language=data.get('language', 'chinese')
                )
            else:
                app.logger.info("Using add_subtitles_to_video for landscape video")
                success = add_subtitles_to_video(
                    input_video_path=base_video_path,
                    subtitle_path=subtitle_path,
                    output_video_path=final_output,
                    font_size=data.get('font_size'),
                    outline_color=data.get('outline_color', "&H00000000"),
                    background_box=data.get('background_box', True),
                    background_opacity=data.get('background_opacity', 0.2),
                    language=data.get('language', 'chinese')
                )
                
            if not success:
                shutil.rmtree(work_dir)
                return jsonify({"error": "Adding subtitles failed"}), 500
        else:
            # No subtitles, just move the base video to final output
            app.logger.info("No subtitles requested, using base video as final output")
            shutil.move(base_video_path, final_output)
        
        # Verify final output exists
        if os.path.exists(final_output):
            file_size = os.path.getsize(final_output)
            
            # Store metadata
            file_metadata[file_id] = {
                "filename": output_filename,
                "original_name": data.get('output_filename', 'output.mp4'),
                "size": file_size,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            
            # Clean up work directory
            shutil.rmtree(work_dir)
            
            # Generate download endpoint path (relative)
            # Client should prepend their API base URL
            download_endpoint = f"/download/{file_id}"
            
            # Log processing summary
            # Recalculate for scenario detection
            has_effects = bool(data.get('effects', []))
            has_subtitles = bool(data.get('subtitle'))
            
            scenario = "unknown"
            if not has_effects and not has_subtitles:
                scenario = "baseline"
            elif not has_effects and has_subtitles:
                scenario = "subtitles_only"
            elif has_effects and not has_subtitles:
                scenario = "effects_only"
            elif has_effects and has_subtitles:
                scenario = "full_featured"
                
            app.logger.info(f"Successfully processed video - Scenario: {scenario}, Size: {file_size} bytes")
            
            return jsonify({
                "success": True,
                "file_id": file_id,
                "download_endpoint": download_endpoint,
                "filename": data.get('output_filename', 'output.mp4'),
                "size": file_size,
                "scenario": scenario
            })
        else:
            shutil.rmtree(work_dir)
            return jsonify({"error": "Final video file not found"}), 500
            
    except Exception as e:
        app.logger.error(f"Exception in unified create_video_onestep: {e}", exc_info=True)
        if 'work_dir' in locals() and os.path.exists(work_dir):
            shutil.rmtree(work_dir)
        return jsonify({"error": str(e)}), 500

@app.route('/download/<file_id>')
def download_file(file_id):
    """Download generated video file"""
    # Check if file exists in metadata
    if file_id not in file_metadata:
        return jsonify({"error": "File not found"}), 404
    
    metadata = file_metadata[file_id]
    
    # Check if file expired
    if datetime.now() > metadata['expires_at']:
        # Clean up expired file
        file_path = os.path.join(OUTPUT_DIR, metadata['filename'])
        if os.path.exists(file_path):
            os.remove(file_path)
        del file_metadata[file_id]
        return jsonify({"error": "File expired"}), 404
    
    file_path = os.path.join(OUTPUT_DIR, metadata['filename'])
    if os.path.exists(file_path):
        return send_file(
            file_path,
            mimetype='video/mp4',
            as_attachment=True,
            download_name=metadata['original_name']
        )
    else:
        return jsonify({"error": "File not found on disk"}), 404

@app.route('/cleanup')
def cleanup_expired_files():
    """Clean up expired files"""
    cleaned = 0
    current_time = datetime.now()
    
    # Clean up expired files
    expired_ids = []
    for file_id, metadata in file_metadata.items():
        if current_time > metadata['expires_at']:
            file_path = os.path.join(OUTPUT_DIR, metadata['filename'])
            if os.path.exists(file_path):
                os.remove(file_path)
                cleaned += 1
            expired_ids.append(file_id)
    
    # Remove from metadata
    for file_id in expired_ids:
        del file_metadata[file_id]
    
    return jsonify({
        "cleaned": cleaned,
        "active_files": len(file_metadata)
    })


def main():
    """Main entry point for the API server"""
    import logging
    logging.basicConfig(level=logging.INFO)
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\nStarting Fixed Video Processing API on port {port}")
    print("Available endpoints:")
    print("- GET  /health")
    print("- POST /create_video_onestep")
    print("- GET  /download/<file_id>")
    print("- GET  /cleanup")
    print("\n")
    
    app.run(host='0.0.0.0', port=port)

if __name__ == '__main__':
    main()