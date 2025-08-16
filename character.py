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
        # 冷却结束自动隐藏cd_hint
        if self.cd_hint and (time.time() - self.last_shoot_time >= 1.0):
            self.cd_hint = False

    def shoot(self, bullet_type='normal'):
        now = time.time()
        if now - self.last_shoot_time < 1.0:  # 冷却1秒
            self.cd_hint = True
            return
        self.cd_hint = False
        self.last_shoot_time = now
        # 计算落点
        bullet_x = self.rect.centerx
        bullet_y = self.rect.centery - 120
        # 添加PendingPlayerBullet
        pending = PendingPlayerBullet(
            bullet_x,
            bullet_y,
            self.bg_scroll_speed_per_frame,
            self.bullets_group,
            self.bullets_group  # 这里all_sprites会在main.py中补充
        )
        self.bullets_group.add(pending)
        # 注意：main.py中也要将pending加入all_sprites

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
        # 敌人子弹，速度为bullet_speed，伤害类型1
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, bullet_speed)
        all_sprites.add(bullet)
        bullets_group.add(bullet)

    def try_shoot(self, bullet_speed, now, all_sprites, bullets_group):
        if not hasattr(self, 'last_shoot_time'):
            self.last_shoot_time = now
        if now - self.last_shoot_time >= 3:
            self.shoot(bullet_speed, all_sprites, bullets_group)
            self.last_shoot_time = now

class Bullet(pygame.sprite.Sprite):
    """
    Base class for bullets, can be used for both player and enemy bullets.
    """
    def __init__(self, x, y, speedx, speedy, damage_type, color, size=(5, 5)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedx = speedx
        self.speedy = speedy
        self.damage_type = damage_type  # 0: 对敌, 1: 对玩家

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()

class PendingPlayerBullet(pygame.sprite.Sprite):
    """
    只做落点感叹号提示，不参与碰撞和伤害。用文字"!"显示。
    """
    def __init__(self, x, y, speedy, bullets_group, all_sprites):
        super().__init__()
        self.x = x
        self.y = y
        self.speedy = speedy
        self.bullets_group = bullets_group
        self.all_sprites = all_sprites
        self.spawn_time = time.time()
        # 用文字"!"作为感叹号
        font = pygame.font.SysFont(None, 48)
        self.image = font.render("!", True, (255, 0, 0))
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.centery = y

    def update(self):
        # 0.2s后生成真正的玩家子弹，仅生成，不参与碰撞
        if time.time() - self.spawn_time > 0.2:
            bullet = PlayerBullet(self.x, self.y, self.speedy)
            self.bullets_group.add(bullet)
            self.all_sprites.add(bullet)
            self.kill()

class PlayerBullet(Bullet):
    """
    50 * 50, harm type 0, only harm enemy, lifecycle 0.5s
    """
    def __init__(self, x, y, speedy):
        super().__init__(x, y, 0, speedy, damage_type=0, color=GREEN, size=(50, 50))
        self.spawn_time = time.time()

    def update(self):
        super().update()
        if time.time() - self.spawn_time > 0.5:
            self.kill()

class EnemyBullet(Bullet):
    """
    5 * 5, harm type 1, only harm player, destroy when hit player
    支持贴图PB01.gif
    """
    def __init__(self, x, y, speedy):
        super().__init__(x, y, 0, speedy, damage_type=1, color=RED, size=(5, 5))
        img_path = path.join(IMG_FOLDER, "PB01.gif")
        if path.exists(img_path):
            image = pygame.image.load(img_path).convert_alpha()
            image = pygame.transform.scale(image, (24, 24))
            self.image = image
            self.rect = self.image.get_rect()
            self.rect.centerx = x
            self.rect.top = y

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedy
        if self.rect.top > SCREEN_HEIGHT or self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > SCREEN_WIDTH:
            self.kill()