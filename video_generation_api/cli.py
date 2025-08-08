"""
Command-line interface for Video Generation API
"""

import argparse
import sys
from .api_client import VideoGenerationClient


def main():
    """Main CLI entry point"""
    parser = argparse.ArgumentParser(
        description="Video Generation API Client",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a simple video
  video-generation-cli create --image image.jpg --audio audio.mp3 --output output.mp4

  # Create video with subtitles
  video-generation-cli create --image image.jpg --audio audio.mp3 --subtitle subtitles.srt --output output.mp4

  # Create video with effects
  video-generation-cli create --image image.jpg --audio audio.mp3 --effects zoom_in zoom_out --output output.mp4

  # Check API health
  video-generation-cli health --api-url http://localhost:5000
        """
    )
    
    parser.add_argument(
        "--api-url",
        default="http://localhost:5000",
        help="API base URL (default: http://localhost:5000)"
    )
    
    parser.add_argument(
        "--auth-key",
        help="Authentication key for secure mode"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Commands")
    
    # Health check command
    health_parser = subparsers.add_parser("health", help="Check API health")
    
    # Create video command
    create_parser = subparsers.add_parser("create", help="Create video")
    create_parser.add_argument("--image", required=True, help="Path to input image")
    create_parser.add_argument("--audio", required=True, help="Path to input audio")
    create_parser.add_argument("--subtitle", help="Path to subtitle file (SRT)")
    create_parser.add_argument("--effects", nargs="+", help="Effects to apply")
    create_parser.add_argument("--language", default="chinese", choices=["chinese", "english"], help="Subtitle language")
    create_parser.add_argument("--font-size", type=int, help="Custom font size")
    create_parser.add_argument("--no-background", action="store_true", help="Disable subtitle background")
    create_parser.add_argument("--background-opacity", type=float, default=0.2, help="Background opacity (0-1)")
    create_parser.add_argument("--portrait", action="store_true", help="Force portrait orientation")
    create_parser.add_argument("--watermark", help="Path to watermark image")
    create_parser.add_argument("--output", default="output.mp4", help="Output file path")
    
    # Cleanup command
    cleanup_parser = subparsers.add_parser("cleanup", help="Cleanup expired files on server")
    
    args = parser.parse_args()
    
    if not args.command:
        parser.print_help()
        sys.exit(1)
    
    # Create client
    client = VideoGenerationClient(args.api_url, args.auth_key)
    
    try:
        if args.command == "health":
            result = client.health_check()
            print(f"API Status: {result['status']}")
            print(f"FFmpeg: {result['ffmpeg_version']}")
            print(f"GPU Available: {result['gpu_available']}")
            print(f"Authentication Mode: {result['authentication']['mode']}")
            
        elif args.command == "create":
            print(f"Creating video...")
            result = client.create_video(
                image_path=args.image,
                audio_path=args.audio,
                subtitle_path=args.subtitle,
                effects=args.effects,
                language=args.language,
                background_box=not args.no_background,
                background_opacity=args.background_opacity,
                font_size=args.font_size,
                is_portrait=args.portrait if args.portrait else None,
                watermark_path=args.watermark,
                output_path=args.output
            )
            
            if result.get("success"):
                print(f"✅ Video created successfully!")
                print(f"Output: {result['local_path']}")
                print(f"Size: {result['size']} bytes")
                print(f"Scenario: {result['scenario']}")
            else:
                print(f"❌ Failed to create video: {result}")
                
        elif args.command == "cleanup":
            result = client.cleanup_expired_files()
            print(f"Cleaned {result['cleaned']} expired files")
            print(f"Active files: {result['active_files']}")
            
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()