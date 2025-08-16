import setting
import face_detection

setting.pygame.init()
webcam = setting.cv.VideoCapture(0) # Capture using default webcam 

SMOOTH_ALPHA = 0.1 # lower -> smoother, higher -> snappier 
DEAD_ZONE_HORIZONTAL = 20 # Zone which is 40 pixels 
                        # from the right/left of center of the screen 
                        # where no movement capture occured
DEAD_ZONE_VERTICAL = 10 # Zone which is 20 pixels 
                        # from above/below of center of the screen 
                        # where no movement capture occured
COOLDOWN_S = 0.1 # Time taken between each consecutive commands
COOLDOWN_MOVE = 0.5 # Time taken between each consecutive processing command

# FaceMesh landmark indices for irises when refine_landmarks=True:
# (These are standard for the MP 468+ iris topology.)
LEFT_IRIS_IDX  = [469, 470, 471, 472]  # left eye (as seen by the person)
RIGHT_IRIS_IDX = [474, 475, 476, 477]  # right eye

# Display
WIDTH = 450
HEIGHT = 720
screen = setting.pygame.display.set_mode((WIDTH, HEIGHT))
setting.pygame.display.set_caption("PVZ")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (255, 0, 0)
GREEN = (0, 255, 0)
BLUE = (0, 0, 255)

# Load image
def load_image(name, scale=1):
    img = setting.pygame.Surface((50, 40))
    img.fill(BLUE if name == "player" else RED)
    return img


# Player
class Player(setting.pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        image = setting.pygame.image.load(setting.path.join(setting.img_folder,"hero.png"))
        self.image = setting.pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        # Status
        self.grid_x = 2  # Spam from third column
        self.grid_y = 6  # Spam from 7th row
        self.update_position()
        self.health = 100
        self.last_move_time = 0 # Record command timeline
        self.move_cooldown = COOLDOWN_MOVE # Seconds between moves

    def update_position(self):
        self.rect.x = self.grid_x * 75
        self.rect.y = 30 + self.grid_y * 60

    def update(self, command):
        now = setting.time.time()
        if ((now - self.last_move_time) < self.move_cooldown):
            return  # too soon, skip this frame
        
        moved = False
        if (command == "UP" and self.grid_y > 0):
            self.grid_y -= 1
            moved = True
        if (command == "UPRIGHT" and self.grid_y > 0 and self.grid_x < 5):
            self.grid_x += 0.5
            self.grid_y -= 0.5
            moved = True
        if (command == "RIGHT" and self.grid_x < 5):
            self.grid_x += 1
            moved = True
        if (command == "DOWNRIGHT" and self.grid_y < 10 and self.grid_x < 5):
            self.grid_x += 0.5
            self.grid_y += 0.5
            moved = True
        if (command == "DOWN" and self.grid_y < 10):
            self.grid_y += 1
            moved = True
        if (command == "DOWNLEFT" and self.grid_y < 10 and self.grid_x > 0):
            self.grid_x -= 0.5
            self.grid_y += 0.5
            moved = True
        if (command == "LEFT" and self.grid_x > 0):
            self.grid_x -= 1
            moved = True
        if (command == "UPLEFT" and self.grid_y > 0 and self.grid_x > 0):
            self.grid_x -= 0.5
            self.grid_y -= 0.5
            moved = True

        if moved:
            self.update_position()
            self.last_move_time = now

    # def shoot(self):
    #     bullet = Bullet(self.rect.centerx, self.rect.top)
    #     all_sprites.add(bullet)
    #     bullets.add(bullet)

# Enemy
class Enemy(setting.pygame.sprite.Sprite):
    def __init__(self):
        super().__init__()
        image = setting.pygame.image.load(setting.path.join(setting.img_folder,"peashooter_candidate_0.png"))
        self.image = setting.pygame.transform.scale(image,(60,45))
        self.rect = self.image.get_rect()
        # Random grid coordinates
        self.grid_x = setting.random.randint(0, 5)
        self.grid_y = setting.random.randint(-6, 0)  # Spam above and at the top of the screen.
        self.update_position()
        self.speedy = 80.0 # speed in pixels/sec
        self.out_time = None  # Record screen time

    def update_position(self):
        self.rect.x = self.grid_x * 75
        self.rect.y = 30 + self.grid_y * 60

    def scroll_with_bg(self, scroll_amount):
        self.grid_y += scroll_amount // 60  # The back ground moves one space each time.
        self.update_position()

    def update(self, command):
        # The enemy does not move automatically but only moves with the move of the bg.
        self.update_position()
        # Check if it is off screen.
        if self.rect.top > HEIGHT:
            if self.out_time is None:
                self.out_time = setting.time.time()
            elif setting.time.time() - self.out_time > 1:
                self.kill()
        else:
            self.out_time = None

class Peashooter(Enemy):
    def __init__(self):
        super().__init__()
        image = setting.pygame.image.load(setting.path.join(setting.img_folder,"peashooter_candidate_0.png"))
        self.image = setting.pygame.transform.scale(image,(75,60))
        self.rect = self.image.get_rect()
        self.rect.x = setting.random.randrange(WIDTH - self.rect.width)
        self.rect.y = setting.random.randrange(-100, -40)
        self.speedy = setting.random.randrange(1, 5)

# Bullet type
class Bullet(setting.pygame.sprite.Sprite):
    def __init__(self, x, y):
        super().__init__()
        self.image = setting.pygame.Surface((10, 20))
        self.image.fill(GREEN)
        self.rect = self.image.get_rect()
        self.rect.centerx = x
        self.rect.bottom = y
        self.speedy = -10
    
    def update(self, command):
        self.rect.y += self.speedy
        # If the bullet flies out of the top of the screen, delete it.
        if self.rect.bottom < 0:
            self.kill()

def main_game():
    ema_left  = None # EMA-smoothed left-iris coordinates (x, y)
    ema_right = None # EMA-smoothed right-iris coordinates (x, y)
    last_cmd_time = 0.0 # Time point when last command was executed
    
    # -------------------MediaPipe setup -----------------------
    # ----------------------------------------------------------
    mediapipe_face = setting.mp.solutions.face_mesh
    face_mesh = mediapipe_face.FaceMesh(
        static_image_mode = False,
        max_num_faces = 1,
        refine_landmarks = True,
        min_detection_confidence = 0.5,
        min_tracking_confidence = 0.5
    )

    # Create a sprite group
    all_sprites = setting.pygame.sprite.Group()
    enemies = setting.pygame.sprite.Group()
    bullets = setting.pygame.sprite.Group()

    # Create an enemy
    for i in range(4):
        enemy = Enemy()
        all_sprites.add(enemy)
        enemies.add(enemy)

    # Create Player
    player = Player()
    all_sprites.add(player)

    # Score
    score = 0
    font = setting.pygame.font.SysFont(None, 36)

    # Game loop
    clock = setting.pygame.time.Clock()
    running = True
    # Load background image
    bg_img = setting.pygame.image.load(setting.path.join(setting.img_folder, "background.png")).convert()
    bg_img = setting.pygame.transform.scale(bg_img, (WIDTH, HEIGHT))
    bg_y1 = 0
    bg_y2 = -HEIGHT
    BG_SCROLL_SPEED = 60  # The background scrolled each time by pixels
    last_scroll_time = setting.time.time()

    while (running and webcam.isOpened()):
        # Keep the loop running at the correct speed.
        clock.tick(30)

        #player.shoot() # Keeping the player shooting

        canRead, frame = webcam.read() # Read the webcam 
                                   # and check if it was sucessfully read
        if (canRead == False):
            raise SystemExit("ERROR: Could not open webcam.")
            exit(-1)

        frameH, frameW = frame.shape[:2] # Get screen width and height
        # Horizontal flip (make the laptop as a mirror)
        frame = setting.cv.flip(frame, 1) 
        # MediaPipe expects RGB
        rgb = setting.cv.cvtColor(frame, setting.cv.COLOR_BGR2RGB)
        result = face_mesh.process(rgb)

        if (result.multi_face_landmarks):
            landmarks = result.multi_face_landmarks[0].landmark
            # --- Compute left & right iris centers (mean of 4 iris points) ---
            left_iris_pts = [face_detection.to_px(landmarks[i], frameW, frameH) for i in LEFT_IRIS_IDX]
            right_iris_pts = [face_detection.to_px(landmarks[i], frameW, frameH) for i in RIGHT_IRIS_IDX]
            
            # Find the mean coordinates within the range of coordinates
            left_iris_center  = face_detection.avg_points(left_iris_pts)
            right_iris_center = face_detection.avg_points(right_iris_pts)

            # Smooth each eye separately, then average for a robust "pupil" center
            ema_left  = face_detection.ema_update(ema_left,  left_iris_center, SMOOTH_ALPHA)
            ema_right = face_detection.ema_update(ema_right, right_iris_center, SMOOTH_ALPHA)

            # Use the midpoint of the two smoothed irises as the single "gaze point"
            iris_center = face_detection.avg_points([ema_left, ema_right])

            # -------- Debug drawing --------
            # Iris contours
            for p in left_iris_pts:
                setting.cv.circle(frame, p, 2, (0, 255, 0), -1)
            for p in right_iris_pts:
                setting.cv.circle(frame, p, 2, (0, 255, 0), -1)

            # Smoothed iris centers
            setting.cv.circle(frame, ema_left,  4, (255, 0, 0), -1)
            setting.cv.circle(frame, ema_right, 4, (255, 0, 0), -1)

            # Combined "gaze" point
            setting.cv.circle(frame, iris_center, 6, (0, 0, 255), -1)

        # Draw a dead-zone box around a screen-centered point
        shift_x, shift_y = -50, 30
        screen_center = ((frameW // 2) + shift_x, (frameH // 2) + shift_y)
        setting.cv.rectangle(frame, (screen_center[0] - DEAD_ZONE_HORIZONTAL, screen_center[1] - DEAD_ZONE_VERTICAL),
                    (screen_center[0] + DEAD_ZONE_HORIZONTAL, screen_center[1] + DEAD_ZONE_VERTICAL),
                    (0, 255, 255), 1)
        setting.cv.circle(frame, screen_center, 6, (0, 255, 255), 1) # Coordinates (0, 0)
        
        # Get command
        command = face_detection.determine_command(iris_center, screen_center, DEAD_ZONE_HORIZONTAL, DEAD_ZONE_VERTICAL) 

        now = setting.time.time() # Get current time
        if ((now - last_cmd_time) > COOLDOWN_S):
            # Print command every certain time
            print("Command = ",  command)
            print("\n")
            last_cmd_time = now # Update time line
            # Draw the command
            setting.cv.putText(frame, command, (20, 40), setting.cv.FONT_HERSHEY_SIMPLEX, 1.1, (0, 200, 255), 3)

        # Open/update Frame window image
        setting.cv.imshow("Frame", frame)
        
        # Background scrolling logic, moves every 1 second.
        now = setting.time.time()
        scroll_amount = 0
        if now - last_scroll_time >= 1:
            bg_y1 += BG_SCROLL_SPEED
            bg_y2 += BG_SCROLL_SPEED
            scroll_amount = BG_SCROLL_SPEED
            last_scroll_time = now
        # Two pictures loop
        if bg_y1 >= HEIGHT:
            bg_y1 = bg_y2 - HEIGHT
        if bg_y2 >= HEIGHT:
            bg_y2 = bg_y1 - HEIGHT
        # The enemy moves with the background.
        if scroll_amount > 0:
            for enemy in enemies:
                enemy.scroll_with_bg(scroll_amount)
        
        # Update
        all_sprites.update(command)
        
        # Check if the bullet hit the enemy.
        hits = setting.pygame.sprite.groupcollide(enemies, bullets, True, True)
        for hit in hits:
            score += 10
            enemy = Enemy()
            all_sprites.add(enemy)
            enemies.add(enemy)
        
        # Check if the enemy has collided with the player.
        hits = setting.pygame.sprite.spritecollide(player, enemies, False)
        if hits:
            player.health -= 1
            if player.health <= 0:
                running = False
        
        # Fill
        screen.fill(BLACK)
        screen.blit(bg_img, (0, bg_y1))
        screen.blit(bg_img, (0, bg_y2))
        all_sprites.draw(screen)
        
        # Display Score
        score_text = font.render(f"Score: {score}", True, WHITE)
        screen.blit(score_text, (10, 10))
        
        # Display health
        health_text = font.render(f"Health: {player.health}", True, WHITE)
        screen.blit(health_text, (10, 50))

        if (setting.cv.waitKey(1) & 0xFF == 27): # If ESC is pressed, escape
            break
        
        # Refresh the screen
        setting.pygame.display.flip()

    # Free the web cam and terminate all windows
    webcam.release()
    setting.cv.destroyAllWindows()
    setting.pygame.quit()
