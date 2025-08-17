from hand_detection import HandDetector 
from game import GameArea, Settings
from support import *
import pygame
import os
import os.path as path
import sys

snd_folder = path.join("entity", "snd")
BGM_MENU = path.join(snd_folder, "bgm_menu.mp3")
BGM_GAME = path.join(snd_folder, "bgm_game.mp3")
SFX_MENU_ENTER = path.join(snd_folder, "menu_enter.mp3")
SFX_MENU_SWITCH_ON = path.join(snd_folder, "menu_switch_on.mp3")
SFX_MENU_SWITCH_OFF = path.join(snd_folder, "menu_switch_off.mp3")
SFX_QUIT = path.join(snd_folder, "quit.mp3")

pygame.init()
pygame.mixer.init()

def play_bgm(bgm_path):
    pygame.mixer.music.stop()
    if os.path.exists(bgm_path):
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.play(-1)

def play_sfx(sfx_path):
    if os.path.exists(sfx_path):
        try:
            sound = pygame.mixer.Sound(sfx_path)
            sound.play()
        except Exception:
            pass

# Screen
SCREEN_WIDTH = 450
SCREEN_HEIGHT = 720
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Wrist in Peas")
clock = pygame.time.Clock()
font = pygame.font.SysFont("consolas", 32, bold=True)

# Colors
WHITE = (255, 255, 255)
DARK_GREEN = (34, 139, 34)
LIGHT_GREEN = (50, 205, 50)
SHADOW_COLOR = (0, 0, 0, 100)
SKY_BLUE = (135, 206, 235)
GRASS_GREEN = (60, 179, 113)

def basic_button(text, x, y, selected):
    width, height = 245, 90

    button_surf = pygame.Surface((width, height), pygame.SRCALPHA)

    border_color = (100, 255, 100, 180) if selected else (50, 150, 50, 120)

    bg_color = (0, 100, 0, 80) if selected else (0, 50, 0, 60)

    pygame.draw.rect(button_surf, bg_color, (0, 0, width, height), border_radius=15)

    pygame.draw.rect(button_surf, border_color, (0, 0, width, height), width=3, border_radius=15)

    txt = font.render(text, True, (255, 255, 255))
    rect = txt.get_rect(center=(width // 2, height // 2))
    button_surf.blit(txt, rect)

    screen.blit(button_surf, (x, y))

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
    rage_quit_sfx_played = False

    menu_bg = pygame.image.load("assets/images/Background/background.png").convert()
    menu_bg = pygame.transform.scale(menu_bg, (SCREEN_WIDTH, SCREEN_HEIGHT))

    btn_positions = [200, 315, 428]  

    if current_mode == ControlMode.HAND:
        detector.enabled = False
        detector.start_calibration()
        detector.enabled = True

    while running:
        # Background
        screen.blit(menu_bg, (0, 0))

        if getattr(detector, "enabled", True):
            detector.update()
            if getattr(detector, "is_fuck", False):
                show_rage_quit_msg = True
                rage_quit_timer = pygame.time.get_ticks()
                detector.is_fuck = False
                if not rage_quit_sfx_played:
                    play_sfx(SFX_QUIT)
                    rage_quit_sfx_played = True

        new_grab = detector.is_grab and not last_grab and detector.hand_center
        last_grab = detector.is_grab

        for i, btn in enumerate(buttons):
            basic_button(btn, 100, btn_positions[i], selected == i)

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_DOWN:
                    selected = (selected + 1) % len(buttons)
                    play_sfx(SFX_MENU_SWITCH_OFF)
                elif event.key == pygame.K_UP:
                    selected = (selected - 1) % len(buttons)
                    play_sfx(SFX_MENU_SWITCH_ON)
                elif event.key == pygame.K_RETURN:
                    play_sfx(SFX_MENU_ENTER)
                    if buttons[selected] == "Start":
                        play_bgm(BGM_GAME)
                        area.layout_game_area()
                        play_bgm(BGM_MENU)
                    elif buttons[selected] == "Settings":
                        settings.layout_setting()
                    elif buttons[selected] == "Exit":
                        running = False

        if detector.hand_center:
            current_time = pygame.time.get_ticks()
            if detector.movement and current_time - last_move_time > 300:
                if detector.movement == "Down":
                    selected = (selected + 1) % len(buttons)
                elif detector.movement == "Up":
                    selected = (selected - 1) % len(buttons)
                last_move_time = current_time

            if new_grab and current_time - last_move_time > 300:
                play_sfx(SFX_MENU_ENTER)
                if buttons[selected] == "Start":
                    play_bgm(BGM_GAME)
                    area.layout_game_area()
                    play_bgm(BGM_MENU)
                elif buttons[selected] == "Settings":
                    settings.layout_setting()
                elif buttons[selected] == "Exit":
                    running = False
                last_move_time = current_time
        if show_rage_quit_msg:
            elapsed = pygame.time.get_ticks() - rage_quit_timer

            if elapsed < 6000:
                msg = font.render("Rage quit detected !", True, (255, 0, 0))
                screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 100))
            else:
                show_rage_quit_msg = False
                rage_quit_sfx_played = False  

        pygame.display.flip()
        clock.tick(30)

layout_menu()
