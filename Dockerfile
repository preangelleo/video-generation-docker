# Multi-stage build for Video Generation Flask API
FROM ubuntu:22.04

# Set environment variables
ENV DEBIAN_FRONTEND=noninteractive
ENV PYTHONUNBUFFERED=1
ENV LANG=C.UTF-8
ENV LC_ALL=C.UTF-8

# Install system dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    python3-venv \
    ffmpeg \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    libgomp1 \
    wget \
    curl \
    fontconfig \
    fonts-dejavu-core \
    && rm -rf /var/lib/apt/lists/*

# Install Chinese fonts (LXGW WenKai Bold)
RUN mkdir -p /usr/share/fonts/truetype/lxgw && \
    wget -O /usr/share/fonts/truetype/lxgw/LXGWWenKai-Bold.ttf \
    "https://github.com/lxgw/LxgwWenKai/releases/download/v1.320/LXGWWenKai-Bold.ttf" && \
    fc-cache -fv

# Create working directory
WORKDIR /workspace/video_generation

# Copy Python requirements and install
COPY requirements.txt .
RUN pip3 install --no-cache-dir -r requirements.txt

# Copy application files
COPY . .

# Create necessary directories
RUN mkdir -p /workspace/video_generation/outputs && \
    mkdir -p /tmp/video_processing && \
    chmod 755 /workspace/video_generation/outputs && \
    chmod 755 /tmp/video_processing

# Expose Flask port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=30s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:5000/health || exit 1

# Start Flask API
CMD ["python3", "app.py"]