#!/usr/bin/env python3

import time
import sys
import signal
import os
from config_manager import ConfigManager
from display_manager import DisplayManager
from config_server import ConfigServer
from spotify_client import SpotifyClient
from wiim_client import WiiMClient

class AlbumDisplay:
    def __init__(self):
        self.config = ConfigManager()
        self.display = None
        self.config_server = None
        self.spotify = None
        self.wiim = None
        self.running = True
        
        # Register signal handlers
        signal.signal(signal.SIGINT, self.signal_handler)
        signal.signal(signal.SIGTERM, self.signal_handler)
    
    def signal_handler(self, signum, frame):
        """Handle shutdown signals"""
        print("\nShutting down gracefully...")
        self.running = False
        if self.display:
            self.display.clear()
        sys.exit(0)
    
    def check_disable_flag(self):
        """Check if user wants to disable the service"""
        flag_file = '/boot/disable-album-display'
        
        if os.path.exists(flag_file):
            print("DISABLE FLAG DETECTED - Service will not start")
            try:
                os.remove(flag_file)
            except:
                pass
            return True
        return False
    
    def handle_config(self, data):
        """Handle configuration data from web interface"""
        response = {'success': True, 'errors': {}}
        
        print(f"Processing configuration...")
        
        # Configure Spotify
        if data.get('spotify_access_token'):
            print("Testing Spotify...")
            
            self.spotify = SpotifyClient(
                data['spotify_access_token'],
                data.get('spotify_refresh_token'),
                self.config
            )
            
            if self.spotify.test_connection():
                self.config.update('spotify_access_token', data['spotify_access_token'])
                self.config.update('spotify_refresh_token', data.get('spotify_refresh_token'))
                self.config.update('spotify_token_expiry', data.get('spotify_token_expiry'))
                print("✓ Spotify connected")
            else:
                response['errors']['spotify'] = 'Failed to connect to Spotify'
                response['success'] = False
        
        # Configure WiiM
        if data.get('wiim_ip'):
            print("Testing WiiM...")
            
            self.wiim = WiiMClient(data['wiim_ip'])
            
            if self.wiim.test_connection():
                self.config.update('wiim_ip', data['wiim_ip'])
                print(f"✓ WiiM connected at {data['wiim_ip']}")
            else:
                response['errors']['wiim'] = 'Cannot reach WiiM device at that IP'
                if not data.get('spotify_access_token'):
                    response['success'] = False
        
        # Verify at least one audio source is configured
        if not (self.config.get('spotify_access_token') or self.config.get('wiim_ip')):
            response['errors']['audio'] = 'At least one audio source required'
            response['success'] = False
        
        # Update configuration status
        if response['success']:
            self.config.update('configured', True)
            print("✓ Configuration complete")
            # Restart to apply changes
            time.sleep(2)
            os.system('sudo systemctl restart album-display')
        
        return response
    
    def run_config_server(self):
        """Run the configuration web server"""
        print(f"\n{'='*50}")
        print("CONFIGURATION SERVER MODE")
        print(f"{'='*50}")
        print("\nThe display is ready to be configured.")
        print("Open a browser and go to: http://albumdisplay.local")
        print(f"{'='*50}\n")
        
        # Start config web server
        self.config_server = ConfigServer(self.handle_config)
        self.config_server.start(host='0.0.0.0', port=80)
        
        # Keep server running
        while self.running:
            time.sleep(1)
    
    def run_display_mode(self):
        """Run in album display mode"""
        print(f"\n{'='*50}")
        print("ALBUM DISPLAY MODE")
        print(f"{'='*50}")
        
        # Initialize display
        print("Initializing display...")
        self.display = DisplayManager()
        
        # Initialize audio clients
        if self.config.get('wiim_ip'):
            print(f"Initializing WiiM client ({self.config.get('wiim_ip')})...")
            self.wiim = WiiMClient(self.config.get('wiim_ip'))
        
        if self.config.get('spotify_access_token'):
            print("Initializing Spotify client...")
            self.spotify = SpotifyClient(
                self.config.get('spotify_access_token'),
                self.config.get('spotify_refresh_token'),
                self.config
            )
        
        # Start config server in background (always available for reconfiguration)
        print("Starting config server (available at http://albumdisplay.local)...")
        self.config_server = ConfigServer(self.handle_config)
        self.config_server.start(host='0.0.0.0', port=80)
        
        self.display.show_status(wifi=True, audio=True, message="Ready!")
        time.sleep(2)
        
        print("✓ Album Display running")
        print("  Config available at: http://albumdisplay.local")
        print("  Priority: WiiM > Spotify")
        print("  Polling every 5 seconds")
        print(f"{'='*50}\n")
        
        # Main display loop
        last_album_art = None
        no_music_count = 0
        
        while self.running:
            try:
                album_art = None
                
                # Priority: WiiM > Spotify
                if self.wiim:
                    album_art = self.wiim.get_current_track()
                
                if not album_art and self.spotify:
                    album_art = self.spotify.get_current_track()
                
                if album_art:
                    self.display.show_album_art(album_art)
                    if album_art != last_album_art:
                        print("♫ Now playing (album art updated)")
                        last_album_art = album_art
                        no_music_count = 0
                else:
                    no_music_count += 1
                    if no_music_count == 1:
                        print("⏸ No music playing")
                
                time.sleep(5)
                
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"Error in main loop: {e}")
                time.sleep(5)
    
    def run(self):
        """Main application entry point"""
        print(f"\n{'='*50}")
        print("ALBUM DISPLAY STARTING")
        print(f"{'='*50}\n")
        
        time.sleep(2)
        
        # Check for disable flag
        if self.check_disable_flag():
            print("Service disabled by user flag. Exiting.")
            return
        
        # Check if configured
        if self.config.is_configured():
            # Run in display mode (with config server available)
            self.run_display_mode()
        else:
            # Run config server only
            self.run_config_server()

if __name__ == '__main__':
    try:
        app = AlbumDisplay()
        app.run()
    except Exception as e:
        print(f"Fatal error: {e}")
        import traceback
        traceback.print_exc()
    finally:
        print("\nAlbum Display stopped")