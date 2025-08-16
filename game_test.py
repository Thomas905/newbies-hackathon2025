import pygame, sys

from support import *
from background import Background
pygame.init()

# Globals Variables
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NewBies Game")
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

# Layout Menu
def layout_menu():
    running = True
    selected = 0
    buttons = ["Start", "Settings"]
    while running:

        basic_button("Start", 215, 362, selected == 0)
        basic_button("Settings", 215, 462, selected == 1)

        for event in pygame.event.get():
            screen.fill(BLACK)
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(buttons)
                elif event.key == pygame.K_RETURN:
                    if buttons[selected] == "Start":
                        layout_game_area()
                    else:
                        print("settoing")
        pygame.display.flip()

# Layout Game Area
def layout_game_area():
    running = True
    cols = 6
    rows = 12
    cell_width = SCREEN_WIDTH // cols #75PX
    cell_height = SCREEN_HEIGHT // rows #60PX
    background = Background("assets/images/background.png")

    center_col = cols // 2
    bottom_row = rows - 2

    player_col = center_col
    player_row = bottom_row


    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.MOUSEBUTTONDOWN:
                mouse_x, mouse_y = pygame.mouse.get_pos()
                col_clicked = mouse_x // cell_width
                row_clicked = mouse_y // cell_height
                print(f"Click case : X={col_clicked}, Y={row_clicked}")

            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    running = False
                elif event.key == pygame.K_LEFT:
                    if player_col > 0:
                        player_col -= 1
                elif event.key == pygame.K_RIGHT:
                    if player_col < cols - 1:
                        player_col += 1
                elif event.key == pygame.K_UP:
                    if player_row > 1:
                        player_row -= 1
                elif event.key == pygame.K_DOWN:
                    if player_row < rows - 2:
                        player_row += 1

            screen.fill(WHITE)

            # Design Rows
            for row in range(rows):
                for col in range(cols):
                    rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                    pygame.draw.rect(screen, BLACK, rect, 1)

            # Design Player
            center_rect = pygame.Rect(
                player_col * cell_width + 5,
                player_row * cell_height + 5,
                cell_width - 10,
                cell_height - 10
            )
            pygame.draw.rect(screen, RED, center_rect)

            pygame.display.flip()

        
layout_menu()