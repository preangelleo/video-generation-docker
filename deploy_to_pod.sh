#!/bin/bash
# 部署视频处理服务到 RunPod

set -e

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

echo -e "${GREEN}=== RunPod 视频处理服务部署脚本 ===${NC}"

# 检查是否有 Pod ID
if [ ! -f ".runpod_video_generation_id" ]; then
    echo -e "${RED}❌ 错误: 没有找到 .runpod_video_generation_id 文件${NC}"
    echo "   请先运行: python3 create_runpod.py"
    exit 1
fi

POD_ID=$(cat .runpod_video_generation_id)
echo -e "${YELLOW}Pod ID: ${POD_ID}${NC}"

# 获取 SSH 信息
echo -e "\n${YELLOW}获取 Pod 连接信息...${NC}"
if [ -f ".runpod_ssh_info" ]; then
    SSH_CMD=$(cat .runpod_ssh_info)
    echo -e "${GREEN}SSH 命令: $SSH_CMD${NC}"
else
    echo -e "${RED}❌ 没有找到 SSH 连接信息${NC}"
    echo "请先运行: python3 check_pod_status.py"
    exit 1
fi

# 准备文件
echo -e "\n${YELLOW}准备部署文件...${NC}"
DEPLOY_DIR="deploy_package"
rm -rf $DEPLOY_DIR
mkdir -p $DEPLOY_DIR

# 复制必要文件
cp core_functions.py $DEPLOY_DIR/
cp app.py $DEPLOY_DIR/
cp requirements.txt $DEPLOY_DIR/
cp Dockerfile $DEPLOY_DIR/

# 创建部署脚本
cat > $DEPLOY_DIR/setup.sh << 'EOF'
#!/bin/bash
# RunPod 内部设置脚本

echo "=== 开始设置环境 ==="

# 更新系统
echo "更新系统包..."
apt-get update -qq

# 安装中文字体
echo "安装中文字体..."
apt-get install -y fonts-noto-cjk fonts-wqy-microhei fontconfig

# 下载 LXGW WenKai 字体
echo "下载 LXGW WenKai 字体..."
mkdir -p /usr/share/fonts/truetype/lxgw
wget -q https://github.com/lxgw/LxgwWenKai/releases/download/v1.330/LXGWWenKai-Regular.ttf \
    -O /usr/share/fonts/truetype/lxgw/LXGWWenKai-Regular.ttf
fc-cache -f -v

# 安装 Python 依赖
echo "安装 Python 依赖..."
pip3 install --no-cache-dir -r requirements.txt

# 创建工作目录
mkdir -p /workspace/video_generation

# 启动 API 服务
echo "启动 API 服务..."
cd /workspace/video_generation
nohup python3 app.py > api.log 2>&1 &

echo "API 服务已启动，日志: /workspace/video_generation/api.log"
echo "健康检查: curl http://localhost:5000/health"
echo "=== 设置完成 ==="
EOF

chmod +x $DEPLOY_DIR/setup.sh

# 创建测试脚本
cat > $DEPLOY_DIR/test_api.py << 'EOF'
#!/usr/bin/env python3
import requests
import time

print("等待 API 启动...")
for i in range(30):
    try:
        response = requests.get("http://localhost:5000/health", timeout=2)
        if response.status_code == 200:
            print("✅ API 服务已启动!")
            print(response.json())
            break
    except:
        pass
    time.sleep(1)
else:
    print("❌ API 启动超时")
EOF

# 打包文件
echo -e "${YELLOW}打包文件...${NC}"
tar -czf deploy_package.tar.gz -C $DEPLOY_DIR .

# 上传到 Pod
echo -e "\n${YELLOW}上传文件到 Pod...${NC}"

# 从 SSH 命令提取目标地址
SCP_TARGET=$(echo "$SSH_CMD" | awk '{print $NF}')

echo "执行: scp -i ~/.ssh/runpod/runpod_key -P 20435 deploy_package.tar.gz root@157.157.221.29:/workspace/"
scp -i ~/.ssh/runpod/runpod_key -P 20435 deploy_package.tar.gz root@157.157.221.29:/workspace/

# 在 Pod 中执行部署
echo -e "\n${YELLOW}在 Pod 中部署...${NC}"
$SSH_CMD << 'REMOTE_COMMANDS'
cd /workspace
echo "解压文件..."
tar -xzf deploy_package.tar.gz -C video_generation/ || mkdir -p video_generation && tar -xzf deploy_package.tar.gz -C video_generation/

cd video_generation
echo "运行设置脚本..."
bash setup.sh

echo "测试 API..."
python3 test_api.py
REMOTE_COMMANDS

# 清理本地文件
rm -rf $DEPLOY_DIR deploy_package.tar.gz

echo -e "\n${GREEN}✅ 部署完成!${NC}"
echo -e "${YELLOW}下一步:${NC}"
echo "1. SSH 进入 Pod: $SSH_CMD"
echo "2. 查看日志: tail -f /workspace/video_generation/api.log"
echo "3. 测试 API: curl http://localhost:5000/health"