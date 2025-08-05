#!/bin/bash
# RunPod Serverless 启动脚本

echo "🚀 Starting RunPod Serverless Video Generation Handler..."

# 显示环境信息
echo "Environment Info:"
echo "  Python Version: $(python3 --version)"
echo "  Working Directory: $(pwd)"
echo "  RUNPOD_ENDPOINT_ID: $RUNPOD_ENDPOINT_ID"
echo "  PYTHONPATH: $PYTHONPATH"

# 检查关键文件
echo "Checking files:"
ls -la serverless_handler.py core_functions.py

# 检查字体安装
echo "Checking fonts:"
fc-list | grep -i "lxgw\|wenkai" || echo "No LXGW fonts found"

# 创建必要的目录
mkdir -p /tmp/video_processing /app/outputs

# 启动 Handler
echo "Starting handler..."
exec python3 -u serverless_handler.py