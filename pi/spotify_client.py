import requests
import time
from PIL import Image
from io import BytesIO

class SpotifyClient:
    def __init__(self, access_token, refresh_token, config_manager):
        self.access_token = access_token
        self.refresh_token = refresh_token
        self.config_manager = config_manager
        self.base_url = 'https://api.spotify.com/v1'
        self.client_id = None  # Set via environment or config
        self.client_secret = None  # Set via environment or config
    
    def get_current_track(self):
        """Get currently playing track and return album art"""
        headers = {'Authorization': f'Bearer {self.access_token}'}
        
        try:
            response = requests.get(
                f'{self.base_url}/me/player/currently-playing',
                headers=headers,
                timeout=10
            )
            
            if response.status_code == 401:
                # Token expired, try to refresh
                if self.refresh_access_token():
                    return self.get_current_track()
                return None
            
            if response.status_code == 204:
                # Nothing playing
                return None
            
            if response.status_code == 200:
                data = response.json()
                
                if data and data.get('is_playing'):
                    item = data.get('item')
                    if item and 'album' in item:
                        images = item['album'].get('images', [])
                        if images:
                            album_art_url = images[0]['url']
                            return self.download_album_art(album_art_url)
            
            return None
            
        except Exception as e:
            print(f"Spotify error: {e}")
            return None
    
    def download_album_art(self, url):
        """Download and resize album art to 64x64"""
        try:
            response = requests.get(url, timeout=10)
            img = Image.open(BytesIO(response.content))
            img = img.resize((64, 64), Image.LANCZOS)
            return img.convert('RGB')
        except Exception as e:
            print(f"Error downloading album art: {e}")
            return None
    
    def refresh_access_token(self):
        """Refresh Spotify access token"""
        # Note: You'll need to implement this with your Spotify credentials
        # For now, return False
        print("Token refresh not implemented")
        return False
    
    def test_connection(self):
        """Test if Spotify credentials work"""
        try:
            headers = {'Authorization': f'Bearer {self.access_token}'}
            response = requests.get(
                f'{self.base_url}/me', 
                headers=headers,
                timeout=10
            )
            return response.status_code == 200
        except:
            return False