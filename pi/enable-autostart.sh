#!/bin/bash

set -e

echo "============================================"
echo "Enable Album Display Auto-Start on Boot"
echo "============================================"
echo ""

# Check if running as pi user
if [ "$USER" != "pi" ]; then
    echo "Please run as pi user"
    exit 1
fi

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
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable service
echo "Enabling service to start on boot..."
sudo systemctl enable album-display.service

# Start service now
echo "Starting service..."
sudo systemctl start album-display.service

# Wait a moment for service to start
sleep 2

# Show status
echo ""
echo "============================================"
echo "Service Status:"
echo "============================================"
sudo systemctl status album-display.service --no-pager

echo ""
echo "============================================"
echo "Auto-Start Enabled!"
echo "============================================"
echo ""
echo "The display will now start automatically on boot."
echo ""
echo "Useful commands:"
echo "  View logs:       sudo journalctl -u album-display -f"
echo "  Stop service:    sudo systemctl stop album-display"
echo "  Restart service: sudo systemctl restart album-display"
echo "  Disable auto-start: sudo systemctl disable album-display"
echo ""
echo "Test auto-start with: sudo reboot"
echo ""