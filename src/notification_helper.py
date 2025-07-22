"""macOS notification helper for StreamDeck errors."""

import subprocess
import os


def send_notification(title: str, message: str, sound: bool = True):
    """Send a macOS notification using osascript."""
    try:
        # Build the AppleScript command
        script = f'''
        display notification "{message}" with title "{title}" sound name "Basso"
        '''
        
        # Execute the AppleScript
        subprocess.run(['osascript', '-e', script], check=True, capture_output=True)
        
        # Also speak the error if it's critical
        if "ERROR" in title.upper() or "FAILED" in title.upper():
            subprocess.run(['say', '-v', 'Samantha', f"{title}. {message}"], capture_output=True)
            
    except Exception as e:
        # Fallback to terminal-notifier if available
        try:
            subprocess.run([
                'terminal-notifier',
                '-title', title,
                '-message', message,
                '-sound', 'Basso' if sound else 'default',
                '-group', 'streamdeck-error'
            ], check=True, capture_output=True)
        except:
            # If all else fails, just print
            print(f"\n⚠️  {title}: {message}\n")


def notify_usb_error():
    """Specific notification for USB permission errors."""
    send_notification(
        "StreamDeck USB Error",
        "Cannot access StreamDeck. Try unplugging and replugging the device, or run with 'sudo make'",
        sound=True
    )


def notify_startup_error(error_msg: str):
    """Notification for general startup errors."""
    send_notification(
        "StreamDeck Startup Failed",
        f"Error: {error_msg}",
        sound=True
    )


def notify_crash(error_msg: str):
    """Notification for crashes during runtime."""
    send_notification(
        "StreamDeck Crashed",
        f"The StreamDeck controller crashed: {error_msg}",
        sound=True
    )