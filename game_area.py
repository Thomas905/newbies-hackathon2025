import pygame
from hand_detection import HandDetector

pygame.init()

# Globals Variables
SCREEN_WIDTH = 630
SCREEN_HEIGHT = 804
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("NewBies Game")
clock = pygame.time.Clock()
font = pygame.font.SysFont(None, 50)
detector = HandDetector()

##Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 40, 0)
BLUE = (38, 0, 255)
LIGHT_BLUE = (100, 180, 255)
YELLOW = (255, 195, 0)

class GameArea:
    def layout_game_area(self):
        running = True
        cols = 7
        rows = 12
        cell_width = SCREEN_WIDTH // cols #90PX
        cell_height = SCREEN_HEIGHT // rows #67PX

        
        center_col = cols // 2
        bottom_row = rows - 2

        player_col = center_col
        player_row = bottom_row


        while running:
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    running = False

            screen.fill(WHITE)

            detector.update()

            if detector.hand_center:
                pygame.draw.circle(screen, (255,0,0), detector.hand_center, 20)
            if detector.is_grab:
                print("GRAB")


            for row in range(rows):
                for col in range(cols):
                    rect = pygame.Rect(col * cell_width, row * cell_height, cell_width, cell_height)
                    pygame.draw.rect(screen, BLACK, rect, 1)
            
            # Design Player
            center_rect = pygame.Rect(
                player_col * cell_width + 5,
                player_row * cell_height + 5,
                cell_width - 10,
                cell_height - 10
            )
            pygame.draw.rect(screen, RED, center_rect)

            pygame.display.flip()
            clock.tick(30)
