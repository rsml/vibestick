"""Parse human-readable keyboard shortcuts into system events."""
import re
from typing import List, Dict, Tuple


class KeyboardShortcutParser:
    """Parse keyboard shortcuts like 'Cmd+C', 'Ctrl+C Ctrl+C', 'Alt+Space' etc."""
    
    # Modifier key mappings
    MODIFIERS = {
        'cmd': 'command down',
        'command': 'command down',
        'ctrl': 'control down',
        'control': 'control down',
        'alt': 'option down',
        'option': 'option down',
        'opt': 'option down',
        'shift': 'shift down',
        'fn': 'function down'
    }
    
    # Special key mappings
    SPECIAL_KEYS = {
        'space': 49,
        'return': 36,
        'enter': 36,
        'tab': 48,
        'delete': 51,
        'backspace': 51,
        'escape': 53,
        'esc': 53,
        'up': 126,
        'down': 125,
        'left': 123,
        'right': 124,
        'home': 115,
        'end': 119,
        'pageup': 116,
        'pagedown': 121,
        'f1': 122, 'f2': 120, 'f3': 99, 'f4': 118, 'f5': 96,
        'f6': 97, 'f7': 98, 'f8': 100, 'f9': 101, 'f10': 109,
        'f11': 103, 'f12': 111, 'f13': 105, 'f14': 107, 'f15': 113
    }
    
    # Regular key to key code mappings
    KEY_CODES = {
        'a': 0, 's': 1, 'd': 2, 'f': 3, 'h': 4, 'g': 5, 'z': 6, 'x': 7,
        'c': 8, 'v': 9, 'b': 11, 'q': 12, 'w': 13, 'e': 14, 'r': 15,
        'y': 16, 't': 17, '1': 18, '2': 19, '3': 20, '4': 21, '6': 22,
        '5': 23, '=': 24, '9': 25, '7': 26, '-': 27, '8': 28, '0': 29,
        ']': 30, 'o': 31, 'u': 32, '[': 33, 'i': 34, 'p': 35, 'l': 37,
        'j': 38, "'": 39, 'k': 40, ';': 41, '\\': 42, ',': 43, '/': 44,
        'n': 45, 'm': 46, '.': 47, '`': 50
    }
    
    @classmethod
    def parse(cls, shortcut: str) -> List[Dict]:
        """
        Parse a keyboard shortcut string into a list of keystroke actions.
        
        Examples:
            'Cmd+C' -> Single keystroke with command modifier
            'Ctrl+C Ctrl+C' -> Two separate keystrokes
            'Cmd+Shift+N' -> Single keystroke with multiple modifiers
            
        Returns:
            List of action dictionaries ready for execution
        """
        if not shortcut:
            return []
            
        # Split by spaces to get individual key combinations
        combinations = shortcut.strip().split()
        actions = []
        
        for combo in combinations:
            action = cls._parse_single_combination(combo)
            if action:
                actions.append(action)
                
        return actions
    
    @classmethod
    def _parse_single_combination(cls, combo: str) -> Dict:
        """Parse a single key combination like 'Cmd+C'."""
        # Split by + to get modifiers and main key
        parts = [p.strip().lower() for p in combo.split('+')]
        
        if not parts:
            return None
            
        # Last part is the main key, others are modifiers
        main_key = parts[-1]
        modifiers = parts[:-1] if len(parts) > 1 else []
        
        # Build the action
        action = {
            'type': 'keystroke',
            'modifiers': [],
            'key': main_key
        }
        
        # Process modifiers
        for mod in modifiers:
            if mod in cls.MODIFIERS:
                action['modifiers'].append(mod)
                
        return action
    
    @classmethod
    def to_applescript(cls, action: Dict) -> str:
        """Convert a parsed action to AppleScript."""
        if action['type'] != 'keystroke':
            return ""
            
        key = action['key']
        modifiers = action.get('modifiers', [])
        
        # Build modifier clause
        using_clause = ""
        if modifiers:
            mod_list = [cls.MODIFIERS.get(mod, f"{mod} down") for mod in modifiers]
            using_clause = f" using {{{', '.join(mod_list)}}}"
        
        # Check if it's a special key or regular key
        if key in cls.SPECIAL_KEYS:
            key_code = cls.SPECIAL_KEYS[key]
            return f'tell application "System Events" to key code {key_code}{using_clause}'
        elif key in cls.KEY_CODES:
            key_code = cls.KEY_CODES[key]
            return f'tell application "System Events" to key code {key_code}{using_clause}'
        elif len(key) == 1:
            # Single character keystroke
            return f'tell application "System Events" to keystroke "{key}"{using_clause}'
        else:
            # Try to parse as a number for key code
            try:
                key_code = int(key)
                return f'tell application "System Events" to key code {key_code}{using_clause}'
            except ValueError:
                # Fallback to keystroke
                return f'tell application "System Events" to keystroke "{key}"{using_clause}'
    
    @classmethod
    def get_legacy_format(cls, shortcut: str) -> List[List[str]]:
        """Convert modern shortcut format to legacy format for backwards compatibility."""
        actions = cls.parse(shortcut)
        legacy_actions = []
        
        for action in actions:
            keys = action.get('modifiers', []).copy()
            keys.append(action['key'])
            legacy_actions.append(keys)
            
        return legacy_actions