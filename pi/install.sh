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

echo "Configuring network settings..."
# Note: We're NOT restarting NetworkManager to avoid SSH disconnection
# The unmanaged setting will take effect on next reboot
sudo mkdir -p /etc/NetworkManager/conf.d
echo '[keyfile]' | sudo tee /etc/NetworkManager/conf.d/99-unmanage-wlan.conf > /dev/null
echo 'unmanaged-devices=interface-name:wlan0' | sudo tee -a /etc/NetworkManager/conf.d/99-unmanage-wlan.conf > /dev/null

# Install RGB Matrix library
if [ ! -d "/home/pi/rpi-rgb-led-matrix" ]; then
    echo "Installing RGB Matrix library (this takes 3-5 minutes)..."
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

# Create systemd service file
echo "Creating systemd service..."
sudo bash -c 'cat > /etc/systemd/system/album-display.service' << 'EOF'
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
echo "IMPORTANT: Reboot for network settings to take effect:"
echo "  sudo reboot"
echo ""
echo "After reboot:"
echo "  1. SSH back in: ssh pi@albumdisplay.local"
echo "  2. Start service: sudo systemctl start album-display"
echo "  3. View logs: sudo journalctl -u album-display -f"
echo "  4. Configure: http://albumdisplay.local"
echo ""