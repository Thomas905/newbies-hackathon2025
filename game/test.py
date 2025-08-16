import pygame
import random
import os
import os.path as path
import setting
pygame.init()

# Screen settings
WIDTH = 450
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ")

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Load image
def load_image(name, scale=1):
    img = pygame.Surface((50, 40))
    img.fill(BLUE if name == "player" else RED)
    return img


# Player sprite
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        image = pygame.image.load(path.join(setting.img_folder,"hero.png"))
        self.image = pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        # Initial pixel coordinates, centered
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
        # Limit movement range
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

# Enemy class
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

# Bullet class
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
        if self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()


# Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

# Create player
player = Player()
all_sprites.add(player)

# Create enemies
for i in range(4):
    enemy = Enemy()
    all_sprites.add(enemy)
    enemies.add(enemy)

# Score
score = 0
font = pygame.font.SysFont(None, 36)

# Game loop
clock = pygame.time.Clock()
running = True
import time
# Load background image
bg_img = pygame.image.load(path.join(setting.img_folder, "background2.png")).convert()
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
bg_y1 = 0
bg_y2 = -HEIGHT
BG_SCROLL_SPEED = 60  # pixels per scroll

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

while running:
    # Keep loop running at the right speed
    clock.tick(60)
    
    # Handle input events
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        '''
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()
        '''
    # --- Difficulty increases every DIFFICULTY_INTERVAL seconds ---
    now = time.time()
    if now - last_difficulty_time >= DIFFICULTY_INTERVAL:
        difficulty += 1
        max_enemies = BASE_MAX_ENEMIES + difficulty // 10
        scroll_speed = BASE_SCROLL_SPEED + difficulty
        enemy_speed = BASE_ENEMY_SPEED + difficulty
        bg_scroll_speed_per_frame = scroll_speed // 60
        # Update speed for all existing enemies
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
                # New enemy y coordinate aligns with current background offset
                enemy = Enemy(speed=enemy_speed, bg_offset=bg_y1)
                all_sprites.add(enemy)
                enemies.add(enemy)
        last_enemy_check_time = now
    
    # Enemies shoot bullets
    bullet_speed = bg_scroll_speed_per_frame * 2  # twice the scroll speed
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

    # Check if bullet hits enemy (only allow player bullets, here assume player bullet is GREEN)
    hits = pygame.sprite.groupcollide(enemies, bullets, True, False)
    for enemy, hit_bullets in hits.items():
        # Only green bullets count as hitting the enemy
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
    
    # Render
    screen.fill(BLACK)
    screen.blit(bg_img, (0, bg_y1))
    screen.blit(bg_img, (0, bg_y2))
    all_sprites.draw(screen)
    
    # Display score
    score_text = font.render(f"score: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # Display health
    health_text = font.render(f"hp: {player.health}", True, WHITE)
    screen.blit(health_text, (10, 50))
    
    # Refresh screen
    pygame.display.flip()

pygame.quit()
