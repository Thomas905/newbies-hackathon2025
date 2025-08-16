import os.path as path
from enum import Enum

SCREEN_WIDTH = 450
SCREEN_HEIGHT = 720

FRAME_RATE = 60

# --- Difficulty and enemy refresh parameters ---
BASE_SCROLL_SPEED = 60  # initial scroll speed (pixels/sec)
BASE_ENEMY_SPEED = 0    # initial enemy speed (pixels/sec)
BASE_MAX_ENEMIES = 2
DIFFICULTY_INTERVAL = 1  # seconds per difficulty up
ENEMY_CHECK_INTERVAL = 2  # seconds per enemy check

SHOOT_CD = 200  # milliseconds

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 40, 0)
GREEN = (0, 255, 0)
BLUE = (38, 0, 255)
LIGHT_BLUE = (100, 180, 255)
YELLOW = (255, 195, 0)

# project folders
project_folder = path.dirname(__file__)
IMG_FOLDER = path.join(project_folder,"entity")
SND_FOLDER = path.join(project_folder,"entity")


#ControlMode [HAND, KEY]
class ControlMode(Enum):
    HAND = "hand"
    KEY = "key"

current_mode = ControlMode.HAND

def set_mode(mode: ControlMode):
    global current_mode
    current_mode = mode

def get_mode() -> ControlMode:
    return current_mode
