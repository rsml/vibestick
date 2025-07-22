from typing import Dict, List, Optional, Tuple, Callable
from dataclasses import dataclass
from enum import Enum


class ButtonState(Enum):
    """Button states for visual feedback."""
    NORMAL = "normal"
    SELECTED = "selected"
    PRESSED = "pressed"


@dataclass
class Button:
    """Represents a single button on the Stream Deck."""
    index: int
    row: int
    column: int
    mode: Optional[str] = None
    label: Optional[str] = None
    image_path: Optional[str] = None
    action: Optional[Dict] = None
    state: ButtonState = ButtonState.NORMAL
    computer: Optional[str] = None


class ButtonManager:
    """Manages button layout and state for the Stream Deck."""
    
    def __init__(self, rows: int = 3, columns: int = 5):
        self.rows = rows
        self.columns = columns
        self.total_buttons = rows * columns
        self.buttons: Dict[int, Button] = {}
        self.current_mode = "terminal"
        self.current_computer = "laptop"
        self.selected_button: Optional[int] = None
        
        # Initialize empty buttons
        for i in range(self.total_buttons):
            row, col = self._index_to_position(i)
            self.buttons[i] = Button(index=i, row=row, column=col)
    
    def _index_to_position(self, index: int) -> Tuple[int, int]:
        """Convert button index to row, column position."""
        row = index // self.columns
        column = index % self.columns
        return row, column
    
    def _position_to_index(self, row: int, column: int) -> int:
        """Convert row, column position to button index."""
        return row * self.columns + column
    
    def setup_fixed_buttons(self, side: str, buttons_config: List[Dict], computer: str):
        """Setup fixed buttons on left or right side."""
        for button_config in buttons_config:
            pos = button_config.get("position", {})
            row = pos.get("row")
            col = pos.get("column")
            
            if row is None or col is None:
                continue
                
            index = self._position_to_index(row, col)
            if 0 <= index < self.total_buttons:
                self.buttons[index] = Button(
                    index=index,
                    row=row,
                    column=col,
                    mode=button_config.get("mode"),
                    label=button_config.get("label"),
                    image_path=button_config.get("image"),
                    action=button_config.get("action"),
                    computer=computer
                )
    
    def setup_center_buttons(self, buttons_config: List[Dict], mode: str):
        """Setup center buttons for current mode."""
        # Clear center buttons (columns 1-3)
        for row in range(self.rows):
            for col in range(1, 4):  # Center columns
                index = self._position_to_index(row, col)
                self.buttons[index] = Button(index=index, row=row, column=col)
        
        # Setup new buttons
        for button_config in buttons_config:
            pos = button_config.get("position", {})
            row = pos.get("row")
            col = pos.get("column")
            
            if row is None or col is None:
                continue
                
            # Only set center buttons (columns 1-3)
            if 1 <= col <= 3:
                index = self._position_to_index(row, col)
                if 0 <= index < self.total_buttons:
                    self.buttons[index] = Button(
                        index=index,
                        row=row,
                        column=col,
                        mode=mode,
                        label=button_config.get("label"),
                        image_path=button_config.get("image"),
                        action=button_config.get("action"),
                        computer=self.current_computer
                    )
    
    def get_button(self, index: int) -> Optional[Button]:
        """Get button by index."""
        return self.buttons.get(index)
    
    def get_button_by_position(self, row: int, column: int) -> Optional[Button]:
        """Get button by position."""
        index = self._position_to_index(row, column)
        return self.get_button(index)
    
    def set_selected_button(self, index: Optional[int]):
        """Set the selected button and update states."""
        # Clear previous selection
        if self.selected_button is not None:
            if self.selected_button in self.buttons:
                self.buttons[self.selected_button].state = ButtonState.NORMAL
        
        # Set new selection
        self.selected_button = index
        if index is not None and index in self.buttons:
            self.buttons[index].state = ButtonState.SELECTED
    
    def press_button(self, index: int) -> Optional[Button]:
        """Handle button press and return the button."""
        if index not in self.buttons:
            return None
            
        button = self.buttons[index]
        
        # Handle mode/computer switching for fixed columns
        if button.column in [0, 4] and button.mode:
            # Switch mode
            self.current_mode = button.mode
            
            # Switch computer based on column
            if button.column == 0:
                self.current_computer = "laptop"
            else:
                self.current_computer = "desktop"
            
            # Update selection
            self.set_selected_button(index)
            
        return button
    
    def get_current_mode(self) -> str:
        """Get current selected mode."""
        return self.current_mode
    
    def get_current_computer(self) -> str:
        """Get current selected computer."""
        return self.current_computer
    
    def get_all_buttons(self) -> List[Button]:
        """Get all buttons in order."""
        return [self.buttons[i] for i in range(self.total_buttons)]