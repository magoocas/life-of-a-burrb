"""
Collision detection system for Life of a Burrb.

Handles:
- World-space movement (can_move_to)
- Interior movement (can_move_interior)
- Door proximity detection (get_nearby_door_building, is_at_interior_door)
"""

import math
import pygame

from src.constants import WORLD_WIDTH, WORLD_HEIGHT
from src.entities.building import Building


def can_move_to(x, y, buildings):
    """Check if the burrb can move to position (x, y) in the world."""
    # World boundaries
    if x < 20 or x > WORLD_WIDTH - 20 or y < 20 or y > WORLD_HEIGHT - 20:
        return False
    # Building collision (use a small rect around the burrb's feet)
    burrb_rect = pygame.Rect(x - 10, y + 5, 20, 14)
    for b in buildings:
        if burrb_rect.colliderect(b.get_rect()):
            return False
    return True


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


def get_nearby_door_building(bx, by, buildings):
    """Check if the burrb is near any building's door (outside).
    Returns the building or None."""
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
