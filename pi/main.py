#!/usr/bin/env python3

import time
import sys
import signal
import os
from config_manager import ConfigManager
from display_manager import DisplayManager
from config_server import ConfigServer
from wiim_client import WiiMClient

class AlbumDisplay:
    def __init__(self):
        self.config = ConfigManager()
        self.display = None
        self.config_server = None
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
        
        # Handle test mode
        if data.get('test_mode'):
            self.config.update('test_mode', True)
            print("✓ Test mode enabled")
        else:
            self.config.update('test_mode', False)
            print("✓ Test mode disabled")
        
        # Configure WiiM
        if data.get('wiim_ip'):
            print("Testing WiiM...")
            
            self.wiim = WiiMClient(data['wiim_ip'])
            
            if self.wiim.test_connection():
                self.config.update('wiim_ip', data['wiim_ip'])
                print(f"✓ WiiM connected at {data['wiim_ip']}")
            else:
                response['errors']['wiim'] = 'Cannot reach WiiM device at that IP'
                response['success'] = False
        
        # Allow saving with just test mode (no WiiM required for testing)
        # if not data.get('wiim_ip') and not data.get('test_mode'):
            # response['errors']['config'] = 'Please enter WiiM IP or enable Test Mode'
            # response['success'] = False
        
        # Update configuration status
        if response['success']:
            self.config.update('configured', True)
            print("✓ Configuration complete")
            # Restart to apply changes
            time.sleep(2)
            os.system('sudo systemctl restart album-display')
        
        return response
    
    def create_test_images(self):
        """Create test images for demo mode"""
        from PIL import Image, ImageDraw, ImageFont
        
        images = []
        colors = [
            (255, 0, 0),    # Red
            (0, 255, 0),    # Green
            (0, 0, 255),    # Blue
            (255, 255, 0),  # Yellow
            (255, 0, 255),  # Magenta
            (0, 255, 255),  # Cyan
        ]
        
        for i, color in enumerate(colors):
            img = Image.new('RGB', (64, 64), color=color)
            draw = ImageDraw.Draw(img)
            
            # Add text
            try:
                font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 20)
            except:
                font = ImageFont.load_default()
            
            text = f"#{i+1}"
            # Calculate text position to center it
            bbox = draw.textbbox((0, 0), text, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            x = (64 - text_width) // 2
            y = (64 - text_height) // 2
            
            draw.text((x, y), text, fill=(255, 255, 255), font=font)
            images.append(img)
        
        return images
    
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
        
        # Initialize WiiM client if configured
        if self.config.get('wiim_ip'):
            print(f"Initializing WiiM client ({self.config.get('wiim_ip')})...")
            self.wiim = WiiMClient(self.config.get('wiim_ip'))
        
        # Start config server in background (always available for reconfiguration)
        print("Starting config server (available at http://albumdisplay.local)...")
        self.config_server = ConfigServer(self.handle_config)
        self.config_server.start(host='0.0.0.0', port=80)
        
        # Check if in test mode
        if self.config.get('test_mode'):
            print("✓ Test Mode enabled - cycling through test images")
            self.display.show_status(wifi=True, audio=True, message="Test Mode\nActive")
        else:
            self.display.show_status(wifi=True, audio=True, message="Ready!")
        
        time.sleep(2)
        
        print("✓ Album Display running")
        print("  Config available at: http://albumdisplay.local")
        if self.config.get('test_mode'):
            print("  Mode: TEST - Cycling colored images")
        else:
            print("  Mode: NORMAL - Showing WiiM album art")
        print("  Polling every 5 seconds")
        print(f"{'='*50}\n")
        
        # Main display loop
        last_album_art = None
        no_music_count = 0
        test_image_index = 0
        
        # Create test images
        test_images = self.create_test_images()
        
        while self.running:
           try:
               album_art = None
               
               # Check if in test mode
               if self.config.get('test_mode'):
                   # Cycle through test images every 5 seconds
                   album_art = test_images[test_image_index % len(test_images)]
                   print(f"🎨 Test image #{test_image_index % len(test_images) + 1}")
                   test_image_index += 1
               else:
                   # Normal mode: Get album art from WiiM
                   if self.wiim:
                       album_art = self.wiim.get_current_track()
               
               if album_art:
                   # Crossfade to new album art
                   if album_art != last_album_art:
                       if last_album_art:
                           self.display.crossfade(last_album_art, album_art)
                       else:
                           self.display.show_album_art(album_art)
                       
                       if not self.config.get('test_mode'):
                           print("♫ Album art updated")
                       last_album_art = album_art
                       no_music_count = 0
               else:
                   # No music playing
                   no_music_count += 1
                   if no_music_count == 1 and not self.config.get('test_mode'):
                       print("⏸ No music playing - showing waiting message")
                       self.display.show_waiting_message()
                       last_album_art = None
               
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
