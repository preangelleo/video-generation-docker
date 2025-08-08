import os
from setuptools import setup, find_packages

# Read the README file
with open("README.md", "r", encoding="utf-8") as fh:
    long_description = fh.read()

# Read requirements
with open("requirements.txt", "r", encoding="utf-8") as fh:
    requirements = [line.strip() for line in fh if line.strip() and not line.startswith("#")]

setup(
    name="video-generation-api",
    version="1.0.0",
    author="Leo Wang",
    author_email="preangelleo@gmail.com",
    description="A powerful Docker-based API for intelligent video generation with professional effects and subtitles",
    long_description=long_description,
    long_description_content_type="text/markdown",
    url="https://github.com/preangelleo/video-generation-docker",
    packages=find_packages(),
    classifiers=[
        "Development Status :: 5 - Production/Stable",
        "Intended Audience :: Developers",
        "Topic :: Multimedia :: Video",
        "Topic :: Multimedia :: Video :: Conversion",
        "Topic :: Software Development :: Libraries :: Python Modules",
        "License :: OSI Approved :: MIT License",
        "Programming Language :: Python :: 3",
        "Programming Language :: Python :: 3.8",
        "Programming Language :: Python :: 3.9",
        "Programming Language :: Python :: 3.10",
        "Programming Language :: Python :: 3.11",
        "Programming Language :: Python :: 3.12",
        "Operating System :: OS Independent",
    ],
    python_requires=">=3.8",
    install_requires=requirements,
    extras_require={
        "dev": [
            "pytest>=7.0.0",
            "pytest-cov>=4.0.0",
            "black>=22.0.0",
            "flake8>=6.0.0",
        ],
    },
    entry_points={
        "console_scripts": [
            "video-generation-api=video_generation_api.app:main",
            "video-generation-cli=video_generation_api.cli:main",
        ],
    },
    include_package_data=True,
    package_data={
        "video_generation_api": ["*.md", "Dockerfile"],
    },
    keywords="video generation api docker flask moviepy ffmpeg subtitles effects animation",
    project_urls={
        "Bug Reports": "https://github.com/preangelleo/video-generation-docker/issues",
        "Source": "https://github.com/preangelleo/video-generation-docker",
        "Documentation": "https://github.com/preangelleo/video-generation-docker#readme",
    },
)