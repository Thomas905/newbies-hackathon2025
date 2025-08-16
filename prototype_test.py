import pygame
from hand_detection import HandDetector

detector = HandDetector()

pygame.init()
screen = pygame.display.set_mode((800, 600))
clock = pygame.time.Clock()
running = True

while running:
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False

    detector.update()
    screen.fill((255,0,0))

    if detector.hand_center:
        pygame.draw.circle(screen, (255,0,0), detector.hand_center, 20)
    if detector.movement:
        print(detector.movement)
    if detector.is_grab:
        print("GRAB!")

    pygame.display.flip()
    clock.tick(30)

detector.release()
pygame.quit()
