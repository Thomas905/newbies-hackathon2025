from hand_detection import HandDetector 
from game import GameArea, Settings
from support import *
import pygame
import os
import os.path as path
import sys

snd_folder = path.join("entity", "snd")
# 声音文件变量
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
    play_bgm(BGM_MENU)
    running = True
    selected = 0
    buttons = ["Start", "Settings", "Exit"]
    last_move_time = 0 
    last_grab = False
    current_mode = get_mode()
    show_rage_quit_msg = False
    rage_quit_timer = 0
    rage_quit_sfx_played = False  # 新增变量，防止多次播放

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
                if not rage_quit_sfx_played:
                    play_sfx(SFX_QUIT)
                    rage_quit_sfx_played = True

        new_grab = detector.is_grab and not last_grab and detector.hand_center
        last_grab = detector.is_grab

        for i, btn in enumerate(buttons):
            basic_button(btn, 125, 250 + i * 120, selected == i)

        # Event handling
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            # if mode == ControlMode.KEY and event.type == pygame.KEYDOWN:
            if event.type == pygame.KEYDOWN:
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
            if elapsed < 2000:
                msg = font.render("Rage quit detected!", True, (255, 0, 0))
                screen.blit(msg, (SCREEN_WIDTH // 2 - msg.get_width() // 2, 100))
            else:
                show_rage_quit_msg = False
                rage_quit_sfx_played = False  # 允许下次rage quit时再次播放
        pygame.display.flip()
        clock.tick(30)
layout_menu()
