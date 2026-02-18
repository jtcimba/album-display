#!/bin/bash

set -e

echo "============================================"
echo "Album Display Installation"
echo "============================================"
echo ""

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "Please run as pi user"
    exit 1
fi

# Update system
echo "Updating system packages..."
sudo apt update

# Install system dependencies
echo "Installing system dependencies..."
sudo apt install -y \
    python3-pip \
    python3-dev \
    python3-pil \
    git \
    libopenjp2-7 \
    libtiff-dev \
    libatlas3-base \
    cython3 \
    libcap2-bin

# Install RGB Matrix library
if [ ! -d "/home/pi/rpi-rgb-led-matrix" ]; then
    echo "Installing RGB Matrix library (this takes 3-5 minutes)..."
    cd /home/pi
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
    cd rpi-rgb-led-matrix
    make build-python PYTHON=$(which python3)
    sudo make install-python PYTHON=$(which python3)
else
    echo "RGB Matrix library already installed, skipping..."
fi

# Install Python dependencies
echo "Installing Python packages..."
cd /home/pi/album-display/pi
pip3 install -r requirements.txt --break-system-packages

# Give Python permission to bind to port 80
echo "Configuring permissions..."
PYTHON_PATH=$(readlink -f $(which python3))
sudo setcap CAP_NET_BIND_SERVICE=+eip $PYTHON_PATH

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Test manually:"
echo "     cd ~/album-display/pi"
echo "     python3 main.py"
echo ""
echo "  2. Configure display:"
echo "     Open browser to http://albumdisplay.local"
echo ""
echo "  3. After testing, enable auto-start:"
echo "     cd ~/album-display/pi"
echo "     ./enable-autostart.sh"
echo ""