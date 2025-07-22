import os
import threading
import time
from typing import Optional
from pathlib import Path
from StreamDeck.DeviceManager import DeviceManager
from StreamDeck.Devices import StreamDeck

from .config_loader import ConfigLoader
from .button_manager import ButtonManager, ButtonState
from .image_manager import ImageManager
from .command_executor import CommandExecutor
from .notification_helper import notify_usb_error, notify_startup_error
from .config_watcher import ConfigWatcher


class StreamDeckController:
    """Main controller for the Stream Deck dual-computer control system."""
    
    def __init__(self, config_dir: str = "config", verbose: bool = False):
        self.config_dir = config_dir
        self.verbose = verbose
        self.config = ConfigLoader(config_dir)
        self.button_manager = ButtonManager(
            rows=self.config.get_layout()["rows"],
            columns=self.config.get_layout()["columns"]
        )
        self.command_executor = CommandExecutor(verbose=verbose)
        self.deck: Optional[StreamDeck] = None
        self.image_manager: Optional[ImageManager] = None
        self.running = False
        
        # Set up config watcher
        self.config_watcher = ConfigWatcher(config_dir)
        self.config_watcher.add_callback(self._on_config_changed)
        
        # Set initial state
        self.button_manager.current_mode = self.config.get_default_mode()
        self.button_manager.current_computer = self.config.get_default_computer()
        
        if self.verbose:
            print(f"[VERBOSE] Controller initialized")
            print(f"[VERBOSE] Default mode: {self.button_manager.current_mode}")
            print(f"[VERBOSE] Default computer: {self.button_manager.current_computer}")
        
    def connect(self) -> bool:
        """Connect to the Stream Deck device."""
        decks = DeviceManager().enumerate()
        
        if not decks:
            print("No Stream Deck found!")
            notify_startup_error("No Stream Deck device found. Please connect your Stream Deck.")
            return False
            
        self.deck = decks[0]
        
        # Try to open with retry for USB permission issues
        max_retries = 3
        for attempt in range(max_retries):
            try:
                self.deck.open()
                self.deck.reset()
                break
            except Exception as e:
                if "Could not open HID device" in str(e):
                    print(f"USB permission error (attempt {attempt + 1}/{max_retries}). Retrying...")
                    if attempt < max_retries - 1:
                        time.sleep(2)
                    else:
                        print("\nERROR: Cannot access Stream Deck. This is usually a USB permissions issue.")
                        print("Please try:")
                        print("1. Unplug and replug your Stream Deck")
                        print("2. Run 'sudo make' to run with elevated permissions")
                        print("3. Check that no other Stream Deck software is running")
                        notify_usb_error()
                        return False
                else:
                    raise
        
        # Set brightness
        self.deck.set_brightness(75)
        
        # Initialize image manager
        self.image_manager = ImageManager(self.deck)
        
        # Set up button callback
        print("Setting up button callback...")
        self.deck.set_key_callback(self._key_change_callback)
        print("Button callback registered successfully")
        
        print(f"Connected to {self.deck.deck_type()} with {self.deck.key_count()} keys")
        return True
    
    def setup_buttons(self):
        """Initialize all buttons from configuration."""
        print("Setting up buttons...", flush=True)
        
        # Setup fixed columns
        for side in ["left", "right"]:
            computer_key = self.config.overview["fixedColumns"][side]["computer"]
            buttons = self.config.get_fixed_buttons(side)
            self.button_manager.setup_fixed_buttons(side, buttons, computer_key)
            print(f"  Configured {len(buttons)} buttons for {side} side ({computer_key})", flush=True)
        
        # Setup center buttons for current mode
        self._update_center_buttons()
        
        # Set initial selection
        self._set_initial_selection()
        
        # Update all button images
        self._update_all_buttons()
        
        print(f"Button setup complete! Total buttons: {len(self.button_manager.get_all_buttons())}", flush=True)
    
    def _update_center_buttons(self):
        """Update center buttons based on current mode."""
        mode = self.button_manager.get_current_mode()
        try:
            buttons = self.config.get_mode_buttons(mode)
            self.button_manager.setup_center_buttons(buttons, mode)
        except ValueError as e:
            print(f"Error loading mode {mode}: {e}")
    
    def _set_initial_selection(self):
        """Set initial selected button based on current mode and computer."""
        mode = self.button_manager.get_current_mode()
        computer = self.button_manager.get_current_computer()
        
        # Find the button that matches current mode and computer
        for button in self.button_manager.get_all_buttons():
            if (button.mode == mode and 
                button.column in [0, 4] and
                ((computer == "laptop" and button.column == 0) or
                 (computer == "desktop" and button.column == 4))):
                self.button_manager.set_selected_button(button.index)
                break
    
    def _update_all_buttons(self):
        """Update all button images on the Stream Deck."""
        if not self.deck or not self.image_manager:
            return
            
        for button in self.button_manager.get_all_buttons():
            self._update_button_image(button.index)
    
    def _update_button_image(self, index: int):
        """Update a single button image."""
        if not self.deck or not self.image_manager:
            return
            
        button = self.button_manager.get_button(index)
        if not button:
            return
        
        # Debug logging only in verbose mode
        if self.verbose and (button.image_path or button.label):
            print(f"[VERBOSE] Button {index}: image={button.image_path}, label={button.label}, state={button.state.value}")
        
        # Get appropriate image
        if button.image_path or button.label:
            image = self.image_manager.get_image(
                button.image_path,
                button.label,
                button.state.value,
                position=index
            )
        else:
            image = self.image_manager.get_blank_image()
        
        # Update the button
        self.deck.set_key_image(index, image)
    
    def _key_change_callback(self, deck, key, state):
        """Handle button press/release events."""
        # Immediate feedback for any key event
        print(f"[KEY EVENT] Button {key}, State: {'pressed' if state else 'released'}", flush=True)
        
        if not state:  # Button released
            if self.verbose:
                print(f"[VERBOSE] Button {key} released", flush=True)
            return
            
        # Always show button press in any mode
        print(f"\n>>> BUTTON {key} PRESSED", flush=True)
        
        # Handle button press
        button = self.button_manager.press_button(key)
        if not button:
            print(f"    No button configured at index {key}", flush=True)
            return
            
        # Always show basic info
        if button.label:
            print(f"    Button: {button.label}", flush=True)
        
        # Show detailed info in verbose mode
        if self.verbose:
            print(f"    [VERBOSE] Mode: {button.mode}")
            print(f"    [VERBOSE] Computer: {button.computer}")
            print(f"    [VERBOSE] Column: {button.column}, Row: {button.row}")
            if button.action:
                print(f"    [VERBOSE] Action Type: {button.action.get('type')}")
                if button.action.get('type') == 'keystroke':
                    print(f"    [VERBOSE] Shortcut: {button.action.get('shortcut', button.action.get('keys'))}")
                elif button.action.get('type') == 'app_shortcut':
                    print(f"    [VERBOSE] App: {button.action.get('app')}")
                    print(f"    [VERBOSE] Shortcut: {button.action.get('shortcut')}")
        
        # Check if this is a mode switch
        if button.column in [0, 4] and button.mode:
            # Mode/computer switch
            print(f"    Switching to: {button.mode} mode on {self.button_manager.get_current_computer()}", flush=True)
            
            # Update center buttons
            self._update_center_buttons()
            
            # Update all button images to reflect new state
            self._update_all_buttons()
            
            # Execute the action (open app)
            if button.action:
                computer_config = self.config.get_computer_config(button.computer)
                if self.verbose:
                    print(f"    [VERBOSE] Opening {button.action.get('app', 'app')}")
                success = self.command_executor.execute_action(button.action, button.computer, computer_config)
                if self.verbose:
                    print(f"    [VERBOSE] Action result: {'Success' if success else 'Failed'}")
        
        elif button.action:
            # Regular action button
            computer = self.button_manager.get_current_computer()
            computer_config = self.config.get_computer_config(computer)
            
            # Show what action will be executed
            action_type = button.action.get('type')
            if action_type == 'keystroke':
                shortcut = button.action.get('shortcut', button.action.get('keys'))
                print(f"    Executing: {shortcut}", flush=True)
            elif action_type == 'app_shortcut':
                app = button.action.get('app')
                shortcut = button.action.get('shortcut')
                print(f"    Executing: {app} → {shortcut}", flush=True)
            elif action_type == 'command':
                cmd = button.action.get('command', '')[:50]
                print(f"    Executing: {cmd}...", flush=True)
            else:
                print(f"    Executing: {action_type}", flush=True)
            
            # Show pressed state briefly
            button.state = ButtonState.PRESSED
            self._update_button_image(key)
            
            # Execute action in background
            threading.Thread(
                target=self._execute_and_restore,
                args=(button, computer, computer_config, key),
                daemon=True
            ).start()
    
    def _execute_and_restore(self, button, computer, computer_config, key):
        """Execute action and restore button state."""
        try:
            # Execute the action
            if self.verbose:
                print(f"    [VERBOSE] Executing {button.action.get('type')} action...")
            success = self.command_executor.execute_action(button.action, computer, computer_config)
            if self.verbose:
                print(f"    [VERBOSE] Action completed: {'Success' if success else 'Failed'}")
            
            # Brief delay for visual feedback
            time.sleep(0.1)
            
        except Exception as e:
            print(f"    ERROR: {e}", flush=True)
            
        finally:
            # Restore button state
            button.state = ButtonState.NORMAL
            self._update_button_image(button.index)
    
    def _on_config_changed(self, changed_files):
        """Handle configuration file changes."""
        print("Reloading configuration...")
        
        # Reload the configuration
        self.config = ConfigLoader(self.config_dir)
        
        # Reinitialize command executor to refresh local hostname detection
        self.command_executor = CommandExecutor(verbose=self.verbose)
        
        # Check which files changed
        files_changed = [Path(f).name for f in changed_files]
        
        # Update center buttons if current mode config changed
        mode = self.button_manager.get_current_mode()
        mode_file = f"{mode}-mode.json"
        
        if mode_file in files_changed:
            self._update_center_buttons()
            self._update_all_buttons()
            print(f"Reloaded {mode} mode configuration")
        elif "overview.json" in files_changed:
            # Reload fixed buttons
            self.setup_buttons()
            print("Reloaded overview configuration")
        elif "computers.json" in files_changed:
            # Just reload the config, no UI update needed
            print("Reloaded computer IP addresses")
    
    def run(self):
        """Run the main controller loop."""
        if not self.deck:
            print("No deck connected!")
            return
            
        self.running = True
        
        # Start config watcher
        self.config_watcher.start()
        
        print("\nStarting Stream Deck Controller...", flush=True)
        print("=" * 50, flush=True)
        print("Press Ctrl+C to exit", flush=True)
        print("Configuration files are being watched for changes", flush=True)
        if self.verbose:
            print("VERBOSE MODE: Detailed logging enabled", flush=True)
        print("=" * 50, flush=True)
        print("\nWaiting for button presses...", flush=True)
        
        try:
            while self.running:
                time.sleep(0.1)
        except KeyboardInterrupt:
            print("\nShutting down...")
        finally:
            self.cleanup()
    
    def cleanup(self):
        """Clean up resources."""
        self.running = False
        
        # Stop config watcher
        self.config_watcher.stop()
        
        if self.deck:
            try:
                self.deck.reset()
                self.deck.close()
            except:
                pass
                
        self.command_executor.cleanup()
        print("Cleanup complete")