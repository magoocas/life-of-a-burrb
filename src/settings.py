"""
Settings for Life of a Burrb.
Screen dimensions, FPS, and spawn configuration.
"""

import pygame

from src.constants import WORLD_WIDTH, WORLD_HEIGHT

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
FPS = 60

# Spawn square - the burrb starts here, and nothing spawns inside it!
# It's a safe clearing in the middle of the city so you have room to look around.
SPAWN_X = WORLD_WIDTH // 2
SPAWN_Y = WORLD_HEIGHT // 2
SPAWN_SIZE = 200  # 200x200 pixel square
SPAWN_RECT = pygame.Rect(
    SPAWN_X - SPAWN_SIZE // 2, SPAWN_Y - SPAWN_SIZE // 2, SPAWN_SIZE, SPAWN_SIZE
)
