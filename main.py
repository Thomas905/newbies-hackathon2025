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

class GameArea:
    def __init__(self, detector):
        self.detector = detector
        self.all_sprites = pygame.sprite.Group()
        self.enemies = pygame.sprite.Group()
        self.bullets = pygame.sprite.Group()
        self.player = None

    def layout_game_area(self):
        # ...existing code...
        import time
        # Load background image
        bg_img = pygame.image.load(path.join(IMG_FOLDER, "background2.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (SCREEN_WIDTH, SCREEN_HEIGHT))
        bg_y1 = 0
        bg_y2 = -SCREEN_HEIGHT

        difficulty = 0
        scroll_speed = BASE_SCROLL_SPEED
        enemy_speed = BASE_ENEMY_SPEED
        max_enemies = BASE_MAX_ENEMIES

        start_time = time.time()
        last_difficulty_time = start_time
        last_enemy_check_time = start_time
        bg_scroll_speed_per_frame = scroll_speed / FRAME_RATE

        shoot_cooldown = SHOOT_CD
        last_shoot_time = 0

        # Create player
        self.player = Player(self.detector, self.bullets, bg_scroll_speed_per_frame)
        self.all_sprites.add(self.player)

        # Create enemies
        for _ in range(4):
            enemy = Peashooter()
            self.all_sprites.add(enemy)
            self.enemies.add(enemy)

        score = 0
        font = pygame.font.SysFont(None, 36)
        running = True

        while running:
            clock.tick(FRAME_RATE)
            self.detector.update()

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            current_time = pygame.time.get_ticks()
            if self.detector.is_grab:
                if current_time - last_shoot_time > shoot_cooldown:
                    self.player.shoot()
                    last_shoot_time = current_time

            now = time.time()
            if now - last_difficulty_time >= DIFFICULTY_INTERVAL:
                difficulty += 1
                max_enemies = BASE_MAX_ENEMIES + difficulty // 10
                scroll_speed = BASE_SCROLL_SPEED + difficulty
                enemy_speed = BASE_ENEMY_SPEED + difficulty
                bg_scroll_speed_per_frame = scroll_speed / FRAME_RATE
                for enemy in self.enemies:
                    enemy.speedy = enemy_speed
                last_difficulty_time = now

            bg_y1 += bg_scroll_speed_per_frame
            bg_y2 += bg_scroll_speed_per_frame
            if bg_y1 >= SCREEN_HEIGHT:
                bg_y1 = bg_y2 - SCREEN_HEIGHT
            if bg_y2 >= SCREEN_HEIGHT:
                bg_y2 = bg_y1 - SCREEN_HEIGHT
            for enemy in self.enemies:
                enemy.scroll_with_bg(bg_scroll_speed_per_frame)

            if now - last_enemy_check_time >= ENEMY_CHECK_INTERVAL:
                missing = max_enemies - len(self.enemies)
                for _ in range(missing):
                    if random.random() < 0.8:
                        enemy = Peashooter(speed=enemy_speed, bg_offset=bg_y1)
                        self.all_sprites.add(enemy)
                        self.enemies.add(enemy)
                last_enemy_check_time = now

            bullet_speed = bg_scroll_speed_per_frame * 3
            now = time.time()
            for enemy in self.enemies:
                enemy.try_shoot(bullet_speed, 0.1 * random.randrange(0, 10) + now, self.all_sprites, self.bullets)
            self.all_sprites.update()
            self.bullets.update()

            for bullet in self.bullets:
                if bullet.image.get_at((0,0)) == RED:
                    if self.player.rect.colliderect(bullet.rect):
                        self.player.hp -= 1
                        bullet.kill()
                        if self.player.hp <= 0:
                            running = False

            hits = pygame.sprite.groupcollide(self.enemies, self.bullets, True, False)
            for enemy, hit_bullets in hits.items():
                for bullet in hit_bullets:
                    if bullet.image.get_at((0,0)) == GREEN:
                        score += 10

            screen.fill(BLACK)
            screen.blit(bg_img, (0, bg_y1))
            screen.blit(bg_img, (0, bg_y2))
            self.all_sprites.draw(screen)
            self.bullets.draw(screen)

            score_text = font.render(f"score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            hp_text = font.render(f"hp: {self.player.hp}", True, WHITE)
            screen.blit(hp_text, (10, 50))

            if getattr(self.player, 'cd_hint', False):
                cd_text = font.render("CD", True, RED)
                cd_x = self.player.rect.centerx - cd_text.get_width() // 2
                cd_y = self.player.rect.top - cd_text.get_height() - 5
                screen.blit(cd_text, (cd_x, cd_y))

            pygame.display.flip()

def layout_menu(detector):
    running = True
    selected = 0
    buttons = ["Start", "Settings"]
    last_move_time = 0
    area = GameArea(detector)
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

def main():
    detector = HandDetector()
    layout_menu(detector)

if __name__ == "__main__":
    main()