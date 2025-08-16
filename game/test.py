import pygame
import random
import os
import os.path as path
import setting
pygame.init()

# 屏幕设置
WIDTH = 450
HEIGHT = 720
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("PVZ")

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
        # 网格参数
        self.grid_x = 2  # 初始在第3列
        self.grid_y = 6  # 初始在第7行（中间11行的中间）
        self.update_position()
        self.health = 100

    def update_position(self):
        self.rect.x = self.grid_x * 75
        self.rect.y = 30 + self.grid_y * 60

    def update(self):
        keys = pygame.key.get_pressed()
        moved = False
        if keys[pygame.K_LEFT] and self.grid_x > 0:
            self.grid_x -= 1
            moved = True
        if keys[pygame.K_RIGHT] and self.grid_x < 5:
            self.grid_x += 1
            moved = True
        # 主角只能在中间11行（grid_y = 0 ~ 10）移动
        if keys[pygame.K_UP] and self.grid_y > 0:
            self.grid_y -= 1
            moved = True
        if keys[pygame.K_DOWN] and self.grid_y < 10:
            self.grid_y += 1
            moved = True
        if moved:
            self.update_position()

    def shoot(self):
        bullet = Bullet(self.rect.centerx, self.rect.top)
        all_sprites.add(bullet)
        bullets.add(bullet)

# 敌人类
class Enemy(pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        image = pygame.image.load(path.join(setting.img_folder,"peashooter_candidate_0.png"))
        self.image = pygame.transform.scale(image,(60,45))
        self.rect = self.image.get_rect()
        # 随机格子坐标
        self.grid_x = random.randint(0, 5)
        self.grid_y = random.randint(-6, 0)  # 出生在屏幕外上方和顶端半行
        self.update_position()
        self.speedx = 0
        self.speedy = 0
        self.out_time = None  # 记录出屏时间

    def update_position(self):
        self.rect.x = self.grid_x * 75
        self.rect.y = 30 + self.grid_y * 60

    def scroll_with_bg(self, scroll_amount):
        self.grid_y += scroll_amount // 60  # 每次卷轴移动一格
        self.update_position()

    def update(self):
        # 敌人默认不自动移动，只随卷轴移动
        self.update_position()
        # 检查是否出屏
        if self.rect.top > HEIGHT:
            if self.out_time is None:
                self.out_time = time.time()
            elif time.time() - self.out_time > 1:
                self.kill()
        else:
            self.out_time = None
'''
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
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface((10, 20))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10
    
    def update(self):
        self.rect.y += self.speedy
        # 如果子弹飞出屏幕顶部，则删除
        if self.rect.bottom < 0:
            self.kill()
'''
# 创建精灵组
all_sprites = pygame.sprite.Group()
enemies = pygame.sprite.Group()
bullets = pygame.sprite.Group()

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
bg_img = pygame.image.load(path.join(setting.img_folder, "background.png")).convert()
bg_img = pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
bg_y1 = 0
bg_y2 = -HEIGHT
BG_SCROLL_SPEED = 60  # 每次滚动的像素
last_scroll_time = time.time()

while running:
    # 保持循环以正确的速度运行
    clock.tick(12)
    
    # 处理输入事件
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key == pygame.K_SPACE:
                player.shoot()
    
    # 背景滚动逻辑，每1秒移动一次
    now = time.time()
    scroll_amount = 0
    if now - last_scroll_time >= 1:
        bg_y1 += BG_SCROLL_SPEED
        bg_y2 += BG_SCROLL_SPEED
        scroll_amount = BG_SCROLL_SPEED
        last_scroll_time = now
    # 两张图循环
    if bg_y1 >= HEIGHT:
        bg_y1 = bg_y2 - HEIGHT
    if bg_y2 >= HEIGHT:
        bg_y2 = bg_y1 - HEIGHT
    # 敌人随背景卷动
    if scroll_amount > 0:
        for enemy in enemies:
            enemy.scroll_with_bg(scroll_amount)
    
    # 更新
    all_sprites.update()
    
    # 检查子弹是否击中敌人
    hits = pygame.sprite.groupcollide(enemies, bullets, True, True)
    for hit in hits:
        score += 10
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)
    
    # 检查敌人是否撞到玩家
    hits = pygame.sprite.spritecollide(player, enemies, False)
    if hits:
        player.health -= 1
        if player.health <= 0:
            running = False
    
    # 渲染
    screen.fill(BLACK)
    screen.blit(bg_img, (0, bg_y1))
    screen.blit(bg_img, (0, bg_y2))
    all_sprites.draw(screen)
    
    # 显示分数
    score_text = font.render(f"分数: {score}", True, WHITE)
    screen.blit(score_text, (10, 10))
    
    # 显示生命值
    health_text = font.render(f"生命: {player.health}", True, WHITE)
    screen.blit(health_text, (10, 50))
    
    # 刷新屏幕
    pygame.display.flip()

pygame.quit()
