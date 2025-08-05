#!/bin/bash
# Video Generation Serverless Docker Image Build Script

# 配置
IMAGE_NAME="video-generation-serverless"
DOCKER_HUB_USER="your-dockerhub-username"  # 需要修改为你的 Docker Hub 用户名
VERSION="1.0.0"

# 颜色输出
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo -e "${GREEN}Building Video Generation Serverless Docker Image...${NC}"

# 检查必要文件是否存在
echo "Checking required files..."
required_files=("Dockerfile.serverless" "requirements.txt" "serverless_handler.py" "core_functions.py")
for file in "${required_files[@]}"; do
    if [ ! -f "$file" ]; then
        echo -e "${RED}Error: Required file '$file' not found!${NC}"
        exit 1
    fi
done

# 构建镜像
echo -e "${YELLOW}Building Docker image for Serverless...${NC}"
docker build -f Dockerfile.serverless -t $IMAGE_NAME:$VERSION -t $IMAGE_NAME:latest .

if [ $? -eq 0 ]; then
    echo -e "${GREEN}Build successful!${NC}"
else
    echo -e "${RED}Build failed!${NC}"
    exit 1
fi

# 可选：推送到 Docker Hub
read -p "Push to Docker Hub? (y/n) " -n 1 -r
echo
if [[ $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Tagging for Docker Hub...${NC}"
    docker tag $IMAGE_NAME:$VERSION $DOCKER_HUB_USER/$IMAGE_NAME:$VERSION
    docker tag $IMAGE_NAME:latest $DOCKER_HUB_USER/$IMAGE_NAME:latest
    
    echo -e "${YELLOW}Pushing to Docker Hub...${NC}"
    docker push $DOCKER_HUB_USER/$IMAGE_NAME:$VERSION
    docker push $DOCKER_HUB_USER/$IMAGE_NAME:latest
    
    if [ $? -eq 0 ]; then
        echo -e "${GREEN}Push successful!${NC}"
        echo -e "${GREEN}Image available at: $DOCKER_HUB_USER/$IMAGE_NAME:$VERSION${NC}"
        echo -e "${YELLOW}Update create_serverless.py with this image name:${NC}"
        echo -e "${YELLOW}  docker_image: $DOCKER_HUB_USER/$IMAGE_NAME:$VERSION${NC}"
    else
        echo -e "${RED}Push failed!${NC}"
    fi
fi

# 显示镜像信息
echo -e "${GREEN}Image info:${NC}"
docker images | grep $IMAGE_NAME

echo -e "\n${GREEN}Next steps:${NC}"
echo -e "1. Update create_serverless.py with your Docker Hub username"
echo -e "2. Run: python3 create_serverless.py create"
echo -e "3. Test: python3 create_serverless.py test"