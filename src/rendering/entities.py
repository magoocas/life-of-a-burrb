"""
src/rendering/entities.py
Entity rendering: draw_burrb, draw_npc_topdown, draw_car_topdown.
Moved from game.py Phase 4.
"""

import math
import pygame

from src.constants import (
    WHITE,
    BLACK,
    BURRB_BLUE,
    BURRB_LIGHT_BLUE,
    BURRB_DARK_BLUE,
    BURRB_ORANGE,
    BURRB_EYE,
)
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


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
