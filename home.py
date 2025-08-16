from hand_detection import HandDetector 
from game_area import GameArea
import pygame

pygame.init()

# Globals Variables
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NewBies Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)

##Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 40, 0)
BLUE = (38, 0, 255)
LIGHT_BLUE = (100, 180, 255)
YELLOW = (255, 195, 0)

def basic_button(text, x, y, selected):
    color = LIGHT_BLUE if selected else BLUE
    pygame.draw.rect(screen, color, (x, y, 200, 80))
    txt = font.render(text, True, WHITE)
    rect = txt.get_rect(center=(x + 100, y + 40))
    screen.blit(txt, rect)

detector = HandDetector()
area = GameArea()

# Layout Menu
def layout_menu():
    running = True
    selected = 0
    buttons = ["Start", "Settings"]
    last_move_time = 0 

    while running:
        screen.fill(YELLOW)  

        detector.update()

        basic_button("Start", 215, 362, selected == 0)
        basic_button("Settings", 215, 462, selected == 1)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

        if detector.movement and detector.hand_center:
            current_time = pygame.time.get_ticks()
            if current_time - last_move_time > 300:
                if detector.movement == "Down":
                    selected = (selected + 1) % len(buttons)
                elif detector.movement == "Up":
                    selected = (selected - 1) % len(buttons)
                last_move_time = current_time

        if detector.is_grab:
            if buttons[selected] == "Start":
                area.layout_game_area()
            else:
                detector.start_calibration()

        pygame.display.flip()
        clock.tick(30)

layout_menu()