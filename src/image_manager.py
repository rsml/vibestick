import os
from pathlib import Path
from typing import Optional, Dict, Tuple
from PIL import Image, ImageDraw, ImageFont
from StreamDeck.ImageHelpers import PILHelper


class ImageManager:
    """Manages images for Stream Deck buttons."""
    
    def __init__(self, deck, image_dir: str = "."):
        self.deck = deck
        self.image_dir = Path(image_dir)
        self.button_size = deck.key_image_format()['size']
        self.image_cache: Dict[str, Image.Image] = {}
        
        # Colors for different states
        self.colors = {
            "normal": (0, 0, 0),
            "selected": (0, 122, 255),  # Blue
            "pressed": (255, 149, 0),    # Orange
            "background": (30, 30, 30),  # Dark gray
            "text": (255, 255, 255)      # White
        }
        
    def get_image(self, image_path: Optional[str], label: Optional[str], 
                  state: str = "normal", position: int = -1) -> bytes:
        """Get formatted image for a button."""
        try:
            # Create base image with transparency
            image = Image.new("RGBA", self.button_size, (0, 0, 0, 0))
            draw = ImageDraw.Draw(image)
            
            # Determine which column this button is in
            column = position % 5  # 5 columns total
            
            # Check if this is a center button (columns 1, 2, 3)
            is_center_button = column in [1, 2, 3]
            
            if is_center_button and label:
                # Show centered text for all center buttons
                self._add_centered_text(draw, label)
            # Load icon if path provided (for side columns only)
            elif image_path and not is_center_button:
                try:
                    icon = self._load_and_resize_image(image_path)
                    if icon:
                        # Special handling for iPhone icons - make them larger
                        if "iphone" in image_path.lower():
                            icon.thumbnail((50, 50), Image.Resampling.LANCZOS)
                        else:
                            icon.thumbnail((40, 40), Image.Resampling.LANCZOS)
                        
                        # Center the icon
                        icon_pos = ((self.button_size[0] - icon.width) // 2,
                                   (self.button_size[1] - icon.height) // 2)
                        
                        # Paste icon with transparency
                        if icon.mode == 'RGBA':
                            image.paste(icon, icon_pos, icon)
                        else:
                            image.paste(icon, icon_pos)
                except Exception as e:
                    print(f"Error loading image {image_path}: {e}")
                    # Fallback to label only
            
            # Add label if provided and no image loaded
            elif label:
                self._add_label(draw, label)
            
            # Add border for selected state
            if state == "selected":
                self._add_border(draw, self.colors["selected"], width=3)
            elif state == "pressed":
                self._add_border(draw, self.colors["pressed"], width=3)
            
            # Convert RGBA to RGB for Stream Deck
            rgb_image = Image.new("RGB", self.button_size, (0, 0, 0))
            rgb_image.paste(image, (0, 0), image)
            
            # Convert to Stream Deck format
            return PILHelper.to_native_format(self.deck, rgb_image)
        except Exception as e:
            print(f"Error creating image: {e}")
            # Return a blank image as fallback
            return self.get_blank_image()
    
    def get_blank_image(self) -> bytes:
        """Get a blank button image."""
        image = Image.new("RGB", self.button_size, self.colors["background"])
        return PILHelper.to_native_format(self.deck, image)
    
    def _file_exists(self, path: str) -> bool:
        """Check if image file exists."""
        full_path = self.image_dir / path if not os.path.isabs(path) else Path(path)
        return full_path.exists()
    
    def _load_and_resize_image(self, path: str) -> Optional[Image.Image]:
        """Load and resize image to fit button."""
        try:
            # Check cache first
            if path in self.image_cache:
                return self.image_cache[path]
            
            # Load image
            full_path = self.image_dir / path if not os.path.isabs(path) else Path(path)
            img = Image.open(full_path)
            
            # Convert to RGBA if needed
            if img.mode != 'RGBA':
                img = img.convert('RGBA')
            
            # Resize to fit button (leaving space for label)
            max_size = (self.button_size[0] - 10, self.button_size[1] - 30)
            img.thumbnail(max_size, Image.Resampling.LANCZOS)
            
            # Cache the image
            self.image_cache[path] = img
            
            return img
            
        except Exception as e:
            print(f"Error loading image {path}: {e}")
            return None
    
    def _add_label(self, draw: ImageDraw.Draw, label: str):
        """Add text label to button."""
        try:
            # Try to use a better font
            font_size = 12
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # Calculate text position (bottom center)
            bbox = draw.textbbox((0, 0), label, font=font)
            text_width = bbox[2] - bbox[0]
            text_height = bbox[3] - bbox[1]
            
            x = (self.button_size[0] - text_width) // 2
            y = self.button_size[1] - text_height - 5
            
            # Draw text
            draw.text((x, y), label, fill=self.colors["text"], font=font)
            
        except Exception as e:
            print(f"Error adding label: {e}")
    
    def _add_border(self, draw: ImageDraw.Draw, color: Tuple[int, int, int], width: int = 2):
        """Add border to button image."""
        # Draw border with alpha channel
        for i in range(width):
            draw.rectangle(
                [i, i, self.button_size[0] - i - 1, self.button_size[1] - i - 1],
                outline=(*color, 255),
                width=1
            )
    
    def _add_centered_text(self, draw: ImageDraw.Draw, text: str):
        """Add centered text to button with word wrapping."""
        try:
            # Use a smaller font for better fit
            font_size = 14
            try:
                font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", font_size)
            except:
                font = ImageFont.load_default()
            
            # Split text into words for wrapping
            words = text.split()
            lines = []
            current_line = []
            max_width = self.button_size[0] - 10  # Leave 5px padding on each side
            
            # Build lines that fit within max_width
            for word in words:
                test_line = ' '.join(current_line + [word])
                bbox = draw.textbbox((0, 0), test_line, font=font)
                line_width = bbox[2] - bbox[0]
                
                if line_width <= max_width:
                    current_line.append(word)
                else:
                    if current_line:
                        lines.append(' '.join(current_line))
                        current_line = [word]
                    else:
                        # Word is too long, add it anyway
                        lines.append(word)
            
            if current_line:
                lines.append(' '.join(current_line))
            
            # Calculate total height of all lines
            line_height = font_size + 4  # Add some spacing between lines
            total_height = len(lines) * line_height
            
            # Start position for centering vertically
            y = (self.button_size[1] - total_height) // 2
            
            # Draw each line centered horizontally
            for line in lines:
                bbox = draw.textbbox((0, 0), line, font=font)
                text_width = bbox[2] - bbox[0]
                x = (self.button_size[0] - text_width) // 2
                draw.text((x, y), line, fill=(255, 255, 255, 255), font=font)
                y += line_height
            
        except Exception as e:
            print(f"Error adding centered text: {e}")
    
    def create_placeholder_images(self):
        """Create placeholder images for testing."""
        placeholder_images = {
            "images/common/terminal.png": self._create_icon_image("T", (0, 255, 0)),
            "images/common/simulator.png": self._create_icon_image("S", (0, 122, 255)),
            "images/common/fork.png": self._create_icon_image("F", (255, 149, 0)),
        }
        
        for path, image in placeholder_images.items():
            full_path = self.image_dir / path
            full_path.parent.mkdir(parents=True, exist_ok=True)
            image.save(full_path, "PNG")
    
    def _create_icon_image(self, letter: str, color: Tuple[int, int, int]) -> Image.Image:
        """Create a simple icon image with a letter."""
        size = (64, 64)
        image = Image.new("RGBA", size, (0, 0, 0, 0))
        draw = ImageDraw.Draw(image)
        
        # Draw circle
        draw.ellipse([5, 5, size[0]-5, size[1]-5], fill=color, outline=(255, 255, 255))
        
        # Draw letter
        try:
            font = ImageFont.truetype("/System/Library/Fonts/Helvetica.ttc", 36)
        except:
            font = ImageFont.load_default()
            
        bbox = draw.textbbox((0, 0), letter, font=font)
        text_width = bbox[2] - bbox[0]
        text_height = bbox[3] - bbox[1]
        
        x = (size[0] - text_width) // 2
        y = (size[1] - text_height) // 2
        
        draw.text((x, y), letter, fill=(255, 255, 255), font=font)
        
        return image