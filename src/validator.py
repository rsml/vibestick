"""Configuration validation utilities."""

from typing import Dict, Any, List
from pathlib import Path


class ConfigValidator:
    """Validates configuration files and data."""
    
    @staticmethod
    def validate_overview(config: Dict[str, Any]) -> List[str]:
        """Validate overview configuration."""
        errors = []
        
        # Check required fields
        required_fields = ["layout", "computers", "fixedColumns"]
        for field in required_fields:
            if field not in config:
                errors.append(f"Missing required field: {field}")
        
        # Validate layout
        if "layout" in config:
            layout = config["layout"]
            if not isinstance(layout.get("rows"), int) or layout.get("rows", 0) < 1:
                errors.append("Invalid layout.rows: must be positive integer")
            if not isinstance(layout.get("columns"), int) or layout.get("columns", 0) < 1:
                errors.append("Invalid layout.columns: must be positive integer")
        
        # Validate computers
        if "computers" in config:
            computers = config["computers"]
            if not isinstance(computers, dict):
                errors.append("Invalid computers: must be object")
            else:
                for comp_id, comp_config in computers.items():
                    if not isinstance(comp_config.get("hostname"), str):
                        errors.append(f"Invalid hostname for computer {comp_id}")
                    if not isinstance(comp_config.get("name"), str):
                        errors.append(f"Invalid name for computer {comp_id}")
        
        # Validate fixed columns
        if "fixedColumns" in config:
            fixed = config["fixedColumns"]
            for side in ["left", "right"]:
                if side not in fixed:
                    errors.append(f"Missing fixedColumns.{side}")
                else:
                    side_config = fixed[side]
                    if "computer" not in side_config:
                        errors.append(f"Missing computer in fixedColumns.{side}")
                    if "buttons" not in side_config or not isinstance(side_config["buttons"], list):
                        errors.append(f"Invalid buttons in fixedColumns.{side}")
        
        return errors
    
    @staticmethod
    def validate_mode(config: Dict[str, Any]) -> List[str]:
        """Validate mode configuration."""
        errors = []
        
        # Check required fields
        if "mode" not in config:
            errors.append("Missing required field: mode")
        if "centerButtons" not in config:
            errors.append("Missing required field: centerButtons")
        elif not isinstance(config["centerButtons"], list):
            errors.append("Invalid centerButtons: must be array")
        
        # Validate buttons
        if isinstance(config.get("centerButtons"), list):
            for i, button in enumerate(config["centerButtons"]):
                errors.extend(ConfigValidator.validate_button(button, f"centerButtons[{i}]"))
        
        return errors
    
    @staticmethod
    def validate_button(button: Dict[str, Any], path: str) -> List[str]:
        """Validate a button configuration."""
        errors = []
        
        # Check position
        if "position" not in button:
            errors.append(f"{path}: missing position")
        else:
            pos = button["position"]
            if "row" not in pos or "column" not in pos:
                errors.append(f"{path}: position must have row and column")
            elif not isinstance(pos["row"], int) or not isinstance(pos["column"], int):
                errors.append(f"{path}: row and column must be integers")
        
        # Check action
        if "action" in button:
            action = button["action"]
            if "type" not in action:
                errors.append(f"{path}: action missing type")
            else:
                action_type = action["type"]
                if action_type == "command" and "command" not in action:
                    errors.append(f"{path}: command action missing command")
                elif action_type == "app" and "app" not in action:
                    errors.append(f"{path}: app action missing app")
                elif action_type == "applescript" and "script" not in action:
                    errors.append(f"{path}: applescript action missing script")
                elif action_type == "keystroke" and "keys" not in action:
                    errors.append(f"{path}: keystroke action missing keys")
        
        return errors
    
    @staticmethod
    def validate_all(config_dir: str) -> Dict[str, List[str]]:
        """Validate all configuration files."""
        all_errors = {}
        config_path = Path(config_dir)
        
        # Validate overview
        overview_path = config_path / "overview.json"
        if overview_path.exists():
            import json
            with open(overview_path) as f:
                overview = json.load(f)
            errors = ConfigValidator.validate_overview(overview)
            if errors:
                all_errors["overview.json"] = errors
        else:
            all_errors["overview.json"] = ["File not found"]
        
        # Validate mode files
        mode_files = ["terminal-mode.json", "simulator-mode.json", "fork-mode.json"]
        for mode_file in mode_files:
            mode_path = config_path / mode_file
            if mode_path.exists():
                with open(mode_path) as f:
                    mode_config = json.load(f)
                errors = ConfigValidator.validate_mode(mode_config)
                if errors:
                    all_errors[mode_file] = errors
            else:
                all_errors[mode_file] = ["File not found"]
        
        return all_errors