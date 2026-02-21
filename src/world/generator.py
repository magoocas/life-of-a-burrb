"""
World generator for Life of a Burrb.
All random.seed(42) world generation lives here.
Returns a WorldData dataclass with everything the game needs.
"""

import random
import pygame

from src.constants import (
    BLOCK_SIZE,
    ROAD_WIDTH,
    SIDEWALK_WIDTH,
    WORLD_WIDTH,
    WORLD_HEIGHT,
)
from src.biomes import CITY_X1, CITY_Y1, CITY_X2, CITY_Y2
from src.entities.building import Building
from src.entities.npc import NPC, spawn_npcs
from src.entities.car import Car, spawn_cars
from src.settings import SPAWN_RECT


# Building color palettes (Super Mario 3D World style - bright candy colors!)
BUILDING_COLORS = [
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


class WorldData:
    """All the generated world data. Created once at startup."""

    def __init__(self):
        self.buildings = []
        self.trees = []
        self.parks = []
        self.biome_objects = []  # list of (x, y, kind, size)
        self.biome_collectibles = []  # list of [x, y, kind, collected]
        self.npcs = []
        self.cars = []


def generate_world() -> WorldData:
    """
    Generate the entire game world using random.seed(42).
    Returns a WorldData instance with all objects placed.
    """
    world = WorldData()

    random.seed(42)  # Same world every time you play

    # --------------------------------------------------------
    # BUILDINGS - city blocks in a grid pattern
    # --------------------------------------------------------
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
                for b in world.buildings:
                    if new_rect.colliderect(b.get_rect()):
                        overlap = True
                        break
                if not overlap:
                    color, roof_color = random.choice(BUILDING_COLORS)
                    world.buildings.append(Building(px, py, bw, bh, color, roof_color))

            # Fewer trees in the city (more urban)
            for _ in range(random.randint(0, 1)):
                margin = SIDEWALK_WIDTH + 8
                tx = random.randint(bx + margin, bx + BLOCK_SIZE - margin)
                ty = random.randint(by + margin, by + BLOCK_SIZE - margin)
                # Don't place on buildings
                tree_rect = pygame.Rect(tx - 8, ty - 8, 16, 16)
                overlap = any(
                    tree_rect.colliderect(b.get_rect()) for b in world.buildings
                )
                if not overlap:
                    world.trees.append((tx, ty, random.randint(12, 22)))

    # --------------------------------------------------------
    # PARKS - a few open green areas (in the city)
    # --------------------------------------------------------
    for _ in range(5):
        px = random.randint(CITY_X1 + 200, CITY_X2 - 400)
        py = random.randint(CITY_Y1 + 200, CITY_Y2 - 400)
        pw = random.randint(120, 220)
        ph = random.randint(120, 220)
        world.parks.append(pygame.Rect(px, py, pw, ph))
        # Remove buildings that overlap with parks
        world.buildings = [
            b
            for b in world.buildings
            if not pygame.Rect(px - 10, py - 10, pw + 20, ph + 20).colliderect(
                b.get_rect()
            )
        ]
        # Add extra trees in parks
        for _ in range(8):
            tx = random.randint(px + 20, px + pw - 20)
            ty = random.randint(py + 20, py + ph - 20)
            world.trees.append((tx, ty, random.randint(14, 24)))

    # --------------------------------------------------------
    # BIOME DECORATIONS
    # --------------------------------------------------------
    # --- FOREST biome (top-left): lots of big trees, mushrooms, flowers ---
    for _ in range(300):
        fx = random.randint(100, WORLD_WIDTH // 2 - 100)
        fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
        if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
            continue
        world.trees.append((fx, fy, random.randint(16, 30)))

    for _ in range(60):
        fx = random.randint(100, WORLD_WIDTH // 2 - 100)
        fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
        if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((fx, fy, "mushroom", random.randint(6, 12)))

    for _ in range(40):
        fx = random.randint(100, WORLD_WIDTH // 2 - 100)
        fy = random.randint(100, WORLD_HEIGHT // 2 - 100)
        if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((fx, fy, "flower", random.randint(4, 8)))

    # --- SNOW biome (top-right): snowy trees, snowmen, ice patches ---
    for _ in range(200):
        sx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
        sy = random.randint(100, WORLD_HEIGHT // 2 - 100)
        if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((sx, sy, "snow_tree", random.randint(14, 26)))

    for _ in range(25):
        sx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
        sy = random.randint(200, WORLD_HEIGHT // 2 - 200)
        if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((sx, sy, "snowman", random.randint(10, 16)))

    for _ in range(40):
        sx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
        sy = random.randint(100, WORLD_HEIGHT // 2 - 100)
        if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((sx, sy, "ice_patch", random.randint(20, 50)))

    # --- SWAMP biome (bottom-left): dead trees, lily pads, puddles ---
    for _ in range(180):
        wx = random.randint(100, WORLD_WIDTH // 2 - 100)
        wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((wx, wy, "dead_tree", random.randint(12, 24)))

    for _ in range(80):
        wx = random.randint(100, WORLD_WIDTH // 2 - 100)
        wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((wx, wy, "lily_pad", random.randint(6, 14)))

    for _ in range(50):
        wx = random.randint(100, WORLD_WIDTH // 2 - 100)
        wy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((wx, wy, "puddle", random.randint(15, 40)))

    # --- DESERT biome (bottom-right): cacti, rocks, tumbleweeds ---
    for _ in range(120):
        dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
        dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((dx, dy, "cactus", random.randint(10, 22)))

    for _ in range(80):
        dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
        dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((dx, dy, "rock", random.randint(8, 18)))

    for _ in range(30):
        dx = random.randint(WORLD_WIDTH // 2 + 100, WORLD_WIDTH - 100)
        dy = random.randint(WORLD_HEIGHT // 2 + 100, WORLD_HEIGHT - 100)
        if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
            continue
        world.biome_objects.append((dx, dy, "tumbleweed", random.randint(6, 12)))

    # --------------------------------------------------------
    # BIOME COLLECTIBLES
    # --------------------------------------------------------
    # Forest: Berries (12 scattered around - rare!)
    for _ in range(12):
        fx = random.randint(200, WORLD_WIDTH // 2 - 200)
        fy = random.randint(200, WORLD_HEIGHT // 2 - 200)
        if CITY_X1 - 50 < fx < CITY_X2 + 50 and CITY_Y1 - 50 < fy < CITY_Y2 + 50:
            continue
        world.biome_collectibles.append([fx, fy, "berry", False])

    # Snow: Snowflakes (12 scattered around - rare!)
    for _ in range(12):
        sx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
        sy = random.randint(200, WORLD_HEIGHT // 2 - 200)
        if CITY_X1 - 50 < sx < CITY_X2 + 50 and CITY_Y1 - 50 < sy < CITY_Y2 + 50:
            continue
        world.biome_collectibles.append([sx, sy, "snowflake", False])

    # Swamp: Glowing Mushrooms (12 scattered around - rare!)
    for _ in range(12):
        wx = random.randint(200, WORLD_WIDTH // 2 - 200)
        wy = random.randint(WORLD_HEIGHT // 2 + 200, WORLD_HEIGHT - 200)
        if CITY_X1 - 50 < wx < CITY_X2 + 50 and CITY_Y1 - 50 < wy < CITY_Y2 + 50:
            continue
        world.biome_collectibles.append([wx, wy, "glow_mushroom", False])

    # Desert: Gems (12 scattered around - rare!)
    for _ in range(12):
        dx = random.randint(WORLD_WIDTH // 2 + 200, WORLD_WIDTH - 200)
        dy = random.randint(WORLD_HEIGHT // 2 + 200, WORLD_HEIGHT - 200)
        if CITY_X1 - 50 < dx < CITY_X2 + 50 and CITY_Y1 - 50 < dy < CITY_Y2 + 50:
            continue
        world.biome_collectibles.append([dx, dy, "gem", False])

    # --------------------------------------------------------
    # NPCs and CARS
    # --------------------------------------------------------
    world.npcs = spawn_npcs(world.buildings)
    world.cars = spawn_cars()

    # --------------------------------------------------------
    # SPAWN SQUARE CLEANUP
    # Remove ALL objects from the spawn square so the player
    # starts in a clear area with nothing in the way.
    # --------------------------------------------------------
    _sp = 10  # padding
    _spawn_padded = pygame.Rect(
        SPAWN_RECT.x - _sp,
        SPAWN_RECT.y - _sp,
        SPAWN_RECT.w + _sp * 2,
        SPAWN_RECT.h + _sp * 2,
    )

    world.buildings = [
        b for b in world.buildings if not _spawn_padded.colliderect(b.get_rect())
    ]
    world.trees = [
        (tx, ty, ts)
        for (tx, ty, ts) in world.trees
        if not _spawn_padded.collidepoint(tx, ty)
    ]
    world.biome_objects = [
        (ox, oy, ok, os)
        for (ox, oy, ok, os) in world.biome_objects
        if not _spawn_padded.collidepoint(ox, oy)
    ]
    world.biome_collectibles = [
        c
        for c in world.biome_collectibles
        if not _spawn_padded.collidepoint(c[0], c[1])
    ]
    world.npcs = [n for n in world.npcs if not _spawn_padded.collidepoint(n.x, n.y)]
    world.cars = [c for c in world.cars if not _spawn_padded.collidepoint(c.x, c.y)]
    world.parks = [p for p in world.parks if not _spawn_padded.colliderect(p)]

    return world
