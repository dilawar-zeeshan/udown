#!/usr/bin/env bash
# exit on error
set -o errexit

# Install ffmpeg locally in the build environment
mkdir -p bin
curl -L https://github.com/yt-dlp/FFmpeg-Builds/releases/download/latest/ffmpeg-master-latest-linux64-gpl.tar.xz | tar -xJ --strip-components=1 -C bin bin/ffmpeg

# Add bin to path for this session
export PATH=$PATH:$(pwd)/bin

# Install python dependencies
pip install -r requirements.txt
