import subprocess
import time
import os

class AccessPointManager:
    AP_SSID = "Album-Display-Setup"
    AP_PASSWORD = "albumdisplay"
    AP_IP = "192.168.4.1"
    AP_INTERFACE = "wlan0"
    
    def __init__(self):
        self.running = False
    
    def start_ap(self):
        """Start WiFi Access Point mode"""
        if self.running:
            print("Access Point already running")
            return
        
        print("Starting Access Point...")
        
        try:
            # Stop any existing WiFi connections
            subprocess.run(['sudo', 'systemctl', 'stop', 'wpa_supplicant'], 
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'killall', 'wpa_supplicant'], 
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'killall', 'dhclient'], 
                        stderr=subprocess.DEVNULL)
            
            # Bring interface down
            subprocess.run(['sudo', 'ip', 'link', 'set', self.AP_INTERFACE, 'down'],
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', self.AP_INTERFACE],
                        stderr=subprocess.DEVNULL)
            
            # Configure static IP
            subprocess.run(['sudo', 'ip', 'addr', 'add', f'{self.AP_IP}/24', 
                          'dev', self.AP_INTERFACE], check=True)
            subprocess.run(['sudo', 'ip', 'link', 'set', self.AP_INTERFACE, 'up'], 
                        check=True)
            
            # Create hostapd config
            hostapd_conf = f"""interface={self.AP_INTERFACE}
driver=nl80211
ssid={self.AP_SSID}
hw_mode=g
channel=7
wmm_enabled=0
macaddr_acl=0
auth_algs=1
ignore_broadcast_ssid=0
wpa=2
wpa_passphrase={self.AP_PASSWORD}
wpa_key_mgmt=WPA-PSK
wpa_pairwise=TKIP
rsn_pairwise=CCMP
"""
            with open('/tmp/hostapd.conf', 'w') as f:
                f.write(hostapd_conf)
            
            subprocess.run(['sudo', 'cp', '/tmp/hostapd.conf', '/etc/hostapd/hostapd.conf'],
                        check=True)
            
            # Create dnsmasq config (DHCP + DNS)
            dnsmasq_conf = f"""interface={self.AP_INTERFACE}
dhcp-range=192.168.4.2,192.168.4.20,255.255.255.0,24h
dhcp-option=3,{self.AP_IP}
dhcp-option=6,{self.AP_IP}
address=/#/{self.AP_IP}
no-resolv
log-queries
log-dhcp
"""
            with open('/tmp/dnsmasq.conf', 'w') as f:
                f.write(dnsmasq_conf)
            
            subprocess.run(['sudo', 'cp', '/tmp/dnsmasq.conf', '/etc/dnsmasq.conf'],
                        check=True)
            
            # Start services
            subprocess.run(['sudo', 'systemctl', 'restart', 'dnsmasq'], check=True)
            subprocess.run(['sudo', 'systemctl', 'restart', 'hostapd'], check=True)
            
            self.running = True
            print(f"✓ Access Point started")
            print(f"  SSID: {self.AP_SSID}")
            print(f"  Password: {self.AP_PASSWORD}")
            print(f"  Config URL: http://{self.AP_IP}")
            
        except subprocess.CalledProcessError as e:
            print(f"Error starting Access Point: {e}")
            self.running = False
    
    def stop_ap(self):
        """Stop Access Point and return to normal mode"""
        if not self.running:
            return
        
        print("Stopping Access Point...")
        
        try:
            # Stop services
            subprocess.run(['sudo', 'systemctl', 'stop', 'hostapd'], 
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'systemctl', 'stop', 'dnsmasq'], 
                        stderr=subprocess.DEVNULL)
            
            # Flush IP configuration
            subprocess.run(['sudo', 'ip', 'addr', 'flush', 'dev', self.AP_INTERFACE],
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'ip', 'link', 'set', self.AP_INTERFACE, 'down'],
                        stderr=subprocess.DEVNULL)
            
            self.running = False
            print("✓ Access Point stopped")
            
        except Exception as e:
            print(f"Error stopping Access Point: {e}")
    
    def is_running(self):
        """Check if AP is currently running"""
        return self.running