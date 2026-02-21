"""
Biome definitions for Life of a Burrb.
The world is split into 5 biomes: Forest, Snow, City, Swamp, Desert.

Layout (roughly):
  +-----------+-----------+
  |  FOREST   |   SNOW    |
  |           |           |
  +-----+----+----+------+
  |     |  CITY   |      |
  |     |         |      |
  +-----+----+----+------+
  |  SWAMP   |  DESERT   |
  |          |            |
  +----------+-----------+
"""

from src.constants import WORLD_WIDTH, WORLD_HEIGHT

# Biome name constants
BIOME_CITY = "city"
BIOME_FOREST = "forest"
BIOME_DESERT = "desert"
BIOME_SNOW = "snow"
BIOME_SWAMP = "swamp"

# City occupies the center chunk of the map
CITY_X1 = 3000
CITY_Y1 = 3000
CITY_X2 = 7000
CITY_Y2 = 7000

# Ground colors for each biome
BIOME_COLORS = {
    BIOME_CITY: (190, 185, 175),  # cement gray
    BIOME_FOREST: (80, 140, 55),  # lush green grass
    BIOME_DESERT: (220, 190, 130),  # warm sand
    BIOME_SNOW: (230, 235, 245),  # bright white snow
    BIOME_SWAMP: (60, 80, 50),  # dark murky green
}


def get_biome(x, y):
    """Figure out which biome a world position is in."""
    # City is the center rectangle
    if CITY_X1 <= x <= CITY_X2 and CITY_Y1 <= y <= CITY_Y2:
        return BIOME_CITY
    # Top-left = Forest
    if x < WORLD_WIDTH // 2 and y < WORLD_HEIGHT // 2:
        return BIOME_FOREST
    # Top-right = Snow
    if x >= WORLD_WIDTH // 2 and y < WORLD_HEIGHT // 2:
        return BIOME_SNOW
    # Bottom-left = Swamp
    if x < WORLD_WIDTH // 2 and y >= WORLD_HEIGHT // 2:
        return BIOME_SWAMP
    # Bottom-right = Desert
    return BIOME_DESERT
