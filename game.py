"""
Life of a Burrb
A burrb is a bird-like animal that walks around an open world city.
Use arrow keys or WASD to move around!
"""

import pygame
import math
import random
import asyncio

# Initialize pygame - this starts up the game engine
pygame.init()

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Life of a Burrb")

# Clock controls how fast the game runs (frames per second)
clock = pygame.time.Clock()
FPS = 60

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

# ============================================================
# BIOMES - different areas of the world!
# ============================================================
# The world is split into 5 biomes:
#   Forest (top-left), Snow (top-right), City (center),
#   Swamp (bottom-left), Desert (bottom-right)
#
# Layout (roughly):
#   +-----------+-----------+
#   |  FOREST   |   SNOW    |
#   |           |           |
#   +-----+----+----+------+
#   |     |  CITY   |      |
#   |     |         |      |
#   +-----+----+----+------+
#   |  SWAMP   |  DESERT   |
#   |          |            |
#   +----------+-----------+

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


# ============================================================
# BUILDINGS
# ============================================================
# We'll randomly generate buildings in each city block
class Building:
    """A building in the city. Each one has a random size and color."""

    # Interior tile types
    FLOOR = 0
    WALL = 1
    FURNITURE = 2
    DOOR_TILE = 3
    SOFA = 4
    TV = 5
    CLOSET = 6
    BED = 7

    def __init__(self, x, y, w, h, color, roof_color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.roof_color = roof_color
        # Random windows
        self.windows = []
        win_cols = max(1, w // 30)
        win_rows = max(1, h // 35)
        for row in range(win_rows):
            for col in range(win_cols):
                wx = x + 12 + col * (w - 20) // max(1, win_cols)
                wy = y + 12 + row * (h - 20) // max(1, win_rows)
                # Some windows are lit (yellow), some are dark
                lit = random.random() > 0.3
                self.windows.append((wx, wy, lit))
        # Door
        self.door_x = x + w // 2 - 8
        self.door_y = y + h - 24

        # === INTERIOR ===
        # Each building has a room inside! The interior is a grid
        # of tiles: floor, walls, and furniture.
        # Interior size is always the same so it feels like a
        # proper room inside, regardless of building outer size.
        self.interior_w = 20  # grid width in tiles
        self.interior_h = 16  # grid height in tiles
        self.interior_tile = 24  # pixels per tile
        self.interior = self._generate_interior()

        # Interior colors (based on building color, but lighter for floors)
        self.floor_color = (
            min(255, color[0] + 80),
            min(255, color[1] + 80),
            min(255, color[2] + 60),
        )
        self.wall_interior_color = (
            max(0, color[0] - 20),
            max(0, color[1] - 20),
            max(0, color[2] - 20),
        )
        self.furniture_color = (139, 90, 43)  # wood brown

        # Door position inside (bottom center)
        self.interior_door_col = self.interior_w // 2
        self.interior_door_row = self.interior_h - 1

        # Burrb spawn position when entering (just inside the door)
        self.spawn_x = (
            self.interior_door_col * self.interior_tile + self.interior_tile // 2
        )
        self.spawn_y = (
            self.interior_door_row - 1
        ) * self.interior_tile + self.interior_tile // 2

        # === RESIDENT BURRB (lives in this building!) ===
        # Every building has a burrb sitting on the sofa watching TV
        # and eating potato chips. If you steal their chips, they get
        # mad and chase you!
        rng_resident = random.Random(self.x * 777 + self.y * 333)
        resident_colors = [
            ((220, 80, 80), (180, 50, 50)),  # red
            ((80, 200, 80), (40, 150, 40)),  # green
            ((220, 180, 50), (180, 140, 30)),  # yellow
            ((200, 100, 200), (160, 60, 160)),  # purple
            ((220, 140, 60), (180, 100, 30)),  # orange
            ((220, 100, 160), (180, 60, 120)),  # pink
            ((100, 220, 200), (60, 180, 160)),  # teal
        ]
        rc = rng_resident.choice(resident_colors)
        self.resident_color = rc[0]
        self.resident_detail = rc[1]
        # Resident sits on the sofa (pixel position set after interior gen)
        self.resident_x = 0.0
        self.resident_y = 0.0
        self.resident_angry = False  # are they chasing you?
        self.resident_speed = 1.8
        self.resident_walk_frame = 0

        # Potato chips!
        self.chips_x = 0.0
        self.chips_y = 0.0
        self.chips_stolen = False  # did the player take the chips?

        # Closet! Every house has a closet. Open it for chips... or a scare!
        self.closet_opened = False  # has the closet been opened?
        self.closet_x = 0.0  # pixel position of closet center
        self.closet_y = 0.0
        self.closet_jumpscare = False  # was this closet a jump scare?

        # Bed! Every house has a bed. Shake it and maybe a monster appears!
        self.bed_x = 0.0  # pixel position of bed center
        self.bed_y = 0.0
        self.bed_shaken = False  # has the bed been shaken?
        self.bed_monster = False  # did a monster come out?

        # The 6-legged monster that might live under the bed!
        self.monster_active = False  # is the monster chasing the player?
        self.monster_x = 0.0
        self.monster_y = 0.0
        self.monster_speed = 2.2  # faster than the resident!
        self.monster_walk_frame = 0

        # Find the sofa position to place the resident and chips
        tile = self.interior_tile
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.SOFA:
                    # Put resident on the sofa
                    self.resident_x = col * tile + tile // 2
                    self.resident_y = row * tile + tile // 2
                    # Put chips right next to the sofa
                    self.chips_x = (col + 1) * tile + tile // 2
                    self.chips_y = row * tile + tile // 2
                    break
            else:
                continue
            break

        # Find the closet position
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.CLOSET:
                    self.closet_x = col * tile + tile // 2
                    self.closet_y = row * tile + tile // 2
                    break
            else:
                continue
            break

        # Find the bed position
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.BED:
                    self.bed_x = col * tile + tile // 2
                    self.bed_y = row * tile + tile // 2
                    break
            else:
                continue
            break

    def _generate_interior(self):
        """
        Generate the interior room layout!
        Uses the building's position as a random seed so each
        building always has the same interior.
        """
        rng = random.Random(self.x * 1000 + self.y)
        grid = []
        for row in range(self.interior_h):
            grid_row = []
            for col in range(self.interior_w):
                # Walls around the edges
                if row == 0 or col == 0 or col == self.interior_w - 1:
                    grid_row.append(self.WALL)
                elif row == self.interior_h - 1:
                    # Bottom wall with door opening in the center
                    if col == self.interior_w // 2:
                        grid_row.append(self.DOOR_TILE)
                    else:
                        grid_row.append(self.WALL)
                else:
                    grid_row.append(self.FLOOR)
            grid.append(grid_row)

        # Add furniture randomly!
        # Tables (2x1 or 1x2 blocks)
        num_tables = rng.randint(1, 3)
        for _ in range(num_tables):
            tr = rng.randint(3, self.interior_h - 4)
            tc = rng.randint(3, self.interior_w - 4)
            if grid[tr][tc] == self.FLOOR:
                grid[tr][tc] = self.FURNITURE
                # Make some tables 2 tiles
                if rng.random() > 0.5 and tc + 1 < self.interior_w - 1:
                    if grid[tr][tc + 1] == self.FLOOR:
                        grid[tr][tc + 1] = self.FURNITURE

        # Shelves along walls (but not blocking the door)
        num_shelves = rng.randint(2, 5)
        for _ in range(num_shelves):
            side = rng.choice(["top", "left", "right"])
            if side == "top":
                sc = rng.randint(2, self.interior_w - 3)
                if grid[1][sc] == self.FLOOR:
                    grid[1][sc] = self.FURNITURE
            elif side == "left":
                sr = rng.randint(2, self.interior_h - 3)
                if grid[sr][1] == self.FLOOR:
                    grid[sr][1] = self.FURNITURE
            elif side == "right":
                sr = rng.randint(2, self.interior_h - 3)
                if grid[sr][self.interior_w - 2] == self.FLOOR:
                    grid[sr][self.interior_w - 2] = self.FURNITURE

        # A counter/bar (horizontal line of furniture)
        if rng.random() > 0.4:
            counter_row = rng.randint(4, self.interior_h - 5)
            counter_start = rng.randint(3, self.interior_w // 2 - 1)
            counter_len = rng.randint(3, 6)
            for c in range(
                counter_start, min(self.interior_w - 2, counter_start + counter_len)
            ):
                if grid[counter_row][c] == self.FLOOR:
                    grid[counter_row][c] = self.FURNITURE

        # === LIVING ROOM SETUP ===
        # Every building has a TV against the top wall and a sofa
        # facing it! A burrb sits on the sofa eating potato chips.

        # TV goes against the top wall (row 1), near the right side
        tv_col = self.interior_w - 5
        tv_row = 1
        # Clear space for TV (overwrite any shelf that might be there)
        grid[tv_row][tv_col] = self.TV

        # Sofa goes 3 rows below the TV (facing it)
        sofa_row = tv_row + 3
        sofa_col = tv_col
        # Sofa is 2 tiles wide
        if grid[sofa_row][sofa_col] == self.FLOOR:
            grid[sofa_row][sofa_col] = self.SOFA
        if sofa_col + 1 < self.interior_w - 1:
            if grid[sofa_row][sofa_col + 1] == self.FLOOR:
                grid[sofa_row][sofa_col + 1] = self.SOFA

        # === CLOSET ===
        # Every house has a closet against the left wall!
        # Open it to find chips... or get jump scared!
        closet_row = rng.randint(3, self.interior_h - 4)
        closet_col = 1  # against the left wall
        # Make sure we don't overwrite something important
        if grid[closet_row][closet_col] != self.FLOOR:
            # Try the right wall instead
            closet_col = self.interior_w - 2
        if grid[closet_row][closet_col] == self.FLOOR:
            grid[closet_row][closet_col] = self.CLOSET

        # === BED ===
        # Every house has a bed against the right wall!
        # Shake it and maybe a 6-legged monster crawls out...
        bed_row = rng.randint(3, self.interior_h - 4)
        bed_col = self.interior_w - 2  # against the right wall
        # Make sure we don't overwrite something important
        if grid[bed_row][bed_col] != self.FLOOR:
            bed_col = 1  # try the left wall instead
        if grid[bed_row][bed_col] == self.FLOOR:
            grid[bed_row][bed_col] = self.BED

        return grid

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        # Main building (rounded corners for a smoother look)
        br = min(8, self.w // 6, self.h // 6)
        pygame.draw.rect(
            surface, self.color, (sx, sy, self.w, self.h), border_radius=br
        )
        # Outline
        pygame.draw.rect(surface, BLACK, (sx, sy, self.w, self.h), 2, border_radius=br)
        # Roof accent
        pygame.draw.rect(
            surface, self.roof_color, (sx + 2, sy, self.w - 4, 6), border_radius=3
        )
        # Windows
        for wx, wy, lit in self.windows:
            wsx = wx - cam_x
            wsy = wy - cam_y
            color = (255, 240, 150) if lit else (80, 90, 110)
            pygame.draw.rect(surface, color, (wsx, wsy, 14, 14), border_radius=3)
            pygame.draw.rect(
                surface, (40, 40, 40), (wsx, wsy, 14, 14), 1, border_radius=3
            )
            # Window cross
            pygame.draw.line(
                surface, (40, 40, 40), (wsx + 7, wsy + 2), (wsx + 7, wsy + 12), 1
            )
            pygame.draw.line(
                surface, (40, 40, 40), (wsx + 2, wsy + 7), (wsx + 12, wsy + 7), 1
            )
        # Door
        dx = self.door_x - cam_x
        dy = self.door_y - cam_y
        pygame.draw.rect(surface, BROWN, (dx, dy, 16, 24), border_radius=3)
        pygame.draw.rect(surface, (80, 50, 20), (dx, dy, 16, 24), 1, border_radius=3)
        # Doorknob
        pygame.draw.circle(surface, YELLOW, (dx + 12, dy + 14), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ============================================================
# GENERATE THE CITY
# ============================================================
buildings = []
trees = []
# Building color palettes (Super Mario 3D World style - bright candy colors!)
building_colors = [
    ((255, 100, 100), (220, 60, 60)),  # bright red
    ((100, 200, 255), (60, 160, 220)),  # sky blue
    ((255, 220, 80), (220, 180, 40)),  # sunny yellow
    ((160, 255, 130), (110, 220, 80)),  # lime green
    ((255, 160, 200), (220, 120, 160)),  # bubblegum pink
    ((200, 140, 255), (160, 100, 220)),  # lavender purple
    ((255, 180, 100), (220, 140, 60)),  # tangerine orange
    ((255, 255, 200), (220, 220, 160)),  # cream/vanilla
    ((180, 240, 255), (140, 200, 220)),  # ice blue
    ((255, 140, 140), (220, 100, 100)),  # coral
    ((140, 255, 200), (100, 220, 160)),  # mint green
    ((255, 200, 255), (220, 160, 220)),  # light purple/pink
]

random.seed(42)  # Same world every time you play

# Create city blocks in a grid pattern (ONLY in the city biome!)
for bx in range(CITY_X1, CITY_X2, BLOCK_SIZE + ROAD_WIDTH):
    for by in range(CITY_Y1, CITY_Y2, BLOCK_SIZE + ROAD_WIDTH):
        # Each block gets 3-6 buildings (more packed!)
        num_buildings = random.randint(3, 6)
        for _ in range(num_buildings):
            bw = random.randint(30, 80)  # smaller buildings
            bh = random.randint(30, 70)
            # Place building within the block (with sidewalk margin)
            margin = SIDEWALK_WIDTH + 2
            max_x = bx + BLOCK_SIZE - bw - margin
            max_y = by + BLOCK_SIZE - bh - margin
            if max_x <= bx + margin or max_y <= by + margin:
                continue
            px = random.randint(bx + margin, max_x)
            py = random.randint(by + margin, max_y)

            # Check overlap with existing buildings (tighter spacing)
            new_rect = pygame.Rect(px - 2, py - 2, bw + 4, bh + 4)
            overlap = False
            for b in buildings:
                if new_rect.colliderect(b.get_rect()):
                    overlap = True
                    break
            if not overlap:
                color, roof_color = random.choice(building_colors)
                buildings.append(Building(px, py, bw, bh, color, roof_color))

        # Fewer trees in the city (more urban)
        for _ in range(random.randint(0, 1)):
            margin = SIDEWALK_WIDTH + 8
            tx = random.randint(bx + margin, bx + BLOCK_SIZE - margin)
            ty = random.randint(by + margin, by + BLOCK_SIZE - margin)
            # Don't place on buildings
            tree_rect = pygame.Rect(tx - 8, ty - 8, 16, 16)
            overlap = any(tree_rect.colliderect(b.get_rect()) for b in buildings)
            if not overlap:
                trees.append((tx, ty, random.randint(12, 22)))


# ============================================================
# PARKS - a few open green areas (in the city)
# ============================================================
parks = []
for _ in range(5):
    px = random.randint(CITY_X1 + 200, CITY_X2 - 400)
    py = random.randint(CITY_Y1 + 200, CITY_Y2 - 400)
    pw = random.randint(120, 220)
    ph = random.randint(120, 220)
    parks.append(pygame.Rect(px, py, pw, ph))
    # Remove buildings that overlap with parks
    buildings = [
        b
        for b in buildings
        if not pygame.Rect(px - 10, py - 10, pw + 20, ph + 20).colliderect(b.get_rect())
    ]
    # Add extra trees in parks
    for _ in range(8):
        tx = random.randint(px + 20, px + pw - 20)
        ty = random.randint(py + 20, py + ph - 20)
        trees.append((tx, ty, random.randint(14, 24)))


# ============================================================
# BIOME DECORATIONS - trees and objects for each biome!
# ============================================================
# Each biome gets its own flavor of nature and decorations.
# We store them as (x, y, kind, size) tuples.
# "kind" tells the drawing code what to draw.
biome_objects = []  # list of (x, y, kind, size)

# --- FOREST biome (top-left): lots of big trees, mushrooms, flowers ---
for _ in range(300):
    fx = random.randint(100, WORLD_WIDTH // 2 - 100)
    fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
    # Don't put forest stuff in the city
    if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
        continue
    trees.append((fx, fy, random.randint(16, 30)))

for _ in range(60):
    fx = random.randint(100, WORLD_WIDTH // 2 - 100)
    fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
    if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
        continue
    biome_objects.append((fx, fy, "mushroom", random.randint(6, 12)))

for _ in range(40):
    fx = random.randint(100, WORLD_WIDTH // 2 - 100)
    fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
    if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
        continue
    biome_objects.append((fx, fy, "flower", random.randint(4, 8)))

# --- SNOW biome (top-right): snowy trees, snowmen, ice patches ---
for _ in range(200):
    sx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
    sy = random.randint(100, WORLD_HEIGHT // 2 - 100)
    if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
        continue
    biome_objects.append((sx, sy, "snow_tree", random.randint(14, 26)))

for _ in range(25):
    sx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
    sy = random.randint(200, WORLD_HEIGHT // 2 - 200)
    if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
        continue
    biome_objects.append((sx, sy, "snowman", random.randint(10, 16)))

for _ in range(40):
    sx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
    sy = random.randint(100, WORLD_HEIGHT // 2 - 100)
    if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
        continue
    biome_objects.append((sx, sy, "ice_patch", random.randint(20, 50)))

# --- SWAMP biome (bottom-left): dead trees, lily pads, puddles ---
for _ in range(180):
    wx = random.randint(100, WORLD_WIDTH // 2 - 100)
    wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
        continue
    biome_objects.append((wx, wy, "dead_tree", random.randint(12, 24)))

for _ in range(80):
    wx = random.randint(100, WORLD_WIDTH // 2 - 100)
    wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
        continue
    biome_objects.append((wx, wy, "lily_pad", random.randint(6, 14)))

for _ in range(50):
    wx = random.randint(100, WORLD_WIDTH // 2 - 100)
    wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
        continue
    biome_objects.append((wx, wy, "puddle", random.randint(15, 40)))

# --- DESERT biome (bottom-right): cacti, rocks, tumbleweeds ---
for _ in range(120):
    dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
    dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
        continue
    biome_objects.append((dx, dy, "cactus", random.randint(10, 22)))

for _ in range(80):
    dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
    dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
        continue
    biome_objects.append((dx, dy, "rock", random.randint(8, 18)))

for _ in range(30):
    dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
    dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
    if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
        continue
    biome_objects.append((dx, dy, "tumbleweed", random.randint(6, 12)))


# ============================================================
# NPCs - Other animals and humans walking around the city!
# ============================================================
# "NPC" stands for Non-Player Character. These are characters
# that the computer controls, not you. They wander around the
# city on their own, making it feel alive!
#
# Each NPC has a "type" which determines what it looks like:
#   - "burrb"  = another burrb (different colors!)
#   - "human"  = a person walking around
#   - "cat"    = a little cat
#   - "dog"    = a dog


class NPC:
    """A character that wanders around the city."""

    def __init__(self, x, y, npc_type, color, detail_color):
        self.x = x
        self.y = y
        self.npc_type = npc_type  # "burrb", "human", "cat", "dog"
        self.color = color  # main body color
        self.detail_color = detail_color  # secondary color
        self.speed = random.uniform(0.5, 1.5)
        # Movement direction (in radians)
        self.angle = random.uniform(0, 2 * math.pi)
        # Timer to change direction randomly
        self.dir_timer = random.randint(60, 240)
        self.walk_frame = 0

    def update(self):
        """Move the NPC around. This is its simple 'brain'."""
        # Rocks don't move! They just sit there being a rock.
        if self.npc_type == "rock":
            return

        self.walk_frame += 1

        # Count down the direction timer
        self.dir_timer -= 1
        if self.dir_timer <= 0:
            # Pick a new random direction
            self.angle = random.uniform(0, 2 * math.pi)
            self.speed = random.uniform(0.5, 1.5)
            self.dir_timer = random.randint(60, 240)

        # Move in current direction
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed

        # Check if they'd walk into a building
        npc_rect = pygame.Rect(new_x - 6, new_y - 6, 12, 12)
        blocked = False
        for b in buildings:
            if npc_rect.colliderect(b.get_rect()):
                blocked = True
                break

        # Stay inside the world
        if new_x < 30 or new_x > WORLD_WIDTH - 30:
            blocked = True
        if new_y < 30 or new_y > WORLD_HEIGHT - 30:
            blocked = True

        if blocked:
            # Turn around and try a new direction
            self.angle = random.uniform(0, 2 * math.pi)
            self.dir_timer = random.randint(30, 120)
        else:
            self.x = new_x
            self.y = new_y


# Spawn NPCs throughout the city!
npcs = []

# NPC color palettes - ALL burrbs now! Every color EXCEPT light blue
# because light blue is the player's color.
burrb_colors = [
    ((220, 80, 80), (180, 50, 50)),  # red burrb
    ((80, 200, 80), (40, 150, 40)),  # green burrb
    ((220, 180, 50), (180, 140, 30)),  # yellow burrb
    ((200, 100, 200), (160, 60, 160)),  # purple burrb
    ((220, 140, 60), (180, 100, 30)),  # orange burrb
    ((60, 60, 60), (30, 30, 30)),  # dark/black burrb
    ((240, 240, 240), (200, 200, 200)),  # white burrb
    ((220, 100, 160), (180, 60, 120)),  # pink burrb
    ((160, 120, 60), (120, 80, 30)),  # brown burrb
    ((100, 220, 200), (60, 180, 160)),  # teal burrb
    ((180, 80, 80), (140, 40, 40)),  # dark red burrb
    ((100, 60, 160), (70, 30, 130)),  # indigo burrb
    ((220, 200, 160), (180, 160, 120)),  # cream burrb
    ((50, 120, 50), (30, 80, 30)),  # dark green burrb
    ((200, 60, 200), (160, 30, 160)),  # magenta burrb
]

# Place NPCs across the whole world!
# They're ALL burrbs - burrbs everywhere in every biome!
for _ in range(80):
    # Pick a random spot in the world
    nx = random.randint(100, WORLD_WIDTH - 100)
    ny = random.randint(100, WORLD_HEIGHT - 100)

    # Make sure they don't spawn inside a building
    spawn_rect = pygame.Rect(nx - 10, ny - 10, 20, 20)
    in_building = any(spawn_rect.colliderect(b.get_rect()) for b in buildings)
    if in_building:
        continue

    color, detail = random.choice(burrb_colors)
    npcs.append(NPC(nx, ny, "burrb", color, detail))


# ============================================================
# CARS - vehicles driving on the roads!
# ============================================================
# Cars drive along the road grid. They go in one direction
# (horizontal or vertical) and when they reach an intersection,
# they might turn or keep going straight.


class Car:
    """A car that drives along the roads."""

    def __init__(self, x, y, direction, color, detail_color, car_type):
        self.x = x
        self.y = y
        # direction: 0=right, 1=down, 2=left, 3=up
        self.direction = direction
        self.color = color
        self.detail_color = detail_color
        self.car_type = car_type  # "sedan", "truck", "taxi", "sport"
        self.speed = random.uniform(1.2, 2.5)
        # How long until we check for a turn at an intersection
        self.turn_cooldown = 0

    def update(self):
        """Move the car along the road."""
        # Move in current direction
        if self.direction == 0:  # right
            self.x += self.speed
        elif self.direction == 1:  # down
            self.y += self.speed
        elif self.direction == 2:  # left
            self.x -= self.speed
        elif self.direction == 3:  # up
            self.y -= self.speed

        # Wrap around when leaving the city (cars loop within city)
        margin = 50
        if self.x > CITY_X2 + margin:
            self.x = CITY_X1 - margin
        elif self.x < CITY_X1 - margin:
            self.x = CITY_X2 + margin
        if self.y > CITY_Y2 + margin:
            self.y = CITY_Y1 - margin
        elif self.y < CITY_Y1 - margin:
            self.y = CITY_Y2 + margin

        # Check if we're at an intersection and maybe turn
        self.turn_cooldown -= 1
        if self.turn_cooldown <= 0:
            step = BLOCK_SIZE + ROAD_WIDTH
            # Are we near the center of an intersection?
            # Intersections happen where horizontal and vertical roads cross
            near_h_road = False
            near_v_road = False
            for bx in range(CITY_X1, CITY_X2 + step, step):
                road_x = bx + BLOCK_SIZE
                if abs(self.x - (road_x + ROAD_WIDTH // 2)) < 8:
                    near_v_road = True
                    break
            for by in range(CITY_Y1, CITY_Y2 + step, step):
                road_y = by + BLOCK_SIZE
                if abs(self.y - (road_y + ROAD_WIDTH // 2)) < 8:
                    near_h_road = True
                    break

            if near_h_road and near_v_road:
                # At an intersection! Maybe turn
                choice = random.random()
                if choice < 0.3:
                    # Turn right
                    self.direction = (self.direction + 1) % 4
                    self.turn_cooldown = 60
                elif choice < 0.5:
                    # Turn left
                    self.direction = (self.direction - 1) % 4
                    self.turn_cooldown = 60
                else:
                    # Keep going straight
                    self.turn_cooldown = 30


# Car color palettes
car_colors = [
    ((200, 40, 40), (150, 30, 30), "sedan"),  # red sedan
    ((40, 80, 180), (30, 60, 140), "sedan"),  # blue sedan
    ((60, 60, 60), (40, 40, 40), "sedan"),  # black sedan
    ((220, 220, 220), (180, 180, 180), "sedan"),  # white sedan
    ((40, 140, 60), (30, 100, 40), "sedan"),  # green sedan
    ((255, 200, 0), (200, 160, 0), "taxi"),  # yellow taxi
    ((255, 200, 0), (200, 160, 0), "taxi"),  # yellow taxi (more taxis!)
    ((120, 80, 50), (90, 60, 35), "truck"),  # brown truck
    ((80, 80, 100), (60, 60, 80), "truck"),  # gray truck
    ((200, 50, 50), (160, 30, 30), "sport"),  # red sports car
    ((50, 50, 200), (30, 30, 160), "sport"),  # blue sports car
    ((240, 140, 20), (200, 110, 10), "sport"),  # orange sports car
]

# Spawn cars on city roads only
cars = []
step = BLOCK_SIZE + ROAD_WIDTH

# Cars on horizontal roads (city only)
for by in range(CITY_Y1, CITY_Y2, step):
    road_y = by + BLOCK_SIZE + ROAD_WIDTH // 2
    # Spawn several cars per road
    num_cars = random.randint(2, 4)
    for _ in range(num_cars):
        cx = random.randint(CITY_X1 + 50, CITY_X2 - 50)
        # Drive on the right side of the road
        direction = random.choice([0, 2])  # right or left
        if direction == 0:
            cy = road_y + ROAD_WIDTH // 4  # right side (bottom lane)
        else:
            cy = road_y - ROAD_WIDTH // 4  # left side (top lane)
        color, detail, ctype = random.choice(car_colors)
        cars.append(Car(cx, cy, direction, color, detail, ctype))

# Cars on vertical roads (city only)
for bx in range(CITY_X1, CITY_X2, step):
    road_x = bx + BLOCK_SIZE + ROAD_WIDTH // 2
    num_cars = random.randint(2, 4)
    for _ in range(num_cars):
        cy = random.randint(CITY_Y1 + 50, CITY_Y2 - 50)
        direction = random.choice([1, 3])  # down or up
        if direction == 1:
            cx = road_x + ROAD_WIDTH // 4  # right side
        else:
            cx = road_x - ROAD_WIDTH // 4  # left side
        color, detail, ctype = random.choice(car_colors)
        cars.append(Car(cx, cy, direction, color, detail, ctype))


# ============================================================
# DRAW FUNCTIONS
# ============================================================
def draw_road_grid(surface, cam_x, cam_y):
    """Draw the roads between city blocks (only in the city biome!)."""
    city_w = CITY_X2 - CITY_X1
    city_h = CITY_Y2 - CITY_Y1
    # Horizontal roads
    for by in range(CITY_Y1, CITY_Y2 + BLOCK_SIZE, BLOCK_SIZE + ROAD_WIDTH):
        road_y = by + BLOCK_SIZE
        ry = road_y - cam_y
        # Road surface
        pygame.draw.rect(surface, ROAD_COLOR, (CITY_X1 - cam_x, ry, city_w, ROAD_WIDTH))
        # Center line (dashed)
        center_y = ry + ROAD_WIDTH // 2
        for dx in range(CITY_X1, CITY_X2, 40):
            lx = dx - cam_x
            pygame.draw.rect(surface, ROAD_LINE, (lx, center_y - 1, 20, 3))
        # Sidewalks
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (CITY_X1 - cam_x, ry - SIDEWALK_WIDTH, city_w, SIDEWALK_WIDTH),
        )
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (CITY_X1 - cam_x, ry + ROAD_WIDTH, city_w, SIDEWALK_WIDTH),
        )

    # Vertical roads
    for bx in range(CITY_X1, CITY_X2 + BLOCK_SIZE, BLOCK_SIZE + ROAD_WIDTH):
        road_x = bx + BLOCK_SIZE
        rx = road_x - cam_x
        pygame.draw.rect(surface, ROAD_COLOR, (rx, CITY_Y1 - cam_y, ROAD_WIDTH, city_h))
        # Center line
        center_x = rx + ROAD_WIDTH // 2
        for dy in range(CITY_Y1, CITY_Y2, 40):
            ly = dy - cam_y
            pygame.draw.rect(surface, ROAD_LINE, (center_x - 1, ly, 3, 20))
        # Sidewalks
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (rx - SIDEWALK_WIDTH, CITY_Y1 - cam_y, SIDEWALK_WIDTH, city_h),
        )
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (rx + ROAD_WIDTH, CITY_Y1 - cam_y, SIDEWALK_WIDTH, city_h),
        )


def draw_tree(surface, x, y, size, cam_x, cam_y):
    """Draw a tree at the given world position."""
    sx = x - cam_x
    sy = y - cam_y
    # Trunk (slightly tapered using a polygon for smoothness)
    pygame.draw.polygon(
        surface,
        BROWN,
        [
            (sx - 2, sy + size // 3),
            (sx + 2, sy + size // 3),
            (sx + 3, sy + size // 2),
            (sx - 3, sy + size // 2),
        ],
    )
    # Leaves (multiple overlapping circles for a bushy, round canopy)
    r = size // 2
    leaf_y = sy - size // 4
    pygame.draw.circle(surface, DARK_GREEN, (sx, leaf_y), r)
    pygame.draw.circle(surface, GREEN, (sx - r // 3, leaf_y - r // 4), r - 1)
    pygame.draw.circle(surface, GREEN, (sx + r // 3, leaf_y + r // 5), r - 2)
    pygame.draw.circle(surface, (90, 190, 70), (sx - r // 4, leaf_y - r // 3), r // 2)
    pygame.draw.circle(surface, (100, 200, 80), (sx + r // 5, leaf_y - r // 2), r // 3)


def draw_biome_object(surface, x, y, kind, size, cam_x, cam_y):
    """Draw a biome-specific decoration at the given world position."""
    sx = int(x - cam_x)
    sy = int(y - cam_y)
    # Skip if off-screen
    if sx < -60 or sx > SCREEN_WIDTH + 60 or sy < -60 or sy > SCREEN_HEIGHT + 60:
        return

    if kind == "mushroom":
        # Red cap with white spots on a stubby stem
        pygame.draw.rect(surface, (180, 160, 120), (sx - 2, sy, 4, size // 2))
        pygame.draw.ellipse(
            surface, (200, 40, 40), (sx - size // 2, sy - size // 3, size, size // 2)
        )
        # White spots
        pygame.draw.circle(surface, (255, 255, 255), (sx - 2, sy - size // 5), 2)
        pygame.draw.circle(surface, (255, 255, 255), (sx + 3, sy - size // 4), 1)

    elif kind == "flower":
        # Colorful flower with petals
        stem_h = size
        pygame.draw.line(surface, (60, 140, 40), (sx, sy), (sx, sy + stem_h), 2)
        colors = [(255, 80, 80), (255, 200, 50), (200, 100, 255), (255, 150, 200)]
        c = colors[(x + y) % len(colors)]
        for angle_i in range(5):
            a = angle_i * (math.pi * 2 / 5)
            px = sx + int(math.cos(a) * size * 0.6)
            py_pos = sy + int(math.sin(a) * size * 0.6)
            pygame.draw.circle(surface, c, (px, py_pos), size // 3)
        pygame.draw.circle(surface, (255, 220, 50), (sx, sy), size // 4)

    elif kind == "snow_tree":
        # Pine tree covered in snow
        # Trunk
        pygame.draw.rect(surface, (100, 70, 40), (sx - 2, sy + size // 3, 4, size // 2))
        # Snowy pine layers (triangle shape, white-tipped)
        for layer in range(3):
            w = size - layer * 4
            h = size // 4
            ly = sy - layer * (size // 5) + size // 6
            # Dark green pine
            pts = [(sx, ly - h), (sx - w // 2, ly), (sx + w // 2, ly)]
            pygame.draw.polygon(surface, (30, 80, 30), pts)
            # Snow on top
            snow_pts = [
                (sx, ly - h),
                (sx - w // 3, ly - h // 2),
                (sx + w // 3, ly - h // 2),
            ]
            pygame.draw.polygon(surface, (240, 245, 255), snow_pts)

    elif kind == "snowman":
        # Three stacked circles with a hat and carrot nose!
        # Bottom ball
        pygame.draw.circle(surface, (240, 240, 250), (sx, sy + size // 2), size // 2)
        # Middle ball
        mid_r = size // 3
        pygame.draw.circle(surface, (235, 235, 245), (sx, sy), mid_r)
        # Head
        head_r = size // 4
        pygame.draw.circle(
            surface, (230, 230, 240), (sx, sy - mid_r - head_r + 2), head_r
        )
        # Eyes
        pygame.draw.circle(surface, (20, 20, 20), (sx - 3, sy - mid_r - head_r), 2)
        pygame.draw.circle(surface, (20, 20, 20), (sx + 3, sy - mid_r - head_r), 2)
        # Carrot nose
        nose_y = sy - mid_r - head_r + 3
        pygame.draw.polygon(
            surface,
            (255, 140, 30),
            [(sx, nose_y), (sx + 6, nose_y + 2), (sx, nose_y + 3)],
        )
        # Hat
        hat_y = sy - mid_r - head_r * 2 + 2
        pygame.draw.rect(
            surface, (30, 30, 30), (sx - head_r, hat_y + head_r // 2, head_r * 2, 3)
        )
        pygame.draw.rect(
            surface, (30, 30, 30), (sx - head_r // 2, hat_y, head_r, head_r // 2 + 2)
        )

    elif kind == "ice_patch":
        # Shiny blue-white oval on the ground
        ice_surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        pygame.draw.ellipse(ice_surf, (180, 210, 240, 140), (0, 0, size * 2, size))
        # Shine highlight
        pygame.draw.ellipse(
            ice_surf, (220, 240, 255, 100), (size // 3, size // 6, size, size // 2)
        )
        surface.blit(ice_surf, (sx - size, sy - size // 2))

    elif kind == "dead_tree":
        # Gray/brown trunk with no leaves, just bare branches
        pygame.draw.line(
            surface, (80, 60, 40), (sx, sy + size // 2), (sx, sy - size // 3), 3
        )
        # Branches
        pygame.draw.line(
            surface,
            (70, 55, 35),
            (sx, sy - size // 6),
            (sx - size // 3, sy - size // 2),
            2,
        )
        pygame.draw.line(
            surface,
            (70, 55, 35),
            (sx, sy - size // 4),
            (sx + size // 3, sy - size // 2 + 2),
            2,
        )
        pygame.draw.line(
            surface, (60, 50, 30), (sx, sy), (sx - size // 4, sy - size // 5), 1
        )

    elif kind == "lily_pad":
        # Green circle with a little wedge cut out
        pygame.draw.circle(surface, (40, 120, 40), (sx, sy), size // 2)
        pygame.draw.circle(surface, (50, 140, 50), (sx - 1, sy - 1), size // 2 - 1)
        # Little notch
        pygame.draw.line(surface, (60, 80, 50), (sx, sy), (sx + size // 2, sy - 2), 2)

    elif kind == "puddle":
        # Murky dark water pool
        puddle_surf = pygame.Surface((size * 2, size), pygame.SRCALPHA)
        pygame.draw.ellipse(puddle_surf, (40, 55, 35, 160), (0, 0, size * 2, size))
        pygame.draw.ellipse(
            puddle_surf, (50, 65, 45, 80), (size // 4, size // 6, size, size // 2)
        )
        surface.blit(puddle_surf, (sx - size, sy - size // 2))

    elif kind == "cactus":
        # Green cactus with arms
        # Main trunk
        pygame.draw.rect(surface, (40, 140, 40), (sx - 3, sy - size // 2, 6, size))
        pygame.draw.rect(surface, (50, 160, 50), (sx - 2, sy - size // 2, 4, size))
        # Left arm
        arm_y = sy - size // 4
        pygame.draw.rect(
            surface, (40, 140, 40), (sx - size // 3, arm_y - 3, size // 3, 6)
        )
        pygame.draw.rect(
            surface, (40, 140, 40), (sx - size // 3, arm_y - size // 4, 6, size // 4)
        )
        # Right arm
        arm_y2 = sy - size // 6
        pygame.draw.rect(surface, (40, 140, 40), (sx, arm_y2 - 3, size // 3, 6))
        pygame.draw.rect(
            surface,
            (40, 140, 40),
            (sx + size // 3 - 6, arm_y2 - size // 3, 6, size // 3),
        )

    elif kind == "rock":
        # Gray/brown rock
        pts = [
            (sx - size // 2, sy + size // 4),
            (sx - size // 3, sy - size // 3),
            (sx + size // 4, sy - size // 2),
            (sx + size // 2, sy - size // 6),
            (sx + size // 3, sy + size // 3),
        ]
        pygame.draw.polygon(surface, (140, 130, 120), pts)
        pygame.draw.polygon(surface, (120, 110, 100), pts, 2)
        # Highlight
        pygame.draw.line(surface, (170, 160, 150), pts[1], pts[2], 1)

    elif kind == "tumbleweed":
        # Brown scribble ball
        pygame.draw.circle(surface, (160, 130, 80), (sx, sy), size // 2)
        pygame.draw.circle(surface, (140, 110, 60), (sx, sy), size // 2, 1)
        # Scribble lines
        for i in range(4):
            a = i * 0.8
            x1 = sx + int(math.cos(a) * size * 0.3)
            y1 = sy + int(math.sin(a) * size * 0.3)
            x2 = sx + int(math.cos(a + 2) * size * 0.3)
            y2 = sy + int(math.sin(a + 2) * size * 0.3)
            pygame.draw.line(surface, (120, 90, 50), (x1, y1), (x2, y2), 1)


def draw_biome_ground(surface, cam_x, cam_y):
    """Draw the ground color for each biome that's visible on screen."""
    # Figure out which part of the world is visible
    view_x1 = int(cam_x)
    view_y1 = int(cam_y)
    view_x2 = view_x1 + SCREEN_WIDTH
    view_y2 = view_y1 + SCREEN_HEIGHT

    # We'll paint the ground in chunks for performance
    chunk = 100
    for wx in range(
        max(0, (view_x1 // chunk) * chunk), min(WORLD_WIDTH, view_x2 + chunk), chunk
    ):
        for wy in range(
            max(0, (view_y1 // chunk) * chunk),
            min(WORLD_HEIGHT, view_y2 + chunk),
            chunk,
        ):
            biome = get_biome(wx + chunk // 2, wy + chunk // 2)
            color = BIOME_COLORS[biome]
            rx = wx - cam_x
            ry = wy - cam_y
            pygame.draw.rect(surface, color, (rx, ry, chunk + 1, chunk + 1))


def draw_minimap(surface):
    """Draw a small minimap in the corner so you don't get lost!"""
    # Minimap size and position (bottom-left corner)
    mm_w = 140
    mm_h = 140
    mm_x = 8
    mm_y = SCREEN_HEIGHT - mm_h - 8
    mm_scale_x = mm_w / WORLD_WIDTH
    mm_scale_y = mm_h / WORLD_HEIGHT

    # Background
    mm_surf = pygame.Surface((mm_w, mm_h), pygame.SRCALPHA)

    # Draw biome colors
    mm_chunk = WORLD_WIDTH // 14  # ~714px chunks
    for wx in range(0, WORLD_WIDTH, mm_chunk):
        for wy in range(0, WORLD_HEIGHT, mm_chunk):
            biome = get_biome(wx + mm_chunk // 2, wy + mm_chunk // 2)
            color = BIOME_COLORS[biome]
            rx = int(wx * mm_scale_x)
            ry = int(wy * mm_scale_y)
            rw = max(1, int(mm_chunk * mm_scale_x) + 1)
            rh = max(1, int(mm_chunk * mm_scale_y) + 1)
            pygame.draw.rect(mm_surf, color, (rx, ry, rw, rh))

    # Draw buildings as tiny dots
    for b in buildings:
        bx = int(b.x * mm_scale_x)
        by = int(b.y * mm_scale_y)
        pygame.draw.rect(mm_surf, (100, 100, 100), (bx, by, 2, 2))

    # Draw the player as a bright dot
    px = int(burrb_x * mm_scale_x)
    py = int(burrb_y * mm_scale_y)
    pygame.draw.circle(mm_surf, (255, 50, 50), (px, py), 3)
    pygame.draw.circle(mm_surf, (255, 200, 200), (px, py), 1)

    # Border
    pygame.draw.rect(mm_surf, (200, 200, 200), (0, 0, mm_w, mm_h), 2)

    # Semi-transparent background behind minimap
    bg_surf = pygame.Surface((mm_w + 4, mm_h + 4), pygame.SRCALPHA)
    pygame.draw.rect(
        bg_surf, (0, 0, 0, 120), (0, 0, mm_w + 4, mm_h + 4), border_radius=4
    )
    surface.blit(bg_surf, (mm_x - 2, mm_y - 2))
    surface.blit(mm_surf, (mm_x, mm_y))


def draw_burrb(surface, x, y, cam_x, cam_y, facing_left, walk_frame):
    """
    Draw the burrb character!

    The burrb has:
    - Square blue body with a swirl
    - Spiky feathers on top
    - Teardrop eye
    - Orange beak
    - Thin legs with feet

    Sized to match the NPCs in the city (about 18px body).
    """
    sx = x - cam_x
    sy = y - cam_y
    body_w = 18
    body_h = 16
    bx = sx - body_w // 2
    by = sy - body_h // 2

    # Leg animation - the legs swing back and forth when walking
    leg_offset = math.sin(walk_frame * 0.3) * 3 if walk_frame > 0 else 0

    # Legs (drawn behind body)
    leg_y = by + body_h
    leg1_x = bx + 5
    leg2_x = bx + body_w - 5
    # Left leg
    pygame.draw.line(
        surface, BLACK, (leg1_x, leg_y), (leg1_x + leg_offset, leg_y + 7), 2
    )
    # Foot
    pygame.draw.line(
        surface,
        BLACK,
        (leg1_x + leg_offset, leg_y + 7),
        (leg1_x + leg_offset - 3, leg_y + 7),
        1,
    )
    pygame.draw.line(
        surface,
        BLACK,
        (leg1_x + leg_offset, leg_y + 7),
        (leg1_x + leg_offset + 2, leg_y + 7),
        1,
    )
    # Right leg
    pygame.draw.line(
        surface, BLACK, (leg2_x, leg_y), (leg2_x - leg_offset, leg_y + 7), 2
    )
    # Foot
    pygame.draw.line(
        surface,
        BLACK,
        (leg2_x - leg_offset, leg_y + 7),
        (leg2_x - leg_offset - 3, leg_y + 7),
        1,
    )
    pygame.draw.line(
        surface,
        BLACK,
        (leg2_x - leg_offset, leg_y + 7),
        (leg2_x - leg_offset + 2, leg_y + 7),
        1,
    )

    # Body - main blue rectangle with nicely rounded corners
    pygame.draw.rect(surface, BURRB_BLUE, (bx, by, body_w, body_h), border_radius=4)
    # Lighter blue highlight
    pygame.draw.rect(
        surface,
        BURRB_LIGHT_BLUE,
        (bx + 2, by + 2, body_w - 6, body_h - 6),
        border_radius=3,
    )
    # Outline
    pygame.draw.rect(surface, BLACK, (bx, by, body_w, body_h), 1, border_radius=4)

    # Swirl on the body
    swirl_cx = bx + body_w // 2 - 1
    swirl_cy = by + body_h // 2 + 1
    # Draw swirl as a series of arc segments
    for i in range(8):
        angle_start = i * 0.5
        radius = 1.5 + i * 0.6
        ax = swirl_cx + math.cos(angle_start) * radius * 0.3
        ay = swirl_cy + math.sin(angle_start) * radius * 0.3
        ax2 = swirl_cx + math.cos(angle_start + 0.5) * (radius + 0.6) * 0.3
        ay2 = swirl_cy + math.sin(angle_start + 0.5) * (radius + 0.6) * 0.3
        pygame.draw.line(
            surface, BURRB_DARK_BLUE, (int(ax), int(ay)), (int(ax2), int(ay2)), 1
        )

    # Spiky feathers on top
    spike_base_y = by
    spike_x_center = bx + body_w // 2
    spikes = [(-4, -5), (-1, -7), (2, -8), (4, -6), (6, -4)]
    if facing_left:
        spikes = [(-s[0], s[1]) for s in spikes]
    for ddx, ddy in spikes:
        tip_x = spike_x_center + ddx
        tip_y = spike_base_y + ddy
        base_l = spike_x_center + ddx - 2
        base_r = spike_x_center + ddx + 2
        pygame.draw.polygon(
            surface,
            BURRB_BLUE,
            [(base_l, spike_base_y), (tip_x, tip_y), (base_r, spike_base_y)],
        )
        pygame.draw.polygon(
            surface,
            BURRB_LIGHT_BLUE,
            [
                (base_l + 1, spike_base_y),
                (tip_x, tip_y + 1),
                (base_r - 1, spike_base_y),
            ],
        )

    # Eye (teardrop shape)
    if facing_left:
        eye_x = bx + 4
    else:
        eye_x = bx + body_w - 8
    eye_y = by + 4
    # Teardrop: circle + triangle pointing down
    pygame.draw.circle(surface, BURRB_EYE, (eye_x + 2, eye_y + 2), 2)
    pygame.draw.polygon(
        surface,
        BURRB_EYE,
        [(eye_x, eye_y + 2), (eye_x + 4, eye_y + 2), (eye_x + 2, eye_y + 6)],
    )
    # Small highlight in eye
    pygame.draw.circle(surface, WHITE, (eye_x + 1, eye_y + 1), 1)

    # Beak (orange, pointing in facing direction)
    if facing_left:
        beak_x = bx - 1
        beak_points = [(beak_x, by + 7), (beak_x - 5, by + 8), (beak_x, by + 10)]
    else:
        beak_x = bx + body_w + 1
        beak_points = [(beak_x, by + 7), (beak_x + 5, by + 8), (beak_x, by + 10)]
    pygame.draw.polygon(surface, BURRB_ORANGE, beak_points)
    pygame.draw.polygon(surface, (200, 130, 20), beak_points, 1)


# NPC DRAWING FUNCTIONS
# ============================================================


def draw_npc_topdown(surface, npc, cam_x, cam_y):
    """
    Draw an NPC in top-down mode. Each type looks different:
    - Burrbs are small squares with spikes
    - Humans are circles with a body rectangle
    - Cats are small ovals with pointy ears
    - Dogs are ovals with a tail
    """
    sx = int(npc.x - cam_x)
    sy = int(npc.y - cam_y)
    # Don't draw if off screen
    if sx < -30 or sx > SCREEN_WIDTH + 30 or sy < -30 or sy > SCREEN_HEIGHT + 30:
        return

    leg_offset = math.sin(npc.walk_frame * 0.25) * 3

    if npc.npc_type == "burrb":
        # Small square body like the player burrb
        size = 16
        # Legs
        pygame.draw.line(
            surface,
            BLACK,
            (sx - 3, sy + size // 2),
            (sx - 3 + leg_offset, sy + size // 2 + 6),
            2,
        )
        pygame.draw.line(
            surface,
            BLACK,
            (sx + 3, sy + size // 2),
            (sx + 3 - leg_offset, sy + size // 2 + 6),
            2,
        )
        # Body
        pygame.draw.rect(
            surface,
            npc.color,
            (sx - size // 2, sy - size // 2, size, size),
            border_radius=2,
        )
        pygame.draw.rect(
            surface,
            BLACK,
            (sx - size // 2, sy - size // 2, size, size),
            1,
            border_radius=2,
        )
        # Eye
        eye_x = sx + 2
        pygame.draw.circle(surface, npc.detail_color, (eye_x, sy - 2), 2)
        # Spikes on top
        for i in range(3):
            spike_x = sx - 4 + i * 4
            pygame.draw.polygon(
                surface,
                npc.color,
                [
                    (spike_x - 1, sy - size // 2),
                    (spike_x, sy - size // 2 - 5),
                    (spike_x + 1, sy - size // 2),
                ],
            )
        # Beak
        beak_dir = 1 if math.cos(npc.angle) > 0 else -1
        beak_x = sx + beak_dir * (size // 2 + 1)
        pygame.draw.polygon(
            surface,
            BURRB_ORANGE,
            [
                (beak_x, sy - 2),
                (beak_x + beak_dir * 5, sy),
                (beak_x, sy + 2),
            ],
        )

    elif npc.npc_type == "human":
        # Head (circle)
        pygame.draw.circle(surface, npc.color, (sx, sy - 8), 5)
        pygame.draw.circle(surface, BLACK, (sx, sy - 8), 5, 1)
        # Body (rectangle)
        pygame.draw.rect(surface, npc.detail_color, (sx - 4, sy - 3, 8, 12))
        pygame.draw.rect(surface, BLACK, (sx - 4, sy - 3, 8, 12), 1)
        # Legs
        pygame.draw.line(
            surface, BLACK, (sx - 2, sy + 9), (sx - 2 + leg_offset, sy + 16), 2
        )
        pygame.draw.line(
            surface, BLACK, (sx + 2, sy + 9), (sx + 2 - leg_offset, sy + 16), 2
        )

    elif npc.npc_type == "cat":
        # Small oval body
        pygame.draw.ellipse(surface, npc.color, (sx - 6, sy - 3, 12, 8))
        pygame.draw.ellipse(surface, BLACK, (sx - 6, sy - 3, 12, 8), 1)
        # Head
        pygame.draw.circle(surface, npc.color, (sx + 4, sy - 4), 4)
        pygame.draw.circle(surface, BLACK, (sx + 4, sy - 4), 4, 1)
        # Pointy ears
        pygame.draw.polygon(
            surface, npc.color, [(sx + 2, sy - 7), (sx + 3, sy - 12), (sx + 5, sy - 7)]
        )
        pygame.draw.polygon(
            surface, npc.color, [(sx + 4, sy - 7), (sx + 6, sy - 12), (sx + 7, sy - 7)]
        )
        # Eyes
        pygame.draw.circle(surface, (200, 220, 50), (sx + 3, sy - 5), 1)
        pygame.draw.circle(surface, (200, 220, 50), (sx + 5, sy - 5), 1)
        # Tail
        tail_wave = math.sin(npc.walk_frame * 0.15) * 4
        pygame.draw.line(
            surface, npc.color, (sx - 6, sy), (sx - 12, sy - 4 + tail_wave), 2
        )
        # Legs
        pygame.draw.line(surface, BLACK, (sx - 3, sy + 4), (sx - 3, sy + 8), 1)
        pygame.draw.line(surface, BLACK, (sx + 3, sy + 4), (sx + 3, sy + 8), 1)

    elif npc.npc_type == "dog":
        # Oval body (slightly bigger than cat)
        pygame.draw.ellipse(surface, npc.color, (sx - 8, sy - 4, 16, 10))
        pygame.draw.ellipse(surface, BLACK, (sx - 8, sy - 4, 16, 10), 1)
        # Head
        pygame.draw.circle(surface, npc.color, (sx + 6, sy - 5), 5)
        pygame.draw.circle(surface, BLACK, (sx + 6, sy - 5), 5, 1)
        # Snout
        pygame.draw.ellipse(surface, npc.detail_color, (sx + 8, sy - 5, 5, 3))
        # Nose
        pygame.draw.circle(surface, BLACK, (sx + 11, sy - 4), 1)
        # Ear (floppy)
        pygame.draw.ellipse(surface, npc.detail_color, (sx + 3, sy - 9, 4, 6))
        # Eyes
        pygame.draw.circle(surface, BLACK, (sx + 5, sy - 6), 1)
        # Tail (wagging!)
        tail_wave = math.sin(npc.walk_frame * 0.2) * 5
        pygame.draw.line(
            surface, npc.color, (sx - 8, sy - 2), (sx - 13, sy - 6 + tail_wave), 2
        )
        # Legs
        pygame.draw.line(
            surface, BLACK, (sx - 4, sy + 5), (sx - 4 + leg_offset, sy + 10), 2
        )
        pygame.draw.line(
            surface, BLACK, (sx + 4, sy + 5), (sx + 4 - leg_offset, sy + 10), 2
        )

    elif npc.npc_type == "rock":
        # === ROCK (petrified NPC!) ===
        # A lumpy gray rock sitting on the ground. This used to be
        # a living creature before the burrb's tongue got it!
        # Main rock body (irregular shape from overlapping ellipses)
        pygame.draw.ellipse(surface, npc.color, (sx - 10, sy - 6, 20, 14))
        pygame.draw.ellipse(surface, npc.detail_color, (sx - 7, sy - 9, 14, 10))
        # Small bump on top
        pygame.draw.ellipse(surface, npc.color, (sx - 4, sy - 11, 10, 7))
        # Cracks (dark lines for texture)
        pygame.draw.line(surface, (60, 60, 55), (sx - 3, sy - 8), (sx + 2, sy - 2), 1)
        pygame.draw.line(surface, (60, 60, 55), (sx + 4, sy - 6), (sx + 6, sy + 1), 1)
        pygame.draw.line(surface, (60, 60, 55), (sx - 6, sy - 3), (sx - 2, sy + 3), 1)
        # Outline
        pygame.draw.ellipse(surface, (50, 50, 45), (sx - 10, sy - 6, 20, 14), 1)
        # Little highlight (shiny spot)
        pygame.draw.circle(surface, (160, 160, 150), (sx - 3, sy - 7), 2)


# ============================================================
# CAR DRAWING (top-down and first-person)
# ============================================================


def draw_car_topdown(surface, car, cam_x, cam_y):
    """
    Draw a car from above. Different car types look different!
    - sedan: normal car shape
    - truck: longer, with a cargo bed
    - taxi: sedan with a taxi sign on top
    - sport: low and sleek
    """
    sx = car.x - cam_x
    sy = car.y - cam_y

    # Skip if offscreen
    if sx < -60 or sx > SCREEN_WIDTH + 60 or sy < -60 or sy > SCREEN_HEIGHT + 60:
        return

    # Car dimensions depend on type
    if car.car_type == "truck":
        length = 28
        width = 14
    elif car.car_type == "sport":
        length = 22
        width = 11
    else:  # sedan and taxi
        length = 22
        width = 12

    # Direction determines which axis is length vs width
    # 0=right, 1=down, 2=left, 3=up
    horizontal = car.direction in (0, 2)

    if horizontal:
        hw = length // 2
        hh = width // 2
    else:
        hw = width // 2
        hh = length // 2

    body_color = car.color
    detail = car.detail_color

    # --- BODY ---
    body_rect = pygame.Rect(int(sx - hw), int(sy - hh), hw * 2, hh * 2)
    pygame.draw.rect(surface, body_color, body_rect, border_radius=4)

    # --- WHEELS (4 dark rectangles at the corners) ---
    wheel_color = (30, 30, 30)
    if horizontal:
        ww, wh = 5, 3
        offsets = [
            (-hw + 2, -hh - 1),
            (-hw + 2, hh - 2),
            (hw - 7, -hh - 1),
            (hw - 7, hh - 2),
        ]
    else:
        ww, wh = 3, 5
        offsets = [
            (-hw - 1, -hh + 2),
            (hw - 2, -hh + 2),
            (-hw - 1, hh - 7),
            (hw - 2, hh - 7),
        ]
    for ox, oy in offsets:
        pygame.draw.rect(surface, wheel_color, (int(sx + ox), int(sy + oy), ww, wh))

    # --- WINDOWS (a slightly lighter rect in the front half) ---
    win_color = (160, 200, 230)
    if horizontal:
        win_w = hw - 2
        win_h = hh - 3
        if car.direction == 0:  # facing right, windows in front-right area
            wx = int(sx + 2)
        else:  # facing left
            wx = int(sx - hw + 2)
        wy = int(sy - win_h // 2)
        pygame.draw.rect(surface, win_color, (wx, wy, win_w, win_h), border_radius=2)
    else:
        win_w = hw - 3
        win_h = hh - 2
        wx = int(sx - win_w // 2)
        if car.direction == 1:  # facing down
            wy = int(sy + 2)
        else:  # facing up
            wy = int(sx - hh + 2)
            wy = int(sy - hh + 2)
        pygame.draw.rect(surface, win_color, (wx, wy, win_w, win_h), border_radius=2)

    # --- HEADLIGHTS (two small yellow/white rects at the front) ---
    hl_color = (255, 255, 180)
    tl_color = (200, 40, 40)
    if car.direction == 0:  # right
        # headlights on right end
        pygame.draw.rect(surface, hl_color, (int(sx + hw - 2), int(sy - hh + 1), 3, 3))
        pygame.draw.rect(surface, hl_color, (int(sx + hw - 2), int(sy + hh - 4), 3, 3))
        # taillights on left end
        pygame.draw.rect(surface, tl_color, (int(sx - hw), int(sy - hh + 1), 2, 3))
        pygame.draw.rect(surface, tl_color, (int(sx - hw), int(sy + hh - 4), 2, 3))
    elif car.direction == 2:  # left
        pygame.draw.rect(surface, hl_color, (int(sx - hw - 1), int(sy - hh + 1), 3, 3))
        pygame.draw.rect(surface, hl_color, (int(sx - hw - 1), int(sy + hh - 4), 3, 3))
        pygame.draw.rect(surface, tl_color, (int(sx + hw - 1), int(sy - hh + 1), 2, 3))
        pygame.draw.rect(surface, tl_color, (int(sx + hw - 1), int(sy + hh - 4), 2, 3))
    elif car.direction == 1:  # down
        pygame.draw.rect(surface, hl_color, (int(sx - hw + 1), int(sy + hh - 2), 3, 3))
        pygame.draw.rect(surface, hl_color, (int(sx + hw - 4), int(sy + hh - 2), 3, 3))
        pygame.draw.rect(surface, tl_color, (int(sx - hw + 1), int(sy - hh), 3, 2))
        pygame.draw.rect(surface, tl_color, (int(sx + hw - 4), int(sy - hh), 3, 2))
    elif car.direction == 3:  # up
        pygame.draw.rect(surface, hl_color, (int(sx - hw + 1), int(sy - hh - 1), 3, 3))
        pygame.draw.rect(surface, hl_color, (int(sx + hw - 4), int(sy - hh - 1), 3, 3))
        pygame.draw.rect(surface, tl_color, (int(sx - hw + 1), int(sy + hh - 1), 3, 2))
        pygame.draw.rect(surface, tl_color, (int(sx + hw - 4), int(sy + hh - 1), 3, 2))

    # --- TAXI SIGN (little yellow box on roof) ---
    if car.car_type == "taxi":
        sign_color = (255, 255, 100)
        pygame.draw.rect(
            surface, sign_color, (int(sx - 3), int(sy - 3), 6, 6), border_radius=2
        )
        pygame.draw.rect(
            surface, (180, 180, 0), (int(sx - 3), int(sy - 3), 6, 6), 1, border_radius=2
        )

    # --- TRUCK CARGO BED (darker rear section) ---
    if car.car_type == "truck":
        if car.direction == 0:  # right - cargo on left/rear
            pygame.draw.rect(
                surface, detail, (int(sx - hw), int(sy - hh + 2), hw - 2, hh * 2 - 4)
            )
        elif car.direction == 2:  # left - cargo on right/rear
            pygame.draw.rect(
                surface, detail, (int(sx + 2), int(sy - hh + 2), hw - 2, hh * 2 - 4)
            )
        elif car.direction == 1:  # down - cargo on top/rear
            pygame.draw.rect(
                surface, detail, (int(sx - hw + 2), int(sy - hh), hw * 2 - 4, hh - 2)
            )
        elif car.direction == 3:  # up - cargo on bottom/rear
            pygame.draw.rect(
                surface, detail, (int(sx - hw + 2), int(sy + 2), hw * 2 - 4, hh - 2)
            )

    # --- SPORT CAR STRIPE (racing stripe down the middle) ---
    if car.car_type == "sport":
        stripe_color = (255, 255, 255)
        if horizontal:
            pygame.draw.line(
                surface,
                stripe_color,
                (int(sx - hw + 3), int(sy)),
                (int(sx + hw - 3), int(sy)),
                1,
            )
        else:
            pygame.draw.line(
                surface,
                stripe_color,
                (int(sx), int(sy - hh + 3)),
                (int(sx), int(sy + hh - 3)),
                1,
            )

    # Outline
    pygame.draw.rect(surface, (20, 20, 20), body_rect, 1, border_radius=4)


# ============================================================
# INTERIOR DRAWING AND COLLISION
# ============================================================


def can_move_interior(bld, x, y):
    """Check if the burrb can move to (x,y) inside a building."""
    tile = bld.interior_tile
    # Check a small rect around the burrb
    for check_x, check_y in [
        (x - 6, y - 6),
        (x + 6, y - 6),
        (x - 6, y + 6),
        (x + 6, y + 6),
    ]:
        col = int(check_x) // tile
        row = int(check_y) // tile
        if row < 0 or row >= bld.interior_h or col < 0 or col >= bld.interior_w:
            return False
        cell = bld.interior[row][col]
        if cell in (
            Building.WALL,
            Building.FURNITURE,
            Building.TV,
            Building.CLOSET,
            Building.BED,
        ):
            return False
    return True


def get_nearby_door_building(bx, by):
    """Check if the burrb is near any building's door (outside)."""
    for b in buildings:
        # Door center position
        door_cx = b.door_x + 8
        door_cy = b.door_y + 24  # bottom of door
        dx = bx - door_cx
        dy = by - door_cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 30:
            return b
    return None


def is_at_interior_door(bld, x, y):
    """Check if the burrb is near the door inside a building."""
    tile = bld.interior_tile
    door_x = bld.interior_door_col * tile + tile // 2
    door_y = bld.interior_door_row * tile + tile // 2
    dx = x - door_x
    dy = y - door_y
    return math.sqrt(dx * dx + dy * dy) < tile * 1.5


def draw_interior_topdown(surface, bld, px, py):
    """
    Draw the inside of a building in top-down mode!
    The interior fills the whole screen so it feels like
    you've gone inside.
    """
    tile = bld.interior_tile
    total_w = bld.interior_w * tile
    total_h = bld.interior_h * tile

    # Camera offset to center on the player
    cam_x = px - SCREEN_WIDTH // 2
    cam_y = py - SCREEN_HEIGHT // 2

    # Background
    screen.fill((40, 35, 30))

    # Draw the interior grid
    for row in range(bld.interior_h):
        for col in range(bld.interior_w):
            sx = col * tile - cam_x
            sy = row * tile - cam_y

            # Skip if off screen
            if (
                sx + tile < 0
                or sx > SCREEN_WIDTH
                or sy + tile < 0
                or sy > SCREEN_HEIGHT
            ):
                continue

            cell = bld.interior[row][col]

            if cell == Building.FLOOR or cell == Building.DOOR_TILE:
                # Floor tiles (checkerboard pattern for texture)
                if (row + col) % 2 == 0:
                    floor_c = bld.floor_color
                else:
                    floor_c = (
                        max(0, bld.floor_color[0] - 15),
                        max(0, bld.floor_color[1] - 15),
                        max(0, bld.floor_color[2] - 15),
                    )
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))

                # Door tile gets a special marker
                if cell == Building.DOOR_TILE:
                    pygame.draw.rect(
                        surface, BROWN, (sx + 2, sy + 2, tile - 4, tile - 4)
                    )
                    pygame.draw.rect(
                        surface, (100, 60, 30), (sx + 2, sy + 2, tile - 4, tile - 4), 1
                    )
                    # "EXIT" hint
                    if tile > 16:
                        exit_font = pygame.font.Font(None, 16)
                        exit_text = exit_font.render("EXIT", True, YELLOW)
                        surface.blit(exit_text, (sx + 2, sy + tile // 2 - 4))

            elif cell == Building.WALL:
                # Walls
                pygame.draw.rect(surface, bld.wall_interior_color, (sx, sy, tile, tile))
                pygame.draw.rect(surface, BLACK, (sx, sy, tile, tile), 1)

            elif cell == Building.FURNITURE:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # Furniture on top (brown wooden look)
                margin = 2
                pygame.draw.rect(
                    surface,
                    bld.furniture_color,
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    (100, 60, 25),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    1,
                    border_radius=2,
                )
                # Wood grain lines
                for i in range(2, tile - 4, 5):
                    pygame.draw.line(
                        surface,
                        (120, 75, 35),
                        (sx + margin + 1, sy + margin + i),
                        (sx + tile - margin - 1, sy + margin + i),
                        1,
                    )

            elif cell == Building.SOFA:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # Blue sofa cushion!
                margin = 2
                pygame.draw.rect(
                    surface,
                    (80, 120, 200),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=4,
                )
                # Sofa back (darker blue strip at top)
                pygame.draw.rect(
                    surface,
                    (60, 90, 160),
                    (sx + margin, sy + margin, tile - margin * 2, 6),
                    border_radius=2,
                )
                # Cushion line
                pygame.draw.line(
                    surface,
                    (70, 105, 180),
                    (sx + tile // 2, sy + margin + 6),
                    (sx + tile // 2, sy + tile - margin),
                    1,
                )
                # Outline
                pygame.draw.rect(
                    surface,
                    (40, 60, 120),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    1,
                    border_radius=4,
                )

            elif cell == Building.TV:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # TV screen (dark rectangle with bright image)
                margin = 3
                # TV body
                pygame.draw.rect(
                    surface,
                    (30, 30, 30),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=2,
                )
                # Screen (bright blue-ish glow - it's on!)
                pygame.draw.rect(
                    surface,
                    (100, 180, 255),
                    (
                        sx + margin + 2,
                        sy + margin + 2,
                        tile - margin * 2 - 4,
                        tile - margin * 2 - 4,
                    ),
                    border_radius=1,
                )
                # Little stand at the bottom
                pygame.draw.rect(
                    surface,
                    (50, 50, 50),
                    (sx + tile // 2 - 3, sy + tile - margin, 6, 2),
                )

            elif cell == Building.CLOSET:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                margin = 2
                if bld.closet_opened:
                    # Open closet - dark inside with door swung open
                    pygame.draw.rect(
                        surface,
                        (40, 28, 18),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        border_radius=1,
                    )
                    # Open door (thin strip on the right side)
                    pygame.draw.rect(
                        surface,
                        (160, 110, 60),
                        (sx + tile - margin - 4, sy + margin, 4, tile - margin * 2),
                    )
                else:
                    # Closed closet - wooden double doors
                    pygame.draw.rect(
                        surface,
                        (160, 110, 60),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        border_radius=2,
                    )
                    # Door line down the middle
                    pygame.draw.line(
                        surface,
                        (120, 80, 40),
                        (sx + tile // 2, sy + margin),
                        (sx + tile // 2, sy + tile - margin),
                        1,
                    )
                    # Two little doorknobs
                    pygame.draw.circle(
                        surface, (200, 180, 50), (sx + tile // 2 - 3, sy + tile // 2), 2
                    )
                    pygame.draw.circle(
                        surface, (200, 180, 50), (sx + tile // 2 + 3, sy + tile // 2), 2
                    )
                    # Outline
                    pygame.draw.rect(
                        surface,
                        (100, 65, 30),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        1,
                        border_radius=2,
                    )

            elif cell == Building.BED:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                margin = 2
                # Bed frame (dark brown)
                pygame.draw.rect(
                    surface,
                    (90, 55, 25),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=2,
                )
                # Bedsheets (blue/white)
                pygame.draw.rect(
                    surface,
                    (60, 60, 140),
                    (
                        sx + margin + 2,
                        sy + margin + 2,
                        tile - margin * 2 - 4,
                        tile - margin * 2 - 6,
                    ),
                    border_radius=1,
                )
                # Pillow (white rectangle at the top)
                pygame.draw.rect(
                    surface,
                    (220, 220, 230),
                    (sx + margin + 4, sy + margin + 2, tile - margin * 2 - 8, 6),
                    border_radius=1,
                )
                # Outline
                pygame.draw.rect(
                    surface,
                    (60, 35, 15),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    1,
                    border_radius=2,
                )
                # If shaken and monster came out, bed looks messed up
                if bld.bed_shaken and bld.bed_monster:
                    # Messy sheets (diagonal lines)
                    pygame.draw.line(
                        surface,
                        (40, 40, 100),
                        (sx + 4, sy + 8),
                        (sx + tile - 4, sy + tile - 4),
                        1,
                    )
                    pygame.draw.line(
                        surface,
                        (40, 40, 100),
                        (sx + tile - 4, sy + 8),
                        (sx + 4, sy + tile - 4),
                        1,
                    )

    # Draw the resident burrb (sitting or chasing!)
    if bld.resident_x > 0:
        res_sx = int(bld.resident_x - cam_x)
        res_sy = int(bld.resident_y - cam_y)
        if -30 < res_sx < SCREEN_WIDTH + 30 and -30 < res_sy < SCREEN_HEIGHT + 30:
            res_color = bld.resident_color
            res_detail = bld.resident_detail
            size = 16
            if not bld.resident_angry:
                # Sitting on sofa - draw facing the TV (upward)
                # Body
                pygame.draw.rect(
                    surface,
                    res_color,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    BLACK,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    1,
                    border_radius=2,
                )
                # Eye (looking at TV)
                pygame.draw.circle(surface, res_detail, (res_sx + 2, res_sy - 3), 2)
                # Spikes
                for i in range(3):
                    spike_x = res_sx - 4 + i * 4
                    pygame.draw.polygon(
                        surface,
                        res_color,
                        [
                            (spike_x - 1, res_sy - size // 2),
                            (spike_x, res_sy - size // 2 - 5),
                            (spike_x + 1, res_sy - size // 2),
                        ],
                    )
            else:
                # ANGRY! Chasing the player!
                # Body (slightly red-tinted from anger)
                angry_color = (
                    min(255, res_color[0] + 40),
                    max(0, res_color[1] - 20),
                    max(0, res_color[2] - 20),
                )
                # Walking animation
                leg_off = math.sin(bld.resident_walk_frame * 0.3) * 3
                # Legs
                pygame.draw.line(
                    surface,
                    BLACK,
                    (res_sx - 3, res_sy + size // 2),
                    (res_sx - 3 + leg_off, res_sy + size // 2 + 6),
                    2,
                )
                pygame.draw.line(
                    surface,
                    BLACK,
                    (res_sx + 3, res_sy + size // 2),
                    (res_sx + 3 - leg_off, res_sy + size // 2 + 6),
                    2,
                )
                # Body
                pygame.draw.rect(
                    surface,
                    angry_color,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    (180, 30, 30),
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    1,
                    border_radius=2,
                )
                # Angry eyes (X shaped!)
                pygame.draw.line(
                    surface, (200, 0, 0), (res_sx, res_sy - 4), (res_sx + 4, res_sy), 2
                )
                pygame.draw.line(
                    surface, (200, 0, 0), (res_sx + 4, res_sy - 4), (res_sx, res_sy), 2
                )
                # Angry spikes (pointier)
                for i in range(3):
                    spike_x = res_sx - 4 + i * 4
                    pygame.draw.polygon(
                        surface,
                        angry_color,
                        [
                            (spike_x - 1, res_sy - size // 2),
                            (spike_x, res_sy - size // 2 - 7),
                            (spike_x + 1, res_sy - size // 2),
                        ],
                    )

    # Draw the potato chips (if not stolen!)
    if not bld.chips_stolen and bld.chips_x > 0:
        chip_sx = int(bld.chips_x - cam_x)
        chip_sy = int(bld.chips_y - cam_y)
        if -20 < chip_sx < SCREEN_WIDTH + 20 and -20 < chip_sy < SCREEN_HEIGHT + 20:
            # Chip bag (small orange/yellow rectangle)
            pygame.draw.rect(
                surface,
                (220, 160, 30),
                (chip_sx - 5, chip_sy - 6, 10, 12),
                border_radius=2,
            )
            # Red stripe on bag
            pygame.draw.rect(
                surface,
                (200, 40, 40),
                (chip_sx - 5, chip_sy - 2, 10, 4),
            )
            # "C" for chips
            pygame.draw.rect(
                surface,
                (255, 220, 80),
                (chip_sx - 3, chip_sy - 5, 6, 3),
                border_radius=1,
            )
            # Outline
            pygame.draw.rect(
                surface,
                (150, 100, 20),
                (chip_sx - 5, chip_sy - 6, 10, 12),
                1,
                border_radius=2,
            )

    # Draw the 6-legged monster (if it crawled out from under the bed!)
    if bld.monster_active:
        mon_sx = int(bld.monster_x - cam_x)
        mon_sy = int(bld.monster_y - cam_y)
        if -30 < mon_sx < SCREEN_WIDTH + 30 and -30 < mon_sy < SCREEN_HEIGHT + 30:
            wf = bld.monster_walk_frame
            # Black oval body
            pygame.draw.ellipse(
                surface,
                (15, 15, 15),
                (mon_sx - 10, mon_sy - 6, 20, 12),
            )
            # 6 legs! (3 on each side, animated)
            for leg_i in range(3):
                leg_offset = math.sin(wf * 0.3 + leg_i * 1.2) * 3
                # Left legs
                lx = mon_sx - 8 + leg_i * 5
                pygame.draw.line(
                    surface,
                    (30, 30, 30),
                    (lx, mon_sy),
                    (lx - 4, mon_sy + 8 + int(leg_offset)),
                    2,
                )
                # Right legs
                rx = mon_sx - 8 + leg_i * 5
                pygame.draw.line(
                    surface,
                    (30, 30, 30),
                    (rx, mon_sy),
                    (rx + 4, mon_sy - 8 - int(leg_offset)),
                    2,
                )
            # Two red eyes
            pygame.draw.circle(surface, (255, 0, 0), (mon_sx - 4, mon_sy - 2), 2)
            pygame.draw.circle(surface, (255, 0, 0), (mon_sx + 4, mon_sy - 2), 2)
            # Tiny pincers/mandibles
            pygame.draw.line(
                surface,
                (40, 0, 0),
                (mon_sx - 2, mon_sy - 5),
                (mon_sx - 5, mon_sy - 8),
                1,
            )
            pygame.draw.line(
                surface,
                (40, 0, 0),
                (mon_sx + 2, mon_sy - 5),
                (mon_sx + 5, mon_sy - 8),
                1,
            )

    # Draw the burrb inside
    burrb_sx = px - cam_x
    burrb_sy = py - cam_y
    # Use the regular burrb drawing function with adjusted coordinates
    draw_burrb(surface, px, py, cam_x, cam_y, facing_left, walk_frame)


def draw_jumpscare(surface, frame, level=1):
    """
    Draw a jump scare that gets PROGRESSIVELY MORE TERRIFYING!
    Level 1: basic scare. Level 2+: each one worse than the last.
    More shake, bigger face, more blood, new nightmare effects,
    the birb gets closer, the screen breaks apart...
    """
    sw = SCREEN_WIDTH
    sh = SCREEN_HEIGHT
    lvl = max(1, level)  # scare intensity level

    # === SCALING FACTORS (everything gets worse!) ===
    shake_mult = 1.0 + lvl * 0.5  # shake gets more violent
    size_mult = 1.0 + lvl * 0.08  # face gets bigger each time
    blood_mult = 1.0 + lvl * 0.6  # more and more blood
    glitch_mult = 1.0 + lvl * 0.4  # more screen corruption
    flash_frames = 3 + lvl  # flash lasts longer each time

    # === PHASE 1: BLINDING FLASH ===
    if frame < flash_frames // 2:
        surface.fill((255, 255, 255))
        return
    if frame < flash_frames:
        # At higher levels, flash alternates white/red rapidly (strobe!)
        if lvl >= 3 and frame % 2 == 0:
            surface.fill((255, 255, 255))
        else:
            surface.fill((255, 0, 0))
        return

    # === SCREEN SHAKE (scales with level) ===
    base_shake = int(20 * shake_mult)
    if frame < 40:
        shake_intensity = min(base_shake, int(frame * 2 * shake_mult))
    elif frame < 100:
        shake_intensity = max(0, base_shake - (frame - 40) // 3)
    else:
        # At higher levels, shake NEVER fully stops
        shake_intensity = min(lvl * 2, 12)
    shake_x = random.randint(-shake_intensity, shake_intensity)
    shake_y = random.randint(-shake_intensity, shake_intensity)

    # === THE BIRB LUNGES AT YOU (faster and bigger at higher levels) ===
    lunge_speed = 3.0 + lvl  # lunges faster each time
    if frame < flash_frames + 3:
        grow = (frame - flash_frames) / lunge_speed
    else:
        grow = 1.0
    lunge = min(1.0, frame / max(1, 60 - lvl * 8))
    base_size = int((400 + lvl * 40) * size_mult)
    size = int((base_size + lunge * 150) * max(0.01, grow))
    if size < 10:
        return

    cx = sw // 2 + shake_x
    cy = sh // 2 + shake_y - 20

    # === BACKGROUND (gets darker and more red at higher levels) ===
    bg_r = min(30, lvl * 8)
    surface.fill((bg_r, 0, 0))

    # === FLICKERING STATIC (more intense at higher levels) ===
    static_count = int(80 * glitch_mult)
    if frame % max(1, 4 - lvl) == 0:
        for _ in range(static_count):
            rx = random.randint(0, sw)
            ry = random.randint(0, sh)
            rw = random.randint(2, int(40 * glitch_mult))
            rh = random.randint(1, max(2, int(3 * glitch_mult)))
            brightness = random.randint(40, min(140, 60 + lvl * 20))
            rc = (brightness, 0, 0)
            pygame.draw.rect(surface, rc, (rx, ry, rw, rh))

    # === BLOOD DRIPS (more drips, thicker, faster at higher levels) ===
    blood_seed = random.Random(42 + lvl)  # different pattern each level
    num_drips = int(20 * blood_mult)
    for i in range(num_drips):
        drip_x = blood_seed.randint(0, sw)
        drip_speed = blood_seed.uniform(2.0, 4.0 + lvl * 1.5)
        drip_len = blood_seed.randint(40, int(200 * blood_mult))
        drip_width = blood_seed.randint(2, max(3, 4 + lvl))
        drip_y = int(frame * drip_speed) - blood_seed.randint(0, 100)
        if drip_y > -drip_len:
            drip_top = max(0, drip_y - drip_len)
            drip_bot = min(sh, drip_y)
            if drip_bot > drip_top:
                pygame.draw.line(
                    surface,
                    (160, 0, 0),
                    (drip_x, drip_top),
                    (drip_x, drip_bot),
                    drip_width,
                )
                pygame.draw.circle(
                    surface, (180, 0, 0), (drip_x, drip_bot), drip_width + 1
                )

    # === LEVEL 4+: SCRATCHES ON THE SCREEN (claw marks!) ===
    if lvl >= 4:
        scratch_seed = random.Random(frame // 10 + lvl)
        num_scratches = lvl - 2
        for _ in range(num_scratches):
            s_x1 = scratch_seed.randint(0, sw)
            s_y1 = scratch_seed.randint(0, sh)
            s_x2 = s_x1 + scratch_seed.randint(-200, 200)
            s_y2 = s_y1 + scratch_seed.randint(50, 200)
            for offset in range(-2, 3):
                pygame.draw.line(
                    surface,
                    (100, 0, 0),
                    (s_x1 + offset * 4, s_y1),
                    (s_x2 + offset * 4, s_y2),
                    random.randint(1, 3),
                )

    # === THE SCARY BIRB BODY (bigger each time) ===
    body_w = int(size * 1.2)
    body_h = int(size * 1.3)
    body_color = (max(0, 25 - lvl * 3), max(0, 15 - lvl * 2), max(0, 30 - lvl * 3))
    pygame.draw.ellipse(
        surface,
        body_color,
        (cx - body_w // 2, cy - body_h // 3, body_w, body_h),
    )
    pygame.draw.ellipse(
        surface,
        (15, 5, 15),
        (cx - body_w // 2, cy - body_h // 3, body_w, body_h),
        max(3, size // 20),
    )

    # === SPIKY HAIR (more spikes at higher levels) ===
    spike_base_y = cy - body_h // 3
    num_spikes = 11 + lvl * 2
    for i in range(num_spikes):
        spike_x = cx - size // 2 + i * size // max(1, num_spikes - 1)
        spike_h = random.randint(size // 3, int(size * (0.5 + lvl * 0.08)))
        spike_w = random.randint(size // 14, size // 8)
        spike_color = (
            random.randint(10, 30),
            random.randint(5, 15),
            random.randint(15, 35),
        )
        pygame.draw.polygon(
            surface,
            spike_color,
            [
                (spike_x - spike_w, spike_base_y + 8),
                (spike_x + random.randint(-5, 5), spike_base_y - spike_h),
                (spike_x + spike_w, spike_base_y + 8),
            ],
        )

    # === EYES (pulse faster, glow brighter at higher levels) ===
    eye_y = cy + size // 15
    eye_spacing = int(size * 0.28)
    eye_size = size // 5

    pulse_speed = 0.15 + lvl * 0.05  # heartbeat gets faster!
    pulse = abs(math.sin(frame * pulse_speed)) * 0.4 + 0.6
    glow_size = int(eye_size * (1.3 + pulse * 0.3 + lvl * 0.1))

    # Level 3+: extra eyes appear!
    eye_positions = [cx - eye_spacing, cx + eye_spacing]
    if lvl >= 3:
        # Third eye in the middle (forehead)
        eye_positions.append(cx)
    if lvl >= 5:
        # Even MORE eyes scattered around
        eye_positions.append(cx - eye_spacing * 2)
        eye_positions.append(cx + eye_spacing * 2)

    for idx, eye_x in enumerate(eye_positions):
        # Extra eyes are slightly higher up
        ey = eye_y if idx < 2 else eye_y - eye_size
        # Outer glow
        gs = min(glow_size, 120)
        glow_surf = pygame.Surface((gs * 4, gs * 4), pygame.SRCALPHA)
        for ring in range(gs, 0, -3):
            alpha = max(0, min(255, int((60 + lvl * 10) * (1.0 - ring / gs) * pulse)))
            pygame.draw.circle(
                glow_surf,
                (255, 0, 0, alpha),
                (gs * 2, gs * 2),
                ring,
            )
        surface.blit(glow_surf, (eye_x - gs * 2, ey - gs * 2))

        # Eye
        pygame.draw.circle(surface, (140, 0, 0), (eye_x, ey), eye_size + 6)
        pygame.draw.circle(
            surface,
            (int(255 * pulse), 0, 0),
            (eye_x, ey),
            eye_size,
        )
        # Veins (more at higher levels)
        num_veins = 8 + lvl * 2
        for v in range(num_veins):
            vein_angle = v * (2 * math.pi / num_veins) + random.uniform(-0.2, 0.2)
            vein_len = eye_size * random.uniform(0.5, 0.95)
            vx = eye_x + int(math.cos(vein_angle) * vein_len)
            vy = ey + int(math.sin(vein_angle) * vein_len)
            pygame.draw.line(
                surface,
                (100, 0, 0),
                (eye_x, ey),
                (vx, vy),
                1 + (1 if lvl >= 3 else 0),
            )
        # Pupil (gets SMALLER each level = creepier)
        pupil_size = max(2, eye_size // (5 + lvl))
        pygame.draw.circle(surface, (0, 0, 0), (eye_x, ey), pupil_size)
        # Glint
        pygame.draw.circle(
            surface,
            (255, 200, 200),
            (eye_x - pupil_size, ey - pupil_size),
            max(1, pupil_size // 2),
        )

    # Eyebrows
    brow_thick = max(3, size // 25) + lvl
    pygame.draw.line(
        surface,
        (10, 0, 0),
        (cx - eye_spacing - eye_size - 5, eye_y - eye_size - 8),
        (cx - eye_spacing + eye_size + 5, eye_y - eye_size + 12),
        brow_thick,
    )
    pygame.draw.line(
        surface,
        (10, 0, 0),
        (cx + eye_spacing - eye_size - 5, eye_y - eye_size + 12),
        (cx + eye_spacing + eye_size + 5, eye_y - eye_size - 8),
        brow_thick,
    )

    # === THE MOUTH (opens wider, more teeth at higher levels) ===
    mouth_y = cy + int(size * 0.35)
    mouth_w = int(size * (0.85 + lvl * 0.03))
    mouth_h = int(size * (0.55 + lvl * 0.04))
    jaw_open = min(1.0, frame / max(1, 20 - lvl * 2))
    mouth_h = int(mouth_h * (0.6 + jaw_open * 0.4))

    pygame.draw.ellipse(
        surface,
        (15, 0, 0),
        (cx - mouth_w // 2, mouth_y - mouth_h // 4, mouth_w, mouth_h),
    )
    inner_w = int(mouth_w * 0.75)
    inner_h = int(mouth_h * 0.65)
    pygame.draw.ellipse(
        surface,
        (120, 5, 5),
        (cx - inner_w // 2, mouth_y + mouth_h // 10, inner_w, inner_h),
    )
    throat_r = max(8, size // 10) + lvl * 3
    pygame.draw.circle(surface, (5, 0, 0), (cx, mouth_y + mouth_h // 3), throat_r)

    # === TEETH (more teeth, longer, more blood each level) ===
    num_teeth = 13 + lvl * 2
    tooth_w = max(4, mouth_w // (num_teeth + 1))

    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        tooth_h = random.randint(size // 6, int(size * (0.33 + lvl * 0.04)))
        tooth_color = (220, 210, 180) if i % 3 == 0 else (245, 240, 230)
        # Level 5+: some teeth turn red (stained with blood)
        if lvl >= 5 and i % 4 == 0:
            tooth_color = (220, 180, 180)
        jag = random.randint(-3, 3)
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2 - 1, mouth_y - mouth_h // 8),
                (tx + jag, mouth_y - mouth_h // 8 + tooth_h),
                (tx + tooth_w // 2 + 1, mouth_y - mouth_h // 8),
            ],
        )
        pygame.draw.line(
            surface,
            (180, 170, 150),
            (tx, mouth_y - mouth_h // 8 + 2),
            (tx + jag, mouth_y - mouth_h // 8 + tooth_h - 2),
            1,
        )
        blood_len = random.randint(
            int(size * 0.12 * blood_mult), int(size * 0.4 * blood_mult)
        )
        blood_width = random.randint(1, max(2, 2 + lvl))
        pygame.draw.line(
            surface,
            (random.randint(140, 200), 0, 0),
            (tx + jag, mouth_y - mouth_h // 8 + tooth_h),
            (
                tx + jag + random.randint(-4, 4),
                mouth_y - mouth_h // 8 + tooth_h + blood_len,
            ),
            blood_width,
        )

    # Bottom row
    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        tooth_h = random.randint(size // 6, int(size * (0.33 + lvl * 0.04)))
        tooth_color = (235, 230, 215) if i % 2 == 0 else (215, 200, 170)
        bottom_y = mouth_y + mouth_h - mouth_h // 4
        jag = random.randint(-3, 3)
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2 - 1, bottom_y),
                (tx + jag, bottom_y - tooth_h),
                (tx + tooth_w // 2 + 1, bottom_y),
            ],
        )
        if random.random() > 0.2:
            blood_len = random.randint(size // 10, int(size * 0.2 * blood_mult))
            pygame.draw.line(
                surface,
                (200, 10, 10),
                (tx + jag, bottom_y - tooth_h),
                (tx + jag + random.randint(-3, 3), bottom_y - tooth_h - blood_len),
                max(1, 1 + lvl // 2),
            )

    # Beak edges
    beak_color = (180, 100, 10)
    beak_thick = max(3, size // 30) + lvl
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 8, mouth_y - mouth_h // 2, mouth_w + 16, mouth_h // 2),
        0,
        math.pi,
        beak_thick,
    )
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 8, mouth_y + mouth_h // 2, mouth_w + 16, mouth_h // 2),
        math.pi,
        math.pi * 2,
        beak_thick,
    )

    # === BLOOD SPLATTER (way more at higher levels) ===
    splat_count = int(20 * blood_mult)
    for _ in range(splat_count):
        bx = cx + random.randint(-mouth_w, mouth_w)
        by = mouth_y + random.randint(-mouth_h, mouth_h)
        br = random.randint(3, max(6, int(size * 0.04 * blood_mult)))
        pygame.draw.circle(surface, (random.randint(130, 220), 0, 0), (bx, by), br)
    streak_count = int(6 * blood_mult)
    for _ in range(streak_count):
        sx = cx + random.randint(-size // 2, size // 2)
        sy = cy + random.randint(-size // 4, size // 2)
        ex = sx + random.randint(-80, 80)
        ey = sy + random.randint(20, 100)
        pygame.draw.line(
            surface,
            (160, 0, 0),
            (sx, sy),
            (ex, ey),
            random.randint(2, 3 + lvl),
        )

    # === LEVEL 2+: TEXT GETS MORE UNHINGED ===
    if frame > flash_frames:
        font_size = max(36, int(size * (0.33 + lvl * 0.05)))
        scare_font = pygame.font.Font(None, font_size)
        if lvl == 1:
            messages = ["AAAAAHHH!!!", "SCREEEEECH!", "GET OUT!!!", "RAAAAWWW!!!"]
        elif lvl == 2:
            messages = ["COME BACK...", "I SEE YOU", "SCREEEEECH!", "YOU CAN'T HIDE"]
        elif lvl == 3:
            messages = [
                "I FOUND YOU AGAIN",
                "WHY DO YOU KEEP COMING BACK",
                "SCREEEEE!",
                "THERE IS NO ESCAPE",
            ]
        elif lvl == 4:
            messages = [
                "DID YOU MISS ME?",
                "I'M ALWAYS IN THE CLOSET",
                "ALWAYS WATCHING",
                "I KNOW WHERE YOU LIVE",
            ]
        else:
            messages = [
                "I'M IN EVERY CLOSET NOW",
                "YOU SHOULD HAVE STOPPED",
                "THIS IS YOUR FAULT",
                "I WILL NEVER LEAVE",
            ]
        msg_idx = (frame // max(5, 20 - lvl * 3)) % len(messages)
        msg = messages[msg_idx]
        scare_text = scare_font.render(
            msg,
            True,
            (255, random.randint(0, 40), random.randint(0, 20)),
        )
        text_x = (
            sw // 2
            - scare_text.get_width() // 2
            + random.randint(-12 - lvl * 3, 12 + lvl * 3)
        )
        text_y = 30 + random.randint(-8 - lvl * 2, 8 + lvl * 2)
        # More shadow copies at higher levels (ghosting effect)
        for g in range(min(lvl, 4)):
            ghost = scare_font.render(msg, True, (80, 0, 0))
            gx = text_x + random.randint(-10 - g * 3, 10 + g * 3)
            gy = text_y + random.randint(-5 - g * 2, 5 + g * 2)
            surface.blit(ghost, (gx, gy))
        surface.blit(scare_text, (text_x, text_y))

    # Bottom text (gets more ominous)
    if frame > 15:
        sub_font = pygame.font.Font(None, max(24, size // 5))
        if lvl <= 2:
            sub_msg = "IT WAS IN THE CLOSET THE WHOLE TIME..."
        elif lvl <= 4:
            sub_msg = "IT REMEMBERS YOU FROM LAST TIME..."
        else:
            sub_msg = "IT HAS ALWAYS BEEN HERE. IT WILL ALWAYS BE HERE."
        sub_text = sub_font.render(sub_msg, True, (255, 80, 80))
        sub_x = sw // 2 - sub_text.get_width() // 2 + random.randint(-6, 6)
        sub_y = sh - 70 + random.randint(-4, 4)
        surface.blit(sub_text, (sub_x, sub_y))

    # === LEVEL 2+: SCARE COUNTER (reminds you how many times) ===
    if lvl >= 2 and frame > 30:
        count_font = pygame.font.Font(None, 22)
        count_text = count_font.render(
            f"scare #{lvl}",
            True,
            (120, 0, 0),
        )
        surface.blit(count_text, (sw - count_text.get_width() - 10, sh - 30))

    # === GLITCH EFFECT (way more tears at higher levels) ===
    if frame > 10 and frame % max(1, 3 - lvl // 2) == 0:
        num_tears = random.randint(2 + lvl, int(6 * glitch_mult))
        for _ in range(num_tears):
            tear_y = random.randint(0, sh)
            tear_h = random.randint(2, max(3, int(8 * glitch_mult)))
            tear_offset = random.randint(int(-30 * glitch_mult), int(30 * glitch_mult))
            if 0 < tear_y < sh - tear_h:
                strip = surface.subsurface((0, tear_y, sw, tear_h)).copy()
                surface.blit(strip, (tear_offset, tear_y))

    # === LEVEL 3+: SCREEN INVERSION FLICKER ===
    if lvl >= 3 and frame % (12 - lvl) == 0:
        inv_surf = pygame.Surface((sw, sh))
        inv_surf.fill((255, 255, 255))
        inv_surf.set_alpha(random.randint(20, 60 + lvl * 10))
        surface.blit(inv_surf, (0, 0), special_flags=pygame.BLEND_SUB)

    # === LEVEL 5+: MULTIPLE FACES (smaller faces in the corners!) ===
    if lvl >= 5 and frame > 20:
        mini_size = size // 4
        corners = [(80, 80), (sw - 80, 80), (80, sh - 80), (sw - 80, sh - 80)]
        for corner_x, corner_y in corners:
            if random.random() < 0.7:  # flicker in and out
                # Mini scary eyes
                me_size = mini_size // 5
                me_spacing = mini_size // 4
                pygame.draw.circle(
                    surface, (200, 0, 0), (corner_x - me_spacing, corner_y), me_size
                )
                pygame.draw.circle(
                    surface, (0, 0, 0), (corner_x - me_spacing, corner_y), me_size // 3
                )
                pygame.draw.circle(
                    surface, (200, 0, 0), (corner_x + me_spacing, corner_y), me_size
                )
                pygame.draw.circle(
                    surface, (0, 0, 0), (corner_x + me_spacing, corner_y), me_size // 3
                )
                # Mini mouth
                pygame.draw.ellipse(
                    surface,
                    (30, 0, 0),
                    (
                        corner_x - mini_size // 3,
                        corner_y + me_size + 2,
                        mini_size * 2 // 3,
                        mini_size // 3,
                    ),
                )

    # === RED VIGNETTE ===
    vig_surf = pygame.Surface((sw, sh), pygame.SRCALPHA)
    vig_step = max(4, 8 - lvl)
    for ring in range(0, max(sw, sh), vig_step):
        alpha = min(200 + lvl * 10, ring * (200 + lvl * 15) // max(sw, sh))
        alpha = min(255, alpha)
        pygame.draw.rect(
            vig_surf,
            (0, 0, 0, alpha),
            (ring // 2, ring // 2, sw - ring, sh - ring),
            max(2, vig_step - 1),
        )
    surface.blit(vig_surf, (0, 0))

    # === FADE OUT AT THE END ===
    total_duration = JUMPSCARE_DURATION + lvl * 60
    fade_start = total_duration - 20
    if frame > fade_start:
        fade_out = (frame - fade_start) / 20.0
        flash_surf = pygame.Surface((sw, sh))
        flash_surf.fill((0, 0, 0))
        flash_surf.set_alpha(min(255, int(fade_out * 255)))
        surface.blit(flash_surf, (0, 0))


# ============================================================
# GAME STATE
# ============================================================
# The burrb starts in the middle of the world
burrb_x = WORLD_WIDTH // 2.0
burrb_y = WORLD_HEIGHT // 2.0
burrb_speed = 3
facing_left = False
walk_frame = 0
is_walking = False

# First person mode!
# "angle" is the direction the burrb is looking, measured in
# radians. 0 = looking right, pi/2 = looking down, pi = left, etc.
# Think of it like a compass but using math angles.
burrb_angle = 0.0  # start facing right

# Building interiors!
# When this is not None, the burrb is inside a building.
inside_building = None
# Position inside the building (in interior pixel coordinates)
interior_x = 0.0
interior_y = 0.0
# Saved outdoor position (so we can put the burrb back when exiting)
saved_outdoor_x = 0.0
saved_outdoor_y = 0.0
saved_outdoor_angle = 0.0

# Camera position (top-left corner of what we see)
cam_x = 0.0
cam_y = 0.0

# Tongue ability!
# The burrb can extend its tongue by pressing O. When the tongue
# hits an NPC, that NPC turns into a rock! Like a magic petrifying tongue.
tongue_active = False  # is the tongue currently shooting out?
tongue_length = 0.0  # how far the tongue has extended so far
tongue_max_length = 120.0  # max reach of the tongue
tongue_speed = 8.0  # how fast the tongue extends per frame
tongue_retracting = False  # is the tongue pulling back in?
tongue_angle = 0.0  # direction the tongue is going (radians)
tongue_hit_npc = None  # did we hit someone? (for visual feedback)

# Chip collecting!
# Every building has a bag of chips. Steal them all!
chips_collected = 0

# Jump scare from closets!
# When you open a closet and get unlucky, a scary birb jumps out!
jumpscare_timer = 0  # frames remaining for jump scare (0 = not active)
jumpscare_frame = 0  # animation frame counter for the scare
JUMPSCARE_DURATION = 150  # 2.5 seconds at 60fps - longer = scarier!
scare_level = 0  # goes up each time you get jump scared - each one gets WORSE
closet_msg_timer = 0  # frames to show "found chips!" message

# ============================================================
# ABILITIES!
# ============================================================
# You can spend potato chips to unlock awesome new powers!
# Each ability has a cost, an unlocked flag, and some have
# active timers (they only last a few seconds when used).
#
# Ability list:
#   DASH        - 2 chips - Press SHIFT to zoom forward!
#   SUPER SPEED - 3 chips - Hold SHIFT to run really fast!
#   MEGA TONGUE - 3 chips - Tongue reaches twice as far!
#   FREEZE      - 4 chips - Press F to freeze all nearby burrbs!
#   INVISIBILITY- 5 chips - Press I to become invisible!
#   GIANT MODE  - 6 chips - Press G to become HUGE!
#   BOUNCE      - 4 chips - Press B to bounce over buildings!
#   TELEPORT    - 5 chips - Press T to teleport forward!
#   EARTHQUAKE  - 7 chips - Press Q to stun everything nearby!

# The shop menu
shop_open = False  # is the shop screen showing?
shop_cursor = 0  # which ability is highlighted in the shop

# Ability definitions: (name, cost, key_hint, description)
ABILITIES = [
    ("Dash", 2, "SHIFT", "Zoom forward super fast!"),
    ("Super Speed", 3, "SHIFT hold", "Run way faster!"),
    ("Mega Tongue", 3, "auto", "Tongue reaches 2x farther!"),
    ("Freeze", 4, "F", "Freeze all nearby burrbs!"),
    ("Invisibility", 5, "I", "Turn invisible for 5 sec!"),
    ("Giant Mode", 6, "G", "Become HUGE for 8 sec!"),
    ("Bounce", 4, "B", "Jump over buildings!"),
    ("Teleport", 5, "T", "Warp forward instantly!"),
    ("Earthquake", 7, "Q", "Stun everything nearby!"),
]

# Which abilities have been unlocked (bought with chips)
ability_unlocked = [False] * len(ABILITIES)

# Active ability timers (frames remaining, 0 = not active)
# Some abilities are always-on once unlocked (Mega Tongue, Super Speed),
# others are timed bursts.
dash_cooldown = 0  # frames until dash can be used again
dash_active = 0  # frames remaining in a dash burst
freeze_timer = 0  # frames remaining for freeze effect
invisible_timer = 0  # frames remaining for invisibility
giant_timer = 0  # frames remaining for giant mode
giant_scale = 1.0  # current size multiplier (smoothly grows/shrinks)
bounce_timer = 0  # frames remaining in a bounce (airborne!)
bounce_cooldown = 0  # frames until next bounce
bounce_height = 0.0  # current visual height (pixels above ground)
BOUNCE_DURATION = 45  # how long a bounce lasts (frames)
teleport_cooldown = 0  # frames until next teleport
teleport_flash = 0  # frames remaining for the teleport flash effect
TELEPORT_DISTANCE = 200  # how far you warp forward (pixels)
earthquake_timer = 0  # frames remaining for earthquake stun
earthquake_cooldown = 0  # frames until next earthquake
earthquake_shake = 0  # frames remaining for screen shake
EARTHQUAKE_DURATION = 240  # how long the stun lasts (4 seconds)
EARTHQUAKE_RADIUS = 300  # how far the earthquake reaches (pixels)

# Font for UI
font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 42)
shop_font = pygame.font.Font(None, 32)
shop_title_font = pygame.font.Font(None, 48)

# ============================================================
# TOUCH CONTROLS
# ============================================================
# Touch support for phones, tablets, and touchscreen computers!
# Tap the screen to move, use on-screen buttons for actions.
# Touch is auto-detected: buttons appear when you touch the screen.

touch_active = False  # has the player used touch? (shows buttons)
touch_move_target = None  # (x, y) world position to walk toward, or None
touch_held = False  # is a finger currently touching the screen?
touch_pos = (0, 0)  # current touch position on screen
touch_start_pos = (0, 0)  # where the finger first touched
touch_finger_id = None  # track which finger is the main one

# On-screen button layout (right side of screen)
# Each button: (label, center_x, center_y, radius, key_action)
TOUCH_BTN_RADIUS = 28
TOUCH_BTN_PAD = 8
_br = TOUCH_BTN_RADIUS
_bx = SCREEN_WIDTH - _br - 12  # right edge
_bx2 = _bx - _br * 2 - TOUCH_BTN_PAD  # second column from right

TOUCH_BUTTONS = [
    # Right column (main actions)
    ("E", _bx, SCREEN_HEIGHT - _br - 12, _br, "action_e"),
    ("O", _bx, SCREEN_HEIGHT - _br * 3 - 20, _br, "action_o"),
    # Second column
    ("SHOP", _bx2, SCREEN_HEIGHT - _br - 12, _br, "toggle_shop"),
]

# Extra ability buttons (only shown when unlocked)
TOUCH_ABILITY_BUTTONS = [
    ("F", _bx2, SCREEN_HEIGHT - _br * 5 - 28, _br - 4, "ability_f"),
    ("I", _bx, SCREEN_HEIGHT - _br * 5 - 28, _br - 4, "ability_i"),
    (
        "G",
        _bx2 + _br + TOUCH_BTN_PAD // 2,
        SCREEN_HEIGHT - _br * 7 - 36,
        _br - 4,
        "ability_g",
    ),
    ("B", _bx2, SCREEN_HEIGHT - _br * 9 - 44, _br - 4, "ability_b"),
    ("T", _bx, SCREEN_HEIGHT - _br * 9 - 44, _br - 4, "ability_t"),
    (
        "Q",
        _bx2 + _br + TOUCH_BTN_PAD // 2,
        SCREEN_HEIGHT - _br * 11 - 52,
        _br - 4,
        "ability_q",
    ),
]

touch_btn_pressed = None  # which button is currently being pressed


def touch_hit_button(tx, ty):
    """Check if a touch at (tx, ty) hits any on-screen button.
    Returns the action string or None."""
    for label, bx, by, br, action in TOUCH_BUTTONS:
        dx = tx - bx
        dy = ty - by
        if dx * dx + dy * dy <= (br + 8) * (br + 8):
            return action
    # Check ability buttons only if unlocked
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        # F=index 3, I=index 4, G=index 5
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            dx = tx - bx
            dy = ty - by
            if dx * dx + dy * dy <= (br + 8) * (br + 8):
                return action
    return None


def draw_touch_buttons(surface):
    """Draw the on-screen touch buttons."""
    btn_font = pygame.font.Font(None, 24)

    for label, bx, by, br, action in TOUCH_BUTTONS:
        # Button background (semi-transparent circle)
        btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
        pressed = touch_btn_pressed == action
        if pressed:
            pygame.draw.circle(btn_surf, (255, 255, 255, 160), (br + 1, br + 1), br)
        else:
            pygame.draw.circle(btn_surf, (255, 255, 255, 70), (br + 1, br + 1), br)
        pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
        surface.blit(btn_surf, (bx - br - 1, by - br - 1))
        # Label
        txt = btn_font.render(label, True, WHITE)
        surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # Ability buttons (only show if unlocked)
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
            pressed = touch_btn_pressed == action
            # Color-code ability buttons
            colors = [(100, 180, 255, 100), (180, 100, 255, 100), (100, 255, 100, 100)]
            bg_color = colors[i] if i < len(colors) else (255, 255, 255, 70)
            if pressed:
                bg_color = (bg_color[0], bg_color[1], bg_color[2], 200)
            pygame.draw.circle(btn_surf, bg_color, (br + 1, br + 1), br)
            pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
            surface.blit(btn_surf, (bx - br - 1, by - br - 1))
            txt = btn_font.render(label, True, WHITE)
            surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # Draw move target indicator if active (small pulsing circle)
    if touch_move_target is not None:
        tgt_x, tgt_y = touch_move_target
        if inside_building is not None:
            # Interior coords to screen coords
            icam_x = interior_x - SCREEN_WIDTH // 2
            icam_y = interior_y - SCREEN_HEIGHT // 2
            sx = int(tgt_x - icam_x)
            sy = int(tgt_y - icam_y)
        else:
            # World coords to screen coords
            sx = int(tgt_x - cam_x)
            sy = int(tgt_y - cam_y)
        if 0 <= sx <= SCREEN_WIDTH and 0 <= sy <= SCREEN_HEIGHT:
            pulse = abs(math.sin(pygame.time.get_ticks() * 0.005)) * 4
            r = int(6 + pulse)
            ind_surf = pygame.Surface((r * 2 + 2, r * 2 + 2), pygame.SRCALPHA)
            pygame.draw.circle(ind_surf, (255, 255, 100, 120), (r + 1, r + 1), r)
            pygame.draw.circle(ind_surf, (255, 255, 100, 200), (r + 1, r + 1), r, 1)
            surface.blit(ind_surf, (sx - r - 1, sy - r - 1))


# ============================================================
# COLLISION - so the burrb can't walk through buildings
# ============================================================
def can_move_to(x, y):
    """Check if the burrb can move to position (x, y)."""
    # World boundaries
    if x < 20 or x > WORLD_WIDTH - 20 or y < 20 or y > WORLD_HEIGHT - 20:
        return False
    # Building collision (use a small rect around the burrb's feet)
    burrb_rect = pygame.Rect(x - 10, y + 5, 20, 14)
    for b in buildings:
        if burrb_rect.colliderect(b.get_rect()):
            return False
    return True


def draw_shop(surface):
    """
    Draw the ability shop screen!
    This is a cool menu where you spend your potato chips
    to unlock awesome new powers for your burrb.
    """
    # Dark semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # Shop box (sized to fit all abilities)
    box_w = 500
    box_h = 90 + len(ABILITIES) * 52 + 40
    box_x = (SCREEN_WIDTH - box_w) // 2
    box_y = (SCREEN_HEIGHT - box_h) // 2

    # Background with border
    pygame.draw.rect(
        surface, (40, 30, 60), (box_x, box_y, box_w, box_h), border_radius=12
    )
    pygame.draw.rect(
        surface, (100, 80, 160), (box_x, box_y, box_w, box_h), 3, border_radius=12
    )

    # Title
    title = shop_title_font.render("CHIP SHOP", True, (255, 220, 50))
    surface.blit(title, (box_x + box_w // 2 - title.get_width() // 2, box_y + 12))

    # Chip count
    chip_str = f"Your chips: {chips_collected}"
    chip_txt = shop_font.render(chip_str, True, (255, 200, 50))
    surface.blit(chip_txt, (box_x + box_w // 2 - chip_txt.get_width() // 2, box_y + 52))

    # Abilities list
    for i, (name, cost, key_hint, desc) in enumerate(ABILITIES):
        row_y = box_y + 90 + i * 52
        # Highlight selected row
        if i == shop_cursor:
            pygame.draw.rect(
                surface,
                (80, 60, 120),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                border_radius=6,
            )
            pygame.draw.rect(
                surface,
                (140, 120, 200),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                2,
                border_radius=6,
            )

        # Already unlocked?
        if ability_unlocked[i]:
            name_color = (100, 220, 100)  # green = owned
            status = "OWNED"
            status_color = (100, 220, 100)
        elif chips_collected >= cost:
            name_color = (255, 255, 255)  # white = can buy
            status = f"{cost} chips"
            status_color = (255, 200, 50)
        else:
            name_color = (120, 120, 120)  # gray = too expensive
            status = f"{cost} chips"
            status_color = (150, 80, 80)

        # Name
        name_txt = shop_font.render(name, True, name_color)
        surface.blit(name_txt, (box_x + 24, row_y))

        # Key hint
        if ability_unlocked[i]:
            key_txt = font.render(f"[{key_hint}]", True, (150, 200, 150))
        else:
            key_txt = font.render(f"[{key_hint}]", True, (100, 100, 100))
        surface.blit(key_txt, (box_x + 24, row_y + 24))

        # Description
        desc_txt = font.render(desc, True, (180, 180, 200))
        surface.blit(desc_txt, (box_x + 140, row_y + 24))

        # Cost / status on the right
        cost_txt = shop_font.render(status, True, status_color)
        surface.blit(cost_txt, (box_x + box_w - cost_txt.get_width() - 20, row_y + 4))

    # Instructions at the bottom
    instr = font.render(
        "UP/DOWN select  |  ENTER buy  |  TAB close", True, (180, 180, 200)
    )
    surface.blit(
        instr, (box_x + box_w // 2 - instr.get_width() // 2, box_y + box_h - 30)
    )


async def main():
    """Main game loop, async for Pygbag web support."""
    global running, burrb_x, burrb_y, burrb_angle, facing_left
    global walk_frame, is_walking
    global shop_open, shop_cursor
    global inside_building, interior_x, interior_y
    global saved_outdoor_x, saved_outdoor_y, saved_outdoor_angle
    global tongue_active, tongue_length, tongue_retracting
    global tongue_angle, tongue_hit_npc
    global chips_collected, ability_unlocked
    global dash_cooldown, dash_active
    global freeze_timer, invisible_timer, giant_timer, giant_scale
    global bounce_timer, bounce_cooldown, bounce_height
    global teleport_cooldown, teleport_flash
    global earthquake_timer, earthquake_cooldown, earthquake_shake
    global jumpscare_timer, jumpscare_frame, closet_msg_timer, scare_level
    global cam_x, cam_y
    global touch_active, touch_move_target, touch_held
    global touch_pos, touch_start_pos, touch_finger_id, touch_btn_pressed

    # ============================================================
    # MAIN GAME LOOP
    # ============================================================
    # This is the heart of the game! It runs over and over, about
    # 60 times per second. Each time through the loop:
    #   1. Check what keys are pressed
    #   2. Move the burrb
    #   3. Move the camera
    #   4. Draw everything on screen
    running = True

    while running:
        # --- EVENT HANDLING ---
        # Events are things like key presses, mouse clicks, or
        # clicking the X button to close the window
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if shop_open:
                        shop_open = False
                    else:
                        running = False

                # TAB opens/closes the chip shop!
                if event.key == pygame.K_TAB:
                    shop_open = not shop_open
                    shop_cursor = 0

                # When the shop is open, handle shop navigation
                if shop_open:
                    if event.key == pygame.K_UP:
                        shop_cursor = (shop_cursor - 1) % len(ABILITIES)
                    if event.key == pygame.K_DOWN:
                        shop_cursor = (shop_cursor + 1) % len(ABILITIES)
                    if event.key == pygame.K_RETURN:
                        # Try to buy the selected ability!
                        cost = ABILITIES[shop_cursor][1]
                        if (
                            not ability_unlocked[shop_cursor]
                            and chips_collected >= cost
                        ):
                            chips_collected -= cost
                            ability_unlocked[shop_cursor] = True
                    # Skip all other game input when shop is open
                    continue

                # Press O to shoot the tongue!
                if event.key == pygame.K_o:
                    if not tongue_active and inside_building is None:
                        tongue_active = True
                        tongue_length = 0.0
                        tongue_retracting = False
                        tongue_hit_npc = None
                        # Tongue shoots in the direction the burrb is facing
                        if facing_left:
                            tongue_angle = math.pi  # left
                        else:
                            tongue_angle = 0.0  # right

                # Press E to enter/exit buildings!
                if event.key == pygame.K_e:
                    if inside_building is None:
                        # Try to enter a building (check if near a door)
                        nearby = get_nearby_door_building(burrb_x, burrb_y)
                        if nearby is not None:
                            inside_building = nearby
                            # Save outdoor position so we can come back
                            saved_outdoor_x = burrb_x
                            saved_outdoor_y = burrb_y
                            saved_outdoor_angle = burrb_angle
                            # Move burrb to interior spawn point
                            interior_x = float(nearby.spawn_x)
                            interior_y = float(nearby.spawn_y)
                            burrb_angle = math.pi * 1.5  # face upward (into the room)
                            touch_move_target = None  # clear touch target
                    else:
                        # Try to open the closet!
                        bld = inside_building
                        if (
                            not bld.closet_opened
                            and bld.closet_x > 0
                            and jumpscare_timer <= 0
                        ):
                            cl_dx = interior_x - bld.closet_x
                            cl_dy = interior_y - bld.closet_y
                            cl_dist = math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
                            if cl_dist < 30:  # close enough to open!
                                bld.closet_opened = True
                                # 10% chance of jump scare, 90% chance of 2 chips!
                                if random.random() < 0.1:
                                    # JUMP SCARE! Gets worse every time!
                                    bld.closet_jumpscare = True
                                    scare_level += 1
                                    # Lasts longer each time: 2.5s, 3.5s, 4.5s, 5.5s...
                                    jumpscare_timer = (
                                        JUMPSCARE_DURATION + scare_level * 60
                                    )
                                    jumpscare_frame = 0
                                else:
                                    # Found 2 chips!
                                    chips_collected += 2
                                    closet_msg_timer = 120  # show message for 2 sec

                        # Try to steal the chips! (check if near the chip bag)
                        if not bld.chips_stolen and bld.chips_x > 0:
                            chip_dx = interior_x - bld.chips_x
                            chip_dy = interior_y - bld.chips_y
                            chip_dist = math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
                            if chip_dist < 30:  # close enough to grab!
                                bld.chips_stolen = True
                                bld.resident_angry = True  # uh oh!
                                chips_collected += 1

                        # Try to shake the bed! (check if near the bed)
                        if not bld.bed_shaken and bld.bed_x > 0:
                            bed_dx = interior_x - bld.bed_x
                            bed_dy = interior_y - bld.bed_y
                            bed_dist = math.sqrt(bed_dx * bed_dx + bed_dy * bed_dy)
                            if bed_dist < 30:  # close enough to shake!
                                bld.bed_shaken = True
                                # 30% chance a monster crawls out!
                                if random.random() < 0.3:
                                    bld.bed_monster = True
                                    bld.monster_active = True
                                    bld.monster_x = bld.bed_x
                                    bld.monster_y = bld.bed_y

                        # Try to exit the building (check if near interior door)
                        if is_at_interior_door(inside_building, interior_x, interior_y):
                            # Put burrb back outside, just below the door
                            burrb_x = saved_outdoor_x
                            burrb_y = saved_outdoor_y
                            burrb_angle = saved_outdoor_angle
                            inside_building = None
                            touch_move_target = None  # clear touch target

                # --- ABILITY ACTIVATION KEYS ---

                # Press F to FREEZE all nearby burrbs!
                if event.key == pygame.K_f:
                    if ability_unlocked[3] and freeze_timer <= 0:
                        freeze_timer = 300  # 5 seconds at 60fps

                # Press I to become INVISIBLE!
                if event.key == pygame.K_i:
                    if ability_unlocked[4] and invisible_timer <= 0:
                        invisible_timer = 300  # 5 seconds

                # Press G to become GIANT!
                if event.key == pygame.K_g:
                    if ability_unlocked[5] and giant_timer <= 0:
                        giant_timer = 480  # 8 seconds

                # Press B to BOUNCE over buildings!
                if event.key == pygame.K_b:
                    if (
                        ability_unlocked[6]
                        and bounce_timer <= 0
                        and bounce_cooldown <= 0
                    ):
                        if inside_building is None:  # can't bounce indoors!
                            bounce_timer = BOUNCE_DURATION
                            bounce_cooldown = 60  # 1 second cooldown

                # Press T to TELEPORT forward!
                if event.key == pygame.K_t:
                    if ability_unlocked[7] and teleport_cooldown <= 0:
                        if inside_building is None:  # can't teleport indoors!
                            # Teleport in the direction the burrb is facing
                            tp_x = burrb_x + math.cos(burrb_angle) * TELEPORT_DISTANCE
                            tp_y = burrb_y + math.sin(burrb_angle) * TELEPORT_DISTANCE
                            # Clamp to world boundaries
                            tp_x = max(30, min(WORLD_WIDTH - 30, tp_x))
                            tp_y = max(30, min(WORLD_HEIGHT - 30, tp_y))
                            # If we'd land inside a building, scoot to the nearest open spot
                            if not can_move_to(tp_x, tp_y):
                                # Try shorter distances until we find open ground
                                for shrink in range(1, 10):
                                    shorter = TELEPORT_DISTANCE * (1.0 - shrink * 0.1)
                                    test_x = burrb_x + math.cos(burrb_angle) * shorter
                                    test_y = burrb_y + math.sin(burrb_angle) * shorter
                                    test_x = max(30, min(WORLD_WIDTH - 30, test_x))
                                    test_y = max(30, min(WORLD_HEIGHT - 30, test_y))
                                    if can_move_to(test_x, test_y):
                                        tp_x = test_x
                                        tp_y = test_y
                                        break
                                else:
                                    tp_x = burrb_x  # can't teleport, stay put
                                    tp_y = burrb_y
                            burrb_x = tp_x
                            burrb_y = tp_y
                            teleport_cooldown = 90  # 1.5 second cooldown
                            teleport_flash = 15  # flash effect for 0.25 seconds

                # Press Q for EARTHQUAKE!
                if event.key == pygame.K_q:
                    if (
                        ability_unlocked[8]
                        and earthquake_timer <= 0
                        and earthquake_cooldown <= 0
                    ):
                        if inside_building is None:  # can't earthquake indoors!
                            earthquake_timer = EARTHQUAKE_DURATION
                            earthquake_cooldown = 360  # 6 second cooldown
                            earthquake_shake = 30  # screen shakes for 0.5 seconds
                            # Stun all NPCs in range - flip their direction and slow them
                            for npc in npcs:
                                if npc.npc_type == "rock":
                                    continue
                                eq_dx = npc.x - burrb_x
                                eq_dy = npc.y - burrb_y
                                eq_dist = math.sqrt(eq_dx * eq_dx + eq_dy * eq_dy)
                                if eq_dist < EARTHQUAKE_RADIUS:
                                    # Push them away from the burrb!
                                    if eq_dist > 1:
                                        push_x = (eq_dx / eq_dist) * 20
                                        push_y = (eq_dy / eq_dist) * 20
                                        npc.x += push_x
                                        npc.y += push_y
                                    npc.dir_timer = EARTHQUAKE_DURATION  # stunned
                                    npc.speed = 0.0  # frozen in place
                            # Also stun nearby cars!
                            for car in cars:
                                eq_dx = car.x - burrb_x
                                eq_dy = car.y - burrb_y
                                eq_dist = math.sqrt(eq_dx * eq_dx + eq_dy * eq_dy)
                                if eq_dist < EARTHQUAKE_RADIUS:
                                    car.speed = 0.0  # cars stop

            # === TOUCH / MOUSE INPUT ===
            # Handle finger touch events (phones/tablets) AND mouse clicks
            # (touchscreen laptops report mouse events for touch)
            if event.type == pygame.FINGERDOWN:
                touch_active = True
                tx = int(event.x * SCREEN_WIDTH)
                ty = int(event.y * SCREEN_HEIGHT)
                touch_held = True
                touch_pos = (tx, ty)
                touch_start_pos = (tx, ty)
                touch_finger_id = event.finger_id

                # Check if a button was pressed
                btn = touch_hit_button(tx, ty)
                if btn is not None:
                    touch_btn_pressed = btn
                else:
                    touch_btn_pressed = None
                    # Tap to move! Convert screen position to world/interior position
                    if not shop_open:
                        if inside_building is not None:
                            # Inside a building: figure out interior coords from screen
                            bld = inside_building
                            tile = bld.interior_tile
                            # Top-down interior: screen is centered on burrb
                            icam_x = interior_x - SCREEN_WIDTH // 2
                            icam_y = interior_y - SCREEN_HEIGHT // 2
                            touch_move_target = (tx + icam_x, ty + icam_y)
                        else:
                            # Top-down outdoor: convert screen coords to world coords
                            touch_move_target = (tx + cam_x, ty + cam_y)

            if event.type == pygame.FINGERMOTION:
                if event.finger_id == touch_finger_id:
                    tx = int(event.x * SCREEN_WIDTH)
                    ty = int(event.y * SCREEN_HEIGHT)
                    touch_pos = (tx, ty)

            if event.type == pygame.FINGERUP:
                if event.finger_id == touch_finger_id:
                    tx = int(event.x * SCREEN_WIDTH)
                    ty = int(event.y * SCREEN_HEIGHT)

                    # If a button was pressed, trigger its action on release
                    if touch_btn_pressed is not None:
                        btn = touch_hit_button(tx, ty)
                        if btn == touch_btn_pressed:
                            # Trigger the button action!
                            if btn == "action_e":
                                # Simulate pressing E
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_e
                                )
                                pygame.event.post(fake_event)
                            elif btn == "action_o":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_o
                                )
                                pygame.event.post(fake_event)
                            elif btn == "toggle_shop":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_TAB
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_f":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_f
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_i":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_i
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_g":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_g
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_b":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_b
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_t":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_t
                                )
                                pygame.event.post(fake_event)
                            elif btn == "ability_q":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_q
                                )
                                pygame.event.post(fake_event)

                    touch_held = False
                    touch_btn_pressed = None
                    touch_finger_id = None

            # Also handle mouse clicks as touch (for touchscreen laptops)
            if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                touch_active = True
                tx, ty = event.pos
                touch_held = True
                touch_pos = (tx, ty)
                touch_start_pos = (tx, ty)

                btn = touch_hit_button(tx, ty)
                if btn is not None:
                    touch_btn_pressed = btn
                else:
                    touch_btn_pressed = None
                    if not shop_open:
                        if inside_building is not None:
                            icam_x = interior_x - SCREEN_WIDTH // 2
                            icam_y = interior_y - SCREEN_HEIGHT // 2
                            touch_move_target = (tx + icam_x, ty + icam_y)
                        else:
                            touch_move_target = (tx + cam_x, ty + cam_y)

            if event.type == pygame.MOUSEMOTION and touch_held:
                touch_pos = event.pos

            if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
                tx, ty = event.pos
                if touch_btn_pressed is not None:
                    btn = touch_hit_button(tx, ty)
                    if btn == touch_btn_pressed:
                        if btn == "action_e":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
                            )
                        elif btn == "action_o":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o)
                            )
                        elif btn == "toggle_shop":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)
                            )
                        elif btn == "ability_f":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f)
                            )
                        elif btn == "ability_i":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i)
                            )
                        elif btn == "ability_g":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)
                            )
                        elif btn == "ability_b":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_b)
                            )
                        elif btn == "ability_t":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_t)
                            )
                        elif btn == "ability_q":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_q)
                            )
                touch_held = False
                touch_btn_pressed = None

        # Handle touch input for the shop (tap abilities to select/buy)
        if shop_open and touch_active and touch_held:
            tx, ty = touch_pos
            box_w = 500
            box_h = 90 + len(ABILITIES) * 52 + 40
            box_x = (SCREEN_WIDTH - box_w) // 2
            box_y = (SCREEN_HEIGHT - box_h) // 2
            # Check if tap is inside the shop box
            if box_x <= tx <= box_x + box_w:
                for i in range(len(ABILITIES)):
                    row_y = box_y + 90 + i * 52
                    if row_y - 4 <= ty <= row_y + 48:
                        if shop_cursor == i:
                            # Already selected - try to buy!
                            cost = ABILITIES[i][1]
                            if not ability_unlocked[i] and chips_collected >= cost:
                                chips_collected -= cost
                                ability_unlocked[i] = True
                        else:
                            shop_cursor = i
                        touch_held = False  # prevent repeated taps
                        break

        # Skip movement and updates when shop is open (game is paused)
        if shop_open:
            draw_shop(screen)
            if touch_active:
                draw_touch_buttons(screen)
            pygame.display.flip()
            clock.tick(FPS)
            await asyncio.sleep(0)
            continue

        # --- ABILITY TIMERS ---
        # Count down all active ability timers each frame
        if dash_cooldown > 0:
            dash_cooldown -= 1
        if dash_active > 0:
            dash_active -= 1
        if freeze_timer > 0:
            freeze_timer -= 1
        if invisible_timer > 0:
            invisible_timer -= 1
        if giant_timer > 0:
            giant_timer -= 1
        if jumpscare_timer > 0:
            jumpscare_timer -= 1
            jumpscare_frame += 1
        if closet_msg_timer > 0:
            closet_msg_timer -= 1
        # Smoothly grow/shrink for giant mode
        target_giant = 2.5 if giant_timer > 0 else 1.0
        giant_scale += (target_giant - giant_scale) * 0.15

        # Bounce timer and height (smooth arc using sine!)
        if bounce_timer > 0:
            bounce_timer -= 1
            # Sine curve: goes up then comes back down smoothly
            t = bounce_timer / BOUNCE_DURATION  # 1.0 -> 0.0
            bounce_height = math.sin(t * math.pi) * 80  # max 80 pixels high
        else:
            bounce_height = 0.0
        if bounce_cooldown > 0:
            bounce_cooldown -= 1

        # Teleport cooldown and flash
        if teleport_cooldown > 0:
            teleport_cooldown -= 1
        if teleport_flash > 0:
            teleport_flash -= 1

        # Earthquake timers
        if earthquake_timer > 0:
            earthquake_timer -= 1
            # When earthquake ends, unstun NPCs and cars
            if earthquake_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock":
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
                for car in cars:
                    if car.speed == 0.0:
                        car.speed = random.uniform(1.2, 2.5)
        if earthquake_cooldown > 0:
            earthquake_cooldown -= 1
        if earthquake_shake > 0:
            earthquake_shake -= 1

        # --- MOVEMENT ---
        # Check which keys are currently held down
        keys = pygame.key.get_pressed()
        dx = 0
        dy = 0

        # Calculate speed multiplier from abilities!
        speed_mult = 1.0
        # Super Speed: hold SHIFT to go fast (ability index 1)
        if ability_unlocked[1] and keys[pygame.K_LSHIFT]:
            speed_mult = 2.2
        # Dash: press SHIFT for a burst (ability index 0)
        # Dash activates when SHIFT is pressed and we have the dash ability
        if ability_unlocked[0] and not ability_unlocked[1]:
            # Only dash if super speed is NOT unlocked (otherwise SHIFT = super speed)
            if keys[pygame.K_LSHIFT] and dash_cooldown <= 0 and dash_active <= 0:
                dash_active = 12  # 12 frames of dash burst
                dash_cooldown = 45  # cooldown before next dash
        # If BOTH dash and super speed are unlocked, SHIFT = super speed,
        # and dash triggers automatically when you start running fast
        if ability_unlocked[0] and ability_unlocked[1]:
            if keys[pygame.K_LSHIFT] and dash_cooldown <= 0 and dash_active <= 0:
                dash_active = 12
                dash_cooldown = 45
        if dash_active > 0:
            speed_mult = max(speed_mult, 4.0)  # dash is faster than super speed
        # Giant mode makes you a little slower (you're big!)
        if giant_timer > 0:
            speed_mult *= 0.8
        current_speed = burrb_speed * speed_mult

        # Cancel touch movement if keyboard is used
        if any(
            keys[k]
            for k in (
                pygame.K_LEFT,
                pygame.K_RIGHT,
                pygame.K_UP,
                pygame.K_DOWN,
                pygame.K_a,
                pygame.K_d,
                pygame.K_w,
                pygame.K_s,
            )
        ):
            touch_move_target = None

        # TOP-DOWN CONTROLS:
        # Arrow keys / WASD move in that direction directly
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            dx = -current_speed
            facing_left = True
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            dx = current_speed
            facing_left = False
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dy = -current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dy = current_speed

        # Diagonal movement shouldn't be faster
        if dx != 0 and dy != 0:
            dx *= 0.707
            dy *= 0.707

        # Update the angle to match movement direction
        if dx != 0 or dy != 0:
            burrb_angle = math.atan2(dy, dx)

        # --- TOUCH MOVEMENT ---
        # If no keyboard input and we have a touch move target, walk toward it!
        if dx == 0 and dy == 0 and touch_move_target is not None and touch_active:
            target_x, target_y = touch_move_target
            if inside_building is not None:
                # Moving inside a building
                tmx = target_x - interior_x
                tmy = target_y - interior_y
            else:
                # Moving outside
                tmx = target_x - burrb_x
                tmy = target_y - burrb_y
            touch_dist = math.sqrt(tmx * tmx + tmy * tmy)
            if touch_dist > 8:  # not close enough yet, keep walking
                # Normalize and apply speed
                dx = (tmx / touch_dist) * current_speed
                dy = (tmy / touch_dist) * current_speed
                # Update facing direction
                facing_left = dx < 0
                burrb_angle = math.atan2(dy, dx)
            else:
                # Arrived at target!
                touch_move_target = None

        # Try to move (check collisions)!
        is_walking = dx != 0 or dy != 0

        if inside_building is not None:
            # INSIDE A BUILDING - use interior collision
            if dx != 0:
                new_x = interior_x + dx
                if can_move_interior(inside_building, new_x, interior_y):
                    interior_x = new_x
            if dy != 0:
                new_y = interior_y + dy
                if can_move_interior(inside_building, interior_x, new_y):
                    interior_y = new_y
        else:
            # OUTSIDE - use world collision
            # When bouncing, the burrb is in the air and can fly over buildings!
            if bounce_timer > 0:
                new_x = burrb_x + dx
                new_y = burrb_y + dy
                # Still clamp to world boundaries
                new_x = max(20, min(WORLD_WIDTH - 20, new_x))
                new_y = max(20, min(WORLD_HEIGHT - 20, new_y))
                burrb_x = new_x
                burrb_y = new_y
            else:
                if dx != 0:
                    new_x = burrb_x + dx
                    if can_move_to(new_x, burrb_y):
                        burrb_x = new_x
                if dy != 0:
                    new_y = burrb_y + dy
                    if can_move_to(burrb_x, new_y):
                        burrb_y = new_y

        if is_walking:
            walk_frame += 1
        else:
            walk_frame = 0

        # --- UPDATE RESIDENT BURRB (angry chase!) ---
        # If we're inside a building and the resident is angry (we stole chips!),
        # the resident chases us around the room!
        # BUT if we're invisible, they can't see us - they just wander confused!
        if inside_building is not None and inside_building.resident_angry:
            bld = inside_building
            if invisible_timer > 0:
                # Can't see us! Wander randomly
                rand_angle = math.sin(bld.resident_walk_frame * 0.05) * 0.8
                chase_dx = math.cos(rand_angle) * bld.resident_speed * 0.5
                chase_dy = math.sin(rand_angle) * bld.resident_speed * 0.5
                new_rx = bld.resident_x + chase_dx
                new_ry = bld.resident_y + chase_dy
                if can_move_interior(bld, new_rx, bld.resident_y):
                    bld.resident_x = new_rx
                if can_move_interior(bld, bld.resident_x, new_ry):
                    bld.resident_y = new_ry
                bld.resident_walk_frame += 1
            else:
                pass  # (chase logic continues below)
        if (
            inside_building is not None
            and inside_building.resident_angry
            and invisible_timer <= 0
        ):
            bld = inside_building
            # Move resident toward the player
            chase_dx = interior_x - bld.resident_x
            chase_dy = interior_y - bld.resident_y
            chase_dist = math.sqrt(chase_dx * chase_dx + chase_dy * chase_dy)
            if chase_dist > 0:
                # Normalize and move at resident speed
                move_x = (chase_dx / chase_dist) * bld.resident_speed
                move_y = (chase_dy / chase_dist) * bld.resident_speed
                # Try to move (respect interior walls!)
                new_rx = bld.resident_x + move_x
                new_ry = bld.resident_y + move_y
                if can_move_interior(bld, new_rx, bld.resident_y):
                    bld.resident_x = new_rx
                if can_move_interior(bld, bld.resident_x, new_ry):
                    bld.resident_y = new_ry
                bld.resident_walk_frame += 1

            # Did the resident catch the player? Push them back!
            catch_dx = interior_x - bld.resident_x
            catch_dy = interior_y - bld.resident_y
            catch_dist = math.sqrt(catch_dx * catch_dx + catch_dy * catch_dy)
            if catch_dist < 14:  # caught!
                # Push the player away from the resident
                if catch_dist > 0:
                    push_x = (catch_dx / catch_dist) * 8
                    push_y = (catch_dy / catch_dist) * 8
                    new_px = interior_x + push_x
                    new_py = interior_y + push_y
                    if can_move_interior(bld, new_px, interior_y):
                        interior_x = new_px
                    if can_move_interior(bld, interior_x, new_py):
                        interior_y = new_py

        # --- UPDATE MONSTER (6-legged bed creature chase!) ---
        # If the monster crawled out from under the bed, it chases the player!
        # It's faster than the resident (speed 2.2 vs 1.8) and ignores invisibility!
        if inside_building is not None and inside_building.monster_active:
            bld = inside_building
            # Move monster toward the player
            mon_dx = interior_x - bld.monster_x
            mon_dy = interior_y - bld.monster_y
            mon_dist = math.sqrt(mon_dx * mon_dx + mon_dy * mon_dy)
            if mon_dist > 0:
                mon_move_x = (mon_dx / mon_dist) * bld.monster_speed
                mon_move_y = (mon_dy / mon_dist) * bld.monster_speed
                new_mx = bld.monster_x + mon_move_x
                new_my = bld.monster_y + mon_move_y
                if can_move_interior(bld, new_mx, bld.monster_y):
                    bld.monster_x = new_mx
                if can_move_interior(bld, bld.monster_x, new_my):
                    bld.monster_y = new_my
                bld.monster_walk_frame += 1

            # Did the monster catch the player? Push them back!
            mcatch_dx = interior_x - bld.monster_x
            mcatch_dy = interior_y - bld.monster_y
            mcatch_dist = math.sqrt(mcatch_dx * mcatch_dx + mcatch_dy * mcatch_dy)
            if mcatch_dist < 14:  # caught!
                if mcatch_dist > 0:
                    mpush_x = (mcatch_dx / mcatch_dist) * 10
                    mpush_y = (mcatch_dy / mcatch_dist) * 10
                    new_px = interior_x + mpush_x
                    new_py = interior_y + mpush_y
                    if can_move_interior(bld, new_px, interior_y):
                        interior_x = new_px
                    if can_move_interior(bld, interior_x, new_py):
                        interior_y = new_py

        # --- UPDATE NPCs ---
        # Every frame, each NPC takes a step and maybe changes direction
        # UNLESS they're frozen by the Freeze ability!
        if freeze_timer <= 0:
            for npc in npcs:
                npc.update()
        # (When frozen, NPCs just stand perfectly still - like statues!)

        # --- UPDATE CARS ---
        # Cars drive along roads every frame
        if inside_building is None:
            for car in cars:
                car.update()

        # --- UPDATE TONGUE ---
        # The tongue extends outward, checks if it hits any NPC,
        # then retracts back. If it hits an NPC, that NPC turns to stone!
        # Mega Tongue ability doubles the range!
        effective_tongue_max = tongue_max_length * (2.0 if ability_unlocked[2] else 1.0)
        if tongue_active:
            if not tongue_retracting:
                # Tongue is shooting outward
                tongue_length += tongue_speed
                if tongue_length >= effective_tongue_max:
                    # Reached max length, start pulling back
                    tongue_retracting = True

                # Check if tongue tip hit any NPC!
                tip_x = burrb_x + math.cos(tongue_angle) * tongue_length
                tip_y = burrb_y + math.sin(tongue_angle) * tongue_length
                for npc in npcs:
                    if npc.npc_type == "rock":
                        continue  # already a rock, skip
                    ddx = npc.x - tip_x
                    ddy = npc.y - tip_y
                    hit_dist = math.sqrt(ddx * ddx + ddy * ddy)
                    if hit_dist < 16:  # close enough = hit!
                        # PETRIFY! Turn this NPC into a rock!
                        npc.npc_type = "rock"
                        npc.color = (120, 120, 110)  # gray rock color
                        npc.detail_color = (90, 90, 80)  # darker gray
                        npc.speed = 0  # rocks don't move
                        tongue_hit_npc = npc
                        tongue_retracting = True  # tongue snaps back
                        break
            else:
                # Tongue is retracting
                tongue_length -= tongue_speed * 1.5  # retract faster
                if tongue_length <= 0:
                    tongue_length = 0
                    tongue_active = False
                    tongue_hit_npc = None

        # --- CAMERA ---
        # Smoothly follow the burrb (the camera "lerps" toward the burrb)
        target_cam_x = burrb_x - SCREEN_WIDTH // 2
        target_cam_y = burrb_y - SCREEN_HEIGHT // 2
        cam_x += (target_cam_x - cam_x) * 0.08
        cam_y += (target_cam_y - cam_y) * 0.08
        # Earthquake screen shake!
        if earthquake_shake > 0:
            cam_x += random.randint(-6, 6)
            cam_y += random.randint(-6, 6)

        # --- DRAWING ---
        if inside_building is not None:
            # ========== INSIDE A BUILDING ==========
            # Top-down inside the building
            draw_interior_topdown(screen, inside_building, interior_x, interior_y)

            # Door prompt if near interior door
            if is_at_interior_door(inside_building, interior_x, interior_y):
                prompt = font.render("Press E to exit", True, YELLOW)
                prompt_shadow = font.render("Press E to exit", True, BLACK)
                px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
                screen.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
                screen.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))

            # Chip stealing prompt if near the chip bag!
            bld = inside_building
            if not bld.chips_stolen and bld.chips_x > 0:
                chip_dx = interior_x - bld.chips_x
                chip_dy = interior_y - bld.chips_y
                chip_dist = math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
                if chip_dist < 30:
                    chip_prompt = font.render(
                        "Press E to take chips!", True, (255, 200, 50)
                    )
                    chip_shadow = font.render("Press E to take chips!", True, BLACK)
                    cpx = SCREEN_WIDTH // 2 - chip_prompt.get_width() // 2
                    screen.blit(chip_shadow, (cpx + 1, SCREEN_HEIGHT // 2 + 71))
                    screen.blit(chip_prompt, (cpx, SCREEN_HEIGHT // 2 + 70))

            # Closet prompt if near the closet!
            if not bld.closet_opened and bld.closet_x > 0:
                cl_dx = interior_x - bld.closet_x
                cl_dy = interior_y - bld.closet_y
                cl_dist = math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
                if cl_dist < 30:
                    cl_prompt = font.render(
                        "Press E to open closet!", True, (200, 170, 100)
                    )
                    cl_shadow = font.render("Press E to open closet!", True, BLACK)
                    clpx = SCREEN_WIDTH // 2 - cl_prompt.get_width() // 2
                    screen.blit(cl_shadow, (clpx + 1, SCREEN_HEIGHT // 2 + 41))
                    screen.blit(cl_prompt, (clpx, SCREEN_HEIGHT // 2 + 40))

            # Bed prompt if near the bed!
            if not bld.bed_shaken and bld.bed_x > 0:
                bed_dx = interior_x - bld.bed_x
                bed_dy = interior_y - bld.bed_y
                bed_dist = math.sqrt(bed_dx * bed_dx + bed_dy * bed_dy)
                if bed_dist < 30:
                    bed_prompt = font.render(
                        "Press E to shake bed!", True, (180, 140, 220)
                    )
                    bed_shadow = font.render("Press E to shake bed!", True, BLACK)
                    bpx = SCREEN_WIDTH // 2 - bed_prompt.get_width() // 2
                    screen.blit(bed_shadow, (bpx + 1, SCREEN_HEIGHT // 2 + 11))
                    screen.blit(bed_prompt, (bpx, SCREEN_HEIGHT // 2 + 10))

            # Monster warning text!
            if bld.monster_active:
                mon_text = font.render("SOMETHING CRAWLED OUT!", True, (200, 0, 200))
                mon_shadow = font.render("SOMETHING CRAWLED OUT!", True, BLACK)
                mpx = SCREEN_WIDTH // 2 - mon_text.get_width() // 2
                # Flash every half-second
                if (pygame.time.get_ticks() // 350) % 2 == 0:
                    screen.blit(mon_shadow, (mpx + 1, 91))
                    screen.blit(mon_text, (mpx, 90))

            # "Found chips in closet!" message
            if closet_msg_timer > 0:
                found_text = font.render(
                    "Found 2 chips in the closet!", True, (100, 255, 100)
                )
                found_shadow = font.render("Found 2 chips in the closet!", True, BLACK)
                ftx = SCREEN_WIDTH // 2 - found_text.get_width() // 2
                screen.blit(found_shadow, (ftx + 1, SCREEN_HEIGHT // 2 - 29))
                screen.blit(found_text, (ftx, SCREEN_HEIGHT // 2 - 30))

            # Warning text when resident is angry!
            if bld.resident_angry:
                warn_text = font.render("THE BURRB IS ANGRY!", True, (255, 60, 60))
                warn_shadow = font.render("THE BURRB IS ANGRY!", True, BLACK)
                wpx = SCREEN_WIDTH // 2 - warn_text.get_width() // 2
                # Make it flash by only showing every other half-second
                if (pygame.time.get_ticks() // 400) % 2 == 0:
                    screen.blit(warn_shadow, (wpx + 1, 71))
                    screen.blit(warn_text, (wpx, 70))

        else:
            # ========== TOP-DOWN MODE (the original view) ==========
            # Fill the background with biome colors
            draw_biome_ground(screen, cam_x, cam_y)

            # Draw biome objects that are behind the burrb
            for ox, oy, okind, osize in biome_objects:
                if oy < burrb_y:
                    draw_biome_object(screen, ox, oy, okind, osize, cam_x, cam_y)

            # Draw parks (in the city)
            for park in parks:
                pr = pygame.Rect(park.x - cam_x, park.y - cam_y, park.w, park.h)
                pygame.draw.rect(screen, (100, 180, 80), pr, border_radius=12)
                pygame.draw.rect(screen, DARK_GREEN, pr, 2, border_radius=12)

            # Draw roads (only in the city!)
            draw_road_grid(screen, cam_x, cam_y)

            # Draw cars on the roads
            for car in sorted(cars, key=lambda c: c.y):
                draw_car_topdown(screen, car, cam_x, cam_y)

            # Draw trees (behind the burrb if they're above it)
            for tx, ty, tsize in trees:
                if ty < burrb_y:
                    draw_tree(screen, tx, ty, tsize, cam_x, cam_y)

            # Draw buildings (sorted by y position for depth)
            for b in sorted(buildings, key=lambda b: b.y + b.h):
                b.draw(screen, cam_x, cam_y)

            # Draw NPCs (sorted by Y so ones lower on screen draw on top)
            for npc in sorted(npcs, key=lambda n: n.y):
                draw_npc_topdown(screen, npc, cam_x, cam_y)
                # Freeze effect: draw a blue ice overlay on frozen NPCs
                if freeze_timer > 0 and npc.npc_type != "rock":
                    npc_sx = int(npc.x - cam_x)
                    npc_sy = int(npc.y - cam_y)
                    if (
                        -20 < npc_sx < SCREEN_WIDTH + 20
                        and -20 < npc_sy < SCREEN_HEIGHT + 20
                    ):
                        ice_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                        ice_alpha = 100 + int(math.sin(freeze_timer * 0.1) * 40)
                        pygame.draw.rect(
                            ice_surf,
                            (100, 180, 255, ice_alpha),
                            (0, 0, 20, 20),
                            border_radius=4,
                        )
                        # Little ice sparkles
                        for sp in range(3):
                            spx = 4 + sp * 6
                            spy = 3 + (sp % 2) * 10
                            pygame.draw.circle(
                                ice_surf, (200, 230, 255, 180), (spx, spy), 2
                            )
                        screen.blit(ice_surf, (npc_sx - 10, npc_sy - 10))

            # Bounce: draw a shadow on the ground when airborne!
            if bounce_timer > 0:
                shadow_sx = int(burrb_x - cam_x)
                shadow_sy = int(burrb_y - cam_y)
                shadow_w = int(
                    16 * (1.0 - bounce_height / 120)
                )  # shadow shrinks as you go up
                shadow_h = max(2, shadow_w // 3)
                shadow_surf = pygame.Surface(
                    (shadow_w * 2, shadow_h * 2), pygame.SRCALPHA
                )
                shadow_alpha = int(80 * (1.0 - bounce_height / 120))
                pygame.draw.ellipse(
                    shadow_surf,
                    (0, 0, 0, shadow_alpha),
                    (0, 0, shadow_w * 2, shadow_h * 2),
                )
                screen.blit(shadow_surf, (shadow_sx - shadow_w, shadow_sy - shadow_h))

            # Bounce height offset for drawing the burrb
            bounce_y_offset = -bounce_height  # negative = up on screen

            # Draw the burrb (with Giant Mode and Invisibility effects!)
            if giant_scale > 1.05 or invisible_timer > 0:
                # Draw to a temp surface so we can scale/alpha it
                temp_size = int(60 * giant_scale)
                temp_surf = pygame.Surface((temp_size, temp_size), pygame.SRCALPHA)
                # Draw burrb centered on temp surface
                draw_burrb(
                    temp_surf,
                    temp_size // 2,
                    temp_size // 2,
                    0,
                    0,
                    facing_left,
                    walk_frame,
                )
                # Scale it up for giant mode
                if giant_scale > 1.05:
                    new_w = int(temp_size * giant_scale)
                    new_h = int(temp_size * giant_scale)
                    temp_surf = pygame.transform.scale(temp_surf, (new_w, new_h))
                else:
                    new_w = temp_size
                    new_h = temp_size
                # Invisibility = semi-transparent + blue tint
                if invisible_timer > 0:
                    temp_surf.set_alpha(60)
                # Blit at the correct world position (with bounce offset!)
                blit_x = int(burrb_x - cam_x - new_w // 2)
                blit_y = int(burrb_y - cam_y - new_h // 2 + bounce_y_offset)
                screen.blit(temp_surf, (blit_x, blit_y))
            else:
                draw_burrb(
                    screen,
                    burrb_x,
                    burrb_y + bounce_y_offset,
                    cam_x,
                    cam_y,
                    facing_left,
                    walk_frame,
                )

            # Teleport flash effect!
            if teleport_flash > 0:
                flash_surf = pygame.Surface(
                    (SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA
                )
                flash_alpha = int(200 * (teleport_flash / 15))
                pygame.draw.circle(
                    flash_surf,
                    (100, 200, 255, flash_alpha),
                    (int(burrb_x - cam_x), int(burrb_y - cam_y)),
                    int(60 + (15 - teleport_flash) * 10),
                )
                screen.blit(flash_surf, (0, 0))

            # Earthquake shockwave effect!
            if earthquake_shake > 0:
                eq_sx = int(burrb_x - cam_x)
                eq_sy = int(burrb_y - cam_y)
                # Expanding ring
                ring_radius = int((30 - earthquake_shake) * 12)
                ring_alpha = int(180 * (earthquake_shake / 30))
                eq_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                pygame.draw.circle(
                    eq_surf,
                    (200, 150, 50, ring_alpha),
                    (eq_sx, eq_sy),
                    ring_radius,
                    max(3, 8 - (30 - earthquake_shake) // 4),
                )
                # Inner dust cloud
                if earthquake_shake > 15:
                    inner_r = ring_radius // 2
                    pygame.draw.circle(
                        eq_surf,
                        (180, 160, 100, ring_alpha // 2),
                        (eq_sx, eq_sy),
                        inner_r,
                    )
                screen.blit(eq_surf, (0, 0))

            # Dash trail effect!
            if dash_active > 0:
                burrb_sx = int(burrb_x - cam_x)
                burrb_sy = int(burrb_y - cam_y)
                for trail_i in range(3):
                    trail_offset = (trail_i + 1) * 8
                    trail_alpha = 120 - trail_i * 40
                    trail_x = burrb_sx - int(math.cos(burrb_angle) * trail_offset)
                    trail_y = burrb_sy - int(math.sin(burrb_angle) * trail_offset)
                    trail_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                    pygame.draw.rect(
                        trail_surf,
                        (60, 150, 220, trail_alpha),
                        (0, 0, 16, 16),
                        border_radius=4,
                    )
                    screen.blit(trail_surf, (trail_x - 8, trail_y - 8))

            # Draw the tongue in top-down mode!
            if tongue_active and tongue_length > 0:
                burrb_sx = burrb_x - cam_x
                burrb_sy = burrb_y - cam_y
                tip_sx = burrb_sx + math.cos(tongue_angle) * tongue_length
                tip_sy = burrb_sy + math.sin(tongue_angle) * tongue_length
                # Tongue is pink/red, gets thicker near the base
                # Base (thick part)
                pygame.draw.line(
                    screen,
                    (220, 80, 100),
                    (int(burrb_sx), int(burrb_sy)),
                    (int(tip_sx), int(tip_sy)),
                    4,
                )
                # Center line (lighter pink)
                pygame.draw.line(
                    screen,
                    (255, 140, 160),
                    (int(burrb_sx), int(burrb_sy)),
                    (int(tip_sx), int(tip_sy)),
                    2,
                )
                # Tongue tip (round blob)
                pygame.draw.circle(
                    screen,
                    (220, 60, 80),
                    (int(tip_sx), int(tip_sy)),
                    5,
                )
                pygame.draw.circle(
                    screen,
                    (255, 120, 140),
                    (int(tip_sx), int(tip_sy)),
                    3,
                )

            # Draw trees in front of burrb (if they're below it)
            for tx, ty, tsize in trees:
                if ty >= burrb_y:
                    draw_tree(screen, tx, ty, tsize, cam_x, cam_y)

            # Draw biome objects in front of burrb
            for ox, oy, okind, osize in biome_objects:
                if oy >= burrb_y:
                    draw_biome_object(screen, ox, oy, okind, osize, cam_x, cam_y)

            # Show which biome we're in
            cur_biome = get_biome(burrb_x, burrb_y)
            biome_names = {
                BIOME_CITY: "City",
                BIOME_FOREST: "Forest",
                BIOME_DESERT: "Desert",
                BIOME_SNOW: "Snow",
                BIOME_SWAMP: "Swamp",
            }
            biome_label = font.render(biome_names[cur_biome], True, (255, 255, 255))
            biome_shadow = font.render(biome_names[cur_biome], True, (0, 0, 0))
            screen.blit(biome_shadow, (SCREEN_WIDTH - biome_label.get_width() - 11, 41))
            screen.blit(biome_label, (SCREEN_WIDTH - biome_label.get_width() - 12, 40))

            # Minimap!
            draw_minimap(screen)

        # --- UI overlay (shown in both modes) ---
        # Game title
        title_text = title_font.render("Life of a Burrb", True, WHITE)
        title_shadow = title_font.render("Life of a Burrb", True, BLACK)
        screen.blit(title_shadow, (12, 12))
        screen.blit(title_text, (10, 10))

        # Mode indicator
        if inside_building is not None:
            mode_text = font.render("[INSIDE]", True, YELLOW)
            mode_shadow = font.render("[INSIDE]", True, BLACK)
            help_msg = "Arrows/WASD walk  |  E take/exit  |  ESC quit"
        else:
            mode_text = font.render("[TOP DOWN]", True, BURRB_LIGHT_BLUE)
            mode_shadow = font.render("[TOP DOWN]", True, BLACK)
            help_msg = (
                "Arrows/WASD walk  |  O tongue  |  E enter  |  TAB shop  |  ESC quit"
            )

        screen.blit(mode_shadow, (12, 42))
        screen.blit(mode_text, (10, 40))

        # Chips collected counter!
        if chips_collected > 0:
            chip_str = f"Chips: {chips_collected}"
            chip_text = font.render(chip_str, True, (255, 200, 50))
            chip_shadow = font.render(chip_str, True, BLACK)
            chip_x_pos = SCREEN_WIDTH - chip_text.get_width() - 12
            screen.blit(chip_shadow, (chip_x_pos + 1, 12))
            screen.blit(chip_text, (chip_x_pos, 10))
            # Little chip bag icon next to the counter
            icon_x = chip_x_pos - 16
            pygame.draw.rect(
                screen, (220, 160, 30), (icon_x, 8, 12, 16), border_radius=2
            )
            pygame.draw.rect(screen, (200, 40, 40), (icon_x, 14, 12, 5))
            pygame.draw.rect(
                screen, (150, 100, 20), (icon_x, 8, 12, 16), 1, border_radius=2
            )

        # Active ability indicators (shown on the right side below chip counter)
        ability_y = 34
        # Show active timed abilities with remaining time bars
        active_abilities = []
        if freeze_timer > 0:
            active_abilities.append(("FREEZE", (100, 180, 255), freeze_timer, 300))
        if invisible_timer > 0:
            active_abilities.append(
                ("INVISIBLE", (180, 140, 255), invisible_timer, 300)
            )
        if giant_timer > 0:
            active_abilities.append(("GIANT", (255, 140, 60), giant_timer, 480))
        if dash_active > 0:
            active_abilities.append(("DASH!", (255, 255, 100), dash_active, 12))
        if bounce_timer > 0:
            active_abilities.append(
                ("BOUNCE!", (100, 255, 200), bounce_timer, BOUNCE_DURATION)
            )
        if earthquake_timer > 0:
            active_abilities.append(
                ("QUAKE!", (200, 150, 50), earthquake_timer, EARTHQUAKE_DURATION)
            )
        # Show always-on abilities as small badges
        passive_badges = []
        if ability_unlocked[1]:  # Super Speed
            passive_badges.append(("SPD", (100, 255, 100)))
        if ability_unlocked[2]:  # Mega Tongue
            passive_badges.append(("TNG", (255, 120, 160)))
        if (
            ability_unlocked[0] and not ability_unlocked[1]
        ):  # Dash (only if no super speed)
            passive_badges.append(("DSH", (255, 255, 100)))

        for ab_name, ab_color, ab_timer, ab_max in active_abilities:
            # Background bar
            bar_w = 90
            bar_h = 14
            bar_x = SCREEN_WIDTH - bar_w - 12
            bar_y = ability_y
            pygame.draw.rect(
                screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3
            )
            # Fill bar
            fill_w = int(bar_w * ab_timer / ab_max)
            pygame.draw.rect(
                screen, ab_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3
            )
            # Label
            ab_txt = font.render(ab_name, True, WHITE)
            screen.blit(ab_txt, (bar_x - ab_txt.get_width() - 6, bar_y - 2))
            ability_y += 20

        # Passive ability badges
        if passive_badges:
            badge_x = SCREEN_WIDTH - 12
            for badge_name, badge_color in passive_badges:
                badge_txt = font.render(badge_name, True, badge_color)
                badge_x -= badge_txt.get_width() + 8
                screen.blit(badge_txt, (badge_x, ability_y))
            ability_y += 20

        # Mini instructions
        help_text = font.render(help_msg, True, WHITE)
        help_shadow = font.render(help_msg, True, BLACK)
        screen.blit(help_shadow, (12, SCREEN_HEIGHT - 28))
        screen.blit(help_text, (10, SCREEN_HEIGHT - 30))

        # Door prompt when near a building outside
        if inside_building is None:
            nearby = get_nearby_door_building(burrb_x, burrb_y)
            if nearby is not None:
                prompt = font.render("Press E to enter", True, YELLOW)
                prompt_shadow = font.render("Press E to enter", True, BLACK)
                px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
                screen.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
                screen.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))

        # Draw touch buttons (only if touch has been used)
        if touch_active:
            draw_touch_buttons(screen)

        # JUMP SCARE! Draw the scary birb on top of EVERYTHING!
        if jumpscare_timer > 0:
            draw_jumpscare(screen, jumpscare_frame, scare_level)

        # Update the display (flip the "page" so we see what we just drew)
        pygame.display.flip()

        # Tick the clock - this keeps the game at 60 FPS
        clock.tick(FPS)
        await asyncio.sleep(0)

    # Clean up when the game is done
    pygame.quit()


asyncio.run(main())
