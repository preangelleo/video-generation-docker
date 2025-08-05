#!/usr/bin/env python3
"""
Fixed Flask API for video processing with file download support
"""

import os
import sys
import base64
import json
import tempfile
import shutil
import uuid
from datetime import datetime, timedelta
from flask import Flask, request, jsonify, send_file, url_for

# Add current directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Import core functions
from core_functions import (
    create_video_with_subtitles_onestep,
    merge_audio_image_to_video_with_effects,
    add_subtitles_to_video,
    add_subtitles_to_video_portrait
)

# Create Flask app
app = Flask(__name__)

# Configure directories - adapt to both Mac and Linux environments
if os.path.exists('/workspace'):
    # RunPod environment
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', '/workspace/video_generation/outputs')
    TEMP_DIR = os.environ.get('TEMP_DIR', '/tmp/video_processing')
else:
    # Mac local environment
    OUTPUT_DIR = os.environ.get('OUTPUT_DIR', './outputs')
    TEMP_DIR = os.environ.get('TEMP_DIR', './temp')

os.makedirs(OUTPUT_DIR, exist_ok=True)
os.makedirs(TEMP_DIR, exist_ok=True)

# Store file metadata (in production, use Redis or database)
file_metadata = {}

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    try:
        import subprocess
        result = subprocess.run(['ffmpeg', '-version'], capture_output=True, text=True)
        ffmpeg_version = result.stdout.split('\n')[0] if result.returncode == 0 else "Not installed"
        
        # Check GPU
        gpu_available = os.path.exists('/dev/nvidia0')
        
        return jsonify({
            "status": "healthy",
            "ffmpeg_version": ffmpeg_version,
            "gpu_available": gpu_available,
            "output_dir": OUTPUT_DIR,
            "temp_dir": TEMP_DIR,
            "available_endpoints": [
                "/create_video_onestep",
                "/merge_audio_image", 
                "/add_subtitles",
                "/add_subtitles_portrait",
                "/download/<file_id>"
            ]
        })
    except Exception as e:
        return jsonify({"status": "error", "error": str(e)}), 500

@app.route('/create_video_onestep', methods=['POST'])
def create_video_onestep_api():
    """Create video with subtitles in one step"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Create work directory
        work_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        work_dir = os.path.join(TEMP_DIR, work_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # Process input files
        input_image = save_input_file(data.get('input_image'), work_dir, 'input.png')
        input_audio = save_input_file(data.get('input_audio'), work_dir, 'input.mp3')
        subtitle_path = save_input_file(data.get('subtitle_path'), work_dir, 'subtitle.srt') if data.get('subtitle_path') else None
        watermark_path = save_input_file(data.get('watermark_path'), work_dir, 'watermark.png') if data.get('watermark_path') else None
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mp4"
        temp_output = os.path.join(work_dir, "output.mp4")
        final_output = os.path.join(OUTPUT_DIR, output_filename)
        
        # Call core function
        success = create_video_with_subtitles_onestep(
            input_image=input_image,
            input_audio=input_audio,
            subtitle_path=subtitle_path,
            output_video=temp_output,
            font_size=data.get('font_size'),
            outline_color=data.get('outline_color', "&H00000000"),
            background_box=data.get('background_box', True),
            background_opacity=data.get('background_opacity', 0.5),
            language=data.get('language', 'english'),
            is_portrait=data.get('is_portrait', False),
            effects=data.get('effects'),
            watermark_path=watermark_path,
            progress_callback=lambda msg: app.logger.debug(f"Progress: {msg}")
        )
        
        if success and os.path.exists(temp_output):
            # Move to output directory
            shutil.move(temp_output, final_output)
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
            
            # Generate download URL - always use RunPod proxy format
            pod_id = os.environ.get('RUNPOD_POD_ID')
            download_url = f"https://{pod_id}-5000.proxy.runpod.net/download/{file_id}"
            
            return jsonify({
                "success": True,
                "file_id": file_id,
                "download_url": download_url,
                "filename": data.get('output_filename', 'output.mp4'),
                "size": file_size
            })
        else:
            shutil.rmtree(work_dir)
            return jsonify({"error": "Video creation failed"}), 500
            
    except Exception as e:
        app.logger.error(f"Exception in create_video_onestep: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/merge_audio_image', methods=['POST'])
def merge_audio_image_api():
    """Merge audio and image with effects"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Create work directory
        work_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        work_dir = os.path.join(TEMP_DIR, work_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # Process input files
        input_mp3 = save_input_file(data.get('input_mp3'), work_dir, 'input.mp3')
        input_image = save_input_file(data.get('input_image'), work_dir, 'input.png')
        watermark_path = save_input_file(data.get('watermark_path'), work_dir, 'watermark.png') if data.get('watermark_path') else None
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mp4"
        temp_output = os.path.join(work_dir, "output.mp4")
        final_output = os.path.join(OUTPUT_DIR, output_filename)
        
        # Call core function without zoom_factor
        success, result = merge_audio_image_to_video_with_effects(
            input_mp3=input_mp3,
            input_image=input_image,
            output_video=temp_output,
            effects=data.get('effects', ["zoom_in", "zoom_out"]),
            watermark_path=watermark_path
        )
        
        if success and os.path.exists(result):
            # Move to output directory
            shutil.move(result, final_output)
            file_size = os.path.getsize(final_output)
            
            # Store metadata
            file_metadata[file_id] = {
                "filename": output_filename,
                "original_name": data.get('output_filename', 'output.mp4'),
                "size": file_size,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            
            # Clean up
            shutil.rmtree(work_dir)
            
            # Generate download URL - always use RunPod proxy format
            pod_id = os.environ.get('RUNPOD_POD_ID')
            download_url = f"https://{pod_id}-5000.proxy.runpod.net/download/{file_id}"
            
            return jsonify({
                "success": True,
                "file_id": file_id,
                "download_url": download_url,
                "filename": data.get('output_filename', 'output.mp4'),
                "size": file_size
            })
        else:
            shutil.rmtree(work_dir)
            return jsonify({"error": f"Merge failed: {result}"}), 500
            
    except Exception as e:
        app.logger.error(f"Exception in merge_audio_image: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/add_subtitles', methods=['POST'])
def add_subtitles_api():
    """Add subtitles to video"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Create work directory
        work_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        work_dir = os.path.join(TEMP_DIR, work_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # Process input files
        input_video = save_input_file(data.get('input_video'), work_dir, 'input.mp4')
        subtitle_path = save_input_file(data.get('subtitle_path'), work_dir, 'subtitle.srt')
        watermark_path = save_input_file(data.get('watermark_path'), work_dir, 'watermark.png') if data.get('watermark_path') else None
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mp4"
        temp_output = os.path.join(work_dir, "output.mp4")
        final_output = os.path.join(OUTPUT_DIR, output_filename)
        
        # Call core function
        success = add_subtitles_to_video(
            input_video_path=input_video,
            subtitle_path=subtitle_path,
            output_video_path=temp_output,
            font_size=data.get('font_size'),
            outline_color=data.get('outline_color', "&H00000000"),
            background_box=data.get('background_box', True),
            background_opacity=data.get('background_opacity', 0.5),
            language=data.get('language', 'english')
        )
        
        if success and os.path.exists(temp_output):
            # Move to output directory
            shutil.move(temp_output, final_output)
            file_size = os.path.getsize(final_output)
            
            # Store metadata
            file_metadata[file_id] = {
                "filename": output_filename,
                "original_name": data.get('output_filename', 'output.mp4'),
                "size": file_size,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            
            # Clean up
            shutil.rmtree(work_dir)
            
            # Generate download URL - always use RunPod proxy format
            pod_id = os.environ.get('RUNPOD_POD_ID')
            download_url = f"https://{pod_id}-5000.proxy.runpod.net/download/{file_id}"
            
            return jsonify({
                "success": True,
                "file_id": file_id,
                "download_url": download_url,
                "filename": data.get('output_filename', 'output.mp4'),
                "size": file_size
            })
        else:
            shutil.rmtree(work_dir)
            return jsonify({"error": "Adding subtitles failed"}), 500
            
    except Exception as e:
        app.logger.error(f"Exception in add_subtitles: {e}", exc_info=True)
        return jsonify({"error": str(e)}), 500

@app.route('/add_subtitles_portrait', methods=['POST'])
def add_subtitles_portrait_api():
    """Add subtitles to portrait video"""
    try:
        data = request.get_json()
        if not data:
            return jsonify({"error": "No JSON data provided"}), 400
        
        # Create work directory
        work_id = datetime.now().strftime('%Y%m%d_%H%M%S_%f')
        work_dir = os.path.join(TEMP_DIR, work_id)
        os.makedirs(work_dir, exist_ok=True)
        
        # Process input files
        input_video = save_input_file(data.get('input_video'), work_dir, 'input.mp4')
        subtitle_path = save_input_file(data.get('subtitle_path'), work_dir, 'subtitle.srt')
        watermark_path = save_input_file(data.get('watermark_path'), work_dir, 'watermark.png') if data.get('watermark_path') else None
        
        # Generate unique file ID
        file_id = str(uuid.uuid4())
        output_filename = f"{file_id}.mp4"
        temp_output = os.path.join(work_dir, "output.mp4")
        final_output = os.path.join(OUTPUT_DIR, output_filename)
        
        # Call core function
        success = add_subtitles_to_video_portrait(
            input_video_path=input_video,
            subtitle_path=subtitle_path,
            output_video_path=temp_output,
            font_size=data.get('font_size'),
            outline_color=data.get('outline_color', "&H00000000"),
            background_box=data.get('background_box', True),
            background_opacity=data.get('background_opacity', 0.5),
            language=data.get('language', 'english')
        )
        
        if success and os.path.exists(temp_output):
            # Move to output directory
            shutil.move(temp_output, final_output)
            file_size = os.path.getsize(final_output)
            
            # Store metadata
            file_metadata[file_id] = {
                "filename": output_filename,
                "original_name": data.get('output_filename', 'output.mp4'),
                "size": file_size,
                "created_at": datetime.now(),
                "expires_at": datetime.now() + timedelta(hours=1)
            }
            
            # Clean up
            shutil.rmtree(work_dir)
            
            # Generate download URL - always use RunPod proxy format
            pod_id = os.environ.get('RUNPOD_POD_ID')
            download_url = f"https://{pod_id}-5000.proxy.runpod.net/download/{file_id}"
            
            return jsonify({
                "success": True,
                "file_id": file_id,
                "download_url": download_url,
                "filename": data.get('output_filename', 'output.mp4'),
                "size": file_size
            })
        else:
            shutil.rmtree(work_dir)
            return jsonify({"error": "Adding subtitles failed"}), 500
            
    except Exception as e:
        app.logger.error(f"Exception in add_subtitles_portrait: {e}", exc_info=True)
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

if __name__ == '__main__':
    import logging
    logging.basicConfig(level=logging.INFO)
    
    port = int(os.environ.get('PORT', 5000))
    
    print(f"\nStarting Fixed Video Processing API on port {port}")
    print("Available endpoints:")
    print("- GET  /health")
    print("- POST /create_video_onestep")
    print("- POST /merge_audio_image")
    print("- POST /add_subtitles")
    print("- POST /add_subtitles_portrait")
    print("- GET  /download/<file_id>")
    print("- GET  /cleanup")
    print("\n")
    
    app.run(host='0.0.0.0', port=port)