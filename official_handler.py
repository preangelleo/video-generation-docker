#!/usr/bin/env python3
"""
RunPod 官方 2025 标准最简化 Handler
完全按照官方文档格式
"""

import runpod

def handler(job):
    """
    RunPod Serverless Handler - 官方标准格式
    
    Args:
        job: RunPod 作业对象，包含 'input' 和 'id' 键
    
    Returns:
        处理结果 (dict 或其他可序列化对象)
    """
    
    print(f"🚀 Handler started for job: {job.get('id', 'unknown')}")
    
    # 获取输入数据
    job_input = job.get("input", {})
    endpoint = job_input.get("endpoint", "unknown")
    
    print(f"📋 Processing endpoint: {endpoint}")
    
    # 处理不同端点
    if endpoint == "health":
        return {
            "status": "success",
            "message": "Official handler is working perfectly!",
            "job_id": job.get('id'),
            "handler_version": "official_2025_v1.0",
            "test_data": {
                "number": 42,
                "text": "Hello RunPod!"
            }
        }
    elif endpoint == "echo":
        # 简单的回声测试
        return {
            "status": "success",
            "echo": job_input,
            "job_id": job.get('id')
        }
    else:
        return {
            "status": "success",
            "message": f"Received unknown endpoint: {endpoint}",
            "job_id": job.get('id'),
            "available_endpoints": ["health", "echo"]
        }

# 按照官方文档启动 Serverless
if __name__ == "__main__":
    print("🔧 Starting Official RunPod Serverless Handler...")
    runpod.serverless.start({"handler": handler})