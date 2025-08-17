import pygame
import random
import os
import os.path as path
import setting
import time
from hand_detection import HandDetector
from support import get_mode, set_mode, ControlMode
pygame.init()
pygame.mixer.init()

# 音乐与音效文件名变量
BGM_MENU = path.join(setting.snd_folder, "bgm_menu.mp3")
BGM_GAME = path.join(setting.snd_folder, "bgm_game.mp3")
# SFX_SHOOT = path.join(setting.snd_folder, "shoot.mp3")
SFX_START = path.join(setting.snd_folder, "start.mp3")
SFX_HIT = path.join(setting.snd_folder, "hit.mp3")
SFX_MENU_ENTER = path.join(setting.snd_folder, "menu_enter.mp3")
SFX_MENU_SWITCH_ON = path.join(setting.snd_folder, "menu_switch_on.mp3")
SFX_MENU_SWITCH_OFF = path.join(setting.snd_folder, "menu_switch_off.mp3")
SFX_QUIT = path.join(setting.snd_folder, "quit.mp3")  # 新增：退出音效

# Globals & Create sprite groups
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets_0 = pygame.sprite.Group()
bullets_1 = pygame.sprite.Group()
bombs = pygame.sprite.Group()  # 新增：用于管理所有炸弹

playing_mode_set = 0

# Screen settings
WIDTH = 450
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))

# 设置窗口icon
icon_path = path.join(setting.img_folder, "icon.png")
if os.path.exists(icon_path):
    icon_img = pygame.image.load(icon_path)
    pygame.display.set_icon(icon_img)

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


def play_bgm(bgm_path):
    pygame.mixer.music.stop()
    if os.path.exists(bgm_path):
        pygame.mixer.music.load(bgm_path)
        pygame.mixer.music.play(-1)  # 循环播放

def play_sfx(sfx_path):
    if os.path.exists(sfx_path):
        try:
            sound = pygame.mixer.Sound(sfx_path)
            sound.play()
        except Exception:
            pass

# Player sprite
class Player(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        gif_path = path.join(setting.img_folder, "hero.gif")
        self.frames = []
        try:
            # 读取GIF所有帧
            import PIL.Image
            pil_img = PIL.Image.open(gif_path)
            for frame in range(0, pil_img.n_frames):
                pil_img.seek(frame)
                mode = pil_img.mode
                frame_img = pil_img.convert("RGBA")
                raw_str = frame_img.tobytes()
                size = frame_img.size
                py_img = pygame.image.frombuffer(raw_str, size, "RGBA")
                py_img = pygame.transform.scale(py_img, (100, 80))
                self.frames.append(py_img)
        except Exception as e:
            # 失败则用静态图
            image = pygame.image.load(gif_path)
            self.frames = [pygame.transform.scale(image, (75, 60))]
        self.frame_idx = 0
        self.frame_time = 0
        self.frame_interval = 100  # 每帧间隔(ms)
        self.image = self.frames[0]
        self.rect = self.image.get_rect()
        # Initial pixel coordinates, centered
        self.rect.x = 2 * 75
        self.rect.y = 30 + 8 * 60
        self.hp = 5
        self.last_shoot_time = 0
        self.cd_hint = False  # Whether to show "CD" above player
        self.last_bomb_time = 0  # 新增：炸弹冷却
        self.dead = False  # 新增：死亡状态

    def update(self):
        if get_mode() == ControlMode.HAND:
            detector.update()
            if detector.hand_center:
                hand_x, hand_y = detector.hand_center
                hand_x = screen.get_width() - hand_x  
                self.rect.centerx = hand_x
                self.rect.centery = hand_y

        elif get_mode() == ControlMode.KEY:
            keys = pygame.key.get_pressed()
            speed = 5  # vitesse de déplacement
            if keys[pygame.K_LEFT]:
                self.rect.x -= speed
            if keys[pygame.K_RIGHT]:
                self.rect.x += speed
            if keys[pygame.K_UP]:
                self.rect.y -= speed
            if keys[pygame.K_DOWN]:
                self.rect.y += speed

        # 动画帧切换
        now = pygame.time.get_ticks()
        if now - self.frame_time > self.frame_interval:
            self.frame_idx = (self.frame_idx + 1) % len(self.frames)
            self.image = self.frames[self.frame_idx]
            self.frame_time = now

        self.rect.clamp_ip(screen.get_rect())

    def shoot(self):
        bullet = PlayerBullet(self.rect.centerx, self.rect.top, 5)
        all_sprites.add(bullet)
        bullets_0.add(bullet)
        # play_sfx(SFX_SHOOT)  # 子弹射出音效

    def release_bomb(self):
        now = pygame.time.get_ticks()
        if now - self.last_bomb_time > 1000:  # 1s 冷却
            bomb_x = self.rect.centerx
            bomb_y = self.rect.centery - 60
            warning_img_path = path.join(setting.img_folder, "bomb_warning_0.png")
            explode_img_path = path.join(setting.img_folder, "bomb_explode_0.png")
            bomb = Bomb(
                bomb_x, bomb_y, player=self, enemies=enemies, damage_type=0,
                warning_time=0.3, radius=50,
                warning_img_path=warning_img_path,
                explode_img_path=explode_img_path
            )
            all_sprites.add(bomb)
            bombs.add(bomb)
            self.last_bomb_time = now

    def set_dead(self):
        if not self.dead:
            dead_img_path = path.join(setting.img_folder, "ZombieDie.gif")
            if os.path.exists(dead_img_path):
                self.image = pygame.transform.scale(
                    pygame.image.load(dead_img_path), self.image.get_size()
                )
            self.dead = True

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
        self.speedY = speed  # enemy speed (pixels/sec)
        self.out_time = None

    def update_position(self, bg_offset=0):
        self.rect.x = 20 + self.grid_x * 75
        self.rect.y = 5 + self.grid_y * 60 + int(bg_offset) % 60

    def scroll_with_bg(self, scroll_amount):
        self.rect.y += scroll_amount

    def update(self):
        # Enemy moves by its own speed (difficulty)
        self.rect.y += self.speedY / 60  # move per frame
        # Check if out of screen
        if self.rect.top > HEIGHT:
            if self.out_time is None:
                self.out_time = time.time()
            elif time.time() - self.out_time > 1:
                self.kill()
        else:
            self.out_time = None
    def shoot(self, bullet_speed):
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, bullet_speed)
        all_sprites.add(bullet)
        bullets_1.add(bullet)
        # play_sfx(SFX_SHOOT)  # 敌人射击也可用同一音效

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
        bullet = EnemyBullet(self.rect.centerx, self.rect.bottom, bullet_speed)
        all_sprites.add(bullet)
        bullets_1.add(bullet)
    def try_shoot(self, bullet_speed, now):
        if not hasattr(self, 'last_shoot_time'):
            self.last_shoot_time = now
            # play_sfx(SFX_SHOOT)  # 敌人射击也可用同一音效
        if now - self.last_shoot_time >= 3:
            self.shoot(bullet_speed)
            self.last_shoot_time = now
            

# Bullet class
class Bullet(pygame.sprite.Sprite):
    def __init__(self, x, y, speedx, speedY, damage_type, color, size=(10, 10)):
        super().__init__()
        self.image = pygame.Surface(size)
        self.image.fill(color)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.top = y
        self.speedx = speedx
        self.speedY = speedY
        self.damage_type = damage_type  # 0: 对敌, 1: 对玩家

    def update(self):
        self.rect.x += self.speedx
        self.rect.y += self.speedY
        if self.rect.top > HEIGHT or self.rect.bottom < 0 or self.rect.right < 0 or self.rect.left > WIDTH:
            self.kill()

class PlayerBullet(Bullet):
    def __init__(self, x, y, speedY):
        # 优先用PB01.gif
        img_path = path.join(setting.img_folder, "PB01.gif")
        if os.path.exists(img_path):
            size = 16
            image = pygame.image.load(img_path).convert_alpha()
            image = pygame.transform.scale(image, (size, size))
            super().__init__(x, y, 0, -speedY, damage_type=0, color=GREEN, size=(size, size))
            self.image = image
            self.rect = self.image.get_rect()
            self.rect.centerx = x
            self.rect.top = y
        else:
            super().__init__(x, y, 0, -speedY, damage_type=0, color=GREEN, size=(size, size))
        self.spawn_time = time.time()


class EnemyBullet(Bullet):
    def __init__(self, x, y, speedY):
        # 优先用PB11.gif
        size = 21
        img_path = path.join(setting.img_folder, "PB11.gif")
        if os.path.exists(img_path):
            image = pygame.image.load(img_path).convert_alpha()
            image = pygame.transform.scale(image, (size, size))
            super().__init__(x, y, 0, speedY, damage_type=1, color=RED, size=(size, size))
            self.image = image
            self.rect = self.image.get_rect()
            self.rect.centerx = x
            self.rect.top = y
        else:
            super().__init__(x, y, 0, speedY, damage_type=1, color=RED, size=(9, 9))
class Bomb(pygame.sprite.Sprite):
    def __init__(self, x, y, player, enemies, damage_type=0, warning_time=1.0, radius=60, 
                 warning_img_path=None, explode_img_path=None):
        super().__init__()
        self.x = x
        self.y = y
        self.radius = radius
        self.warning_time = warning_time
        self.start_time = time.time()
        self.state = "warning"
        self.damage_type = damage_type
        self.player = player
        self.enemies = enemies
        # 贴图路径
        self.warning_img = pygame.Surface((int(radius*1.0), int(radius*1.0)), pygame.SRCALPHA)
        self.explode_img = pygame.Surface((int(radius*2), int(radius*2)), pygame.SRCALPHA)
        if warning_img_path and os.path.exists(warning_img_path):
            self.warning_img = pygame.transform.scale(
                pygame.image.load(warning_img_path), (int(radius*1.0), int(radius*1.0))
            )
        if explode_img_path and os.path.exists(explode_img_path):
            self.explode_img = pygame.transform.scale(
                pygame.image.load(explode_img_path), (int(radius*2), int(radius*2))
            )
        self.image = self.warning_img
        self.rect = self.image.get_rect(center=(x, y))
        self.explode_duration = 0.2
        self.explode_start = None
        self.has_exploded = False

    def update(self):
        now = time.time()
        if self.state == "warning":
            if now - self.start_time >= self.warning_time:
                self.state = "explode"
                self.image = self.explode_img
                self.rect = self.image.get_rect(center=(self.x, self.y))
                self.explode_start = now
                # 只在爆炸瞬间检测一次
                if not self.has_exploded:
                    if self.damage_type == 0:
                        # 伤害敌人
                        for target in list(self.enemies):
                            dx = target.rect.centerx - self.x
                            dy = target.rect.centery - self.y
                            if dx*dx + dy*dy < self.radius*self.radius:
                                target.kill()
                    elif self.damage_type == 1:
                        # 伤害玩家
                        dx = self.player.rect.centerx - self.x
                        dy = self.player.rect.centery - self.y
                        if dx*dx + dy*dy < self.radius*self.radius:
                            self.player.hp -= 2
                            if self.player.hp <= 0:
                                self.player.kill()
                                GameArea.running = False
                    self.has_exploded = True
        elif self.state == "explode":
            if now - self.explode_start > self.explode_duration:
                self.kill()
                
class GameArea:
    def layout_game_area(self):
        play_bgm(BGM_GAME)  # 进入游戏切换BGM
        play_sfx(SFX_START)
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
        
        shoot_cooldown = 2000
        last_shoot_time = 0

        effects = []  # 用于存储爆炸视觉效果

        # 预加载PeaBulletHit.gif的第一帧
        pea_hit_img = None
        pea_hit_path = path.join(setting.img_folder, "PeaBulletHit.gif")
        if os.path.exists(pea_hit_path):
            try:
                import PIL.Image
                pil_img = PIL.Image.open(pea_hit_path)
                pil_img.seek(0)
                frame_img = pil_img.convert("RGBA")
                raw_str = frame_img.tobytes()
                size = frame_img.size
                pea_hit_img = pygame.image.frombuffer(raw_str, size, "RGBA")
                pea_hit_img = pygame.transform.scale(pea_hit_img, (40, 40))
            except Exception:
                pea_hit_img = None

        last_bomb_check_time = time.time()  # 新增：上次敌方炸弹生成时间

        dead_time = None  # 新增：记录死亡时间
        quit_sound_played = False  # 新增：只播放一次死亡音效

        while running:
            # Keep loop running at the right speed
            clock.tick(60)
    
            detector.update()

            current_time = pygame.time.get_ticks()
            
            # Handle input events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False
                if event.type == pygame.KEYDOWN and ControlMode.KEY:
                    if event.key == pygame.K_SPACE:
                        if current_time - last_shoot_time > shoot_cooldown:
                            player.shoot()
                            last_shoot_time = current_time
            

            current_time = pygame.time.get_ticks()

            if ControlMode.HAND and detector.is_grab:
                if current_time - last_shoot_time >= shoot_cooldown:
                    player.shoot()
                    last_shoot_time = current_time

            if detector.is_fuck:
                running = False
        
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
                    enemy.speedY = enemy_speed
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
            
            # Enemies shoot bullets_1
            bullet_speed = bg_scroll_speed_per_frame * 5  # 3 times of the scroll speed
            now = time.time()
            for enemy in enemies:
                enemy.try_shoot(bullet_speed, 0.1 * random.randrange(0, 10) + now)
            # Update
            all_sprites.update()

            # 检查敌人子弹击中玩家
            for bullet in list(bullets_1):
                if player.rect.colliderect(bullet.rect):
                    player.hp -= 1
                    # 添加爆炸视觉效果
                    if pea_hit_img:
                        effect_rect = pea_hit_img.get_rect(center=bullet.rect.center)
                        effects.append({
                            "image": pea_hit_img,
                            "rect": effect_rect,
                            "start_time": time.time()
                        })
                    play_sfx(SFX_HIT)  # 播放击中音效
                    bullet.kill()
                    if player.hp <= 0:
                        player.set_dead()
                        if dead_time is None:
                            dead_time = time.time()
                            if not quit_sound_played:
                                play_sfx(SFX_QUIT)
                                quit_sound_played = True

            # 检查玩家子弹击中敌人
            hits = pygame.sprite.groupcollide(enemies, bullets_0, True, False)
            for enemy, hit_bullets in hits.items():
                for bullet in hit_bullets:
                    score += 10
                    if pea_hit_img:
                        effect_rect = pea_hit_img.get_rect(center=bullet.rect.center)
                        effects.append({
                            "image": pea_hit_img,
                            "rect": effect_rect,
                            "start_time": time.time()
                        })
                    play_sfx(SFX_HIT)  # 播放击中音效
                    bullet.kill()

            # 玩家手势释放炸弹（假设用 detector.is_open_palm 触发，可根据实际手势调整）
            # 这里以按空格键为例，也可用手势
            keys = pygame.key.get_pressed()
            if keys[pygame.K_SPACE]:
                player.release_bomb()

            # 每隔1s检定一次，35%概率生成伤害类型为1的bomb
            now_time = time.time()
            if now_time - last_bomb_check_time >= 1.5:
                if random.random() < 0.35:
                    # 生成坐标为player中心xy+-30
                    px, py = player.rect.centerx, player.rect.centery
                    bomb_x = px + random.choice([-30, 30])
                    bomb_y = py + random.choice([-30, 30])
                    warning_img_path = path.join(setting.img_folder, "bomb_warning_1.gif")
                    explode_img_path = path.join(setting.img_folder, "bomb_explode_1.gif")
                    bomb = Bomb(
                        bomb_x, bomb_y, player=player, enemies=enemies, damage_type=1,
                        warning_time=0.3, radius=50,
                        warning_img_path=warning_img_path,
                        explode_img_path=explode_img_path
                    )
                    all_sprites.add(bomb)
                    bombs.add(bomb)
                last_bomb_check_time = now_time

            # Render
            screen.fill(BLACK)
            screen.blit(bg_img, (0, bg_y1))
            screen.blit(bg_img, (0, bg_y2))
            all_sprites.draw(screen)

            # 渲染爆炸视觉效果
            now = time.time()
            effects[:] = [e for e in effects if now - e["start_time"] < 0.1]
            for e in effects:
                screen.blit(e["image"], e["rect"])

            # Display score
            coin_image = pygame.image.load("assets/images/Customs/coin.png") 
            coin_image = pygame.transform.scale(coin_image, (40, 40))
            score_text = font.render(f"{score}", True, WHITE)
            screen.blit(score_text, (20, 10))
            screen.blit(coin_image, (10 + score_text.get_width() + 10, 3))
            
            # Display hp
            heart_image = pygame.image.load("assets/images/Customs/Heart.png") 
            heart_image = pygame.transform.scale(heart_image, (40, 40))
            for i in range(player.hp):
                screen.blit(heart_image, (10 + i * 50, 50))
            
            # Refresh screen
            pygame.display.flip()

            # 死亡后延迟1秒退出
            if dead_time is not None and (time.time() - dead_time) >= 1.0:
                running = False

        play_bgm(BGM_MENU)  # 游戏退出切回菜单BGM

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
            play_sfx(SFX_MENU_SWITCH_ON)
        elif keys[pygame.K_DOWN] and current_time - self.last_move_time > self.cooldown:
            self.selected_index = (self.selected_index + 1) % len(self.options)
            self.last_move_time = current_time
            play_sfx(SFX_MENU_SWITCH_OFF)
    def handle_navigation_hand(self):
        current_time = pygame.time.get_ticks()
        if detector.movement and detector.hand_center:
            if current_time - self.last_move_time > self.cooldown:
                if detector.movement == "Down":
                    self.selected_index = (self.selected_index + 1) % len(self.options)
                    play_sfx(SFX_MENU_SWITCH_OFF)
                elif detector.movement == "Up":
                    self.selected_index = (self.selected_index - 1) % len(self.options)
                    play_sfx(SFX_MENU_SWITCH_ON)
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
        play_sfx(SFX_MENU_ENTER)
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
                        detector.start_calibration()
                    elif selected == "Arrow Keys":
                        set_mode(ControlMode.KEY)
                    print(f"Mode changé en: {selected}")
                    
                    running = False

            if get_mode() == ControlMode.HAND:
                self.handle_navigation_hand()
            elif get_mode() == ControlMode.KEY:
                self.handle_navigation_key()
            
            if detector.is_fuck:
                running = False

            pygame.display.flip()
            clock.tick(30)

