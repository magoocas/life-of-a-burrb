"""
src/rendering/world.py
World rendering: ground, roads, trees, biome objects, collectibles.
Moved from game.py Phase 4.
"""

import math
import pygame

from src.constants import (
    BROWN,
    GREEN,
    DARK_GREEN,
    SIDEWALK,
    ROAD_COLOR,
    ROAD_LINE,
    WORLD_WIDTH,
    WORLD_HEIGHT,
    BLOCK_SIZE,
    ROAD_WIDTH,
    SIDEWALK_WIDTH,
)
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.biomes import (
    CITY_X1,
    CITY_Y1,
    CITY_X2,
    CITY_Y2,
    BIOME_COLORS,
    get_biome,
)


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
