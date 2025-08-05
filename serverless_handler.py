#!/usr/bin/env python3
"""
RunPod Serverless Handler for Video Generation API
适配 RunPod Serverless 环境的处理函数
"""

import os
import sys
import json
import tempfile
import base64
import runpod
from typing import Dict, Any

# 添加当前目录到 Python 路径
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from core_functions import (
    create_video_with_subtitles_onestep,
    merge_audio_image_to_video_with_effects,
    add_subtitles_to_video,
    add_subtitles_to_video_portrait
)

def handler(event):
    """
    RunPod Serverless Handler 主函数
    
    Args:
        event: RunPod 事件对象，包含 'input' 键
        
    Returns:
        处理结果
    """
    try:
        # 获取输入数据
        input_data = event.get("input", {})
        endpoint = input_data.get("endpoint", "")
        
        print(f"🚀 Serverless Handler 开始处理: {endpoint}")
        
        # 健康检查
        if endpoint == "health":
            return {
                "status": "success",
                "message": "Video Generation API is healthy",
                "version": "1.0.0",
                "endpoints": [
                    "create_video_onestep",
                    "merge_audio_image", 
                    "add_subtitles",
                    "add_subtitles_portrait"
                ]
            }
        
        # 根据端点分发请求
        if endpoint == "create_video_onestep":
            return handle_create_video_onestep(input_data)
        elif endpoint == "merge_audio_image":
            return handle_merge_audio_image(input_data)
        elif endpoint == "add_subtitles":
            return handle_add_subtitles(input_data)
        elif endpoint == "add_subtitles_portrait":
            return handle_add_subtitles_portrait(input_data)
        else:
            return {
                "status": "error",
                "message": f"未知的端点: {endpoint}",
                "available_endpoints": [
                    "create_video_onestep",
                    "merge_audio_image", 
                    "add_subtitles",
                    "add_subtitles_portrait"
                ]
            }
            
    except Exception as e:
        print(f"❌ Handler 错误: {str(e)}")
        return {
            "status": "error",
            "message": f"处理请求时发生错误: {str(e)}"
        }

def decode_base64_file(base64_data: str, file_extension: str) -> str:
    """将 base64 数据解码并保存为临时文件"""
    try:
        # 移除可能的 data URL 前缀
        if ',' in base64_data:
            base64_data = base64_data.split(',')[1]
        
        # 解码 base64 数据
        file_data = base64.b64decode(base64_data)
        
        # 创建临时文件
        with tempfile.NamedTemporaryFile(delete=False, suffix=file_extension) as tmp_file:
            tmp_file.write(file_data)
            return tmp_file.name
            
    except Exception as e:
        raise Exception(f"解码 base64 文件失败: {str(e)}")

def encode_file_to_base64(file_path: str) -> str:
    """将文件编码为 base64"""
    try:
        with open(file_path, "rb") as f:
            file_data = f.read()
        return base64.b64encode(file_data).decode('utf-8')
    except Exception as e:
        raise Exception(f"编码文件为 base64 失败: {str(e)}")

def cleanup_temp_files(*file_paths):
    """清理临时文件"""
    for file_path in file_paths:
        if file_path and os.path.exists(file_path):
            try:
                os.unlink(file_path)
            except Exception as e:
                print(f"⚠️ 清理临时文件失败 {file_path}: {str(e)}")

def handle_create_video_onestep(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理创建视频的请求"""
    temp_files = []
    
    try:
        # 解码输入文件
        input_image = decode_base64_file(input_data["input_image"], ".png")
        input_audio = decode_base64_file(input_data["input_audio"], ".wav")
        temp_files.extend([input_image, input_audio])
        
        # 可选参数
        subtitle_path = None
        if input_data.get("subtitle_data"):
            subtitle_path = decode_base64_file(input_data["subtitle_data"], ".srt")
            temp_files.append(subtitle_path)
        
        zoom_factor = input_data.get("zoom_factor", 1.2)
        pan_direction = input_data.get("pan_direction", "right")
        language = input_data.get("language", "english")
        
        print(f"📹 处理视频创建请求 - 语言: {language}, 缩放: {zoom_factor}, 方向: {pan_direction}")
        
        # 调用核心函数
        result = create_video_with_subtitles_onestep(
            input_image=input_image,
            input_audio=input_audio,
            subtitle_path=subtitle_path,
            zoom_factor=zoom_factor,
            pan_direction=pan_direction,
            language=language
        )
        
        if result and result.get("success") and result.get("output_video"):
            # 将输出视频编码为 base64
            output_video_base64 = encode_file_to_base64(result["output_video"])
            
            # 清理输出文件
            if os.path.exists(result["output_video"]):
                os.unlink(result["output_video"])
            
            return {
                "status": "success",
                "message": "视频创建成功",
                "video_base64": output_video_base64,
                "processing_time": result.get("processing_time", 0)
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "视频创建失败")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"处理视频创建请求失败: {str(e)}"
        }
    finally:
        cleanup_temp_files(*temp_files)

def handle_merge_audio_image(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理音频图像合并请求"""
    temp_files = []
    
    try:
        # 解码输入文件
        input_image = decode_base64_file(input_data["input_image"], ".png")
        input_audio = decode_base64_file(input_data["input_audio"], ".wav")
        temp_files.extend([input_image, input_audio])
        
        # 可选参数
        zoom_factor = input_data.get("zoom_factor", 1.2)
        pan_direction = input_data.get("pan_direction", "right")
        
        print(f"🎵 处理音频图像合并请求 - 缩放: {zoom_factor}, 方向: {pan_direction}")
        
        # 调用核心函数
        effects = ["zoom_in"] if zoom_factor > 1.0 else []
        if pan_direction in ["left", "right", "up", "down"]:
            effects.append(f"pan_{pan_direction}")
        
        success, result_path = merge_audio_image_to_video_with_effects(
            input_mp3=input_audio,
            input_image=input_image,
            output_video=None,
            effects=effects
        )
        
        result = {
            "success": success,
            "output_video": result_path if success else None,
            "error": None if success else "音频图像合并失败"
        }
        
        if result and result.get("success") and result.get("output_video"):
            # 将输出视频编码为 base64
            output_video_base64 = encode_file_to_base64(result["output_video"])
            
            # 清理输出文件
            if os.path.exists(result["output_video"]):
                os.unlink(result["output_video"])
            
            return {
                "status": "success",
                "message": "音频图像合并成功",
                "video_base64": output_video_base64,
                "processing_time": result.get("processing_time", 0)
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "音频图像合并失败")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"处理音频图像合并请求失败: {str(e)}"
        }
    finally:
        cleanup_temp_files(*temp_files)

def handle_add_subtitles(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理添加字幕请求（横屏）"""
    temp_files = []
    
    try:
        # 解码输入文件
        input_video = decode_base64_file(input_data["input_video"], ".mp4")
        subtitle_path = decode_base64_file(input_data["subtitle_data"], ".srt")
        temp_files.extend([input_video, subtitle_path])
        
        # 可选参数
        language = input_data.get("language", "english")
        
        print(f"📝 处理添加字幕请求（横屏）- 语言: {language}")
        
        # 调用核心函数
        success = add_subtitles_to_video(
            input_video_path=input_video,
            subtitle_path=subtitle_path,
            output_video_path=None,
            language=language
        )
        
        # 构建结果对象
        if success:
            # 假设输出文件名基于输入文件名生成
            output_path = input_video.replace('.mp4', '_subtitled.mp4')
            result = {
                "success": True,
                "output_video": output_path,
                "error": None
            }
        else:
            result = {
                "success": False,
                "output_video": None,
                "error": "字幕添加失败"
            }
        
        if result and result.get("success") and result.get("output_video"):
            # 将输出视频编码为 base64
            output_video_base64 = encode_file_to_base64(result["output_video"])
            
            # 清理输出文件
            if os.path.exists(result["output_video"]):
                os.unlink(result["output_video"])
            
            return {
                "status": "success",
                "message": "字幕添加成功",
                "video_base64": output_video_base64,
                "processing_time": result.get("processing_time", 0)
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "字幕添加失败")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"处理添加字幕请求失败: {str(e)}"
        }
    finally:
        cleanup_temp_files(*temp_files)

def handle_add_subtitles_portrait(input_data: Dict[str, Any]) -> Dict[str, Any]:
    """处理添加字幕请求（竖屏）"""
    temp_files = []
    
    try:
        # 解码输入文件
        input_video = decode_base64_file(input_data["input_video"], ".mp4")
        subtitle_path = decode_base64_file(input_data["subtitle_data"], ".srt")
        temp_files.extend([input_video, subtitle_path])
        
        # 可选参数
        language = input_data.get("language", "english")
        
        print(f"📱 处理添加字幕请求（竖屏）- 语言: {language}")
        
        # 调用核心函数
        success = add_subtitles_to_video_portrait(
            input_video_path=input_video,
            subtitle_path=subtitle_path,
            output_video_path=None,
            language=language
        )
        
        # 构建结果对象
        if success:
            # 假设输出文件名基于输入文件名生成
            output_path = input_video.replace('.mp4', '_portrait_subtitled.mp4')
            result = {
                "success": True,
                "output_video": output_path,
                "error": None
            }
        else:
            result = {
                "success": False,
                "output_video": None,
                "error": "竖屏字幕添加失败"
            }
        
        if result and result.get("success") and result.get("output_video"):
            # 将输出视频编码为 base64
            output_video_base64 = encode_file_to_base64(result["output_video"])
            
            # 清理输出文件
            if os.path.exists(result["output_video"]):
                os.unlink(result["output_video"])
            
            return {
                "status": "success",
                "message": "竖屏字幕添加成功",
                "video_base64": output_video_base64,
                "processing_time": result.get("processing_time", 0)
            }
        else:
            return {
                "status": "error",
                "message": result.get("error", "竖屏字幕添加失败")
            }
            
    except Exception as e:
        return {
            "status": "error",
            "message": f"处理竖屏字幕请求失败: {str(e)}"
        }
    finally:
        cleanup_temp_files(*temp_files)

if __name__ == "__main__":
    # 检查是否在 RunPod 环境中
    if os.environ.get('RUNPOD_ENDPOINT_ID') or os.environ.get('RUNPOD_JOB_ID') or 'runpod' in os.environ.get('HOSTNAME', '').lower():
        print("🚀 Starting RunPod Serverless Handler...")
        print(f"🔧 Environment: RUNPOD_ENDPOINT_ID={os.environ.get('RUNPOD_ENDPOINT_ID')}")
        print(f"🔧 Environment: RUNPOD_JOB_ID={os.environ.get('RUNPOD_JOB_ID')}")
        print(f"🔧 Environment: HOSTNAME={os.environ.get('HOSTNAME')}")
        runpod.serverless.start({"handler": handler})
    else:
        # 本地测试
        print("🧪 Local Testing Mode")
        test_event = {
            "input": {
                "endpoint": "health"
            }
        }
        
        result = handler(test_event)
        print(json.dumps(result, indent=2, ensure_ascii=False))