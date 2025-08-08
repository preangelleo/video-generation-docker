# 视频生成 API Docker 镜像

这是我的第一个开源项目！🎉

## 项目简介

这个 Docker 镜像提供了一个简单易用的视频生成 API 服务。它可以将图片和音频合成为视频，支持添加字幕和各种视觉效果（如缩放、平移等）。

## 主要功能

- 🖼️ 图片 + 音频 → 视频合成
- 📝 自动添加字幕（支持中英文）
- 🎬 视觉效果（缩放、平移动画）
- 🎯 智能场景检测
- 🚀 RESTful API 接口

## 快速开始

### Python 客户端使用（通过 pip 安装）

```python
from video_generation_api import VideoGenerationClient

# 初始化客户端
client = VideoGenerationClient("http://localhost:5000")

# 创建视频
result = client.create_video(
    image_path="image.jpg",
    audio_path="audio.mp3",
    subtitle_path="subtitles.srt",
    effects=["zoom_in"],
    language="chinese",
    output_path="output.mp4"
)
```

### Docker 使用

#### 1. 拉取镜像

```bash
docker pull betashow/video-generation-api:latest
```

#### 2. 运行容器

```bash
docker run -d -p 5000:5000 --name video-api betashow/video-generation-api:latest
```

#### 3. 测试服务

```bash
# 检查服务状态
curl http://localhost:5000/health
```

如果通过 pip 安装，使用以下命令启动服务器：

```bash
video-generation-api
```

## 🚀 想在 AWS 上部署这个服务？

推荐使用我们的最新部署方案：**[CloudBurst Fargate](https://github.com/preangelleo/cloudburst-fargate)**

CloudBurst Fargate 是 CloudBurst 项目的下一代版本，提供 AWS 无服务器部署：
- 🚀 **无服务器架构** - 无需管理服务器
- 💰 **按秒计费** - 只为实际处理时间付费
- ⚡ **自动伸缩** - 自动处理任何工作负载
- 🔧 **零维护** - AWS 管理所有基础设施
- 📊 **更高效率** - 比 EC2 实例更加高效

如需使用传统 EC2 实例部署，请参考原版 [CloudBurst](https://github.com/preangelleo/cloudburst) 项目。

非常适合需要按需生成视频但不想管理服务器的生产场景。

适合偶尔需要生成视频但不想维护昂贵基础设施的生产场景。

## API 使用示例

### 创建视频（统一接口）

```bash
curl -X POST http://localhost:5000/create_video_onestep \
  -H "Content-Type: application/json" \
  -d '{
    "input_image": "base64编码的图片",
    "input_audio": "base64编码的音频",
    "subtitle": "base64编码的SRT字幕（可选）",
    "effects": ["zoom_in"],
    "language": "chinese"
  }'
```

### 下载生成的视频

```bash
curl http://localhost:5000/download/{file_id} -o output.mp4
```

## 🎬 输出效果展示

看看这个 API 能生成什么样的视频：

**英文示例**：
[![英文视频示例](https://img.youtube.com/vi/JiWsyuyw1ao/maxresdefault.jpg)](https://www.youtube.com/watch?v=JiWsyuyw1ao)

**中文示例**：
[![中文视频示例](https://img.youtube.com/vi/WYFyUAk9F6k/maxresdefault.jpg)](https://www.youtube.com/watch?v=WYFyUAk9F6k)

**展示的特性**：
- ✅ 专业字幕（带半透明背景）
- ✅ 流畅的缩放特效（Ken Burns 效果）
- ✅ 完美的音画同步
- ✅ 高质量 1080p 视频输出
- ✅ 支持中英双语

以上示例均使用"完整功能"模式生成，启用了字幕和特效。

## 应用场景

- 📚 教育视频制作
- 🎙️ 播客视频化
- 📖 有声书配图
- 🎨 创意内容生成

## 技术栈

- Python Flask
- FFmpeg
- OpenCV
- Docker

## 📚 相关资源

- **PyPI 包**: https://pypi.org/project/video-generation-api/
- **Docker Hub**: https://hub.docker.com/r/betashow/video-generation-api
- **GitHub 仓库**: https://github.com/preangelleo/video-generation-docker
- **CloudBurst Fargate (推荐 AWS 部署)**: https://github.com/preangelleo/cloudburst-fargate
- **CloudBurst (传统 EC2 部署)**: https://github.com/preangelleo/cloudburst

## 开源协议

MIT License

---

希望这个项目能对大家有所帮助！欢迎提出建议和贡献代码。如果觉得有用，请给个 Star ⭐

第一次做开源项目，还有很多不足之处，感谢大家的理解和支持！🙏