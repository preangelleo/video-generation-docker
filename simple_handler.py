#!/usr/bin/env python3
"""
简化的 RunPod Serverless Handler - 用于调试启动问题
"""

import os
import sys
import json

def handler(job):
    """最简单的 Handler 函数"""
    try:
        print("🚀 Simple Handler started successfully!")
        print(f"📋 Received job: {job}")
        
        input_data = job.get("input", {})
        endpoint = input_data.get("endpoint", "unknown")
        
        print(f"📡 Endpoint: {endpoint}")
        
        if endpoint == "health":
            return {
                "status": "success",
                "message": "Simple handler is working!",
                "version": "debug-1.0",
                "environment": {
                    "RUNPOD_ENDPOINT_ID": os.environ.get('RUNPOD_ENDPOINT_ID'),
                    "RUNPOD_JOB_ID": os.environ.get('RUNPOD_JOB_ID'),
                    "HOSTNAME": os.environ.get('HOSTNAME'),
                    "PWD": os.getcwd(),
                    "PYTHONPATH": os.environ.get('PYTHONPATH')
                }
            }
        else:
            return {
                "status": "success", 
                "message": f"Received request for: {endpoint}",
                "note": "This is a debug handler - only health check implemented"
            }
            
    except Exception as e:
        print(f"❌ Handler error: {str(e)}")
        return {
            "status": "error",
            "message": f"Handler error: {str(e)}"
        }

if __name__ == "__main__":
    print("🔧 Simple Handler Starting...")
    print(f"🐍 Python version: {sys.version}")
    print(f"📁 Working directory: {os.getcwd()}")
    print(f"📋 Environment variables:")
    
    # 打印关键环境变量
    for key in ['RUNPOD_ENDPOINT_ID', 'RUNPOD_JOB_ID', 'HOSTNAME', 'PYTHONPATH']:
        value = os.environ.get(key, 'NOT_SET')
        print(f"   {key}: {value}")
    
    # 检查是否在 RunPod 环境中
    runpod_indicators = [
        os.environ.get('RUNPOD_ENDPOINT_ID'),
        os.environ.get('RUNPOD_JOB_ID'),
        'runpod' in os.environ.get('HOSTNAME', '').lower()
    ]
    
    print(f"🔍 RunPod environment indicators: {runpod_indicators}")
    
    if any(runpod_indicators):
        print("✅ Detected RunPod environment - starting serverless mode")
        try:
            import runpod
            print("✅ RunPod package imported successfully")
            runpod.serverless.start({"handler": handler})
        except ImportError as e:
            print(f"❌ Failed to import runpod: {e}")
            print("📋 Available packages:")
            import pkg_resources
            installed_packages = [d.project_name for d in pkg_resources.working_set]
            for pkg in sorted(installed_packages):
                if 'runpod' in pkg.lower():
                    print(f"   - {pkg}")
            sys.exit(1)
        except Exception as e:
            print(f"❌ Failed to start serverless: {e}")
            sys.exit(1)
    else:
        print("🧪 Local testing mode")
        test_job = {"input": {"endpoint": "health"}}
        result = handler(test_job)
        print(f"📤 Test result: {json.dumps(result, indent=2)}")