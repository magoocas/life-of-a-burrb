"""
Camera system for Life of a Burrb.

Handles smooth camera following and earthquake screen shake.
"""

import random

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


def update_camera(cam_x, cam_y, burrb_x, burrb_y, earthquake_shake):
    """Smoothly follow the burrb and apply earthquake shake if active.

    Returns (new_cam_x, new_cam_y).
    """
    target_cam_x = burrb_x - SCREEN_WIDTH // 2
    target_cam_y = burrb_y - SCREEN_HEIGHT // 2
    cam_x += (target_cam_x - cam_x) * 0.08
    cam_y += (target_cam_y - cam_y) * 0.08
    # Earthquake screen shake!
    if earthquake_shake > 0:
        cam_x += random.randint(-6, 6)
        cam_y += random.randint(-6, 6)
    return cam_x, cam_y
