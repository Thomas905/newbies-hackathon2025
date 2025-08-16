import pygame
import os.path as path
import time
import random

from support import *

# Player sprite
class Player(pygame.sprite.Sprite):
    def __init__(self, detector, bullets_group, bg_scroll_speed_per_frame):
        super().__init__()
        image = pygame.image.load(path.join(IMG_FOLDER,"hero.png"))
        self.image = pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        # Initial pixel coordinates, centered
        self.rect.x = 2 * 75
        self.rect.y = 30 + 8 * 60
        self.hp = 5
        self.last_shoot_time = 0
        self.cd_hint = False
        self.detector = detector
        self.bullets_group = bullets_group
        self.bg_scroll_speed_per_frame = bg_scroll_speed_per_frame

    def update(self):
        self.detector.update()
        if self.detector.hand_center:
            hand_x, hand_y = self.detector.hand_center
            hand_x = SCREEN_WIDTH - hand_x
            self.rect.centerx = hand_x
            self.rect.centery = hand_y

    def shoot(self, bullet_type='normal'):
        now = time.time()
        if now - self.last_shoot_time < 0.3:
            self.cd_hint = True
            return
        self.cd_hint = False
        self.last_shoot_time = now
        if bullet_type == 'big':
            bullet = PlayerBullet(
                self.rect.centerx,
                self.rect.centery - 120,
                self.bg_scroll_speed_per_frame,
                color=GREEN
            )
        else:
            bullet = Bullet(self.rect.centerx, self.rect.top, -self.bg_scroll_speed_per_frame, color=GREEN)
        self.bullets_group.add(bullet)

# Enemy class
class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed=0, bg_offset=0):
        super().__init__()
        image = pygame.image.load(path.join(IMG_FOLDER,"peashooter_candidate_0.png"))
        self.image = pygame.transform.scale(image,(50,60))
        self.rect = self.image.get_rect()
        # Random grid position
        self.grid_x = random.randint(0, 5)
        self.grid_y = random.randint(-6, 0)
        self.rect.x = 20 + self.grid_x * 75
        self.rect.y = 5 + self.grid_y * 60 + int(bg_offset) % 60
        self.speedx = 0
        self.speedy = speed  # enemy speed (pixels/sec)
        self.out_time = None

    def update_position(self, bg_offset=0):
        self.rect.x = 20 + self.grid_x * 75
        self.rect.y = 5 + self.grid_y * 60 + int(bg_offset) % 60

    def scroll_with_bg(self, scroll_amount):
        self.rect.y += scroll_amount

    def update(self):
        # Enemy moves by its own speed (difficulty)
        self.rect.y += self.speedy / FRAME_RATE  # move per frame
        # Check if out of screen
        if self.rect.top > SCREEN_HEIGHT:
            if self.out_time is None:
                self.out_time = time.time()
            elif time.time() - self.out_time > 1:
                self.kill()
        else:
            self.out_time = None

    def shoot(self, bullet_speed, all_sprites, bullets_group):
        pass

    def try_shoot(self, bullet_speed, now, all_sprites, bullets_group):
        pass

class Peashooter(Enemy):
    def __init__(self, speed=0, bg_offset=0):
        super().__init__(speed=speed, bg_offset=bg_offset)
        image = pygame.image.load(path.join(IMG_FOLDER,"peashooter_candidate_0.png"))
        self.image = pygame.transform.scale(image,(50,60))
        self.rect = self.image.get_rect()
        # Set random position (like Enemy)
        self.grid_x = random.randint(0, 5)
        self.grid_y = random.randint(-6, 0)
        self.rect.x = 20 + self.grid_x * 75
        self.rect.y = 5 + self.grid_y * 60

    def shoot(self, bullet_speed, all_sprites, bullets_group):
        bullet = Bullet(self.rect.centerx, self.rect.bottom, bullet_speed, color=RED)
        all_sprites.add(bullet)
        bullets_group.add(bullet)

    def try_shoot(self, bullet_speed, now, all_sprites, bullets_group):
        if not hasattr(self, 'last_shoot_time'):
            self.last_shoot_time = now
        if now - self.last_shoot_time >= 3:
            self.shoot(bullet_speed, all_sprites, bullets_group)
            self.last_shoot_time = now

class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speedy, color=GREEN):
        super().__init__()
        self.image = pygame.Surface((5, 5))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedy = speedy

    def update(self):
        self.rect.y += self.speedy
        # Destroy automatically if out of screen
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()

class PlayerBullet(Bullet):
    def __init__(self, x, y, speedy, color=GREEN):
        super().__init__(x, y, speedy, color)
        self.image = pygame.Surface((50, 50))
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y
        self.spawn_time = time.time()

    def update(self):
        self.rect.y += self.speedy
        # Auto-destroy after 0.5s
        if time.time() - self.spawn_time > 0.5:
            self.kill()
        # Still destroy if out of screen
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0:
            self.kill()