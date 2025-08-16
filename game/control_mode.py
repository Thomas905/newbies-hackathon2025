# control_mode.py
from enum import Enum

class ControlMode(Enum):
    HAND = "hand"
    KEY = "key"

current_mode = ControlMode.HAND

def set_mode(mode: ControlMode):
    global current_mode
    current_mode = mode

def get_mode() -> ControlMode:
    return current_mode
