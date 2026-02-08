import json
import os

CONFIG_FILE = '/home/pi/album-display-config.json'

class ConfigManager:
    def __init__(self):
        self.config = self.load_config()
    
    def load_config(self):
        if os.path.exists(CONFIG_FILE):
            with open(CONFIG_FILE, 'r') as f:
                return json.load(f)
        return {
            'wifi_ssid': None,
            'wifi_password': None,
            'spotify_access_token': None,
            'spotify_refresh_token': None,
            'spotify_token_expiry': None,
            'wiim_ip': None,
            'configured': False
        }
    
    def save_config(self):
        with open(CONFIG_FILE, 'w') as f:
            json.dump(self.config, f, indent=2)
    
    def update(self, key, value):
        self.config[key] = value
        self.save_config()
    
    def get(self, key, default=None):
        return self.config.get(key, default)
    
    def is_configured(self):
        """Check if device has been configured"""
        return (self.config.get('wifi_ssid') and 
                (self.config.get('spotify_access_token') or self.config.get('wiim_ip')))
