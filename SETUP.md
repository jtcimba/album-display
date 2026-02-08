# Album Display Setup Guide

## First Time Setup

### 1. Prepare SD Card

1. Download [Raspberry Pi Imager](https://www.raspberrypi.com/software/)
2. Insert SD card into computer
3. Open Raspberry Pi Imager
4. **Choose Device:** Raspberry Pi 4
5. **Choose OS:** Raspberry Pi OS (64-bit) - recommended
6. **Choose Storage:** Your SD card
7. Click **Next** → **Edit Settings**

### 2. Configure OS Settings

**General Tab:**
- Set hostname: `albumdisplay`
- Set username: `pi`
- Set password: (choose a password)
- ✅ Configure wireless LAN
  - SSID: Your WiFi network name
  - Password: Your WiFi password
  - Wireless LAN country: US
- Set locale settings: (your timezone)

**Services Tab:**
- ✅ Enable SSH
- Use password authentication

Click **Save** → **Yes** → **Yes** to write

### 3. Install on Raspberry Pi

1. Insert SD card into Pi
2. Connect LED matrix hardware
3. Plug in power
4. Wait 90 seconds for first boot

### 4. Install Software

**Option A - SSH Method:**
```bash
# SSH into the Pi
ssh pi@albumdisplay.local

# Clone repository
git clone https://github.com/YOUR_USERNAME/album-display.git

# Run installation
cd album-display/pi
chmod +x install.sh
./install.sh

# Give Python permission to use port 80
sudo apt install -y libcap2-bin
sudo setcap CAP_NET_BIND_SERVICE=+eip /usr/bin/python3.11

# Start the service
sudo systemctl start album-display
```

**Option B - Full Auto Install (Coming Soon):**
Add install script to boot partition for one-command setup.

### 5. Configure Audio Sources

1. On your phone/laptop (connected to same WiFi)
2. Open browser: `http://albumdisplay.local`
3. Configure:
   - **Spotify:** Click "Connect Spotify Account"
   - **WiiM:** Enter IP address (optional)
4. Click "Save Configuration"
5. Album art should appear within seconds!

---

## Changing WiFi Network

**When you move the display to a different location:**

### Method 1: SD Card Edit (2 minutes)

1. Power off display
2. Remove SD card → Insert into computer
3. Open the `boot` or `bootfs` partition
4. Create/edit file: `wpa_supplicant.conf`
```
country=US
ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
update_config=1

network={
    ssid="NewNetworkName"
    psk="NewPassword"
    key_mgmt=WPA-PSK
}
```

5. Eject SD card → Put back in Pi
6. Power on
7. Display connects to new WiFi automatically

### Method 2: Mobile Hotspot (No computer needed)

1. Create mobile hotspot on your phone with SAME name/password as home WiFi
2. Power on display (connects to your hotspot)
3. Go to `http://albumdisplay.local` on your phone
4. Use SSH to update WiFi:
```bash
   ssh pi@albumdisplay.local
   # Edit wpa_supplicant with new credentials
   sudo nano /etc/wpa_supplicant/wpa_supplicant.conf
   sudo reboot
```
5. Turn off hotspot
6. Display connects to new network

---

## Reconfiguring Audio Sources

Anytime you need to change Spotify account or WiiM IP:

1. Open browser: `http://albumdisplay.local`
2. Update settings
3. Click "Save"
4. Changes apply immediately (display restarts)

---

## Troubleshooting

### Can't access http://albumdisplay.local

- Wait 2 minutes after power on
- Make sure you're on the same WiFi network
- Try the IP address instead (check your router)

### Display shows error

- Go to `http://albumdisplay.local` to see status
- Check Spotify/WiiM connections
- View logs: `ssh pi@albumdisplay.local` then `sudo journalctl -u album-display -f`

### Need to disable the service

1. Power off Pi
2. Remove SD card → Insert into computer
3. In `boot` partition, create empty file: `disable-album-display`
4. Put SD card back → Power on
5. Service won't start (for debugging)

---

## Updating Software
```bash
ssh pi@albumdisplay.local
cd ~/album-display
git pull
sudo systemctl restart album-display
```