import subprocess
import time
import os

class WiFiManager:
    def __init__(self):
        self.interface = 'wlan0'
    
    def connect(self, ssid, password, timeout=30):
        """Connect to WiFi network and return success status"""
        try:
            print(f"Connecting to WiFi: {ssid}")
            
            # Create wpa_supplicant configuration
            config = f'''country=US
              ctrl_interface=DIR=/var/run/wpa_supplicant GROUP=netdev
              update_config=1

              network={{
                  ssid="{ssid}"
                  psk="{password}"
                  key_mgmt=WPA-PSK
              }}
            '''
            # Write config
            with open('/tmp/wpa_supplicant.conf', 'w') as f:
                f.write(config)
            
            # Copy to system location
            subprocess.run(['sudo', 'cp', '/tmp/wpa_supplicant.conf', 
                          '/etc/wpa_supplicant/wpa_supplicant.conf'], check=True)
            
            # Bring interface down and up
            subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'down'], 
                        stderr=subprocess.DEVNULL)
            subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'up'], 
                        check=True)
            
            # Restart wpa_supplicant
            subprocess.run(['sudo', 'systemctl', 'restart', 'wpa_supplicant'], 
                        check=True)
            
            # Request DHCP
            subprocess.run(['sudo', 'dhclient', self.interface], 
                        stderr=subprocess.DEVNULL)
            
            # Wait for connection
            print("Waiting for connection...")
            start_time = time.time()
            while time.time() - start_time < timeout:
                if self.is_connected():
                    print(f"Successfully connected to {ssid}")
                    return True
                time.sleep(2)
            
            print(f"Failed to connect to {ssid} (timeout)")
            return False
            
        except Exception as e:
            print(f"WiFi connection error: {e}")
            return False
    
    def is_connected(self):
        """Check if connected to WiFi"""
        try:
            # Check if we have an IP address
            result = subprocess.run(
                ['ip', 'addr', 'show', self.interface], 
                capture_output=True, 
                text=True
            )
            
            # Look for inet address (IPv4)
            if 'inet ' in result.stdout:
                # Also check if we can get SSID
                ssid_result = subprocess.run(
                    ['iwgetid', '-r'], 
                    capture_output=True, 
                    text=True
                )
                return bool(ssid_result.stdout.strip())
            
            return False
        except:
            return False
    
    def get_current_ssid(self):
        """Get currently connected SSID"""
        try:
            result = subprocess.run(['iwgetid', '-r'], 
                                  capture_output=True, text=True)
            return result.stdout.strip()
        except:
            return None
    
    def disconnect(self):
        """Disconnect from WiFi"""
        try:
            subprocess.run(['sudo', 'ip', 'link', 'set', self.interface, 'down'],
                        stderr=subprocess.DEVNULL)
        except:
            pass