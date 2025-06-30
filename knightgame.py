import pygame
import random
import math

# ==============================================================================
# 1. Game Setup and Constants
# ==============================================================================

# Initialize all imported pygame modules
pygame.init()
pygame.font.init()

# Screen dimensions
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600

# Tile size for our grid-based world
TILE_SIZE = 40

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
RED = (217, 30, 24)      # Player color
GREEN = (63, 195, 128)   # Grass
BLUE = (52, 152, 219)    # Water / Walls
GRAY = (149, 165, 166)   # Town
GOLD = (241, 196, 15)    # XP bar
DARK_GREEN = (22, 160, 133) # Slime enemy
PURPLE = (142, 68, 173)  # Goblin enemy
DARK_RED = (192, 57, 43) # Boss
UI_BG_COLOR = (44, 62, 80)
UI_BORDER_COLOR = (52, 73, 94)

# Game constants
GAME_TIMER_SECONDS = 30.0
# MODIFICATION: Respawn time in milliseconds (10 seconds)
ENEMY_RESPAWN_TIME = 10000 

# Setup the game window
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("30-Second Knight")

# Game font for UI elements
UI_FONT = pygame.font.Font(None, 36)
BIG_FONT = pygame.font.Font(None, 74)
SMALL_FONT = pygame.font.Font(None, 24)


# ==============================================================================
# 2. Game World and Map
# ==============================================================================

# The map is represented by a list of strings.
# '.' = Grass (walkable)
# 'W' = Water/Wall (not walkable)
# 'T' = Town (resets timer)
# 'S' = Slime (weak enemy)
# 'G' = Goblin (stronger enemy)
# 'B' = Boss (final enemy)
# 'P' = Player start position
GAME_MAP = [
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "W.S..................S.WWWWWWWWWWWWWWWWW",
    "W....P...............S.WWWWWWWWWWWWWWWWW",
    "W.S..................S.WWWWWWWWWWWWWWWWW",
    "W................T.....WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWW.G.G.WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWW.....WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWW.G.G.WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWW.....WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWWWWWW.WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW.WWWWWWWWWWWW.WWWWWWWWWWWWWWWWW",
    "WWWWWWWWW..............WWWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWWWWWW...WWWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWWWWWW.B.WWWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWWWWWW...WWWWWWWWWWWWWWWWW",
    "WWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWWW",
]

# Calculate map dimensions
MAP_WIDTH = len(GAME_MAP[0]) * TILE_SIZE
MAP_HEIGHT = len(GAME_MAP) * TILE_SIZE


# ==============================================================================
# 3. Player Class
# ==============================================================================

class Player(pygame.sprite.Sprite):
    """
    The player character, controlled by the user.
    """
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE - 8, TILE_SIZE - 8])
        self.image.fill(RED)
        self.rect = self.image.get_rect()
        self.rect.x = x
        self.rect.y = y
        self.speed = 5

        # Player stats
        self.level = 1
        self.hp = 10
        self.max_hp = 10
        self.attack = 2
        self.xp = 0
        self.xp_to_next_level = 10

    # MODIFICATION: Overhauled the move method to be more robust.
    def move(self, dx, dy, walls):
        """ Handles player movement and collision with walls robustly. """
        # Create a movement vector
        vec = pygame.math.Vector2(dx, dy)
        # Normalize the vector to prevent faster diagonal speed
        if vec.length_squared() > 0:
            vec.normalize_ip()

        # Move horizontally and check for collisions
        self.rect.x += vec.x * self.speed
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if vec.x > 0: # Moving right
                    self.rect.right = wall.rect.left
                if vec.x < 0: # Moving left
                    self.rect.left = wall.rect.right
        
        # Move vertically and check for collisions
        self.rect.y += vec.y * self.speed
        for wall in walls:
            if self.rect.colliderect(wall.rect):
                if vec.y > 0: # Moving down
                    self.rect.bottom = wall.rect.top
                if vec.y < 0: # Moving up
                    self.rect.top = wall.rect.bottom

    def gain_xp(self, amount):
        """ Handles gaining experience and leveling up. """
        self.xp += amount
        print(f"Gained {amount} XP! Total XP: {self.xp}/{self.xp_to_next_level}")
        while self.xp >= self.xp_to_next_level:
            self.xp -= self.xp_to_next_level
            self.level_up()

    def level_up(self):
        """ Increases player stats upon leveling up. """
        self.level += 1
        self.max_hp += 5
        self.hp = self.max_hp  # Heal on level up
        self.attack += 2
        self.xp_to_next_level = int(self.xp_to_next_level * 1.5)
        print(f"LEVEL UP! Reached level {self.level}!")
        print(f"Stats: HP {self.max_hp}, ATK {self.attack}")


# ==============================================================================
# 4. Enemy and World Object Classes
# ==============================================================================

class Wall(pygame.sprite.Sprite):
    """ A solid wall tile that blocks movement. """
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.image.fill(BLUE)
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE

class Town(pygame.sprite.Sprite):
    """ A town tile where the player can reset the timer. """
    def __init__(self, x, y):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE, TILE_SIZE])
        self.image.fill(GRAY)
        self.rect = self.image.get_rect()
        self.rect.x = x * TILE_SIZE
        self.rect.y = y * TILE_SIZE
        self.cost = 10 # Cost to reset timer

class Enemy(pygame.sprite.Sprite):
    """ Base class for all enemies. """
    def __init__(self, x, y, name, color, hp, attack, xp_reward):
        super().__init__()
        self.image = pygame.Surface([TILE_SIZE - 4, TILE_SIZE - 4])
        self.image.fill(color)
        self.rect = self.image.get_rect()
        # MODIFICATION: Store original position for respawning
        self.original_x = x
        self.original_y = y
        self.rect.x = x * TILE_SIZE + 2
        self.rect.y = y * TILE_SIZE + 2
        self.name = name
        self.color = color # MODIFICATION: Store color for respawning
        self.hp = hp
        self.max_hp = hp # MODIFICATION: Store max_hp for respawning
        self.attack = attack
        self.xp_reward = xp_reward

# ==============================================================================
# 5. UI and Drawing Functions
# ==============================================================================

def draw_text(text, font, color, surface, x, y, center=False):
    """ Utility function to draw text on the screen. """
    text_obj = font.render(text, True, color)
    text_rect = text_obj.get_rect()
    if center:
        text_rect.center = (x, y)
    else:
        text_rect.topleft = (x, y)
    surface.blit(text_obj, text_rect)

def draw_ui(player, time_left):
    """ Draws all the UI elements like stats and timer. """
    # UI Background
    pygame.draw.rect(screen, UI_BG_COLOR, (0, 0, SCREEN_WIDTH, 50))
    pygame.draw.rect(screen, UI_BORDER_COLOR, (0, 50, SCREEN_WIDTH, 2))

    # Timer
    timer_text = f"{max(0, time_left):.1f}"
    timer_color = RED if time_left < 5 else WHITE
    draw_text(timer_text, BIG_FONT, timer_color, screen, SCREEN_WIDTH // 2, 28, center=True)

    # Player Stats
    stats_text = f"Lvl: {player.level} | HP: {player.hp}/{player.max_hp} | ATK: {player.attack}"
    draw_text(stats_text, UI_FONT, WHITE, screen, 10, 15)

    # XP Bar
    xp_bar_width = 200
    xp_ratio = player.xp / player.xp_to_next_level
    current_xp_width = int(xp_bar_width * xp_ratio)
    pygame.draw.rect(screen, UI_BORDER_COLOR, (SCREEN_WIDTH - xp_bar_width - 15, 15, xp_bar_width + 10, 25))
    pygame.draw.rect(screen, GOLD, (SCREEN_WIDTH - xp_bar_width - 10, 18, current_xp_width, 19))
    draw_text("XP", SMALL_FONT, BLACK, screen, SCREEN_WIDTH - xp_bar_width - 35, 19)

def draw_world(surface, camera):
    """ Draws the grass background. """
    surface.fill(GREEN)


# ==============================================================================
# 6. Camera Class
# ==============================================================================

class Camera:
    """
    The camera follows the player and determines what portion of the map is visible.
    """
    def __init__(self, width, height):
        self.camera = pygame.Rect(0, 0, width, height)
        self.width = width
        self.height = height

    def apply(self, entity):
        """ Applies the camera offset to an entity's rectangle. """
        return entity.rect.move(self.camera.topleft)

    def update(self, target):
        """ Updates the camera's position to follow the target (player). """
        x = -target.rect.centerx + int(SCREEN_WIDTH / 2)
        y = -target.rect.centery + int(SCREEN_HEIGHT / 2)

        # Clamp scrolling to map boundaries
        x = min(0, x)  # Prevent moving too far right
        y = min(0, y)  # Prevent moving too far down
        x = max(-(self.width - SCREEN_WIDTH), x)   # Prevent moving too far left
        y = max(-(self.height - SCREEN_HEIGHT), y) # Prevent moving too far up

        self.camera = pygame.Rect(x, y, self.width, self.height)


# ==============================================================================
# 7. Main Game Function
# ==============================================================================

def game_loop():
    """
    The main loop where the entire game runs.
    """
    
    # --- Game State Initialization ---
    running = True
    game_state = "playing" # Can be "playing", "game_over", "win"
    clock = pygame.time.Clock()

    # Create sprite groups
    all_sprites = pygame.sprite.Group()
    walls = pygame.sprite.Group()
    enemies = pygame.sprite.Group()
    towns = pygame.sprite.Group()
    
    # MODIFICATION: List to track killed enemies for respawning
    killed_enemies = []

    # Parse the GAME_MAP to create objects
    player = None
    for y, row in enumerate(GAME_MAP):
        for x, char in enumerate(row):
            if char == 'P':
                player = Player(x * TILE_SIZE, y * TILE_SIZE)
            elif char == 'W':
                wall = Wall(x, y)
                all_sprites.add(wall)
                walls.add(wall)
            elif char == 'T':
                town = Town(x, y)
                all_sprites.add(town)
                towns.add(town)
            elif char == 'S':
                enemy = Enemy(x, y, "Slime", DARK_GREEN, 5, 1, 5)
                all_sprites.add(enemy)
                enemies.add(enemy)
            elif char == 'G':
                enemy = Enemy(x, y, "Goblin", PURPLE, 15, 4, 15)
                all_sprites.add(enemy)
                enemies.add(enemy)
            elif char == 'B':
                enemy = Enemy(x, y, "Evil Lord", DARK_RED, 50, 10, 100)
                all_sprites.add(enemy)
                enemies.add(enemy)
    
    if player is None:
        print("Error: Player start 'P' not found in map!")
        return

    all_sprites.add(player)
    
    # Create the camera
    camera = Camera(MAP_WIDTH, MAP_HEIGHT)
    
    # Timer variables
    start_ticks = pygame.time.get_ticks()
    time_left = GAME_TIMER_SECONDS
    
    # Battle message variables
    message = ""
    message_timer = 0
    
    # --- Main Game Loop ---
    while running:
        
        # --- Event Handling ---
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if game_state != "playing": # If game over or win screen
                    game_loop() # Restart the game
                    return
                # Timer reset in town
                if pygame.sprite.spritecollide(player, towns, False):
                    time_left = GAME_TIMER_SECONDS
                    start_ticks = pygame.time.get_ticks()
                    message = "Timer Reset!"
                    message_timer = 120 # Show message for 2 seconds

        if game_state == "playing":
            # --- Player Movement ---
            # MODIFICATION: More robust way to get movement direction
            keys = pygame.key.get_pressed()
            dx = (keys[pygame.K_RIGHT] or keys[pygame.K_d]) - (keys[pygame.K_LEFT] or keys[pygame.K_a])
            dy = (keys[pygame.K_DOWN] or keys[pygame.K_s]) - (keys[pygame.K_UP] or keys[pygame.K_w])
            player.move(dx, dy, walls)
            
            # --- Update ---
            camera.update(player)
            
            # --- Game Logic ---
            
            # Timer update
            seconds = (pygame.time.get_ticks() - start_ticks) / 1000
            time_left = GAME_TIMER_SECONDS - seconds
            if time_left <= 0:
                game_state = "game_over"

            # Battle Logic (Collision with enemies)
            collided_enemies = pygame.sprite.spritecollide(player, enemies, False)
            for enemy in collided_enemies:
                # Simple, instant combat
                player_damage = player.attack
                enemy_damage = enemy.attack
                
                enemy.hp -= player_damage
                player.hp -= enemy_damage
                
                if enemy.hp <= 0:
                    message = f"Defeated {enemy.name}!"
                    player.gain_xp(enemy.xp_reward)
                    
                    # MODIFICATION: Add non-boss enemies to the respawn list
                    if enemy.name != "Evil Lord":
                        killed_enemies.append((pygame.time.get_ticks(), enemy))

                    if enemy.name == "Evil Lord":
                        game_state = "win"
                    
                    enemy.kill()
                else:
                    message = f"Fought {enemy.name}, took {enemy_damage} damage."

                message_timer = 120 # Show message for 2 seconds

                if player.hp <= 0:
                    game_state = "game_over"

            # MODIFICATION: Respawn logic
            current_time = pygame.time.get_ticks()
            # Iterate over a copy of the list to allow modification during iteration
            for kill_time, dead_enemy in killed_enemies[:]:
                if current_time - kill_time > ENEMY_RESPAWN_TIME:
                    # Create a new instance of the enemy with its original stats
                    new_enemy = Enemy(dead_enemy.original_x, dead_enemy.original_y, 
                                      dead_enemy.name, dead_enemy.color, 
                                      dead_enemy.max_hp, dead_enemy.attack, 
                                      dead_enemy.xp_reward)
                    all_sprites.add(new_enemy)
                    enemies.add(new_enemy)
                    killed_enemies.remove((kill_time, dead_enemy)) # Remove from respawn list
                    print(f"Respawned a {dead_enemy.name}!")


        # --- Drawing ---
        draw_world(screen, camera)
        
        # Draw all sprites with camera offset
        for sprite in all_sprites:
            screen.blit(sprite.image, camera.apply(sprite))
            
        # Draw UI on top of everything
        draw_ui(player, time_left)

        # Show battle/event messages
        if message_timer > 0:
            draw_text(message, UI_FONT, GOLD, screen, SCREEN_WIDTH // 2, 80, center=True)
            message_timer -= 1
        
        # --- Game Over / Win Screen ---
        if game_state == "game_over":
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0,0,0,180)) # translucent black
            screen.blit(s, (0,0))
            draw_text("GAME OVER", BIG_FONT, DARK_RED, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, center=True)
            draw_text("Press any key to restart", UI_FONT, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)
        elif game_state == "win":
            s = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            s.fill((0,100,0,180)) # translucent green
            screen.blit(s, (0,0))
            draw_text("YOU ARE THE HERO!", BIG_FONT, GOLD, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 - 40, center=True)
            draw_text("Press any key to play again", UI_FONT, WHITE, screen, SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 20, center=True)

        # --- Update the Display ---
        pygame.display.flip()
        
        # --- Cap the Framerate ---
        clock.tick(60)
        
    pygame.quit()

# ==============================================================================
# 8. Run the Game
# ==============================================================================
if __name__ == '__main__':
    game_loop()
