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

# Prevent NetworkManager from interfering
echo "Configuring NetworkManager..."
sudo mkdir -p /etc/NetworkManager/conf.d
sudo tee /etc/NetworkManager/conf.d/99-unmanage-wlan.conf > /dev/null <<'EOF'
[keyfile]
unmanaged-devices=interface-name:wlan0
EOF
sudo systemctl restart NetworkManager 2>/dev/null || true

# Install RGB Matrix library
if [ ! -d "/home/pi/rpi-rgb-led-matrix" ]; then
    echo "Installing RGB Matrix library..."
    cd /home/pi
    git clone https://github.com/hzeller/rpi-rgb-led-matrix.git
    cd rpi-rgb-led-matrix
    make build-python PYTHON=$(which python3)
    sudo make install-python PYTHON=$(which python3)
fi

# Install Python dependencies
echo "Installing Python packages..."
cd /home/pi/album-display/pi
pip3 install -r requirements.txt --break-system-packages

# Give Python permission to bind to port 80
echo "Configuring permissions..."
PYTHON_PATH=$(readlink -f $(which python3))
sudo setcap CAP_NET_BIND_SERVICE=+eip $PYTHON_PATH

# Create systemd service
echo "Creating systemd service..."
sudo tee /etc/systemd/system/album-display.service > /dev/null <<'EOF'
[Unit]
Description=Album Display
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/album-display/pi
ExecStart=/usr/bin/python3 /home/pi/album-display/pi/main.py
Restart=always
RestartSec=10
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
EOF

# Reload systemd
sudo systemctl daemon-reload

# Enable service (will start on boot)
sudo systemctl enable album-display.service

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "Next steps:"
echo "  1. Start the service:"
echo "     sudo systemctl start album-display"
echo ""
echo "  2. View logs:"
echo "     sudo journalctl -u album-display -f"
echo ""
echo "  3. Configure audio sources:"
echo "     Open browser to http://albumdisplay.local"
echo ""