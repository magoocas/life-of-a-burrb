"""
src/rendering/interior.py
Interior drawing: draw_interior_topdown.
Moved from game.py Phase 4.
"""

import math
import pygame

from src.constants import (
    BLACK,
    BROWN,
    YELLOW,
)
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.entities.building import Building
from src.rendering.entities import draw_burrb


def draw_interior_topdown(surface, bld, px, py, facing_left, walk_frame):
    """
    Draw the inside of a building in top-down mode!
    The interior fills the whole screen so it feels like
    you've gone inside.

    Parameters
    ----------
    surface    : pygame.Surface to draw on (the screen)
    bld        : Building object
    px, py     : player's interior position
    facing_left: player facing direction
    walk_frame : player walk animation frame
    """
    tile = bld.interior_tile
    total_w = bld.interior_w * tile
    total_h = bld.interior_h * tile

    # Camera offset to center on the player
    cam_x = px - SCREEN_WIDTH // 2
    cam_y = py - SCREEN_HEIGHT // 2

    # Background
    surface.fill((40, 35, 30))

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
    draw_burrb(surface, px, py, cam_x, cam_y, facing_left, walk_frame)
