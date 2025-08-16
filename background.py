import pygame
from support import *

class Background(pygame.sprite.Sprite):
    def __init__(self, image_name, speed=1):
        super().__init__()
        self.image = pygame.image.load(image_name)
        self.rect = self.image.get_rect()
        self.speed = speed

    def update(self):
        self.rect.y += self.speed

        # 判断是否超出屏幕，超出屏幕则返回图像上方
        screen_rect = pygame.Rect(0, 0, SCREEN_WIDTH, SCREEN_HEIGHT)
        if self.rect.y >= screen_rect.height:
            self.rect.y = -self.rect.height
