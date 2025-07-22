import json
import os
from pathlib import Path
from typing import Dict, Any, List


class ConfigLoader:
    """Loads and manages configuration files for the Stream Deck controller."""
    
    def __init__(self, config_dir: str = "config"):
        self.config_dir = Path(config_dir)
        self.overview = self._load_json("overview.json")
        self.modes = self._load_modes()
        self.computers = self._load_computers()
        
    def _load_json(self, filename: str) -> Dict[str, Any]:
        """Load a JSON file from the config directory."""
        filepath = self.config_dir / filename
        if not filepath.exists():
            raise FileNotFoundError(f"Configuration file not found: {filepath}")
            
        with open(filepath, 'r') as f:
            return json.load(f)
    
    def _load_modes(self) -> Dict[str, Dict[str, Any]]:
        """Load all mode configuration files."""
        modes = {}
        mode_files = ["terminal-mode.json", "simulator-mode.json", "fork-mode.json"]
        
        for mode_file in mode_files:
            try:
                mode_config = self._load_json(mode_file)
                mode_name = mode_config.get("mode")
                if mode_name:
                    modes[mode_name] = mode_config
            except FileNotFoundError:
                print(f"Warning: Mode file {mode_file} not found")
                
        return modes
    
    def _load_computers(self) -> Dict[str, Any]:
        """Load computer configuration from computers.json."""
        try:
            return self._load_json("computers.json")
        except FileNotFoundError:
            print("Warning: computers.json not found, using overview.json for computer config")
            return {}
    
    def get_computer_config(self, computer_key: str) -> Dict[str, Any]:
        """Get configuration for a specific computer."""
        # First check overview.json for computer metadata
        computers = self.overview.get("computers", {})
        if computer_key not in computers:
            raise ValueError(f"Computer '{computer_key}' not found in configuration")
        
        config = computers[computer_key].copy()
        
        # Override with data from computers.json if available
        if computer_key in self.computers:
            computer_data = self.computers[computer_key]
            if isinstance(computer_data, dict):
                # New format with address and BTT config
                config["hostname"] = computer_data.get("address", config.get("hostname"))
                config["betterTouchToolSharedSecret"] = computer_data.get("betterTouchToolSharedSecret")
                config["betterTouchToolPort"] = computer_data.get("betterTouchToolPort", 64873)
            else:
                # Old format with just IP address
                config["hostname"] = computer_data
            
        return config
    
    def get_fixed_buttons(self, side: str) -> List[Dict[str, Any]]:
        """Get fixed button configuration for left or right side."""
        fixed_columns = self.overview.get("fixedColumns", {})
        if side not in fixed_columns:
            raise ValueError(f"Side '{side}' must be 'left' or 'right'")
        return fixed_columns[side].get("buttons", [])
    
    def get_mode_buttons(self, mode: str) -> List[Dict[str, Any]]:
        """Get center button configuration for a specific mode."""
        if mode not in self.modes:
            raise ValueError(f"Mode '{mode}' not found in configuration")
        return self.modes[mode].get("centerButtons", [])
    
    def get_layout(self) -> Dict[str, int]:
        """Get layout configuration."""
        return self.overview.get("layout", {"rows": 3, "columns": 5, "buttonSize": 72})
    
    def get_default_mode(self) -> str:
        """Get the default mode."""
        return self.overview.get("defaultMode", "terminal")
    
    def get_default_computer(self) -> str:
        """Get the default computer."""
        return self.overview.get("defaultComputer", "laptop")