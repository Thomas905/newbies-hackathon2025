from hand_detection import HandDetector 
from game import GameArea, Settings
from support import *
import pygame

pygame.init()

# Screen
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NewBies Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 32, bold=True)

# Colors
WHITE = (255, 255, 255)
DARK_GREEN = (34, 139, 34)
LIGHT_GREEN = (50, 205, 50)
SHADOW_COLOR = (0, 0, 0, 100)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (60, 179, 113)

# Button function with shadow
def basic_button(text, x, y, selected):
    # Shadow
    shadow_offset = 6 if selected else 4
    pygame.draw.rect(screen, (50, 50, 50), (x + shadow_offset, y + shadow_offset, 200, 80), border_radius=15)
    
    # Button
    color = LIGHT_GREEN if selected else DARK_GREEN
    pygame.draw.rect(screen, color, (x, y, 200, 80), border_radius=15)
    
    # Text
    txt = font.render(text, True, WHITE)
    rect = txt.get_rect(center=(x + 100, y + 40))
    screen.blit(txt, rect)

detector = HandDetector()
area = GameArea()
settings = Settings()

def layout_menu():
    running = True
    selected = 0
    buttons = ["Start", "Settings", "Exit"]
    last_move_time = 0 
    last_grab = False
    current_mode = get_mode()

    if current_mode == ControlMode.HAND:
        detector.enabled = False
        detector.start_calibration()
        detector.enabled = True

    while running:
        # Background sky + grass
        screen.fill(SKY_BLUE)
        pygame.draw.rect(screen, GRASS_GREEN, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))
        
        if getattr(detector, "enabled", True):
            detector.update()

        new_grab = detector.is_grab and not last_grab and detector.hand_center
        last_grab = detector.is_grab

        mode = get_mode()
        print(mode)
        if mode != current_mode:
            current_mode = mode
            if mode == ControlMode.HAND:
                detector.enabled = False
                detector.start_calibration()
                detector.enabled = True
            elif mode == ControlMode.KEY:
                print("Keyboard mode selected!")

        # Draw buttons
        for i, btn in enumerate(buttons):
            basic_button(btn, 125, 250 + i*120, selected == i)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if mode == ControlMode.KEY and event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(buttons)
                elif event.key == pygame.K_RETURN:
                    if buttons[selected] == "Start":
                        area.layout_game_area()
                    elif buttons[selected] == "Settings":
                        settings.layout_setting()
                    elif buttons[selected] == "Exit":
                        running = False

        # Hand movement
        if mode == ControlMode.HAND and detector.movement and detector.hand_center:
            current_time = pygame.time.get_ticks()
            if current_time - last_move_time > 300:
                if detector.movement == "Down":
                    selected = (selected + 1) % len(buttons)
                elif detector.movement == "Up":
                    selected = (selected - 1) % len(buttons)
                last_move_time = current_time

        # Hand grab
        if mode == ControlMode.HAND and new_grab:
            current_time = pygame.time.get_ticks()
            if current_time - last_move_time > 300:
                if buttons[selected] == "Start":
                    area.layout_game_area()
                elif buttons[selected] == "Settings":
                    settings.layout_setting()
                elif buttons[selected] == "Exit":
                    running = False
                last_move_time = current_time

        pygame.display.flip()
        clock.tick(30)

layout_menu()
