
import pygame
import random
import os.path as path

from support import *
from character import Player, Peashooter
from hand_detection import HandDetector

pygame.init()

screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NewBies Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)

def basic_button(text, x, y, selected):
    color = LIGHT_BLUE if selected else BLUE
    pygame.draw.rect(screen, color, (x, y, 200, 80))

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
        
def main():
    detector = HandDetector()
    layout_menu(detector)

if __name__ == "__main__":
    main()
