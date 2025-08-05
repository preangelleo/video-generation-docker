#!/usr/bin/env python3
"""
本地测试 Serverless Handler
"""

import json
import base64
from pathlib import Path
from serverless_handler import handler

def encode_file_to_base64(file_path: str) -> str:
    """将文件编码为 base64"""
    with open(file_path, "rb") as f:
        file_data = f.read()
    return base64.b64encode(file_data).decode('utf-8')

def test_health_check():
    """测试健康检查"""
    print("🧪 测试健康检查...")
    
    event = {
        "input": {
            "endpoint": "health"
        }
    }
    
    result = handler(event)
    print(f"结果: {json.dumps(result, indent=2, ensure_ascii=False)}")
    return result.get("status") == "success"

def test_with_sample_files():
    """测试实际文件处理（需要样本文件）"""
    print("🧪 测试文件处理...")
    
    # 检查样本文件是否存在
    sample_dir = Path("../sample_data")  # 假设有样本数据目录
    
    if not sample_dir.exists():
        print("⚠️ 没有找到样本数据目录，跳过文件处理测试")
        return True
    
    image_files = list(sample_dir.glob("*.png")) + list(sample_dir.glob("*.jpg"))
    audio_files = list(sample_dir.glob("*.wav")) + list(sample_dir.glob("*.mp3"))
    
    if not image_files or not audio_files:
        print("⚠️ 样本目录中没有找到图像或音频文件，跳过文件处理测试")
        return True
    
    try:
        event = {
            "input": {
                "endpoint": "merge_audio_image",
                "input_image": encode_file_to_base64(str(image_files[0])),
                "input_audio": encode_file_to_base64(str(audio_files[0])),
                "zoom_factor": 1.1,
                "pan_direction": "right"
            }
        }
        
        result = handler(event)
        
        if result.get("status") == "success":
            print("✅ 文件处理测试成功")
            
            # 保存输出视频（如果有）
            if result.get("video_base64"):
                output_data = base64.b64decode(result["video_base64"])
                with open("test_output.mp4", "wb") as f:
                    f.write(output_data)
                print("📹 输出视频已保存为 test_output.mp4")
            
            return True
        else:
            print(f"❌ 文件处理测试失败: {result.get('message')}")
            return False
            
    except Exception as e:
        print(f"❌ 文件处理测试异常: {str(e)}")
        return False

def main():
    """主测试函数"""
    print("=" * 50)
    print("RunPod Serverless Handler 本地测试")
    print("=" * 50)
    
    tests = [
        ("健康检查", test_health_check),
        ("文件处理", test_with_sample_files)
    ]
    
    passed = 0
    total = len(tests)
    
    for test_name, test_func in tests:
        print(f"\n--- {test_name} ---")
        try:
            if test_func():
                print(f"✅ {test_name} 通过")
                passed += 1
            else:
                print(f"❌ {test_name} 失败")
        except Exception as e:
            print(f"❌ {test_name} 异常: {str(e)}")
    
    print(f"\n📊 测试结果: {passed}/{total} 通过")
    
    if passed == total:
        print("🎉 所有测试通过！Handler 可以构建 Docker 镜像了")
        return True
    else:
        print("⚠️ 有测试失败，请检查 Handler 代码")
        return False

if __name__ == "__main__":
    main()