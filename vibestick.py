#!/usr/bin/env python3
"""
Vibestick - macOS menubar app for StreamDeck Dual Control
"""

import rumps
import subprocess
import os
import sys
import signal
import shutil
from pathlib import Path


class VibestickApp(rumps.App):
    """macOS menubar app for StreamDeck control."""
    
    def __init__(self):
        super(VibestickApp, self).__init__("Vibestick", icon="assets/vibestick-icon.png")
        self.main_process = None
        self.setup_menu()
        self.start_main()
    
    def setup_menu(self):
        """Setup the menu items."""
        self.menu = [
            rumps.MenuItem("Status: Starting...", callback=None),
            None,  # Separator
            rumps.MenuItem("Reload", callback=self.reload_main),
            rumps.MenuItem("Show Logs", callback=self.show_logs),
            None,  # Separator
        ]
    
    def ensure_config(self):
        """Ensure config/mode.json exists, create from default if not."""
        script_dir = Path(__file__).parent
        mode_config = script_dir / "config" / "mode.json"
        
        if not mode_config.exists():
            # Look for terminal-mode.json as default
            default_mode = script_dir / "config" / "terminal-mode.json"
            if default_mode.exists():
                import shutil
                shutil.copy(default_mode, mode_config)
                rumps.notification(
                    "Vibestick", 
                    "Config Created", 
                    "Created default mode.json from terminal-mode template"
                )
            else:
                # Create a minimal config if no templates exist
                mode_config.parent.mkdir(exist_ok=True)
                mode_config.write_text('{"name": "default", "buttons": {}}')
                rumps.notification(
                    "Vibestick", 
                    "Config Created", 
                    "Created minimal mode.json configuration"
                )
    
    def start_main(self):
        """Start main.py as a subprocess."""
        try:
            # Change to the script directory
            script_dir = Path(__file__).parent
            
            # Ensure config/mode.json exists
            self.ensure_config()
            
            # Start main.py
            self.main_process = subprocess.Popen(
                [sys.executable, "main.py"],
                cwd=script_dir,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                universal_newlines=True,
                bufsize=1
            )
            
            self.menu["Status: Starting..."].title = "Status: Running"
            rumps.notification("Vibestick", "Started", "StreamDeck controller is running")
            
        except Exception as e:
            self.menu["Status: Starting..."].title = "Status: Error"
            rumps.notification("Vibestick", "Error", f"Failed to start: {str(e)}")
            print(f"Error starting main.py: {e}")
    
    @rumps.clicked("Reload")
    def reload_main(self, _):
        """Restart main.py."""
        self.stop_main()
        self.start_main()
        rumps.notification("Vibestick", "Reloaded", "StreamDeck controller has been restarted")
    
    def stop_main(self):
        """Stop the main.py process."""
        if self.main_process:
            try:
                # Send SIGTERM for graceful shutdown
                self.main_process.terminate()
                self.main_process.wait(timeout=5)
            except subprocess.TimeoutExpired:
                # Force kill if it doesn't stop
                self.main_process.kill()
            except Exception as e:
                print(f"Error stopping main.py: {e}")
            finally:
                self.main_process = None
                self.menu["Status: Running"].title = "Status: Stopped"
    
    @rumps.clicked("Show Logs")
    def show_logs(self, _):
        """Open Console.app to show logs."""
        os.system("open -a Console")
        rumps.notification("Vibestick", "Logs", "Opening Console.app - filter by 'python' or 'main.py'")
    
    @rumps.clicked("Quit")
    def quit_app(self, _):
        """Quit the application."""
        self.stop_main()
        rumps.quit_application()


if __name__ == "__main__":
    app = VibestickApp()
    app.run()