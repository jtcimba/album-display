#!/usr/bin/env python3

import time
import sys
import signal
import os
from config_manager import ConfigManager
from wifi_manager import WiFiManager
from ap_manager import AccessPointManager
from config_server import ConfigServer

class AlbumDisplay:
    def __init__(self):
        self.config = ConfigManager()
        self.wifi = WiFiManager()
        self.ap = AccessPointManager()
        self.display = None  # Don't initialize display until after config
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
        if self.ap.is_running():
            self.ap.stop_ap()
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
    
    def check_force_config_flag(self):
        """Check if user wants to force config mode"""
        flag_file = '/boot/force-album-display-config'
        
        if os.path.exists(flag_file):
            print("FORCE CONFIG FLAG DETECTED")
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
        
        # Step 1: Configure WiFi
        if 'wifi_ssid' in data and 'wifi_password' in data:
            print("Configuring WiFi...")
            
            # Stop AP before connecting to WiFi
            self.ap.stop_ap()
            time.sleep(2)
            
            # Try to connect
            if self.wifi.connect(data['wifi_ssid'], data['wifi_password']):
                self.config.update('wifi_ssid', data['wifi_ssid'])
                self.config.update('wifi_password', data['wifi_password'])
                print(f"✓ Connected to WiFi: {data['wifi_ssid']}")
            else:
                response['errors']['wifi'] = 'Failed to connect to WiFi network'
                response['success'] = False
                # Restart AP if WiFi failed
                self.ap.start_ap()
                print("WiFi connection failed, restarted AP")
                return response
        
        # Step 2: Configure Spotify
        if data.get('spotify_access_token'):
            print("Testing Spotify...")
            
            # Import here to avoid loading display manager during config
            from spotify_client import SpotifyClient
            
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
        
        # Step 3: Configure WiiM
        if data.get('wiim_ip'):
            print("Testing WiiM...")
            
            from wiim_client import WiiMClient
            
            self.wiim = WiiMClient(data['wiim_ip'])
            
            if self.wiim.test_connection():
                self.config.update('wiim_ip', data['wiim_ip'])
                print(f"✓ WiiM connected at {data['wiim_ip']}")
            else:
                response['errors']['wiim'] = 'Cannot reach WiiM device at that IP'
                # Don't fail completely if WiiM fails but Spotify works
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
        
        return response
    
    def enter_config_mode(self, reason="No configuration found"):
        """Enter configuration mode with WiFi AP"""
        print(f"\n{'='*50}")
        print(f"ENTERING CONFIG MODE: {reason}")
        print(f"{'='*50}")
        
        try:
            print("Starting Access Point...")
            
            # Start Access Point
            self.ap.start_ap()
            time.sleep(3)
            
        except Exception as e:
            print(f"CRITICAL ERROR: Failed to start Access Point: {e}")
            
            # Log the error details
            import traceback
            traceback.print_exc()
            
            # Keep logging error
            while self.running:
                print("ERROR: AP mode failed. Use boot partition recovery.")
                print("RECOVERY: Add wpa_supplicant.conf to boot partition")
                time.sleep(60)
            return
        
        # Start config web server
        try:
            self.config_server = ConfigServer(self.handle_config)
            self.config_server.start(host='0.0.0.0', port=80)
        except Exception as e:
            print(f"ERROR: Failed to start web server: {e}")
            time.sleep(300)
            return
        
        print(f"\n{'='*50}")
        print("SETUP INSTRUCTIONS:")
        print(f"{'='*50}")
        print(f"1. Connect to WiFi: {self.ap.AP_SSID}")
        print(f"   Password: {self.ap.AP_PASSWORD}")
        print(f"2. Open browser to: http://{self.ap.AP_IP}")
        print(f"3. Complete configuration form")
        print(f"{'='*50}\n")
        
        # Wait until configured
        while not self.config.is_configured() and self.running:
            time.sleep(1)
        
        if self.config.is_configured():
            print("\n✓ Configuration received, starting normal mode...\n")
            time.sleep(2)
    
    def run_normal_mode(self):
        """Run in normal album display mode"""
        print(f"\n{'='*50}")
        print("STARTING NORMAL MODE")
        print(f"{'='*50}")
        
        # NOW initialize display manager (after config is done)
        print("Initializing display...")
        from display_manager import DisplayManager
        self.display = DisplayManager()
        
        # Initialize audio clients
        if self.config.get('wiim_ip'):
            print(f"Initializing WiiM client ({self.config.get('wiim_ip')})...")
            from wiim_client import WiiMClient
            self.wiim = WiiMClient(self.config.get('wiim_ip'))
        
        if self.config.get('spotify_access_token'):
            print("Initializing Spotify client...")
            from spotify_client import SpotifyClient
            self.spotify = SpotifyClient(
                self.config.get('spotify_access_token'),
                self.config.get('spotify_refresh_token'),
                self.config
            )
        
        self.display.show_status(wifi=True, audio=True, 
                               message="Ready!")
        time.sleep(2)
        
        print("✓ Album Display running")
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
                    # Keep showing last album art when nothing is playing
                
                time.sleep(5)  # Poll every 5 seconds
                
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
        
        # Check for force config flag
        if self.check_force_config_flag():
            print("Force config mode requested via boot partition flag")
            self.enter_config_mode(reason="Forced by user")
            if not self.running:
                return
        
        # Check if WiFi is configured
        if self.config.get('wifi_ssid'):
            saved_ssid = self.config.get('wifi_ssid')
            print(f"Found saved WiFi: {saved_ssid}")
            
            # Check if already connected
            if self.wifi.is_connected():
                current_ssid = self.wifi.get_current_ssid()
                if current_ssid == saved_ssid:
                    print(f"✓ Already connected to {current_ssid}")
                else:
                    print(f"Connected to {current_ssid}, switching to {saved_ssid}...")
                    if not self.wifi.connect(saved_ssid, self.config.get('wifi_password')):
                        print(f"✗ Failed to connect to {saved_ssid}")
                        self.enter_config_mode(reason=f"Cannot connect to {saved_ssid}")
                        if not self.running:
                            return
            else:
                # Try to connect
                print(f"Connecting to {saved_ssid}...")
                
                if not self.wifi.connect(saved_ssid, self.config.get('wifi_password')):
                    print(f"✗ Failed to connect to {saved_ssid}")
                    print("Entering configuration mode...")
                    self.enter_config_mode(reason=f"Cannot connect to {saved_ssid}")
                    if not self.running:
                        return
                else:
                    print(f"✓ Connected to {saved_ssid}")
        else:
            print("No WiFi configured")
            self.enter_config_mode()
            if not self.running:
                return
        
        # Run normal mode (display manager initialized here)
        self.run_normal_mode()

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