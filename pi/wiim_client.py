import requests
from PIL import Image
from io import BytesIO
import time

class WiiMClient:
    def __init__(self, ip_address):
        self.ip = ip_address
        self.base_url = f'http://{ip_address}/httpapi.asp'
        self.last_track_id = None
    
    def get_current_track(self):
        """Get currently playing track from WiiM"""
        try:
            # Get player status
            status_response = requests.get(
                self.base_url,
                params={'command': 'getPlayerStatus'},
                timeout=5
            )
            
            if status_response.status_code != 200:
                return None
            
            status = status_response.json()
            
            # Check if playing
            if status.get('status') != 'play':
                return None
            
            # Get metadata
            meta_response = requests.get(
                self.base_url,
                params={'command': 'getMetaInfo'},
                timeout=5
            )
            
            if meta_response.status_code != 200:
                return None
            
            meta = meta_response.json()
            
            # Get album art URL
            album_art_url = meta.get('albumArt') or meta.get('cover')
            
            if album_art_url:
                # Check if this is a new track
                track_id = meta.get('title', '') + meta.get('artist', '')
                if track_id != self.last_track_id:
                    self.last_track_id = track_id
                    return self.download_album_art(album_art_url)
            
            return None
            
        except Exception as e:
            print(f"WiiM error: {e}")
            return None
    
    def download_album_art(self, url):
        """Download and resize album art to 64x64"""
        try:
            # Handle relative URLs
            if url.startswith('/'):
                url = f'http://{self.ip}{url}'
            
            response = requests.get(url, timeout=10)
            img = Image.open(BytesIO(response.content))
            img = img.resize((64, 64), Image.LANCZOS)
            return img.convert('RGB')
        except Exception as e:
            print(f"Error downloading WiiM album art: {e}")
            return None
    
    def test_connection(self):
        """Test if WiiM is reachable"""
        try:
            response = requests.get(
                self.base_url,
                params={'command': 'getPlayerStatus'},
                timeout=5
            )
            return response.status_code == 200
        except:
            return False