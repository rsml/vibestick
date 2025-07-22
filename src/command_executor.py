import subprocess
import os
import socket
import urllib.parse
import urllib.request
import json
from typing import Dict, Any, Optional, List, Union
import paramiko
from pathlib import Path
from .keyboard_parser import KeyboardShortcutParser


class CommandExecutor:
    """Executes commands locally or remotely via SSH/Tailscale."""
    
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.ssh_clients: Dict[str, paramiko.SSHClient] = {}
        self._local_hostnames = self._get_local_hostnames()
        
    def _get_local_hostnames(self) -> set:
        """Get all hostnames that refer to the local machine."""
        hostnames = {'localhost', '127.0.0.1', '::1'}
        
        # Add actual hostname
        try:
            hostnames.add(socket.gethostname())
            hostnames.add(socket.gethostname().split('.')[0])  # Short hostname
        except:
            pass
            
        # Add computer name from scutil (macOS)
        try:
            result = subprocess.run(['scutil', '--get', 'ComputerName'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                hostnames.add(result.stdout.strip().lower())
        except:
            pass
            
        # Add local hostname from scutil (macOS)
        try:
            result = subprocess.run(['scutil', '--get', 'LocalHostName'], 
                                  capture_output=True, text=True)
            if result.returncode == 0:
                hostnames.add(result.stdout.strip().lower())
        except:
            pass
            
        # Add all local IP addresses
        try:
            # Get all network interfaces
            import netifaces
            for interface in netifaces.interfaces():
                addrs = netifaces.ifaddresses(interface)
                # IPv4 addresses
                if netifaces.AF_INET in addrs:
                    for addr in addrs[netifaces.AF_INET]:
                        if 'addr' in addr:
                            hostnames.add(addr['addr'])
                # IPv6 addresses
                if netifaces.AF_INET6 in addrs:
                    for addr in addrs[netifaces.AF_INET6]:
                        if 'addr' in addr:
                            hostnames.add(addr['addr'].split('%')[0])  # Remove interface suffix
        except ImportError:
            # If netifaces is not installed, try alternative method
            try:
                # Get IP addresses using socket
                hostname = socket.gethostname()
                for info in socket.getaddrinfo(hostname, None):
                    hostnames.add(info[4][0])
            except:
                pass
            
        if self.verbose:
            print(f"[VERBOSE] Local hostnames detected: {hostnames}")
            
        return hostnames
    
    def _is_local_computer(self, computer_config: Optional[Dict[str, Any]]) -> bool:
        """Check if the computer config refers to the local machine."""
        if not computer_config:
            return True
            
        hostname = computer_config.get('hostname', '').lower()
        if not hostname:
            return True
            
        # Check if hostname matches any local hostname/IP
        return hostname in self._local_hostnames
        
    def execute_action(self, action: Dict[str, Any], computer: Optional[str] = None, 
                      computer_config: Optional[Dict[str, Any]] = None) -> bool:
        """Execute an action based on its type."""
        if not action:
            return False
            
        action_type = action.get("type")
        
        if action_type == "command":
            return self._execute_command(action.get("command"), computer, computer_config)
        elif action_type == "app":
            return self._open_app(action.get("app"), computer, computer_config)
        elif action_type == "applescript":
            return self._execute_applescript(action.get("script"), computer, computer_config)
        elif action_type == "keystroke":
            # Handle new format with command and application
            if "command" in action:
                app = action.get("application")
                shortcut = action.get("command")
                if app and app != "global":
                    # Use app_shortcut behavior for specific applications
                    return self._send_app_shortcut(app, shortcut, computer, computer_config)
                else:
                    # Global shortcut - send without activating any app
                    return self._send_keystroke_from_shortcut(shortcut, computer, computer_config)
            # Handle old formats for backwards compatibility
            elif "shortcut" in action:
                return self._send_keystroke_from_shortcut(action.get("shortcut"), computer, computer_config)
            else:
                return self._send_keystroke(action.get("keys", []), computer, computer_config)
        elif action_type == "app_shortcut":
            return self._send_app_shortcut(action.get("app"), action.get("shortcut"), computer, computer_config)
        elif action_type == "btt_trigger":
            return self._execute_btt_trigger(action.get("trigger_name"), computer_config)
        else:
            print(f"Unknown action type: {action_type}")
            return False
    
    def _execute_command(self, command: str, computer: Optional[str], 
                        computer_config: Optional[Dict[str, Any]]) -> bool:
        """Execute a shell command."""
        if not command:
            return False
            
        try:
            # Check if this should be local execution
            if computer and computer_config and not self._is_local_computer(computer_config):
                # Remote execution via SSH
                if self.verbose:
                    print(f"        [VERBOSE] Executing remotely on {computer_config.get('hostname')}")
                return self._execute_remote_command(command, computer_config)
            else:
                # Local execution
                if self.verbose:
                    print(f"        [VERBOSE] Executing locally")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                if result.returncode != 0:
                    print(f"Command failed: {result.stderr}")
                return result.returncode == 0
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    
    def _open_app(self, app_name: str, computer: Optional[str], 
                  computer_config: Optional[Dict[str, Any]]) -> bool:
        """Open an application."""
        if not app_name:
            return False
            
        command = f"open -a '{app_name}'"
        return self._execute_command(command, computer, computer_config)
    
    def _execute_applescript(self, script: str, computer: Optional[str], 
                            computer_config: Optional[Dict[str, Any]]) -> bool:
        """Execute an AppleScript."""
        if not script:
            return False
            
        if self.verbose:
            print(f"        [VERBOSE] AppleScript: {script[:100]}..." if len(script) > 100 else f"        [VERBOSE] AppleScript: {script}")
        
        # Escape the script for shell
        escaped_script = script.replace('"', '\\"').replace('\n', '\\n')
        command = f'osascript -e "{escaped_script}" 2>&1'
        
        # Execute and capture output
        try:
            # Check if this should be local execution
            if computer and computer_config and not self._is_local_computer(computer_config):
                # Remote execution
                if computer_config.get("betterTouchToolSharedSecret"):
                    # Use BetterTouchTool if configured
                    if self.verbose:
                        print(f"        [VERBOSE] Executing AppleScript via BTT on {computer_config.get('hostname')}")
                    return self._execute_btt_applescript(script, computer_config)
                else:
                    # Fall back to SSH
                    if self.verbose:
                        print(f"        [VERBOSE] Executing AppleScript via SSH on {computer_config.get('hostname')}")
                    result = self._execute_remote_command(command, computer_config)
                    return result
            else:
                # Local execution with detailed output
                if self.verbose:
                    print(f"        [VERBOSE] Executing AppleScript locally")
                result = subprocess.run(command, shell=True, capture_output=True, text=True)
                
                if result.stdout.strip():
                    print(f"        [APPLESCRIPT OUTPUT] {result.stdout.strip()}")
                    
                if result.returncode != 0:
                    print(f"        [APPLESCRIPT ERROR] Exit code: {result.returncode}")
                    if result.stderr.strip():
                        print(f"        [APPLESCRIPT ERROR] {result.stderr.strip()}")
                    # Check for common permission errors
                    if "not allowed" in result.stderr:
                        print(f"        [PERMISSION ERROR] Grant accessibility permissions to the application")
                    return False
                    
                return True
        except Exception as e:
            print(f"        [APPLESCRIPT EXCEPTION] {e}")
            return False
    
    def _send_keystroke(self, keys: list, computer: Optional[str], 
                       computer_config: Optional[Dict[str, Any]]) -> bool:
        """Send keystrokes using AppleScript."""
        if not keys:
            return False
            
        # Build AppleScript for keystrokes
        key_mapping = {
            "cmd": "command down",
            "ctrl": "control down",
            "alt": "option down", 
            "shift": "shift down",
            "return": "return",
            "space": "space",
            "tab": "tab"
        }
        
        # Get the main key (last in list)
        main_key = keys[-1] if keys else None
        modifiers = keys[:-1] if len(keys) > 1 else []
        
        if not main_key:
            return False
            
        # Build the keystroke command
        using_clause = ""
        if modifiers:
            mod_list = [key_mapping.get(mod, f"{mod} down") for mod in modifiers]
            using_clause = f" using {{{', '.join(mod_list)}}}"
        
        # Map single characters or use key code
        if len(main_key) == 1:
            script = f'tell application "System Events" to keystroke "{main_key}"{using_clause}'
        else:
            # For special keys, use key code
            key_codes = {
                "a": 0, "s": 1, "d": 2, "f": 3, "h": 4, "g": 5, "z": 6, "x": 7,
                "c": 8, "v": 9, "b": 11, "q": 12, "w": 13, "e": 14, "r": 15,
                "y": 16, "t": 17, "1": 18, "2": 19, "3": 20, "4": 21, "6": 22,
                "5": 23, "=": 24, "9": 25, "7": 26, "-": 27, "8": 28, "0": 29,
                "]": 30, "o": 31, "u": 32, "[": 33, "i": 34, "p": 35, "l": 37,
                "j": 38, "'": 39, "k": 40, ";": 41, "\\": 42, ",": 43, "/": 44,
                "n": 45, "m": 46, ".": 47, "`": 50,
                "space": 49, "return": 36, "tab": 48, "delete": 51, "escape": 53
            }
            
            if main_key.lower() in key_codes:
                key_code = key_codes[main_key.lower()]
                script = f'tell application "System Events" to key code {key_code}{using_clause}'
            else:
                # Fallback to keystroke
                script = f'tell application "System Events" to keystroke "{main_key}"{using_clause}'
        
        return self._execute_applescript(script, computer, computer_config)
    
    def _send_keystroke_from_shortcut(self, shortcut: str, computer: Optional[str],
                                    computer_config: Optional[Dict[str, Any]]) -> bool:
        """Send keystrokes from a human-readable shortcut string."""
        if not shortcut:
            return False
            
        if self.verbose:
            print(f"        [VERBOSE] Parsing shortcut: {shortcut}")
        actions = KeyboardShortcutParser.parse(shortcut)
        if not actions:
            if self.verbose:
                print(f"        [VERBOSE] ERROR: Failed to parse shortcut")
            return False
            
        # Execute each keystroke action
        for i, action in enumerate(actions):
            script = KeyboardShortcutParser.to_applescript(action)
            if script:
                if self.verbose:
                    print(f"        [VERBOSE] Keystroke {i+1}/{len(actions)}: {action['key']} with modifiers {action.get('modifiers', [])}")
                success = self._execute_applescript(script, computer, computer_config)
                if not success:
                    return False
                    
                # Add small delay between keystrokes in a sequence
                if i < len(actions) - 1:
                    delay_script = 'delay 0.1'
                    self._execute_applescript(delay_script, computer, computer_config)
                    
        return True
    
    def _send_app_shortcut(self, app_name: str, shortcut: str, computer: Optional[str],
                          computer_config: Optional[Dict[str, Any]]) -> bool:
        """Activate an app and send a keyboard shortcut to it."""
        if not app_name or not shortcut:
            return False
            
        if self.verbose:
            print(f"        [VERBOSE] App shortcut: {app_name} -> {shortcut}")
        
        # For remote execution with BTT configured, create a combined AppleScript
        if computer and computer_config and not self._is_local_computer(computer_config) and computer_config.get("betterTouchToolSharedSecret"):
            # Build a combined AppleScript that activates app and sends keystroke
            combined_script = f'tell application "{app_name}" to activate\n'
            combined_script += 'delay 0.2\n'
            
            # Parse the shortcut and build the keystroke command
            actions = KeyboardShortcutParser.parse(shortcut)
            if actions:
                for action in actions:
                    key = action['key']
                    modifiers = action.get('modifiers', [])
                    
                    # Build modifier clause
                    using_clause = ""
                    if modifiers:
                        mod_list = [KeyboardShortcutParser.MODIFIERS.get(mod, f"{mod} down") for mod in modifiers]
                        using_clause = f" using {{{', '.join(mod_list)}}}"
                    
                    # Check if it's a special key or regular key
                    if key in KeyboardShortcutParser.SPECIAL_KEYS:
                        key_code = KeyboardShortcutParser.SPECIAL_KEYS[key]
                        combined_script += f'tell application "System Events" to key code {key_code}{using_clause}\n'
                    elif key in KeyboardShortcutParser.KEY_CODES:
                        key_code = KeyboardShortcutParser.KEY_CODES[key]
                        combined_script += f'tell application "System Events" to key code {key_code}{using_clause}\n'
                    elif len(key) == 1:
                        combined_script += f'tell application "System Events" to keystroke "{key}"{using_clause}\n'
            
            print(f"        [BTT] Sending app shortcut: {app_name} -> {shortcut}")
            return self._execute_applescript(combined_script.rstrip(), computer, computer_config)
        
        # Local execution or SSH fallback - use step by step approach
        # First activate the app
        activate_script = f'tell application "{app_name}" to activate'
        print(f"        [STEP 1/3] Activating {app_name}...")
        success = self._execute_applescript(activate_script, computer, computer_config)
        if not success:
            print(f"        [ERROR] Failed to activate {app_name}")
            return False
        print(f"        [SUCCESS] {app_name} activated")
            
        # Small delay to ensure app is focused
        delay_script = 'delay 0.2'
        print(f"        [STEP 2/3] Waiting for app focus...")
        self._execute_applescript(delay_script, computer, computer_config)
        
        # Then send the shortcut
        print(f"        [STEP 3/3] Sending shortcut {shortcut} to {app_name}...")
        result = self._send_keystroke_from_shortcut(shortcut, computer, computer_config)
        if result:
            print(f"        [SUCCESS] Shortcut sent successfully")
        else:
            print(f"        [ERROR] Failed to send shortcut")
        return result
    
    def _execute_remote_command(self, command: str, computer_config: Dict[str, Any]) -> bool:
        """Execute command on remote computer via SSH."""
        hostname = computer_config.get("hostname")
        username = computer_config.get("username", "ross")
        
        if not hostname:
            print("No hostname configured for remote computer")
            return False
            
        try:
            # Use SSH with Tailscale (assumes Tailscale SSH is configured)
            ssh_command = f"ssh {username}@{hostname} '{command}'"
            print(f"        [SSH] Executing: {ssh_command}")
            
            result = subprocess.run(ssh_command, shell=True, capture_output=True, text=True)
            
            # Always show output and errors for debugging
            if result.stdout.strip():
                print(f"        [SSH OUTPUT] {result.stdout.strip()}")
                
            if result.stderr.strip():
                print(f"        [SSH STDERR] {result.stderr.strip()}")
                
            if result.returncode != 0:
                print(f"        [SSH ERROR] Exit code: {result.returncode}")
                print(f"        [SSH ERROR] Command failed: {ssh_command}")
                # Provide helpful error messages
                if "Connection refused" in result.stderr:
                    print(f"        [SSH HINT] SSH connection refused. Check if SSH is enabled on {hostname}")
                elif "No route to host" in result.stderr:
                    print(f"        [SSH HINT] Cannot reach {hostname}. Check IP address and network connection")
                elif "Permission denied" in result.stderr:
                    print(f"        [SSH HINT] SSH authentication failed. Check SSH keys or password")
                elif "timeout" in result.stderr.lower():
                    print(f"        [SSH HINT] Connection timed out. Host {hostname} may be unreachable")
            else:
                print(f"        [SSH SUCCESS] Command executed successfully")
            
            return result.returncode == 0
            
        except Exception as e:
            print(f"        [REMOTE EXCEPTION] {e}")
            return False
    
    def _execute_btt_trigger(self, trigger_name: str, computer_config: Dict[str, Any]) -> bool:
        """Execute a BetterTouchTool named trigger on a remote computer."""
        hostname = computer_config.get("hostname")
        port = computer_config.get("betterTouchToolPort", 64873)
        shared_secret = computer_config.get("betterTouchToolSharedSecret")
        
        if not all([hostname, shared_secret]):
            print(f"        [BTT ERROR] Missing BTT configuration for remote computer")
            return False
            
        try:
            # Build BTT URL - BTT expects raw shared_secret, not URL-encoded
            url = f"http://{hostname}:{port}/trigger_named/?trigger_name={urllib.parse.quote(trigger_name)}&shared_secret={shared_secret}"
            
            print(f"        [BTT] Triggering: {trigger_name} on {hostname}:{port}")
            
            # Make HTTP request
            with urllib.request.urlopen(url, timeout=5) as response:
                result = response.read().decode('utf-8')
                if self.verbose:
                    print(f"        [BTT RESPONSE] {result}")
                print(f"        [BTT SUCCESS] Trigger executed")
                return True
                
        except urllib.error.URLError as e:
            print(f"        [BTT ERROR] Failed to connect: {e}")
            if "Connection refused" in str(e):
                print(f"        [BTT HINT] Check if BTT web server is enabled on port {port}")
            elif "timed out" in str(e):
                print(f"        [BTT HINT] Host {hostname} may be unreachable")
            return False
        except Exception as e:
            print(f"        [BTT ERROR] Unexpected error: {e}")
            return False
    
    def _execute_btt_applescript(self, script: str, computer_config: Dict[str, Any]) -> bool:
        """Execute AppleScript via BetterTouchTool on a remote computer."""
        hostname = computer_config.get("hostname")
        port = computer_config.get("betterTouchToolPort", 64873)
        shared_secret = computer_config.get("betterTouchToolSharedSecret")
        
        if not all([hostname, shared_secret]):
            print(f"        [BTT ERROR] Missing BTT configuration for remote computer")
            return False
            
        try:
            # Build BTT URL for executing AppleScript - BTT expects raw shared_secret
            encoded_script = urllib.parse.quote(script)
            url = f"http://{hostname}:{port}/execute_applescript/?script={encoded_script}&shared_secret={shared_secret}"
            
            print(f"        [BTT] Executing AppleScript on {hostname}:{port}")
            if self.verbose:
                print(f"        [BTT SCRIPT] {script[:100]}..." if len(script) > 100 else f"        [BTT SCRIPT] {script}")
            
            # Make HTTP request
            with urllib.request.urlopen(url, timeout=10) as response:
                result = response.read().decode('utf-8')
                if result.strip():
                    print(f"        [BTT OUTPUT] {result.strip()}")
                print(f"        [BTT SUCCESS] AppleScript executed")
                return True
                
        except urllib.error.URLError as e:
            print(f"        [BTT ERROR] Failed to connect: {e}")
            return False
        except Exception as e:
            print(f"        [BTT ERROR] Unexpected error: {e}")
            return False
    
    def cleanup(self):
        """Clean up SSH connections."""
        for client in self.ssh_clients.values():
            try:
                client.close()
            except:
                pass
        self.ssh_clients.clear()