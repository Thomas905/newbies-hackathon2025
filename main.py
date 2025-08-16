from hand_detection import HandDetector 
from game import GameArea, Settings
from support import *
import pygame, sys

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

def execute_selection(choice):
    if choice == "Start":
        area.layout_game_area()
    elif choice == "Settings":
        settings.layout_setting()
    elif choice == "Exit":
        pygame.quit()
        sys.exit()

def layout_menu():
    running = True
    selected = 0
    buttons = ["Start", "Settings", "Exit"]
    last_move_time = 0 
    last_grab = False
    current_mode = get_mode()
    show_rage_quit_msg = False
    rage_quit_timer = 0

    if current_mode == ControlMode.HAND:
        detector.enabled = False
        detector.start_calibration()
        detector.enabled = True

    while running:
        # Background
        screen.fill(SKY_BLUE)
        pygame.draw.rect(screen, GRASS_GREEN, (0, SCREEN_HEIGHT // 2, SCREEN_WIDTH, SCREEN_HEIGHT // 2))

        if getattr(detector, "enabled", True):
            detector.update()
            if getattr(detector, "is_fuck", False):
                show_rage_quit_msg = True
                rage_quit_timer = pygame.time.get_ticks()
                detector.is_fuck = False 

        new_grab = detector.is_grab and not last_grab and detector.hand_center
        last_grab = detector.is_grab

        for i, btn in enumerate(buttons):
            basic_button(btn, 125, 250 + i*120, selected == i)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(buttons)
                elif event.key == pygame.K_RETURN:
                    execute_selection(buttons[selected])

        if detector.hand_center:
            current_time = pygame.time.get_ticks()
            if detector.movement and current_time - last_move_time > 300:
                if detector.movement == "Down":
                    selected = (selected + 1) % len(buttons)
                elif detector.movement == "Up":
                    selected = (selected - 1) % len(buttons)
                last_move_time = current_time

            if new_grab and current_time - last_move_time > 300:
                execute_selection(buttons[selected])
                last_move_time = current_time
        if show_rage_quit_msg:
            elapsed = pygame.time.get_ticks() - rage_quit_timer
            if elapsed < 2000:
                msg = font.render("😡 Rage quit detected!", True, (255, 0, 0))
                screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 100))
            else:
                show_rage_quit_msg = False
        pygame.display.flip()
        clock.tick(30)
layout_menu()
