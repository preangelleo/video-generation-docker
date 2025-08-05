FROM nvidia/cuda:12.1.0-runtime-ubuntu22.04

# 设置非交互式安装
ENV DEBIAN_FRONTEND=noninteractive

# 安装系统依赖
RUN apt-get update && apt-get install -y \
    python3-pip \
    python3-dev \
    ffmpeg \
    wget \
    curl \
    git \
    unzip \
    fonts-noto-cjk \
    fonts-wqy-microhei \
    fontconfig \
    && rm -rf /var/lib/apt/lists/*

# 设置工作目录
WORKDIR /app

# 复制 requirements 文件
COPY requirements.txt .

# 安装 Node.js 和 npm (for PM2)
RUN curl -fsSL https://deb.nodesource.com/setup_18.x | bash - && \
    apt-get install -y nodejs && \
    npm install -g pm2

# 安装 Python 依赖
RUN pip3 install --no-cache-dir -r requirements.txt

# 下载并安装 LXGW WenKai Bold 字体 (中文字幕需要)
# 注意：只安装 Bold 版本，不要 Regular，否则 fontconfig 会默认选择 Regular
RUN mkdir -p /usr/share/fonts/truetype/lxgw && \
    cd /tmp && \
    wget -q https://github.com/lxgw/LxgwWenKai/releases/download/v1.330/lxgw-wenkai-v1.330.zip && \
    unzip -j lxgw-wenkai-v1.330.zip 'lxgw-wenkai-v1.330/LXGWWenKai-Bold.ttf' && \
    cp LXGWWenKai-Bold.ttf /usr/share/fonts/truetype/lxgw/ && \
    fc-cache -f -v && \
    rm -f /tmp/lxgw-wenkai-v1.330.zip /tmp/LXGWWenKai-Bold.ttf

# 复制应用代码
COPY app.py .
COPY core_functions.py .
COPY pm2_config.json .
COPY start_with_pm2.sh .

# 创建必要的目录
RUN mkdir -p /tmp/video_processing /app/uploads /app/logs

# 设置环境变量
ENV PYTHONPATH=/app:$PYTHONPATH
ENV PYTHONUNBUFFERED=1

# 暴露端口
EXPOSE 5000

# 健康检查
HEALTHCHECK --interval=30s --timeout=3s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# 设置执行权限
RUN chmod +x start_with_pm2.sh

# 启动命令 - 使用 PM2
CMD ["./start_with_pm2.sh"]