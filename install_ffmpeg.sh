# install_ffmpeg.sh
#!/bin/bash

# Create directory for ffmpeg
mkdir -p ~/bin

# Download static build of ffmpeg
wget https://johnvansickle.com/ffmpeg/releases/ffmpeg-release-amd64-static.tar.xz

# Extract the tarball
tar -xvf ffmpeg-release-amd64-static.tar.xz

# Move ffmpeg and ffprobe to ~/bin
mv ffmpeg-*-amd64-static/ffmpeg ~/bin/
mv ffmpeg-*-amd64-static/ffprobe ~/bin/

# Clean up
rm -rf ffmpeg-release-amd64-static.tar.xz ffmpeg-*-amd64-static
