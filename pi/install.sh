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
    python3-pillow \
    git \
    hostapd \
    dnsmasq \
    libopenjp2-7 \
    libtiff5 \
    libatlas-base-dev

# Stop services (will be configured later)
sudo systemctl stop hostapd
sudo systemctl stop dnsmasq
sudo systemctl disable hostapd
sudo systemctl disable dnsmasq

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

# Enable service
sudo systemctl enable album-display.service

echo ""
echo "============================================"
echo "Installation Complete!"
echo "============================================"
echo ""
echo "To start the service:"
echo "  sudo systemctl start album-display"
echo ""
echo "To view logs:"
echo "  sudo journalctl -u album-display -f"
echo ""
echo "To enable auto-start on boot (already enabled):"
echo "  sudo systemctl enable album-display"
echo ""