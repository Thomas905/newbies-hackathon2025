import pygame
import random
import os
import os.path as path
import setting
import time
from hand_detection import HandDetector
from support import get_mode, set_mode, ControlMode
pygame.init()

# Globals & Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()
playing_mode_set = 0

# Screen settings
WIDTH = 450
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ")
detector = HandDetector()

# Font
font = pygame.font.SysFont("consolas", 32, bold=True)

# Color definitions
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)
BG_COLOR = (15, 15, 20)
HIGHLIGHT = (0, 200, 255)
NORMAL = (200, 50, 50)

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
        self.hp = 5
        self.last_shoot_time = 0
        self.cd_hint = False  # Whether to show "CD" above player

    def update(self):
        detector.update()

        if detector.hand_center:
            hand_x, hand_y = detector.hand_center
            hand_x = screen.get_width() - hand_x  

            self.rect.centerx = hand_x
            self.rect.centery = hand_y

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top, 5)
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
        pass
    def try_shoot(self, bullet_speed, now):
        pass

class Peashooter(Enemy):
    def __init__(self, speed=0, bg_offset=0):
        super().__init__(speed=speed, bg_offset=bg_offset)
        image = pygame.image.load(path.join(setting.img_folder,"peashooter_candidate_0.png"))
        self.image = pygame.transform.scale(image,(50,60))
        self.rect = self.image.get_rect()
        # Set random position (like Enemy)
        self.grid_x = random.randint(0, 5)
        self.grid_y = random.randint(-6, 0)
        self.rect.x = 20 + self.grid_x * 75
        self.rect.y = 5 + self.grid_y * 60

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
        if self.rect.top > HEIGHT or self.rect.bottom < 0:
            self.kill()

class GameArea:
    def layout_game_area(self):
        # Create player
        player = Player()
        all_sprites.add(player)

        # Create enemies
        for i in range(4):
            enemy = Peashooter()
            all_sprites.add(enemy)  # <-- add enemy to all_sprites
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
        
        shoot_cooldown = 200
        last_shoot_time = 0

        while running:
            # Keep loop running at the right speed
            clock.tick(60)
    
            detector.update()
            
            # Handle input events
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
                    if random.random() < 0.8:
                        # New enemy y coordinate aligns with current background offset
                        enemy = Peashooter(speed=enemy_speed, bg_offset=bg_y1)
                        all_sprites.add(enemy)
                        enemies.add(enemy)
                last_enemy_check_time = now
            
            # Enemies shoot bullets
            bullet_speed = bg_scroll_speed_per_frame * 3  # 3 times of the scroll speed
            now = time.time()
            for enemy in enemies:
                enemy.try_shoot(bullet_speed, 0.1 * random.randrange(0, 10) + now)
            # Update
            all_sprites.update()

            # Check if bullet hits player (only enemy bullets, i.e. color=RED)
            for bullet in bullets:
                if bullet.image.get_at((0,0)) == RED:
                    if player.rect.colliderect(bullet.rect):
                        player.hp -= 1
                        bullet.kill()
                        if player.hp <= 0:
                            running = False
            
            # Check if bullet hits enemy (only allow player bullets, here assume player bullet is GREEN)
            hits = pygame.sprite.groupcollide(enemies, bullets, True, False)
            for enemy, hit_bullets in hits.items():
                # Only green bullets (including PlayerBullet) count as hitting the enemy
                for bullet in hit_bullets:
                    if bullet.image.get_at((0,0)) == GREEN:
                        score += 10
                        # bullet.kill()  # <-- Remove this line, don't kill bullet on hit
            

            # No collision damage between enemies and player
            # hits = pygame.sprite.spritecollide(player, enemies, False)
            # if hits:
            #     player.hp -= 1
            #     if player.hp <= 0:
            #         running = False
            
            # Render
            screen.fill(BLACK)
            screen.blit(bg_img, (0, bg_y1))
            screen.blit(bg_img, (0, bg_y2))
            all_sprites.draw(screen)
            
            # Display score
            score_text = font.render(f"score: {score}", True, WHITE)
            screen.blit(score_text, (10, 10))
            
            # Display hp
            hp_text = font.render(f"hp: {player.hp}", True, WHITE)
            screen.blit(hp_text, (10, 50))
            
            # Refresh screen
            pygame.display.flip()

class Settings:
    def __init__(self):
        self.options = ["Hand Tracking", "Arrow Keys"]
        self.selected_index = 0
        self.last_move_time = 0
        self.cooldown = 300

    def handle_navigation_key(self):
        keys = pygame.key.get_pressed()
        current_time = pygame.time.get_ticks()

        if keys[pygame.K_UP] and current_time - self.last_move_time > self.cooldown:
            self.selected_index = (self.selected_index - 1) % len(self.options)
            self.last_move_time = current_time
        elif keys[pygame.K_DOWN] and current_time - self.last_move_time > self.cooldown:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            self.last_move_time = current_time

    def handle_navigation_hand(self):
        current_time = pygame.time.get_ticks()
        if detector.movement and detector.hand_center:
            if current_time - self.last_move_time > self.cooldown:
                if detector.movement == "Down":
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                elif detector.movement == "Up":
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                self.last_move_time = current_time

    def handle_grab(self):
        if detector.is_grab:
            selected = self.options[self.selected_index]
            if selected == "Hand Tracking":
                set_mode(ControlMode.HAND)
            elif selected == "Arrow Keys":
                set_mode(ControlMode.KEY)
            print(f"Mode changé en: {selected}")
            return True
        return False

    def layout_setting(self):
        pygame.display.set_caption("Settings")
        clock = pygame.time.Clock()
        running = True

        while running:
            screen.fill(BG_COLOR)
            detector.update()

            title = font.render("⚙ SETTINGS ⚙", True, HIGHLIGHT)
            screen.blit(title, (WIDTH // 2 - title.get_width() // 2, 60))

            for i, opt in enumerate(self.options):
                color = HIGHLIGHT if i == self.selected_index else NORMAL
                text = font.render(opt, True, color)
                shadow = font.render(opt, True, (color[0] // 3, color[1] // 3, color[2] // 3))
                y = 200 + i * 100
                screen.blit(shadow, (WIDTH // 2 - shadow.get_width() // 2 + 4, y + 4))
                screen.blit(text, (WIDTH // 2 - text.get_width() // 2, y))

            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                elif (event.type == pygame.KEYDOWN and event.key == pygame.K_RETURN) or detector.is_grab:
                    selected = self.options[self.selected_index]
                    if selected == "Hand Tracking":
                        set_mode(ControlMode.HAND)
                    elif selected == "Arrow Keys":
                        set_mode(ControlMode.KEY)
                    print(f"Mode changé en: {selected}")
                    
                    running = False

            if get_mode() == ControlMode.HAND:
                self.handle_navigation_hand()
            elif get_mode() == ControlMode.KEY:
                self.handle_navigation_key()

            pygame.display.flip()
            clock.tick(30)

