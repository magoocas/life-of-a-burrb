"""
Constants for Life of a Burrb.
Colors, world dimensions, and city grid settings.
"""

# Colors - these are (Red, Green, Blue) values from 0-255
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (80, 80, 80)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
GREEN = (80, 180, 80)
DARK_GREEN = (50, 140, 50)
BROWN = (139, 90, 43)
SKY_BLUE = (135, 200, 235)
YELLOW = (255, 220, 50)
SIDEWALK = (210, 200, 185)
ROAD_COLOR = (60, 60, 60)
ROAD_LINE = (220, 210, 50)

# Burrb colors (matching the drawing!)
BURRB_BLUE = (60, 150, 220)
BURRB_LIGHT_BLUE = (100, 180, 240)
BURRB_DARK_BLUE = (30, 100, 170)
BURRB_ORANGE = (230, 160, 30)
BURRB_EYE = (20, 40, 80)

# ============================================================
# WORLD MAP
# ============================================================
# The world is much bigger than the screen - that's what makes
# it "open world"! The camera follows the burrb around.
WORLD_WIDTH = 10000
WORLD_HEIGHT = 10000

# City grid settings
BLOCK_SIZE = 200  # each city block is 200x200 pixels (smaller = denser city)
ROAD_WIDTH = 70  # wider roads for more cement
SIDEWALK_WIDTH = 24  # wider sidewalks
