from rgbmatrix import RGBMatrix, RGBMatrixOptions
from PIL import Image, ImageDraw, ImageFont
import time

class DisplayManager:
    def __init__(self):
        options = RGBMatrixOptions()
        options.rows = 64
        options.cols = 64
        options.chain_length = 1
        options.parallel = 1
        options.hardware_mapping = 'adafruit-hat'
        options.gpio_slowdown = 4
        options.disable_hardware_pulsing = True
        
        self.matrix = RGBMatrix(options=options)
        self.current_image = None
    
    def show_status(self, wifi=None, audio=None, message=None):
        """
        Show configuration status
        None = not applicable, False = pending/connecting, True = connected
        """
        image = Image.new('RGB', (64, 64), color=(0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        try:
            font_large = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf", 10)
            font_small = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf", 8)
        except:
            font_large = ImageFont.load_default()
            font_small = ImageFont.load_default()
        
        y_pos = 5
        
        # Show custom message if provided
        if message:
            # Word wrap message
            words = message.split()
            lines = []
            current_line = []
            
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font_small)
                if bbox[2] - bbox[0] <= 60:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                    current_line = [word]
            
            if current_line:
                lines.append(' '.join(current_line))
            
            for line in lines[:6]:  # Max 6 lines
                draw.text((2, y_pos), line, fill=(255, 255, 255), font=font_small)
                y_pos += 10
        else:
            # Show status icons
            if wifi is not None:
                # WiFi status
                draw.text((2, y_pos), "WiFi", fill=(255, 255, 255), font=font_small)
                if wifi:
                    draw.text((45, y_pos), "✓", fill=(0, 255, 0), font=font_large)
                else:
                    # Pending circle
                    draw.ellipse((45, y_pos+2, 53, y_pos+10), outline=(255, 255, 0), width=1)
                y_pos += 15
            
            if audio is not None:
                # Audio source status
                draw.text((2, y_pos), "Audio", fill=(255, 255, 255), font=font_small)
                if audio:
                    draw.text((45, y_pos), "✓", fill=(0, 255, 0), font=font_large)
                else:
                    draw.ellipse((45, y_pos+2, 53, y_pos+10), outline=(255, 255, 0), width=1)
                y_pos += 15
        
        self.matrix.SetImage(image.convert('RGB'))
        self.current_image = image
    
    def show_album_art(self, image_data):
        """Display album art (PIL Image, should be 64x64)"""
        if image_data.size != (64, 64):
            image_data = image_data.resize((64, 64), Image.LANCZOS)
        
        self.matrix.SetImage(image_data.convert('RGB'))
        self.current_image = image_data
    
    def clear(self):
        """Clear the display"""
        self.matrix.Clear()
        self.current_image = None