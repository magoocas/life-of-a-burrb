"""
Life of a Burrb
A burrb is a bird-like animal that walks around an open world city.
Use arrow keys or WASD to move around!
"""

import pygame
import math
import random
import asyncio

# --- Refactored imports (Phase 1) ---
from src.constants import (
    WHITE,
    BLACK,
    DARK_GRAY,
    GRAY,
    LIGHT_GRAY,
    GREEN,
    DARK_GREEN,
    BROWN,
    SKY_BLUE,
    YELLOW,
    SIDEWALK,
    ROAD_COLOR,
    ROAD_LINE,
    BURRB_BLUE,
    BURRB_LIGHT_BLUE,
    BURRB_DARK_BLUE,
    BURRB_ORANGE,
    BURRB_EYE,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    BLOCK_SIZE,
    ROAD_WIDTH,
    SIDEWALK_WIDTH,
)
from src.settings import (
    SCREEN_WIDTH,
    SCREEN_HEIGHT,
    FPS,
    SPAWN_X,
    SPAWN_Y,
    SPAWN_SIZE,
    SPAWN_RECT,
)
from src.biomes import (
    BIOME_CITY,
    BIOME_FOREST,
    BIOME_DESERT,
    BIOME_SNOW,
    BIOME_SWAMP,
    CITY_X1,
    CITY_Y1,
    CITY_X2,
    CITY_Y2,
    BIOME_COLORS,
    get_biome,
)

# --- Refactored imports (Phase 2) ---
from src.entities.building import Building
from src.entities.npc import NPC, spawn_npcs
from src.entities.car import Car, spawn_cars
from src.entities.player import Player, MAX_HP, HURT_COOLDOWN_TIME

# Initialize pygame - this starts up the game engine
pygame.init()

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Life of a Burrb")

# Clock controls how fast the game runs (frames per second)
clock = pygame.time.Clock()


# ============================================================
# BUILDINGS
# ============================================================
# Building class is in src/entities/building.py (Phase 2 refactor)
# Imported above: from src.entities.building import Building

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

# BIOME COLLECTIBLES - special items to find in each biome!
# City has potato chips (inside buildings). The other biomes have their
# own special items scattered around the open world:
#   Forest  = Berries   (juicy red/purple berries)
#   Desert  = Gems      (shiny crystals poking out of the sand)
#   Snow    = Snowflakes (sparkly magical snowflakes)
#   Swamp   = Mushrooms  (glowing green mushrooms)
# Collecting any of these gives you chips to spend in the shop!
biome_collectibles = []  # list of [x, y, kind, collected]

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

# --- BIOME COLLECTIBLES ---
# Scatter special collectible items throughout each biome!
# Each one is a list (not tuple) so we can mark it as collected.

# Forest: Berries (12 scattered around - rare!)
for _ in range(12):
    fx = random.randint(200, WORLD_WIDTH // 2 - 200)
    fy = random.randint(200, WORLD_HEIGHT // 2 - 200)
    if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
        continue
    biome_collectibles.append([fx, fy, "berry", False])

# Snow: Snowflakes (12 scattered around - rare!)
for _ in range(12):
    sx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
    sy = random.randint(200, WORLD_HEIGHT // 2 - 200)
    if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
        continue
    biome_collectibles.append([sx, sy, "snowflake", False])

# Swamp: Glowing Mushrooms (12 scattered around - rare!)
for _ in range(12):
    wx = random.randint(200, WORLD_WIDTH // 2 - 200)
    wy = random.randint(WORLD_HEIGHT // 2 + 200, WORLD_HEIGHT - 200)
    if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
        continue
    biome_collectibles.append([wx, wy, "glow_mushroom", False])

# Desert: Gems (12 scattered around - rare!)
for _ in range(12):
    dx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
    dy = random.randint(WORLD_HEIGHT // 2 + 200, WORLD_HEIGHT - 200)
    if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
        continue
    biome_collectibles.append([dx, dy, "gem", False])


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


# NPC class is in src/entities/npc.py (Phase 2 refactor)
# Imported above: from src.entities.npc import NPC, spawn_npcs

# Spawn NPCs throughout the world!
npcs = spawn_npcs(buildings)


# ============================================================
# CARS - vehicles driving on the roads!
# ============================================================
# Cars drive along the road grid. They go in one direction
# (horizontal or vertical) and when they reach an intersection,
# they might turn or keep going straight.


# Car class is in src/entities/car.py (Phase 2 refactor)
# Imported above: from src.entities.car import Car, spawn_cars

# Spawn cars on city roads (uses random seed for consistency)
cars = spawn_cars()


# ============================================================
# SPAWN SQUARE CLEANUP
# ============================================================
# Remove ALL objects from the spawn square so the player starts
# in a nice clear area with nothing in the way!
# A little padding so things don't sit right on the edge.
_sp = 10  # padding
_spawn_padded = pygame.Rect(
    SPAWN_RECT.x - _sp,
    SPAWN_RECT.y - _sp,
    SPAWN_RECT.w + _sp * 2,
    SPAWN_RECT.h + _sp * 2,
)

# Remove buildings
buildings = [b for b in buildings if not _spawn_padded.colliderect(b.get_rect())]

# Remove trees
trees = [
    (tx, ty, ts) for (tx, ty, ts) in trees if not _spawn_padded.collidepoint(tx, ty)
]

# Remove biome objects (decorations)
biome_objects = [
    (ox, oy, ok, os)
    for (ox, oy, ok, os) in biome_objects
    if not _spawn_padded.collidepoint(ox, oy)
]

# Remove biome collectibles
biome_collectibles = [
    c for c in biome_collectibles if not _spawn_padded.collidepoint(c[0], c[1])
]

# Remove NPCs
npcs = [n for n in npcs if not _spawn_padded.collidepoint(n.x, n.y)]

# Remove cars
cars = [c for c in cars if not _spawn_padded.collidepoint(c.x, c.y)]

# Remove parks that overlap
parks = [p for p in parks if not _spawn_padded.colliderect(p)]


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


def draw_biome_collectible(surface, x, y, kind, cam_x, cam_y):
    """Draw a collectible biome item with a little bobbing animation."""
    sx = int(x - cam_x)
    sy = int(y - cam_y)
    # Skip if off-screen
    if sx < -40 or sx > SCREEN_WIDTH + 40 or sy < -40 or sy > SCREEN_HEIGHT + 40:
        return
    # Use game ticks for animation (smooth and consistent)
    t = pygame.time.get_ticks() * 0.001  # seconds as float
    # Little floating bob animation (goes up and down gently)
    bob = int(math.sin(t * 3.5 + x * 0.01) * 3)
    sy += bob

    if kind == "berry":
        # A cluster of juicy red and purple berries on a tiny branch!
        # Little branch
        pygame.draw.line(surface, (100, 70, 30), (sx, sy + 4), (sx, sy - 2), 2)
        # Berries - cluster of 3 circles
        pygame.draw.circle(surface, (180, 30, 50), (sx - 4, sy - 2), 5)
        pygame.draw.circle(surface, (140, 20, 80), (sx + 4, sy - 2), 5)
        pygame.draw.circle(surface, (200, 40, 40), (sx, sy - 6), 5)
        # Little shine spots on each berry
        pygame.draw.circle(surface, (255, 150, 150), (sx - 3, sy - 4), 2)
        pygame.draw.circle(surface, (200, 130, 200), (sx + 5, sy - 4), 2)
        pygame.draw.circle(surface, (255, 140, 140), (sx + 1, sy - 8), 2)
        # Sparkle effect!
        sparkle = int(math.sin(t * 6 + x) * 2)
        pygame.draw.circle(surface, (255, 255, 200), (sx - 6, sy - 8 + sparkle), 1)

    elif kind == "gem":
        # A shiny crystal poking out of the sand!
        # Crystal shape - diamond/gem with facets
        gem_pts = [
            (sx, sy - 12),  # top point
            (sx - 7, sy - 4),  # left
            (sx - 4, sy + 4),  # bottom-left
            (sx + 4, sy + 4),  # bottom-right
            (sx + 7, sy - 4),  # right
        ]
        # Main gem body (cyan/teal)
        pygame.draw.polygon(surface, (50, 200, 220), gem_pts)
        # Lighter facet on the left
        pygame.draw.polygon(
            surface, (100, 230, 245), [(sx, sy - 12), (sx - 7, sy - 4), (sx, sy)]
        )
        # Outline
        pygame.draw.polygon(surface, (30, 150, 170), gem_pts, 2)
        # Sparkle at the top!
        sparkle = abs(int(math.sin(t * 7 + x * 0.1) * 3))
        pygame.draw.circle(surface, (255, 255, 255), (sx, sy - 12 - sparkle), 2)
        pygame.draw.circle(surface, (200, 240, 255), (sx + 3, sy - 10), 1)

    elif kind == "snowflake":
        # A sparkly magical snowflake floating just above the ground!
        r = 8
        # Draw 6 branches of the snowflake
        for i in range(6):
            angle = i * (math.pi / 3) + t * 1.2  # slowly rotates!
            ex = sx + int(math.cos(angle) * r)
            ey = sy + int(math.sin(angle) * r)
            pygame.draw.line(surface, (200, 220, 255), (sx, sy), (ex, ey), 2)
            # Little branch tips
            for side in [-0.4, 0.4]:
                bx = sx + int(math.cos(angle) * r * 0.6)
                by = sy + int(math.sin(angle) * r * 0.6)
                tx = bx + int(math.cos(angle + side) * 4)
                ty = by + int(math.sin(angle + side) * 4)
                pygame.draw.line(surface, (180, 200, 255), (bx, by), (tx, ty), 1)
        # Center dot
        pygame.draw.circle(surface, (240, 245, 255), (sx, sy), 3)
        # Sparkle!
        sparkle = abs(int(math.sin(t * 9 + x * 0.05) * 4))
        pygame.draw.circle(surface, (255, 255, 255), (sx - 5, sy - 5 - sparkle), 1)
        pygame.draw.circle(surface, (255, 255, 255), (sx + 6, sy + 3 + sparkle), 1)

    elif kind == "glow_mushroom":
        # A glowing green/teal mushroom with a soft light around it!
        # Glow effect (translucent circle behind the mushroom)
        glow_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
        glow_pulse = 80 + int(math.sin(t * 5 + y * 0.01) * 30)
        pygame.draw.circle(glow_surf, (50, 255, 120, glow_pulse), (20, 20), 16)
        surface.blit(glow_surf, (sx - 20, sy - 20))
        # Stem
        pygame.draw.rect(surface, (180, 200, 160), (sx - 2, sy, 4, 8))
        # Cap (rounded top)
        pygame.draw.ellipse(surface, (30, 200, 100), (sx - 8, sy - 6, 16, 10))
        # Lighter spots on cap
        pygame.draw.circle(surface, (80, 255, 150), (sx - 3, sy - 3), 2)
        pygame.draw.circle(surface, (80, 255, 150), (sx + 4, sy - 2), 2)
        # Sparkle
        sparkle = abs(int(math.sin(t * 6 + y) * 3))
        pygame.draw.circle(surface, (150, 255, 200), (sx, sy - 10 - sparkle), 1)


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
    # Don't draw dead NPCs!
    if not npc.alive:
        return

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
        # Eye - aggressive burrbs have angry red eyes!
        eye_x = sx + 2
        if npc.aggressive:
            eye_color = (220, 30, 30)  # angry red!
        else:
            eye_color = npc.detail_color
        pygame.draw.circle(surface, eye_color, (eye_x, sy - 2), 2)
        # Angry eyebrows on aggressive burrbs
        if npc.aggressive:
            pygame.draw.line(
                surface,
                (180, 0, 0),
                (eye_x - 3, sy - 5),
                (eye_x + 3, sy - 3),
                2,
            )
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
        # Exclamation mark when chasing! So you know they spotted you.
        if npc.chasing:
            alert_font = pygame.font.Font(None, 20)
            alert_text = alert_font.render("!", True, (255, 50, 50))
            surface.blit(alert_text, (sx - 3, sy - size // 2 - 16))

        # Hurt flash! NPC flashes red when hit by the tongue.
        if npc.hurt_flash > 0:
            flash_surf = pygame.Surface((size + 4, size + 4), pygame.SRCALPHA)
            flash_alpha = int(180 * (npc.hurt_flash / 15.0))
            pygame.draw.rect(
                flash_surf,
                (255, 50, 50, flash_alpha),
                (0, 0, size + 4, size + 4),
                border_radius=3,
            )
            surface.blit(flash_surf, (sx - size // 2 - 2, sy - size // 2 - 2))

        # Health bar above NPC (only for aggressive burrbs, only when hurt)
        if npc.aggressive and npc.hp < 3:
            bar_w = 20
            bar_h = 3
            bar_x = sx - bar_w // 2
            bar_y = sy - size // 2 - 20
            # Background (dark)
            pygame.draw.rect(surface, (40, 0, 0), (bar_x, bar_y, bar_w, bar_h))
            # Health fill (red to green based on HP)
            fill_w = int(bar_w * (npc.hp / 3.0))
            if npc.hp >= 2:
                bar_color = (80, 200, 80)
            elif npc.hp >= 1:
                bar_color = (220, 180, 40)
            else:
                bar_color = (220, 40, 40)
            if fill_w > 0:
                pygame.draw.rect(surface, bar_color, (bar_x, bar_y, fill_w, bar_h))

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

# Health system!
# The burrb has hit points. Aggressive NPCs can attack you
# and take away your health. If you run out, you respawn
# back at the spawn square.
MAX_HP = 5
player_hp = MAX_HP
hurt_timer = 0  # frames of red flash when you get hit
hurt_cooldown = 0  # invincibility frames after getting hit (so you don't die instantly)
HURT_COOLDOWN_TIME = 60  # 1 second of invincibility after each hit
death_timer = 0  # frames of the "you died" animation (0 = alive)

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
# hits an NPC, it hurts them! Hit them 3 times to knock them out.
tongue_active = False  # is the tongue currently shooting out?
tongue_length = 0.0  # how far the tongue has extended so far
tongue_max_length = 120.0  # max reach of the tongue
tongue_speed = 8.0  # how fast the tongue extends per frame
tongue_retracting = False  # is the tongue pulling back in?
tongue_angle = 0.0  # direction the tongue is going (radians)
tongue_hit_npc = None  # did we hit someone? (for visual feedback)

# Chip collecting!
# Every building has a bag of chips. Steal them all!
chips_collected = 2

# Biome currencies! Each biome has its own special collectible.
# You spend these to buy biome-specific abilities in the shop.
berries_collected = 0  # Forest biome - nature powers
gems_collected = 0  # Desert biome - power moves
snowflakes_collected = 0  # Snow biome - ice powers
mushrooms_collected = 0  # Swamp biome - spooky powers

# Jump scare from closets!
# When you open a closet and get unlucky, a scary birb jumps out!
jumpscare_timer = 0  # frames remaining for jump scare (0 = not active)
jumpscare_frame = 0  # animation frame counter for the scare
JUMPSCARE_DURATION = 150  # 2.5 seconds at 60fps - longer = scarier!
scare_level = 0  # goes up each time you get jump scared - each one gets WORSE
closet_msg_timer = 0  # frames to show "found chips!" message
collect_msg_timer = 0  # frames to show "collected!" message for biome items
collect_msg_text = ""  # what text to show when you pick something up

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

# ============================================================
# BIOME ABILITIES!
# ============================================================
# Each biome has 3 special abilities bought with that biome's currency.
# They're organized by biome: forest (berries), desert (gems),
# snow (snowflakes), swamp (mushrooms).
#
# Format: (name, cost, key_hint, description, currency)

BIOME_ABILITIES = [
    # --- Forest abilities (berries) ---
    ("Vine Trap", 3, "V", "Trap nearby burrbs in vines!", "berry"),
    ("Camouflage", 4, "C", "Blend into the ground!", "berry"),
    ("Nature Heal", 5, "H", "Push enemies away!", "berry"),
    # --- Desert abilities (gems) ---
    ("Sandstorm", 4, "N", "Blind all nearby burrbs!", "gem"),
    ("Magnet", 3, "M", "Pull collectibles toward you!", "gem"),
    ("Fire Dash", 5, "R", "Dash with a trail of fire!", "gem"),
    # --- Snow abilities (snowflakes) ---
    ("Ice Wall", 3, "L", "Create a wall of ice!", "snowflake"),
    ("Blizzard", 5, "Z", "Freeze AND push burrbs!", "snowflake"),
    ("Snow Cloak", 4, "X", "Roll fast as a snowball!", "snowflake"),
    # --- Swamp abilities (mushrooms) ---
    ("Poison Cloud", 3, "P", "Leave a toxic cloud!", "mushroom"),
    ("Shadow Step", 4, "J", "Teleport to nearest shadow!", "mushroom"),
    ("Swamp Monster", 6, "K", "Summon a monster ally!", "mushroom"),
]

biome_ability_unlocked = [False] * len(BIOME_ABILITIES)

# Biome ability timers
vine_trap_timer = 0  # frames remaining for vine trap
vine_trap_cooldown = 0  # cooldown before next use
VINE_TRAP_DURATION = 240  # 4 seconds
VINE_TRAP_RADIUS = 200  # how far the vines reach

camouflage_timer = 0  # frames remaining for camouflage
CAMOUFLAGE_DURATION = 300  # 5 seconds

nature_heal_timer = 0  # frames remaining for heal push
nature_heal_cooldown = 0
NATURE_HEAL_RADIUS = 250

sandstorm_timer = 0  # frames remaining for sandstorm
sandstorm_cooldown = 0
SANDSTORM_DURATION = 240  # 4 seconds
SANDSTORM_RADIUS = 300

magnet_timer = 0  # frames remaining for magnet pull
magnet_cooldown = 0
MAGNET_DURATION = 300  # 5 seconds
MAGNET_RADIUS = 400  # how far it pulls from

fire_dash_active = 0  # frames remaining in fire dash
fire_dash_cooldown = 0
fire_trail = []  # list of (x, y, timer) for fire particles

ice_wall_cooldown = 0
ice_walls = []  # list of (x, y, timer) for ice wall segments

blizzard_timer = 0  # frames remaining for blizzard
blizzard_cooldown = 0
BLIZZARD_DURATION = 180  # 3 seconds
BLIZZARD_RADIUS = 250

snow_cloak_timer = 0  # frames remaining as snowball
snow_cloak_cooldown = 0
SNOW_CLOAK_DURATION = 300  # 5 seconds

poison_clouds = []  # list of [x, y, timer] for poison clouds
poison_cooldown = 0
POISON_CLOUD_DURATION = 360  # 6 seconds - lasts a while!
POISON_CLOUD_RADIUS = 60  # size of each cloud

shadow_step_cooldown = 0

swamp_monster_active = False  # is the monster ally alive?
swamp_monster_x = 0.0
swamp_monster_y = 0.0
swamp_monster_timer = 0  # frames remaining
swamp_monster_walk = 0  # animation frame
SWAMP_MONSTER_DURATION = 600  # 10 seconds!
SWAMP_MONSTER_SPEED = 2.0
SWAMP_MONSTER_RADIUS = 300  # how far it chases enemies

# ============================================================
# SODA CAN MONSTERS!
# ============================================================
# You start with this ability! Press 1 to spawn a pack of mini
# soda can monsters that chase down nearby burrbs and attack them.
# They're little angry soda cans with tiny legs that run around
# biting everything in sight. You get 3 of them at once!
soda_cans = []  # list of active soda can monsters (dicts)
SODA_CAN_DURATION = 480  # 8 seconds
SODA_CAN_SPEED = 2.8  # fast little guys!
SODA_CAN_RADIUS = 250  # how far they chase enemies
SODA_CAN_COOLDOWN_TIME = 300  # 5 second cooldown between spawns
soda_can_cooldown = 0  # frames until you can spawn more

# The shop now has tabs! LEFT/RIGHT arrows switch between tabs.
shop_tab = 0  # 0=chips, 1=berries, 2=gems, 3=snowflakes, 4=mushrooms

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
    ("UNSTUCK", _bx2, SCREEN_HEIGHT - _br * 3 - 20, _br, "unstuck"),
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


def get_shop_tab_info(tab):
    """Get the abilities list, currency count, currency name, and colors for a shop tab."""
    if tab == 0:
        return (
            ABILITIES,
            chips_collected,
            "chips",
            (255, 200, 50),
            (40, 30, 60),
            (100, 80, 160),
            ability_unlocked,
            list(range(len(ABILITIES))),
        )
    elif tab == 1:
        items = [(n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "berry"]
        indices = [
            i for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES) if cur == "berry"
        ]
        return (
            items,
            berries_collected,
            "berries",
            (255, 100, 120),
            (50, 25, 30),
            (180, 80, 100),
            biome_ability_unlocked,
            indices,
        )
    elif tab == 2:
        items = [(n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "gem"]
        indices = [
            i for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES) if cur == "gem"
        ]
        return (
            items,
            gems_collected,
            "gems",
            (100, 220, 255),
            (25, 40, 55),
            (80, 150, 200),
            biome_ability_unlocked,
            indices,
        )
    elif tab == 3:
        items = [
            (n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "snowflake"
        ]
        indices = [
            i
            for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES)
            if cur == "snowflake"
        ]
        return (
            items,
            snowflakes_collected,
            "snowflakes",
            (200, 220, 255),
            (30, 35, 55),
            (100, 130, 200),
            biome_ability_unlocked,
            indices,
        )
    else:
        items = [
            (n, c, k, d) for n, c, k, d, cur in BIOME_ABILITIES if cur == "mushroom"
        ]
        indices = [
            i
            for i, (_, _, _, _, cur) in enumerate(BIOME_ABILITIES)
            if cur == "mushroom"
        ]
        return (
            items,
            mushrooms_collected,
            "mushrooms",
            (100, 255, 150),
            (25, 45, 30),
            (80, 180, 100),
            biome_ability_unlocked,
            indices,
        )


def draw_shop(surface):
    """
    Draw the ability shop screen with tabs!
    LEFT/RIGHT arrows switch between biome currency tabs.
    Each tab shows abilities you can buy with that currency.
    """
    # Dark semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # Get info for current tab
    (
        tab_abilities,
        currency_count,
        currency_name,
        cur_color,
        bg_color,
        border_color,
        unlock_list,
        indices,
    ) = get_shop_tab_info(shop_tab)
    num_items = len(tab_abilities)

    # Shop box
    box_w = 520
    box_h = 130 + num_items * 52 + 40
    box_x = (SCREEN_WIDTH - box_w) // 2
    box_y = (SCREEN_HEIGHT - box_h) // 2

    # Background with border
    pygame.draw.rect(surface, bg_color, (box_x, box_y, box_w, box_h), border_radius=12)
    pygame.draw.rect(
        surface, border_color, (box_x, box_y, box_w, box_h), 3, border_radius=12
    )

    # Tab bar at the top
    tab_names = ["Chips", "Berries", "Gems", "Snowflakes", "Mushrooms"]
    tab_colors = [
        (255, 200, 50),  # chips gold
        (255, 100, 120),  # berries red
        (100, 220, 255),  # gems cyan
        (200, 220, 255),  # snowflakes blue-white
        (100, 255, 150),  # mushrooms green
    ]
    tab_w = box_w // 5
    for ti, tname in enumerate(tab_names):
        tx = box_x + ti * tab_w
        ty = box_y + 4
        tw = tab_w - 2
        th = 28
        if ti == shop_tab:
            pygame.draw.rect(
                surface, border_color, (tx + 1, ty, tw, th), border_radius=5
            )
            ttxt = font.render(tname, True, tab_colors[ti])
        else:
            ttxt = font.render(tname, True, (100, 100, 100))
        surface.blit(ttxt, (tx + tw // 2 - ttxt.get_width() // 2, ty + 5))

    # Title for current tab
    tab_titles = [
        "CHIP SHOP",
        "BERRY SHOP",
        "GEM SHOP",
        "SNOWFLAKE SHOP",
        "MUSHROOM SHOP",
    ]
    title = shop_title_font.render(tab_titles[shop_tab], True, cur_color)
    surface.blit(title, (box_x + box_w // 2 - title.get_width() // 2, box_y + 38))

    # Currency count
    cur_str = f"Your {currency_name}: {currency_count}"
    cur_txt = shop_font.render(cur_str, True, cur_color)
    surface.blit(cur_txt, (box_x + box_w // 2 - cur_txt.get_width() // 2, box_y + 78))

    # Abilities list
    for row_i, (name, cost, key_hint, desc) in enumerate(tab_abilities):
        row_y = box_y + 118 + row_i * 52
        # Figure out which unlock index to check
        if shop_tab == 0:
            unlocked = unlock_list[row_i]
        else:
            unlocked = unlock_list[indices[row_i]]

        # Highlight selected row
        if row_i == shop_cursor:
            pygame.draw.rect(
                surface,
                (bg_color[0] + 30, bg_color[1] + 30, bg_color[2] + 30),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                border_radius=6,
            )
            pygame.draw.rect(
                surface,
                border_color,
                (box_x + 10, row_y - 4, box_w - 20, 48),
                2,
                border_radius=6,
            )

        # Already unlocked?
        if unlocked:
            name_color = (100, 220, 100)  # green = owned
            status = "OWNED"
            status_color = (100, 220, 100)
        elif currency_count >= cost:
            name_color = (255, 255, 255)  # white = can buy
            status = f"{cost} {currency_name}"
            status_color = cur_color
        else:
            name_color = (120, 120, 120)  # gray = too expensive
            status = f"{cost} {currency_name}"
            status_color = (150, 80, 80)

        # Name
        name_txt = shop_font.render(name, True, name_color)
        surface.blit(name_txt, (box_x + 24, row_y))

        # Key hint
        if unlocked:
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
        "LEFT/RIGHT tab | UP/DOWN select | ENTER buy | TAB close", True, (180, 180, 200)
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
    global berries_collected, gems_collected, snowflakes_collected, mushrooms_collected
    global biome_ability_unlocked, shop_tab
    global vine_trap_timer, vine_trap_cooldown
    global camouflage_timer, nature_heal_timer, nature_heal_cooldown
    global sandstorm_timer, sandstorm_cooldown
    global magnet_timer, magnet_cooldown
    global fire_dash_active, fire_dash_cooldown, fire_trail
    global ice_wall_cooldown, ice_walls
    global blizzard_timer, blizzard_cooldown
    global snow_cloak_timer, snow_cloak_cooldown
    global poison_clouds, poison_cooldown
    global shadow_step_cooldown
    global swamp_monster_active, swamp_monster_x, swamp_monster_y
    global swamp_monster_timer, swamp_monster_walk
    global soda_cans, soda_can_cooldown
    global dash_cooldown, dash_active
    global freeze_timer, invisible_timer, giant_timer, giant_scale
    global bounce_timer, bounce_cooldown, bounce_height
    global teleport_cooldown, teleport_flash
    global earthquake_timer, earthquake_cooldown, earthquake_shake
    global jumpscare_timer, jumpscare_frame, closet_msg_timer, scare_level
    global collect_msg_timer, collect_msg_text
    global cam_x, cam_y
    global player_hp, hurt_timer, hurt_cooldown, death_timer
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
                    # Get current tab's ability list length
                    tab_abs, tab_cur, tab_name, _, _, _, tab_unlock, tab_indices = (
                        get_shop_tab_info(shop_tab)
                    )
                    tab_len = len(tab_abs)
                    if event.key == pygame.K_LEFT:
                        shop_tab = (shop_tab - 1) % 5
                        shop_cursor = 0
                    if event.key == pygame.K_RIGHT:
                        shop_tab = (shop_tab + 1) % 5
                        shop_cursor = 0
                    if event.key == pygame.K_UP:
                        shop_cursor = (shop_cursor - 1) % tab_len
                    if event.key == pygame.K_DOWN:
                        shop_cursor = (shop_cursor + 1) % tab_len
                    if event.key == pygame.K_RETURN:
                        # Try to buy the selected ability!
                        if shop_tab == 0:
                            # Chip shop - original abilities
                            cost = ABILITIES[shop_cursor][1]
                            if (
                                not ability_unlocked[shop_cursor]
                                and chips_collected >= cost
                            ):
                                chips_collected -= cost
                                ability_unlocked[shop_cursor] = True
                        else:
                            # Biome shop - use the right currency
                            cost = tab_abs[shop_cursor][1]
                            real_idx = tab_indices[shop_cursor]
                            if not biome_ability_unlocked[real_idx] and tab_cur >= cost:
                                # Deduct from the right currency
                                if shop_tab == 1:
                                    berries_collected -= cost
                                elif shop_tab == 2:
                                    gems_collected -= cost
                                elif shop_tab == 3:
                                    snowflakes_collected -= cost
                                elif shop_tab == 4:
                                    mushrooms_collected -= cost
                                biome_ability_unlocked[real_idx] = True
                    # Skip all other game input when shop is open
                    continue

                # Press U to unstuck! Teleports you to a random clear spot.
                if event.key == pygame.K_u:
                    if inside_building is not None:
                        # If stuck inside a building, just exit it
                        burrb_x = saved_outdoor_x
                        burrb_y = saved_outdoor_y
                        burrb_angle = saved_outdoor_angle
                        inside_building = None
                        touch_move_target = None
                    else:
                        # Find a random spot with no buildings under it
                        for _try in range(200):
                            rx = random.randint(100, WORLD_WIDTH - 100)
                            ry = random.randint(100, WORLD_HEIGHT - 100)
                            test_rect = pygame.Rect(rx - 15, ry - 15, 30, 30)
                            blocked = any(
                                test_rect.colliderect(b.get_rect()) for b in buildings
                            )
                            if not blocked:
                                burrb_x = float(rx)
                                burrb_y = float(ry)
                                touch_move_target = None
                                break

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
                            # Try to pick up a biome collectible!
                            for coll in biome_collectibles:
                                if coll[3]:  # already collected
                                    continue
                                cdx = burrb_x - coll[0]
                                cdy = burrb_y - coll[1]
                                cdist = math.sqrt(cdx * cdx + cdy * cdy)
                                if cdist < 30:  # close enough to grab!
                                    coll[3] = True  # mark as collected
                                    # Each item adds to its own currency!
                                    if coll[2] == "berry":
                                        berries_collected += 1
                                        collect_msg_text = "Found a berry! +1 berry"
                                    elif coll[2] == "gem":
                                        gems_collected += 1
                                        collect_msg_text = "Found a gem! +1 gem"
                                    elif coll[2] == "snowflake":
                                        snowflakes_collected += 1
                                        collect_msg_text = (
                                            "Caught a snowflake! +1 snowflake"
                                        )
                                    elif coll[2] == "glow_mushroom":
                                        mushrooms_collected += 1
                                        collect_msg_text = (
                                            "Picked a glowing mushroom! +1 mushroom"
                                        )
                                    collect_msg_timer = 90  # show for 1.5 seconds
                                    break  # only pick up one at a time
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

                # === BIOME ABILITIES ===

                # Press V for VINE TRAP! (Forest - index 0)
                if event.key == pygame.K_v:
                    if (
                        biome_ability_unlocked[0]
                        and vine_trap_timer <= 0
                        and vine_trap_cooldown <= 0
                    ):
                        if inside_building is None:
                            vine_trap_timer = VINE_TRAP_DURATION
                            vine_trap_cooldown = 300  # 5 sec cooldown
                            # Trap all NPCs in range!
                            for npc in npcs:
                                if npc.npc_type == "rock":
                                    continue
                                vd = math.sqrt(
                                    (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                                )
                                if vd < VINE_TRAP_RADIUS:
                                    npc.speed = 0.0
                                    npc.dir_timer = VINE_TRAP_DURATION

                # Press C for CAMOUFLAGE! (Forest - index 1)
                if event.key == pygame.K_c:
                    if biome_ability_unlocked[1] and camouflage_timer <= 0:
                        camouflage_timer = CAMOUFLAGE_DURATION

                # Press H for NATURE HEAL! (Forest - index 2)
                if event.key == pygame.K_h:
                    if (
                        biome_ability_unlocked[2]
                        and nature_heal_timer <= 0
                        and nature_heal_cooldown <= 0
                    ):
                        if inside_building is None:
                            nature_heal_timer = 30  # brief push effect
                            nature_heal_cooldown = 300
                            # Push all nearby NPCs away hard!
                            for npc in npcs:
                                if npc.npc_type == "rock":
                                    continue
                                hd = math.sqrt(
                                    (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                                )
                                if hd < NATURE_HEAL_RADIUS and hd > 1:
                                    push_str = 40
                                    npc.x += ((npc.x - burrb_x) / hd) * push_str
                                    npc.y += ((npc.y - burrb_y) / hd) * push_str

                # Press N for SANDSTORM! (Desert - index 3)
                if event.key == pygame.K_n:
                    if (
                        biome_ability_unlocked[3]
                        and sandstorm_timer <= 0
                        and sandstorm_cooldown <= 0
                    ):
                        if inside_building is None:
                            sandstorm_timer = SANDSTORM_DURATION
                            sandstorm_cooldown = 360
                            # Slow + confuse all NPCs in range
                            for npc in npcs:
                                if npc.npc_type == "rock":
                                    continue
                                sd = math.sqrt(
                                    (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                                )
                                if sd < SANDSTORM_RADIUS:
                                    npc.speed = 0.3
                                    npc.dir_timer = SANDSTORM_DURATION

                # Press M for MAGNET! (Desert - index 4)
                if event.key == pygame.K_m:
                    if (
                        biome_ability_unlocked[4]
                        and magnet_timer <= 0
                        and magnet_cooldown <= 0
                    ):
                        magnet_timer = MAGNET_DURATION
                        magnet_cooldown = 360

                # Press R for FIRE DASH! (Desert - index 5)
                if event.key == pygame.K_r:
                    if (
                        biome_ability_unlocked[5]
                        and fire_dash_active <= 0
                        and fire_dash_cooldown <= 0
                    ):
                        if inside_building is None:
                            fire_dash_active = 20  # quick burst
                            fire_dash_cooldown = 90

                # Press L for ICE WALL! (Snow - index 6)
                if event.key == pygame.K_l:
                    if biome_ability_unlocked[6] and ice_wall_cooldown <= 0:
                        if inside_building is None:
                            ice_wall_cooldown = 180  # 3 sec cooldown
                            # Place ice wall segments perpendicular to facing direction
                            perp = burrb_angle + math.pi / 2
                            wall_dist = 40  # how far in front
                            cx = burrb_x + math.cos(burrb_angle) * wall_dist
                            cy = burrb_y + math.sin(burrb_angle) * wall_dist
                            for seg in range(-2, 3):
                                wx = cx + math.cos(perp) * seg * 25
                                wy = cy + math.sin(perp) * seg * 25
                                ice_walls.append([wx, wy, 480])  # lasts 8 seconds

                # Press Z for BLIZZARD! (Snow - index 7)
                if event.key == pygame.K_z:
                    if (
                        biome_ability_unlocked[7]
                        and blizzard_timer <= 0
                        and blizzard_cooldown <= 0
                    ):
                        if inside_building is None:
                            blizzard_timer = BLIZZARD_DURATION
                            blizzard_cooldown = 360
                            # Freeze AND push all NPCs in range
                            for npc in npcs:
                                if npc.npc_type == "rock":
                                    continue
                                bd = math.sqrt(
                                    (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                                )
                                if bd < BLIZZARD_RADIUS:
                                    npc.speed = 0.0
                                    npc.dir_timer = BLIZZARD_DURATION
                                    if bd > 1:
                                        npc.x += ((npc.x - burrb_x) / bd) * 25
                                        npc.y += ((npc.y - burrb_y) / bd) * 25

                # Press X for SNOW CLOAK! (Snow - index 8)
                if event.key == pygame.K_x:
                    if (
                        biome_ability_unlocked[8]
                        and snow_cloak_timer <= 0
                        and snow_cloak_cooldown <= 0
                    ):
                        snow_cloak_timer = SNOW_CLOAK_DURATION
                        snow_cloak_cooldown = 360

                # Press P for POISON CLOUD! (Swamp - index 9)
                if event.key == pygame.K_p:
                    if biome_ability_unlocked[9] and poison_cooldown <= 0:
                        if inside_building is None:
                            poison_cooldown = 240
                            poison_clouds.append(
                                [burrb_x, burrb_y, POISON_CLOUD_DURATION]
                            )

                # Press J for SHADOW STEP! (Swamp - index 10)
                if event.key == pygame.K_j:
                    if biome_ability_unlocked[10] and shadow_step_cooldown <= 0:
                        if inside_building is None:
                            shadow_step_cooldown = 120  # 2 sec cooldown
                            # Find nearest tree or dead_tree or building to teleport to
                            best_dist = 999999
                            best_x, best_y = burrb_x, burrb_y
                            # Check biome objects (trees, dead trees, etc.)
                            for ox, oy, okind, osize in biome_objects:
                                if okind in ("dead_tree", "snow_tree", "cactus"):
                                    sd = math.sqrt(
                                        (ox - burrb_x) ** 2 + (oy - burrb_y) ** 2
                                    )
                                    if 50 < sd < 500 and sd < best_dist:
                                        best_dist = sd
                                        best_x = ox + 20
                                        best_y = oy + 20
                            for tx, ty, tsize in trees:
                                sd = math.sqrt(
                                    (tx - burrb_x) ** 2 + (ty - burrb_y) ** 2
                                )
                                if 50 < sd < 500 and sd < best_dist:
                                    best_dist = sd
                                    best_x = tx + 20
                                    best_y = ty + 20
                            if best_dist < 999999:
                                burrb_x = best_x
                                burrb_y = best_y
                                teleport_flash = 15  # reuse the flash effect

                # Press 1 for SODA CAN MONSTERS! (free ability - no purchase needed!)
                if event.key == pygame.K_1:
                    if len(soda_cans) == 0 and soda_can_cooldown <= 0:
                        if inside_building is None:
                            # Spawn 3 mini soda cans around the player!
                            for i in range(3):
                                angle = i * (2 * math.pi / 3)  # spread evenly
                                sx = burrb_x + math.cos(angle) * 25
                                sy = burrb_y + math.sin(angle) * 25
                                soda_cans.append(
                                    {
                                        "x": sx,
                                        "y": sy,
                                        "timer": SODA_CAN_DURATION,
                                        "walk": 0,
                                        "attack_cd": 0,
                                    }
                                )
                            soda_can_cooldown = SODA_CAN_COOLDOWN_TIME

                # Press K for SWAMP MONSTER! (Swamp - index 11)
                if event.key == pygame.K_k:
                    if biome_ability_unlocked[11] and not swamp_monster_active:
                        if inside_building is None:
                            swamp_monster_active = True
                            swamp_monster_x = burrb_x + 30
                            swamp_monster_y = burrb_y + 30
                            swamp_monster_timer = SWAMP_MONSTER_DURATION
                            swamp_monster_walk = 0

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
                            elif btn == "unstuck":
                                fake_event = pygame.event.Event(
                                    pygame.KEYDOWN, key=pygame.K_u
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
                        elif btn == "unstuck":
                            pygame.event.post(
                                pygame.event.Event(pygame.KEYDOWN, key=pygame.K_u)
                            )
                touch_held = False
                touch_btn_pressed = None

        # Handle touch input for the shop (tap abilities to select/buy)
        if shop_open and touch_active and touch_held:
            tx, ty = touch_pos
            tab_abs, tab_cur, tab_name, _, _, _, tab_unlock, tab_indices = (
                get_shop_tab_info(shop_tab)
            )
            num_items = len(tab_abs)
            box_w = 520
            box_h = 130 + num_items * 52 + 40
            box_x = (SCREEN_WIDTH - box_w) // 2
            box_y = (SCREEN_HEIGHT - box_h) // 2
            # Check if tap is on a tab
            tab_w = box_w // 5
            if box_y + 4 <= ty <= box_y + 32:
                for ti in range(5):
                    ttx = box_x + ti * tab_w
                    if ttx <= tx <= ttx + tab_w:
                        shop_tab = ti
                        shop_cursor = 0
                        touch_held = False
                        break
            # Check if tap is on an ability row
            elif box_x <= tx <= box_x + box_w:
                for i in range(num_items):
                    row_y = box_y + 118 + i * 52
                    if row_y - 4 <= ty <= row_y + 48:
                        if shop_cursor == i:
                            # Already selected - try to buy!
                            if shop_tab == 0:
                                cost = ABILITIES[i][1]
                                if not ability_unlocked[i] and chips_collected >= cost:
                                    chips_collected -= cost
                                    ability_unlocked[i] = True
                            else:
                                cost = tab_abs[i][1]
                                real_idx = tab_indices[i]
                                if (
                                    not biome_ability_unlocked[real_idx]
                                    and tab_cur >= cost
                                ):
                                    if shop_tab == 1:
                                        berries_collected -= cost
                                    elif shop_tab == 2:
                                        gems_collected -= cost
                                    elif shop_tab == 3:
                                        snowflakes_collected -= cost
                                    elif shop_tab == 4:
                                        mushrooms_collected -= cost
                                    biome_ability_unlocked[real_idx] = True
                        else:
                            shop_cursor = i
                        touch_held = False
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
        if collect_msg_timer > 0:
            collect_msg_timer -= 1
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

        # --- BIOME ABILITY TIMERS ---
        if vine_trap_timer > 0:
            vine_trap_timer -= 1
            # When vine trap ends, unstun NPCs
            if vine_trap_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if vine_trap_cooldown > 0:
            vine_trap_cooldown -= 1
        if camouflage_timer > 0:
            camouflage_timer -= 1
        if nature_heal_timer > 0:
            nature_heal_timer -= 1
        if nature_heal_cooldown > 0:
            nature_heal_cooldown -= 1
        if sandstorm_timer > 0:
            sandstorm_timer -= 1
            if sandstorm_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed < 0.5:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if sandstorm_cooldown > 0:
            sandstorm_cooldown -= 1
        if magnet_timer > 0:
            magnet_timer -= 1
            # Pull uncollected items toward the burrb!
            if inside_building is None:
                for coll in biome_collectibles:
                    if coll[3]:
                        continue
                    mdx = burrb_x - coll[0]
                    mdy = burrb_y - coll[1]
                    mdist = math.sqrt(mdx * mdx + mdy * mdy)
                    if mdist < MAGNET_RADIUS and mdist > 5:
                        pull_speed = 3.0
                        coll[0] += (mdx / mdist) * pull_speed
                        coll[1] += (mdy / mdist) * pull_speed
        if magnet_cooldown > 0:
            magnet_cooldown -= 1
        if fire_dash_active > 0:
            fire_dash_active -= 1
            # Drop fire particles behind the burrb
            if inside_building is None:
                fire_trail.append([burrb_x, burrb_y, 60])  # lasts 1 second
        if fire_dash_cooldown > 0:
            fire_dash_cooldown -= 1
        # Update fire trail
        for ft in fire_trail:
            ft[2] -= 1
        fire_trail = [ft for ft in fire_trail if ft[2] > 0]
        # Fire damages NPCs that walk through it!
        for ft in fire_trail:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                fd = math.sqrt((npc.x - ft[0]) ** 2 + (npc.y - ft[1]) ** 2)
                if fd < 15 and fd > 1:
                    # Push NPC away from fire
                    npc.x += ((npc.x - ft[0]) / fd) * 5
                    npc.y += ((npc.y - ft[1]) / fd) * 5
        # Update ice walls
        for iw in ice_walls:
            iw[2] -= 1
        ice_walls = [iw for iw in ice_walls if iw[2] > 0]
        if ice_wall_cooldown > 0:
            ice_wall_cooldown -= 1
        # Ice walls block NPCs
        for iw in ice_walls:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                wd = math.sqrt((npc.x - iw[0]) ** 2 + (npc.y - iw[1]) ** 2)
                if wd < 20 and wd > 1:
                    # Push NPC away from wall
                    npc.x += ((npc.x - iw[0]) / wd) * 3
                    npc.y += ((npc.y - iw[1]) / wd) * 3
        if blizzard_timer > 0:
            blizzard_timer -= 1
            if blizzard_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if blizzard_cooldown > 0:
            blizzard_cooldown -= 1
        if snow_cloak_timer > 0:
            snow_cloak_timer -= 1
        if snow_cloak_cooldown > 0:
            snow_cloak_cooldown -= 1
        # Update poison clouds
        for pc in poison_clouds:
            pc[2] -= 1
            # Push NPCs away from poison
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                pd = math.sqrt((npc.x - pc[0]) ** 2 + (npc.y - pc[1]) ** 2)
                if pd < POISON_CLOUD_RADIUS and pd > 1:
                    npc.x += ((npc.x - pc[0]) / pd) * 2
                    npc.y += ((npc.y - pc[1]) / pd) * 2
        poison_clouds = [pc for pc in poison_clouds if pc[2] > 0]
        if poison_cooldown > 0:
            poison_cooldown -= 1
        if shadow_step_cooldown > 0:
            shadow_step_cooldown -= 1
        # Swamp monster AI
        if swamp_monster_active:
            swamp_monster_timer -= 1
            swamp_monster_walk += 1
            if swamp_monster_timer <= 0:
                swamp_monster_active = False
            else:
                # Find nearest NPC and chase it
                nearest_npc = None
                nearest_dist = SWAMP_MONSTER_RADIUS
                for npc in npcs:
                    if npc.npc_type == "rock":
                        continue
                    md = math.sqrt(
                        (npc.x - swamp_monster_x) ** 2 + (npc.y - swamp_monster_y) ** 2
                    )
                    if md < nearest_dist:
                        nearest_dist = md
                        nearest_npc = npc
                if nearest_npc is not None:
                    md = nearest_dist
                    if md > 1:
                        swamp_monster_x += (
                            (nearest_npc.x - swamp_monster_x) / md
                        ) * SWAMP_MONSTER_SPEED
                        swamp_monster_y += (
                            (nearest_npc.y - swamp_monster_y) / md
                        ) * SWAMP_MONSTER_SPEED
                    # Push NPC away on contact
                    if md < 20 and md > 1:
                        nearest_npc.x += ((nearest_npc.x - swamp_monster_x) / md) * 8
                        nearest_npc.y += ((nearest_npc.y - swamp_monster_y) / md) * 8
                else:
                    # No NPC nearby, follow the burrb
                    fd = math.sqrt(
                        (burrb_x - swamp_monster_x) ** 2
                        + (burrb_y - swamp_monster_y) ** 2
                    )
                    if fd > 50 and fd > 1:
                        swamp_monster_x += (
                            (burrb_x - swamp_monster_x) / fd
                        ) * SWAMP_MONSTER_SPEED
                        swamp_monster_y += (
                            (burrb_y - swamp_monster_y) / fd
                        ) * SWAMP_MONSTER_SPEED

        # Soda can monster AI!
        if soda_can_cooldown > 0:
            soda_can_cooldown -= 1
        for can in soda_cans:
            can["timer"] -= 1
            can["walk"] += 1
            if can["attack_cd"] > 0:
                can["attack_cd"] -= 1
        # Remove expired soda cans
        soda_cans = [c for c in soda_cans if c["timer"] > 0]
        # Each soda can chases the nearest NPC and bites it!
        for can in soda_cans:
            nearest_npc = None
            nearest_dist = SODA_CAN_RADIUS
            for npc in npcs:
                if npc.npc_type == "rock" or not npc.alive:
                    continue
                md = math.sqrt((npc.x - can["x"]) ** 2 + (npc.y - can["y"]) ** 2)
                if md < nearest_dist:
                    nearest_dist = md
                    nearest_npc = npc
            if nearest_npc is not None:
                md = nearest_dist
                if md > 1:
                    can["x"] += ((nearest_npc.x - can["x"]) / md) * SODA_CAN_SPEED
                    can["y"] += ((nearest_npc.y - can["y"]) / md) * SODA_CAN_SPEED
                # Bite NPC on contact! Deal damage!
                if md < 14 and can["attack_cd"] <= 0:
                    nearest_npc.hp -= 1
                    nearest_npc.hurt_flash = 15
                    can["attack_cd"] = 30  # bite cooldown
                    # Knock them back
                    if md > 1:
                        nearest_npc.x += ((nearest_npc.x - can["x"]) / md) * 10
                        nearest_npc.y += ((nearest_npc.y - can["y"]) / md) * 10
                        nearest_npc.x = max(30, min(WORLD_WIDTH - 30, nearest_npc.x))
                        nearest_npc.y = max(30, min(WORLD_HEIGHT - 30, nearest_npc.y))
                    if nearest_npc.hp <= 0:
                        nearest_npc.alive = False
            else:
                # No NPC nearby, follow the burrb
                fd = math.sqrt((burrb_x - can["x"]) ** 2 + (burrb_y - can["y"]) ** 2)
                if fd > 40 and fd > 1:
                    can["x"] += ((burrb_x - can["x"]) / fd) * SODA_CAN_SPEED
                    can["y"] += ((burrb_y - can["y"]) / fd) * SODA_CAN_SPEED

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
        # Fire Dash: even faster than regular dash with fire!
        if fire_dash_active > 0:
            speed_mult = max(speed_mult, 5.0)
        # Snow Cloak: rolling snowball is fast!
        if snow_cloak_timer > 0:
            speed_mult = max(speed_mult, 3.0)
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
            if invisible_timer > 0 or camouflage_timer > 0:
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
            and camouflage_timer <= 0
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
                npc.update(burrb_x, burrb_y, buildings)
        # (When frozen, NPCs just stand perfectly still - like statues!)

        # --- NPC ATTACKS ---
        # Aggressive burrbs that are close enough will peck you!
        # You take 1 damage and get knocked back. There's a short
        # invincibility window so you can escape.
        if hurt_cooldown > 0:
            hurt_cooldown -= 1
        if hurt_timer > 0:
            hurt_timer -= 1

        if inside_building is None and death_timer <= 0:
            for npc in npcs:
                if not npc.aggressive or npc.npc_type == "rock" or not npc.alive:
                    continue
                if npc.attack_cooldown > 0:
                    continue
                adx = burrb_x - npc.x
                ady = burrb_y - npc.y
                adist = math.sqrt(adx * adx + ady * ady)
                if adist < 18:  # close enough to attack!
                    if hurt_cooldown <= 0:
                        # OUCH! You got pecked!
                        player_hp -= 1
                        hurt_timer = 20  # red flash for 20 frames
                        hurt_cooldown = HURT_COOLDOWN_TIME
                        npc.attack_cooldown = 40
                        # Knock the player back!
                        if adist > 1:
                            burrb_x += (adx / adist) * 15
                            burrb_y += (ady / adist) * 15
                            # Keep in world bounds
                            burrb_x = max(20, min(WORLD_WIDTH - 20, burrb_x))
                            burrb_y = max(20, min(WORLD_HEIGHT - 20, burrb_y))

        # --- DEATH AND RESPAWN ---
        # If HP hits 0, play a short death animation then respawn
        # at the spawn square with full health!
        if player_hp <= 0 and death_timer <= 0:
            death_timer = 120  # 2 seconds of death animation
            player_hp = 0
        if death_timer > 0:
            death_timer -= 1
            if death_timer <= 0:
                # Respawn!
                player_hp = MAX_HP
                burrb_x = float(SPAWN_X)
                burrb_y = float(SPAWN_Y)
                hurt_cooldown = 120  # extra invincibility after respawning
                hurt_timer = 0

        # --- UPDATE CARS ---
        # Cars drive along roads every frame
        if inside_building is None:
            for car in cars:
                car.update()

        # --- UPDATE TONGUE ---
        # The tongue extends outward, checks if it hits any NPC,
        # then retracts back. If it hits an NPC, it hurts them!
        # Hit them 3 times to knock them out.
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
                    if npc.npc_type == "rock" or not npc.alive:
                        continue  # skip rocks and dead NPCs
                    ddx = npc.x - tip_x
                    ddy = npc.y - tip_y
                    hit_dist = math.sqrt(ddx * ddx + ddy * ddy)
                    if hit_dist < 16:  # close enough = hit!
                        # OUCH! Hurt the NPC!
                        npc.hp -= 1
                        npc.hurt_flash = 15  # red flash
                        tongue_hit_npc = npc
                        tongue_retracting = True  # tongue snaps back
                        # Knock them back away from the player!
                        if hit_dist > 1:
                            npc.x += (ddx / hit_dist) * 20
                            npc.y += (ddy / hit_dist) * 20
                            npc.x = max(30, min(WORLD_WIDTH - 30, npc.x))
                            npc.y = max(30, min(WORLD_HEIGHT - 30, npc.y))
                        if npc.hp <= 0:
                            # Knocked out! They disappear.
                            npc.alive = False
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

            # Draw the spawn square (a nice clear area where you start!)
            sp_sx = SPAWN_RECT.x - cam_x
            sp_sy = SPAWN_RECT.y - cam_y
            # Only draw if on screen
            if (
                sp_sx + SPAWN_SIZE > 0
                and sp_sx < SCREEN_WIDTH
                and sp_sy + SPAWN_SIZE > 0
                and sp_sy < SCREEN_HEIGHT
            ):
                # Light green floor so it stands out as a safe zone
                pygame.draw.rect(
                    screen,
                    (140, 200, 120),
                    (sp_sx, sp_sy, SPAWN_SIZE, SPAWN_SIZE),
                    border_radius=8,
                )
                # Border around it
                pygame.draw.rect(
                    screen,
                    (100, 160, 80),
                    (sp_sx, sp_sy, SPAWN_SIZE, SPAWN_SIZE),
                    3,
                    border_radius=8,
                )
                # Little "HOME" label in the center
                home_font = pygame.font.Font(None, 22)
                home_text = home_font.render("HOME", True, (80, 130, 60))
                screen.blit(
                    home_text,
                    (
                        sp_sx + SPAWN_SIZE // 2 - home_text.get_width() // 2,
                        sp_sy + SPAWN_SIZE // 2 - home_text.get_height() // 2,
                    ),
                )

            # Draw biome objects that are behind the burrb
            for ox, oy, okind, osize in biome_objects:
                if oy < burrb_y:
                    draw_biome_object(screen, ox, oy, okind, osize, cam_x, cam_y)

            # Draw biome collectibles behind the burrb (not yet collected)
            for coll in biome_collectibles:
                if not coll[3] and coll[1] < burrb_y:
                    draw_biome_collectible(
                        screen, coll[0], coll[1], coll[2], cam_x, cam_y
                    )

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

            # --- BIOME ABILITY VISUAL EFFECTS ---

            # Vine Trap: green vine circles around trapped NPCs
            if vine_trap_timer > 0:
                vt_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                vt_alpha = min(150, vine_trap_timer * 3)
                for npc in npcs:
                    if npc.npc_type == "rock":
                        continue
                    if npc.speed == 0.0:
                        nsx = int(npc.x - cam_x)
                        nsy = int(npc.y - cam_y)
                        if (
                            -30 < nsx < SCREEN_WIDTH + 30
                            and -30 < nsy < SCREEN_HEIGHT + 30
                        ):
                            pygame.draw.circle(
                                vt_surf, (30, 180, 30, vt_alpha), (nsx, nsy), 14, 3
                            )
                            pygame.draw.circle(
                                vt_surf, (60, 220, 60, vt_alpha // 2), (nsx, nsy), 18, 2
                            )
                screen.blit(vt_surf, (0, 0))

            # Camouflage: green tint on the burrb (handled in burrb drawing)
            # (We'll draw a leaf pattern overlay on the burrb area)
            if camouflage_timer > 0:
                camo_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
                camo_alpha = min(140, camouflage_timer * 3)
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y + bounce_y_offset)
                t_val = pygame.time.get_ticks() * 0.003
                for li in range(5):
                    lx = 15 + int(math.sin(t_val + li * 1.2) * 8)
                    ly = 15 + int(math.cos(t_val + li * 0.9) * 8)
                    pygame.draw.circle(
                        camo_surf, (40, 160, 40, camo_alpha), (lx, ly), 5
                    )
                screen.blit(camo_surf, (bsx - 15, bsy - 15))

            # Nature Heal: expanding green ring
            if nature_heal_timer > 0:
                nh_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                nh_r = int((30 - nature_heal_timer) * 10)
                nh_alpha = int(180 * (nature_heal_timer / 30))
                pygame.draw.circle(
                    nh_surf,
                    (80, 255, 80, nh_alpha),
                    (int(burrb_x - cam_x), int(burrb_y - cam_y)),
                    nh_r,
                    4,
                )
                screen.blit(nh_surf, (0, 0))

            # Sandstorm: swirling sand particles
            if sandstorm_timer > 0:
                ss_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                ss_alpha = min(80, sandstorm_timer)
                ss_surf.fill((220, 190, 120, ss_alpha // 3))
                t_val = pygame.time.get_ticks() * 0.001
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y)
                for si in range(20):
                    sa = t_val * 3 + si * 0.3
                    sr = 40 + si * 12
                    sx_p = bsx + int(math.cos(sa) * sr)
                    sy_p = bsy + int(math.sin(sa) * sr)
                    pygame.draw.circle(
                        ss_surf, (200, 170, 100, ss_alpha), (sx_p, sy_p), 3
                    )
                screen.blit(ss_surf, (0, 0))

            # Magnet: blue pull lines toward burrb
            if magnet_timer > 0:
                mg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                mg_alpha = min(120, magnet_timer * 2)
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y)
                for coll in biome_collectibles:
                    if coll[3]:
                        continue
                    mdist = math.sqrt(
                        (burrb_x - coll[0]) ** 2 + (burrb_y - coll[1]) ** 2
                    )
                    if mdist < MAGNET_RADIUS:
                        cx = int(coll[0] - cam_x)
                        cy = int(coll[1] - cam_y)
                        pygame.draw.line(
                            mg_surf, (100, 150, 255, mg_alpha), (bsx, bsy), (cx, cy), 1
                        )
                screen.blit(mg_surf, (0, 0))

            # Fire trail: orange/red flames on the ground
            for ft in fire_trail:
                ftx = int(ft[0] - cam_x)
                fty = int(ft[1] - cam_y)
                if -20 < ftx < SCREEN_WIDTH + 20 and -20 < fty < SCREEN_HEIGHT + 20:
                    ft_alpha = min(200, ft[2] * 5)
                    ft_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
                    pygame.draw.circle(ft_surf, (255, 100, 20, ft_alpha), (10, 10), 8)
                    pygame.draw.circle(
                        ft_surf, (255, 200, 50, ft_alpha // 2), (10, 8), 5
                    )
                    screen.blit(ft_surf, (ftx - 10, fty - 10))

            # Fire dash trail (on the burrb)
            if fire_dash_active > 0:
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y)
                for ti in range(3):
                    to = (ti + 1) * 8
                    ta = 160 - ti * 50
                    tx_p = bsx - int(math.cos(burrb_angle) * to)
                    ty_p = bsy - int(math.sin(burrb_angle) * to)
                    t_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
                    pygame.draw.rect(
                        t_surf, (255, 120, 30, ta), (0, 0, 16, 16), border_radius=4
                    )
                    screen.blit(t_surf, (tx_p - 8, ty_p - 8))

            # Ice walls: blue-white blocks
            for iw in ice_walls:
                iwx = int(iw[0] - cam_x)
                iwy = int(iw[1] - cam_y)
                if -30 < iwx < SCREEN_WIDTH + 30 and -30 < iwy < SCREEN_HEIGHT + 30:
                    iw_alpha = min(200, iw[2])
                    iw_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
                    pygame.draw.rect(
                        iw_surf,
                        (150, 200, 255, iw_alpha),
                        (0, 0, 22, 22),
                        border_radius=4,
                    )
                    pygame.draw.rect(
                        iw_surf,
                        (200, 230, 255, iw_alpha),
                        (3, 3, 16, 16),
                        border_radius=3,
                    )
                    pygame.draw.rect(
                        iw_surf,
                        (100, 160, 220, iw_alpha),
                        (0, 0, 22, 22),
                        2,
                        border_radius=4,
                    )
                    screen.blit(iw_surf, (iwx - 11, iwy - 11))

            # Blizzard: swirling snow + blue overlay
            if blizzard_timer > 0:
                bz_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
                bz_alpha = min(60, blizzard_timer)
                bz_surf.fill((180, 200, 255, bz_alpha // 3))
                t_val = pygame.time.get_ticks() * 0.002
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y)
                for si in range(15):
                    sa = t_val * 4 + si * 0.4
                    sr = 30 + si * 14
                    sx_p = bsx + int(math.cos(sa) * sr)
                    sy_p = bsy + int(math.sin(sa) * sr)
                    pygame.draw.circle(
                        bz_surf, (230, 240, 255, bz_alpha * 2), (sx_p, sy_p), 3
                    )
                screen.blit(bz_surf, (0, 0))

            # Snow Cloak: draw a snowball instead of the burrb
            # (The burrb drawing handles this by checking snow_cloak_timer)
            if snow_cloak_timer > 0:
                sc_surf = pygame.Surface((40, 40), pygame.SRCALPHA)
                sc_roll = pygame.time.get_ticks() * 0.01
                bsx = int(burrb_x - cam_x)
                bsy = int(burrb_y - cam_y + bounce_y_offset)
                pygame.draw.circle(screen, (230, 235, 245), (bsx, bsy), 12)
                pygame.draw.circle(screen, (210, 220, 235), (bsx, bsy), 12, 2)
                # Rolling detail lines
                for ri in range(3):
                    ra = sc_roll + ri * 2.1
                    rx = bsx + int(math.cos(ra) * 6)
                    ry = bsy + int(math.sin(ra) * 6)
                    pygame.draw.circle(screen, (200, 210, 225), (rx, ry), 2)

            # Poison clouds: green toxic clouds
            for pc in poison_clouds:
                pcx = int(pc[0] - cam_x)
                pcy = int(pc[1] - cam_y)
                if -80 < pcx < SCREEN_WIDTH + 80 and -80 < pcy < SCREEN_HEIGHT + 80:
                    pc_alpha = min(120, pc[2] // 2)
                    pc_surf = pygame.Surface(
                        (POISON_CLOUD_RADIUS * 2 + 20, POISON_CLOUD_RADIUS * 2 + 20),
                        pygame.SRCALPHA,
                    )
                    cx = POISON_CLOUD_RADIUS + 10
                    cy = POISON_CLOUD_RADIUS + 10
                    t_val = pygame.time.get_ticks() * 0.002
                    # Multiple overlapping circles for cloud effect
                    for ci in range(5):
                        ca = t_val + ci * 1.3
                        cr = POISON_CLOUD_RADIUS // 2 + int(math.sin(ca) * 10)
                        cox = cx + int(math.cos(ca * 0.7) * 15)
                        coy = cy + int(math.sin(ca * 0.5) * 15)
                        pygame.draw.circle(
                            pc_surf, (40, 180, 40, pc_alpha), (cox, coy), cr
                        )
                    screen.blit(
                        pc_surf,
                        (
                            pcx - POISON_CLOUD_RADIUS - 10,
                            pcy - POISON_CLOUD_RADIUS - 10,
                        ),
                    )

            # Swamp Monster ally
            if swamp_monster_active and inside_building is None:
                smx = int(swamp_monster_x - cam_x)
                smy = int(swamp_monster_y - cam_y)
                if -40 < smx < SCREEN_WIDTH + 40 and -40 < smy < SCREEN_HEIGHT + 40:
                    # Dark green body
                    pygame.draw.ellipse(
                        screen, (30, 100, 40), (smx - 12, smy - 8, 24, 16)
                    )
                    # Eyes (red and glowing)
                    pygame.draw.circle(screen, (255, 50, 50), (smx - 5, smy - 6), 3)
                    pygame.draw.circle(screen, (255, 50, 50), (smx + 5, smy - 6), 3)
                    pygame.draw.circle(screen, (255, 150, 150), (smx - 5, smy - 6), 1)
                    pygame.draw.circle(screen, (255, 150, 150), (smx + 5, smy - 6), 1)
                    # 4 legs
                    leg_off = math.sin(swamp_monster_walk * 0.3) * 3
                    pygame.draw.line(
                        screen,
                        (20, 80, 30),
                        (smx - 8, smy + 4),
                        (smx - 12, smy + 10 + leg_off),
                        2,
                    )
                    pygame.draw.line(
                        screen,
                        (20, 80, 30),
                        (smx + 8, smy + 4),
                        (smx + 12, smy + 10 - leg_off),
                        2,
                    )
                    pygame.draw.line(
                        screen,
                        (20, 80, 30),
                        (smx - 4, smy + 6),
                        (smx - 6, smy + 12 - leg_off),
                        2,
                    )
                    pygame.draw.line(
                        screen,
                        (20, 80, 30),
                        (smx + 4, smy + 6),
                        (smx + 6, smy + 12 + leg_off),
                        2,
                    )

            # Soda Can Monsters!
            if len(soda_cans) > 0 and inside_building is None:
                for can in soda_cans:
                    cx = int(can["x"] - cam_x)
                    cy = int(can["y"] - cam_y)
                    if (
                        cx < -30
                        or cx > SCREEN_WIDTH + 30
                        or cy < -30
                        or cy > SCREEN_HEIGHT + 30
                    ):
                        continue
                    wf = can["walk"]
                    leg_off = math.sin(wf * 0.4) * 2

                    # Tiny legs (2 on each side, animated!)
                    pygame.draw.line(
                        screen,
                        (60, 60, 60),
                        (cx - 4, cy + 7),
                        (cx - 6, cy + 11 + leg_off),
                        2,
                    )
                    pygame.draw.line(
                        screen,
                        (60, 60, 60),
                        (cx + 4, cy + 7),
                        (cx + 6, cy + 11 - leg_off),
                        2,
                    )

                    # Soda can body (red cylinder shape)
                    pygame.draw.rect(
                        screen, (200, 30, 30), (cx - 5, cy - 8, 10, 16), border_radius=3
                    )
                    # Silver top and bottom (like a real can)
                    pygame.draw.rect(
                        screen,
                        (180, 180, 190),
                        (cx - 5, cy - 8, 10, 3),
                        border_radius=2,
                    )
                    pygame.draw.rect(
                        screen,
                        (180, 180, 190),
                        (cx - 5, cy + 5, 10, 3),
                        border_radius=2,
                    )
                    # White label stripe
                    pygame.draw.rect(screen, (240, 240, 240), (cx - 4, cy - 2, 8, 4))
                    # Outline
                    pygame.draw.rect(
                        screen,
                        (120, 15, 15),
                        (cx - 5, cy - 8, 10, 16),
                        1,
                        border_radius=3,
                    )

                    # Angry face on the can!
                    # Eyes (little white dots with black pupils)
                    pygame.draw.circle(screen, (255, 255, 255), (cx - 2, cy - 4), 2)
                    pygame.draw.circle(screen, (255, 255, 255), (cx + 2, cy - 4), 2)
                    pygame.draw.circle(screen, (0, 0, 0), (cx - 2, cy - 4), 1)
                    pygame.draw.circle(screen, (0, 0, 0), (cx + 2, cy - 4), 1)
                    # Angry eyebrows
                    pygame.draw.line(
                        screen, (0, 0, 0), (cx - 4, cy - 7), (cx - 1, cy - 6), 1
                    )
                    pygame.draw.line(
                        screen, (0, 0, 0), (cx + 4, cy - 7), (cx + 1, cy - 6), 1
                    )
                    # Grumpy mouth
                    pygame.draw.line(
                        screen, (0, 0, 0), (cx - 2, cy + 2), (cx + 2, cy + 2), 1
                    )

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

            # Draw biome collectibles in front of the burrb
            for coll in biome_collectibles:
                if not coll[3] and coll[1] >= burrb_y:
                    draw_biome_collectible(
                        screen, coll[0], coll[1], coll[2], cam_x, cam_y
                    )

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
                "WASD walk | O tongue | 1 soda cans | E enter | TAB shop | ESC quit"
            )

        screen.blit(mode_shadow, (12, 42))
        screen.blit(mode_text, (10, 40))

        # Health bar! Shows your HP as little hearts.
        hp_x = 10
        hp_y = 62
        hp_label = font.render("HP:", True, (255, 100, 100))
        hp_shadow = font.render("HP:", True, BLACK)
        screen.blit(hp_shadow, (hp_x + 1, hp_y + 1))
        screen.blit(hp_label, (hp_x, hp_y))
        for i in range(MAX_HP):
            heart_x = hp_x + 32 + i * 18
            heart_y = hp_y + 3
            if i < player_hp:
                # Full heart (red)
                pygame.draw.circle(screen, (220, 40, 40), (heart_x - 3, heart_y), 5)
                pygame.draw.circle(screen, (220, 40, 40), (heart_x + 3, heart_y), 5)
                pygame.draw.polygon(
                    screen,
                    (220, 40, 40),
                    [
                        (heart_x - 7, heart_y + 1),
                        (heart_x, heart_y + 9),
                        (heart_x + 7, heart_y + 1),
                    ],
                )
                # Shine
                pygame.draw.circle(
                    screen, (255, 120, 120), (heart_x - 3, heart_y - 1), 2
                )
            else:
                # Empty heart (dark outline)
                pygame.draw.circle(screen, (80, 30, 30), (heart_x - 3, heart_y), 5, 1)
                pygame.draw.circle(screen, (80, 30, 30), (heart_x + 3, heart_y), 5, 1)
                pygame.draw.polygon(
                    screen,
                    (80, 30, 30),
                    [
                        (heart_x - 7, heart_y + 1),
                        (heart_x, heart_y + 9),
                        (heart_x + 7, heart_y + 1),
                    ],
                    1,
                )

        # Hurt flash! Screen edges flash red when you take damage.
        if hurt_timer > 0:
            flash_alpha = int(150 * (hurt_timer / 20.0))
            flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            # Red vignette around the edges
            for edge in range(20):
                a = max(0, flash_alpha - edge * 8)
                if a <= 0:
                    break
                pygame.draw.rect(
                    flash_surf,
                    (255, 0, 0, a),
                    (edge, edge, SCREEN_WIDTH - edge * 2, SCREEN_HEIGHT - edge * 2),
                    3,
                )
            screen.blit(flash_surf, (0, 0))

        # Death screen! Fades to black and shows "You Died" text.
        if death_timer > 0:
            fade_alpha = int(200 * (1.0 - death_timer / 120.0))
            death_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
            death_surf.fill((0, 0, 0, min(200, fade_alpha)))
            screen.blit(death_surf, (0, 0))
            if death_timer < 90:
                death_font = pygame.font.Font(None, 64)
                dt_text = death_font.render("You Died!", True, (220, 40, 40))
                dt_shadow = death_font.render("You Died!", True, BLACK)
                dtx = SCREEN_WIDTH // 2 - dt_text.get_width() // 2
                dty = SCREEN_HEIGHT // 2 - dt_text.get_height() // 2
                screen.blit(dt_shadow, (dtx + 2, dty + 2))
                screen.blit(dt_text, (dtx, dty))
                # Respawn hint
                if death_timer < 60:
                    hint_text = font.render(
                        "Respawning at HOME...", True, (180, 180, 180)
                    )
                    hx = SCREEN_WIDTH // 2 - hint_text.get_width() // 2
                    screen.blit(hint_text, (hx, dty + 50))

        # Currency counters! Show all collected currencies in the top-right.
        currency_y = 10
        currencies_to_show = [
            ("Chips", chips_collected, (255, 200, 50)),
            ("Berries", berries_collected, (255, 100, 120)),
            ("Gems", gems_collected, (100, 220, 255)),
            ("Snowflakes", snowflakes_collected, (200, 220, 255)),
            ("Mushrooms", mushrooms_collected, (100, 255, 150)),
        ]
        for cur_name, cur_count, cur_color in currencies_to_show:
            if cur_count > 0:
                cur_str = f"{cur_name}: {cur_count}"
                cur_text = font.render(cur_str, True, cur_color)
                cur_shadow = font.render(cur_str, True, BLACK)
                cur_x = SCREEN_WIDTH - cur_text.get_width() - 12
                screen.blit(cur_shadow, (cur_x + 1, currency_y + 1))
                screen.blit(cur_text, (cur_x, currency_y))
                currency_y += 18

        # Active ability indicators (shown on the right side below currencies)
        ability_y = currency_y + 4
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
        # Biome ability timers
        if vine_trap_timer > 0:
            active_abilities.append(
                ("VINES", (30, 200, 30), vine_trap_timer, VINE_TRAP_DURATION)
            )
        if camouflage_timer > 0:
            active_abilities.append(
                ("CAMO", (40, 160, 40), camouflage_timer, CAMOUFLAGE_DURATION)
            )
        if sandstorm_timer > 0:
            active_abilities.append(
                ("STORM", (220, 190, 120), sandstorm_timer, SANDSTORM_DURATION)
            )
        if magnet_timer > 0:
            active_abilities.append(
                ("MAGNET", (100, 150, 255), magnet_timer, MAGNET_DURATION)
            )
        if fire_dash_active > 0:
            active_abilities.append(("FIRE!", (255, 120, 30), fire_dash_active, 20))
        if blizzard_timer > 0:
            active_abilities.append(
                ("BLIZZARD", (180, 200, 255), blizzard_timer, BLIZZARD_DURATION)
            )
        if snow_cloak_timer > 0:
            active_abilities.append(
                ("SNOWBALL", (230, 235, 245), snow_cloak_timer, SNOW_CLOAK_DURATION)
            )
        if swamp_monster_active:
            active_abilities.append(
                ("MONSTER", (30, 100, 40), swamp_monster_timer, SWAMP_MONSTER_DURATION)
            )
        if len(soda_cans) > 0:
            # Show the timer of the soda can with the most time left
            max_timer = max(c["timer"] for c in soda_cans)
            active_abilities.append(
                (
                    "SODA x" + str(len(soda_cans)),
                    (200, 30, 30),
                    max_timer,
                    SODA_CAN_DURATION,
                )
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
        if biome_ability_unlocked[4]:  # Magnet (passive-ish, press to use)
            passive_badges.append(("MAG", (100, 150, 255)))

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
            else:
                # Check if near a biome collectible - show pickup prompt!
                for coll in biome_collectibles:
                    if coll[3]:  # already collected
                        continue
                    cdx = burrb_x - coll[0]
                    cdy = burrb_y - coll[1]
                    cdist = math.sqrt(cdx * cdx + cdy * cdy)
                    if cdist < 30:
                        # Show the right prompt color for each item type
                        prompt_colors = {
                            "berry": (255, 100, 100),
                            "gem": (100, 220, 255),
                            "snowflake": (200, 220, 255),
                            "glow_mushroom": (100, 255, 150),
                        }
                        prompt_names = {
                            "berry": "Press E to pick berries!",
                            "gem": "Press E to grab gem!",
                            "snowflake": "Press E to catch snowflake!",
                            "glow_mushroom": "Press E to pick mushroom!",
                        }
                        pc = prompt_colors.get(coll[2], YELLOW)
                        pt = prompt_names.get(coll[2], "Press E to collect!")
                        prompt = font.render(pt, True, pc)
                        prompt_shadow = font.render(pt, True, BLACK)
                        px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
                        screen.blit(
                            prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101)
                        )
                        screen.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))
                        break

        # "Collected!" message when you pick up a biome item
        if collect_msg_timer > 0:
            msg_alpha = min(255, collect_msg_timer * 6)  # fades out
            msg_color = (100, 255, 100)
            msg = font.render(collect_msg_text, True, msg_color)
            msg_shadow = font.render(collect_msg_text, True, BLACK)
            mx = SCREEN_WIDTH // 2 - msg.get_width() // 2
            # Float upward as it fades
            my = SCREEN_HEIGHT // 2 + 70 - (90 - collect_msg_timer) // 3
            screen.blit(msg_shadow, (mx + 1, my + 1))
            screen.blit(msg, (mx, my))

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
