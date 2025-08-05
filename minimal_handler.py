#!/usr/bin/env python3
"""
最简化的 RunPod Handler - 强制启动 Serverless
"""

import os
import sys

def handler(job):
    """最简单的处理函数"""
    print(f"🚀 Handler called with job: {job}")
    
    input_data = job.get("input", {})
    endpoint = input_data.get("endpoint", "unknown")
    
    return {
        "status": "success",
        "message": f"Minimal handler working! Endpoint: {endpoint}",
        "job_data": job,
        "environment": {
            "RUNPOD_ENDPOINT_ID": os.environ.get('RUNPOD_ENDPOINT_ID'),
            "RUNPOD_JOB_ID": os.environ.get('RUNPOD_JOB_ID'),
            "HOSTNAME": os.environ.get('HOSTNAME')
        }
    }

if __name__ == "__main__":
    print("🔧 Starting Minimal Handler...")
    print(f"🐍 Python: {sys.version}")
    print(f"📁 CWD: {os.getcwd()}")
    
    # 强制启动 Serverless（不做任何环境检测）
    try:
        import runpod
        print("✅ RunPod imported successfully")
        print("🚀 Starting serverless without environment checks...")
        runpod.serverless.start({"handler": handler})
    except Exception as e:
        print(f"❌ Failed to start: {e}")
        # 打印详细错误信息
        import traceback
        traceback.print_exc()
        sys.exit(1)