# Album Display Recovery Guide

## Quick SSH Access (Most Common)

1. Connect Pi to router via Ethernet cable
2. SSH in: `ssh pi@raspberrypi.local`
3. View logs: `sudo journalctl -u album-display -f`
4. Reset config: `rm /home/pi/album-display-config.json`
5. Restart: `sudo systemctl restart album-display`

---

## Boot Partition WiFi Recovery

**When AP mode won't start or you can't connect:**

1. Power off Pi, remove SD card
2. Insert SD card into computer
3. Open the `boot` partition
4. Create file: `wpa_supplicant.conf`
```
   country=US
   ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
   update_config=1
   
   network={
       ssid="YOUR_WIFI_NAME"
       psk="YOUR_WIFI_PASSWORD"
       key_mgmt=WPA-PSK
   }
```
5. Create empty file: `ssh` (no extension)
6. Eject SD card, put back in Pi
7. Power on Pi
8. SSH in: `ssh pi@raspberrypi.local`

---

## Force Config Mode

**To force Pi into setup mode:**

1. Power off Pi, remove SD card
2. Insert SD card into computer
3. Open the `boot` partition
4. Create empty file: `force-album-display-config`
5. Eject SD card, put back in Pi
6. Power on Pi
7. Pi will create "Album-Display-Setup" WiFi network

---

## Display Error Messages

| Display Shows | Meaning | Solution |
|--------------|---------|----------|
| "ERROR! AP failed Use boot partition" | WiFi AP won't start | Use boot partition WiFi recovery |
| "ERROR! Web server failed" | Flask server crashed | SSH in and check logs |
| "WiFi failed. Try again." | Can't connect to WiFi | Check WiFi password, try again |
| "Setup Mode" (stuck here) | Waiting for config | Connect to Album-Display-Setup WiFi |

---

## Emergency Commands
```bash
# View real-time logs
sudo journalctl -u album-display -f

# Stop service
sudo systemctl stop album-display

# Start service
sudo systemctl start album-display

# Restart service
sudo systemctl restart album-display

# Run manually (see errors directly)
cd /home/pi/album-display/pi
python3 main.py

# Delete config (force reconfiguration)
rm /home/pi/album-display-config.json

# Update code from GitHub
cd /home/pi/album-display
git pull origin main
sudo systemctl restart album-display
```

---

## Last Resort: Full Reinstall (No Reflash Needed)
```bash
# SSH into Pi
ssh pi@raspberrypi.local

# Remove old installation
cd ~
rm -rf album-display

# Clone fresh copy
git clone https://github.com/YOUR_USERNAME/album-display.git
cd album-display/pi

# Reinstall
./install.sh

# Start service
sudo systemctl start album-display
```

---

## Common Issues

### Issue: Can't SSH into Pi
**Solution:** Use Ethernet cable and try `ssh pi@<IP_ADDRESS>` (find IP in router)

### Issue: Display shows nothing
**Solution:** Check power supply (needs 5V 4A+), check matrix connections

### Issue: WiFi AP doesn't appear
**Solution:** Use boot partition recovery method above

### Issue: Spotify/WiiM not working
**Solution:** SSH in, check logs for specific errors, verify network connectivity

---

## Getting Help

If you're stuck:
1. Check the logs: `sudo journalctl -u album-display -f`
2. Look for error messages on the display
3. Try SSH access via Ethernet
4. Review this recovery guide