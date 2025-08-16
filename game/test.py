import pygame
import random
import os
import os.path as path
import setting
from hand_detection import HandDetector
pygame.init()

# 屏幕设置
WIDTH = 450
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ")
detector = HandDetector()

# 颜色定义
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# 加载图像
def load_image(name, scale=1):
    img = pygame.Surface((50, 40))
    img.fill(BLUE if name == "player" else RED)
    return img


# 玩家精灵
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        image = pygame.image.load(path.join(setting.img_folder,"hero.png"))
        self.image = pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        # 初始像素坐标，居中
        self.rect.x = 2 * 75
        self.rect.y = 30 + 8 * 60
        self.health = 100

    def update(self):
        keys = pygame.key.get_pressed()
        speed = 5
        if keys[pygame.K_LEFT]:
            self.rect.x -= speed
        if keys[pygame.K_RIGHT]:
            self.rect.x += speed
        if keys[pygame.K_UP]:
            self.rect.y -= speed
        if keys[pygame.K_DOWN]:
            self.rect.y += speed
        # 限制移动范围
        if self.rect.x < -20:
            self.rect.x = -20
        if self.rect.x > 390:
            self.rect.x = 390
        if self.rect.y < 30:
            self.rect.y = 30
        if self.rect.y > 650:
            self.rect.y = 650

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)

# 敌人类
class Enemy(pygame.sprite.Sprite):
    def __init__(self, speed=0, bg_offset=0):
        super().__init__()
        image = pygame.image.load(path.join(setting.img_folder,"peashooter_candidate_0.png"))
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
        self.rect.y += self.speedy / 60  # move per frame
        # Check if out of screen
        if self.rect.top > HEIGHT:
            if self.out_time is None:
                self.out_time = time.time()
            elif time.time() - self.out_time > 1:
                self.kill()
        else:
            self.out_time = None
    def shoot(self, bullet_speed):
        bullet = Bullet(self.rect.centerx, self.rect.bottom, bullet_speed, color=RED)
        all_sprites.add(bullet)
        bullets.add(bullet)
    def try_shoot(self, bullet_speed, now):
        if not hasattr(self, 'last_shoot_time'):
            self.last_shoot_time = now
        if now - self.last_shoot_time >= 3:
            self.shoot(bullet_speed)
            self.last_shoot_time = now
class Peashooter(Enemy):
    def __init__(self):
        super().__init__()
        image = pygame.image.load(path.join(setting.img_folder,"peashooter_candidate_0.png"))
        self.image = pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        self.rect.x = random.randrange(WIDTH - self.rect.width)
        self.rect.y = random.randrange(-100, -40)
        self.speedy = random.randrange(1, 5)
        self.speedx = random.randrange(-2, 2)

# 子弹类
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
        # 超出屏幕自动销毁
        if self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()


# 创建精灵组
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()


class GameArea:
    def layout_game_area(self):
        # 创建玩家
        player = Player()
        all_sprites.add(player)

        # 创建敌人
        for i in range(4):
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)

        # 分数
        score = 0
        font = pygame.font.SysFont(None, 36)

        # 游戏循环
        clock = pygame.time.Clock()
        running = True
        import time
        # 加载背景图像
        bg_img = pygame.image.load(path.join(setting.img_folder, "background2.png")).convert()
        bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
        bg_y1 = 0
        bg_y2 = -HEIGHT
        BG_SCROLL_SPEED = 60  # 每次滚动的像素

        # --- Difficulty and enemy refresh parameters ---
        BASE_SCROLL_SPEED = 60  # initial scroll speed (pixels/sec)
        BASE_ENEMY_SPEED = 0    # initial enemy speed (pixels/sec)
        BASE_MAX_ENEMIES = 2
        DIFFICULTY_INTERVAL = 1  # seconds per difficulty up
        ENEMY_CHECK_INTERVAL = 2  # seconds per enemy check

        difficulty = 0
        scroll_speed = BASE_SCROLL_SPEED
        enemy_speed = BASE_ENEMY_SPEED
        max_enemies = BASE_MAX_ENEMIES

        start_time = time.time()
        last_difficulty_time = start_time
        last_enemy_check_time = start_time
        bg_scroll_speed_per_frame = scroll_speed / 60
        shoot_cooldown = 200
        last_shoot_time = 0

        while running:
            # 保持循环以正确的速度运行
            clock.tick(60)

            detector.update()
            
            # 处理输入事件
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                
                current_time = pygame.time.get_ticks()

                if detector.is_grab:
                    if current_time - last_shoot_time > shoot_cooldown:
                        player.shoot()
                        last_shoot_time = current_time
                
            # --- Difficulty increases every DIFFICULTY_INTERVAL seconds ---
            now = time.time()
            if now - last_difficulty_time >= DIFFICULTY_INTERVAL:
                difficulty += 1
                max_enemies = BASE_MAX_ENEMIES + difficulty // 10
                scroll_speed = BASE_SCROLL_SPEED + difficulty
                enemy_speed = BASE_ENEMY_SPEED + difficulty
                bg_scroll_speed_per_frame = scroll_speed // 60
                # 更新所有现存敌人的速度
                for enemy in enemies:
                    enemy.speedy = enemy_speed
                last_difficulty_time = now

            # Smooth background scroll by pixel per frame
            bg_y1 += bg_scroll_speed_per_frame
            bg_y2 += bg_scroll_speed_per_frame
            # Two background images loop
            if bg_y1 >= HEIGHT:
                bg_y1 = bg_y2 - HEIGHT
            if bg_y2 >= HEIGHT:
                bg_y2 = bg_y1 - HEIGHT
            # Enemies move with background scroll (pixel-based)
            for enemy in enemies:
                enemy.scroll_with_bg(bg_scroll_speed_per_frame)

            # --- Enemy supplement check every ENEMY_CHECK_INTERVAL seconds ---
            if now - last_enemy_check_time >= ENEMY_CHECK_INTERVAL:
                missing = max_enemies - len(enemies)
                for _ in range(missing):
                    if random.random() < 0.5:
                        # 新敌人y坐标与当前背景偏移对齐
                        enemy = Enemy(speed=enemy_speed, bg_offset=bg_y1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                last_enemy_check_time = now
            
            # 敌人发射子弹
            bullet_speed = bg_scroll_speed_per_frame * 2  # 卷轴速度两倍
            now = time.time()
            for enemy in enemies:
                enemy.try_shoot(bullet_speed, now)
            # Update
            all_sprites.update()

            # Check if bullet hits player (only enemy bullets, i.e. color=RED)
            for bullet in bullets:
                if bullet.image.get_at((0,0)) == RED:
                    if player.rect.colliderect(bullet.rect):
                        player.health -= 10
                        bullet.kill()

            # Check if bullet hits enemy (only allow player子弹, 这里假设player子弹为GREEN)
            hits = pygame.sprite.groupcollide(enemies, bullets, True, False)
            for enemy, hit_bullets in hits.items():
                # 只有绿色子弹才算击中敌人
                for bullet in hit_bullets:
                    if bullet.image.get_at((0,0)) == GREEN:
                        score += 10
                        bullet.kill()
            
            # No collision damage between enemies and player
            # hits = pygame.sprite.spritecollide(player, enemies, False)
            # if hits:
            #     player.health -= 1
            #     if player.health <= 0:
            #         running = False
            
            # 渲染
            screen.fill(BLACK)
            screen.blit(bg_img, (0, bg_y1))
            screen.blit(bg_img, (0, bg_y2))
            all_sprites.draw(screen)
            
            # 显示分数
            score_text = font.render(f"score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            # 显示生命值
            health_text = font.render(f"hp: {player.health}", True, WHITE)
            screen.blit(health_text, (10, 50))
            
            # 刷新屏幕
            pygame.display.flip()

pygame.quit()
