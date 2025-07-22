#!/usr/bin/env python3 -u
"""
Stream Deck Dual Control - Control two macOS computers with one Stream Deck
"""

import sys
import os
from pathlib import Path

# Force unbuffered output
sys.stdout = os.fdopen(sys.stdout.fileno(), 'w', 1)
sys.stderr = os.fdopen(sys.stderr.fileno(), 'w', 1)

# Add src to path
sys.path.insert(0, str(Path(__file__).parent))

from src.streamdeck_controller import StreamDeckController
from src.image_manager import ImageManager
from src.notification_helper import notify_crash, notify_startup_error


def create_placeholder_images():
    """Create placeholder images for testing."""
    print("Creating placeholder images...")
    
    # Create a temporary deck-like object for image manager
    class FakeDeck:
        def key_image_format(self):
            return {'size': (72, 72)}
    
    fake_deck = FakeDeck()
    image_manager = ImageManager(fake_deck)
    image_manager.create_placeholder_images()
    
    # Create mode-specific placeholder images
    mode_images = {
        # Terminal mode
        "images/modes/terminal/new-tab.png": ("NT", (0, 200, 100)),
        "images/modes/terminal/clear.png": ("CL", (255, 100, 100)),
        "images/modes/terminal/git-status.png": ("GS", (100, 100, 255)),
        "images/modes/terminal/projects.png": ("PR", (200, 200, 0)),
        "images/modes/terminal/ssh.png": ("SSH", (255, 150, 0)),
        "images/modes/terminal/python.png": ("PY", (50, 100, 200)),
        "images/modes/terminal/node.png": ("JS", (100, 200, 50)),
        "images/modes/terminal/docker.png": ("DK", (0, 150, 255)),
        "images/modes/terminal/logs.png": ("LOG", (150, 150, 150)),
        
        # Simulator mode
        "images/modes/simulator/iphone15.png": ("15", (0, 122, 255)),
        "images/modes/simulator/iphonese.png": ("SE", (100, 100, 100)),
        "images/modes/simulator/ipadpro.png": ("iPad", (200, 200, 200)),
        "images/modes/simulator/screenshot.png": ("📷", (255, 0, 255)),
        "images/modes/simulator/home.png": ("🏠", (0, 200, 0)),
        "images/modes/simulator/rotate.png": ("↻", (255, 150, 0)),
        "images/modes/simulator/reset.png": ("RST", (255, 0, 0)),
        "images/modes/simulator/darkmode.png": ("🌙", (50, 50, 50)),
        "images/modes/simulator/lightmode.png": ("☀️", (255, 255, 100)),
        
        # Fork mode
        "images/modes/fork/fetch.png": ("⬇", (0, 200, 200)),
        "images/modes/fork/pull.png": ("⬇⬇", (0, 150, 150)),
        "images/modes/fork/push.png": ("⬆", (200, 0, 200)),
        "images/modes/fork/commit.png": ("✓", (0, 255, 0)),
        "images/modes/fork/stash.png": ("📦", (200, 150, 100)),
        "images/modes/fork/branch.png": ("⑂", (150, 100, 200)),
        "images/modes/fork/history.png": ("📜", (150, 150, 100)),
        "images/modes/fork/diff.png": ("±", (255, 200, 0)),
        "images/modes/fork/refresh.png": ("⟳", (100, 200, 255)),
    }
    
    for path, (text, color) in mode_images.items():
        img = image_manager._create_icon_image(text, color)
        full_path = Path(path)
        full_path.parent.mkdir(parents=True, exist_ok=True)
        img.save(full_path, "PNG")
    
    print("Placeholder images created!")


def main():
    """Main entry point."""
    # Clear the log file at startup
    log_file = os.path.expanduser("~/.streamdeck.log")
    try:
        with open(log_file, 'w') as f:
            f.write("")  # Clear the log
    except Exception:
        pass  # Ignore errors if log file doesn't exist or can't be written
    
    print("Stream Deck Dual Control")
    print("=" * 50)
    
    # Check command line arguments
    verbose = False
    for arg in sys.argv[1:]:
        if arg in ["-v", "--verbose"]:
            verbose = True
            print("VERBOSE MODE ENABLED")
        elif arg == "--create-images":
            create_placeholder_images()
            return
    
    # Create controller with verbose mode
    controller = StreamDeckController(verbose=verbose)
    
    # Connect to Stream Deck
    if not controller.connect():
        print("Failed to connect to Stream Deck!")
        sys.exit(1)
    
    # Setup buttons
    print("Setting up buttons...")
    controller.setup_buttons()
    
    # Run the controller
    try:
        controller.run()
    except KeyboardInterrupt:
        print("\nShutting down...")
        controller.cleanup()
    except Exception as e:
        error_msg = str(e)
        print(f"Error: {error_msg}")
        notify_crash(error_msg)
        controller.cleanup()
        sys.exit(1)


if __name__ == "__main__":
    main()