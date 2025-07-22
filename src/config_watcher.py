"""Watch configuration files for changes and trigger reloads."""
import os
import json
import time
import threading
from typing import Dict, Callable, Set
from pathlib import Path


class ConfigWatcher:
    """Monitor JSON configuration files for changes."""
    
    def __init__(self, config_dir: str):
        self.config_dir = Path(config_dir)
        self.callbacks: Set[Callable] = set()
        self._file_times: Dict[str, float] = {}
        self._running = False
        self._thread = None
        
        # Get initial modification times
        self._update_file_times()
        
    def add_callback(self, callback: Callable):
        """Add a callback to be called when configuration changes."""
        self.callbacks.add(callback)
        
    def remove_callback(self, callback: Callable):
        """Remove a callback."""
        self.callbacks.discard(callback)
        
    def start(self):
        """Start watching for changes."""
        if self._running:
            return
            
        self._running = True
        self._thread = threading.Thread(target=self._watch_loop, daemon=True)
        self._thread.start()
        
    def stop(self):
        """Stop watching for changes."""
        self._running = False
        if self._thread:
            self._thread.join(timeout=1.0)
            
    def _update_file_times(self):
        """Update tracked modification times."""
        for json_file in self.config_dir.glob("*.json"):
            try:
                mtime = json_file.stat().st_mtime
                self._file_times[str(json_file)] = mtime
            except OSError:
                pass
                
    def _check_for_changes(self) -> Set[str]:
        """Check for changed files."""
        changed_files = set()
        
        for json_file in self.config_dir.glob("*.json"):
            file_path = str(json_file)
            try:
                current_mtime = json_file.stat().st_mtime
                
                # Check if file is new or modified
                if file_path not in self._file_times:
                    changed_files.add(file_path)
                elif current_mtime > self._file_times[file_path]:
                    # Verify it's a valid JSON file before reporting change
                    try:
                        with open(json_file, 'r') as f:
                            json.load(f)
                        changed_files.add(file_path)
                    except (json.JSONDecodeError, OSError):
                        print(f"Skipping invalid JSON file: {file_path}")
                        
                self._file_times[file_path] = current_mtime
                
            except OSError:
                # File might have been deleted
                if file_path in self._file_times:
                    del self._file_times[file_path]
                    
        return changed_files
        
    def _watch_loop(self):
        """Main watching loop."""
        print("Config watcher started")
        
        while self._running:
            try:
                changed_files = self._check_for_changes()
                
                if changed_files:
                    print(f"Config files changed: {[Path(f).name for f in changed_files]}")
                    
                    # Call all callbacks
                    for callback in self.callbacks.copy():
                        try:
                            callback(changed_files)
                        except Exception as e:
                            print(f"Error in config change callback: {e}")
                            
            except Exception as e:
                print(f"Error in config watcher: {e}")
                
            # Check every second
            time.sleep(1.0)
            
        print("Config watcher stopped")