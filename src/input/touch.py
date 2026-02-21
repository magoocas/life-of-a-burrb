"""
Touch / on-screen button support.

Holds touch state, button layout, hit-testing, and drawing helpers.
The TouchState object is owned by game.py and passed around as needed.
"""

import math

import pygame

from src.constants import WHITE
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT


# ============================================================
# BUTTON LAYOUT
# ============================================================

TOUCH_BTN_RADIUS = 28
TOUCH_BTN_PAD = 8
_br = TOUCH_BTN_RADIUS
_bx = SCREEN_WIDTH - _br - 12  # right edge
_bx2 = _bx - _br * 2 - TOUCH_BTN_PAD  # second column from right

# Each entry: (label, center_x, center_y, radius, key_action)
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


# ============================================================
# TOUCH STATE
# ============================================================


class TouchState:
    """All touch/mouse input state bundled together."""

    def __init__(self):
        self.touch_active = False  # has the player used touch? (shows buttons)
        self.touch_move_target = None  # (x, y) world position to walk toward, or None
        self.touch_held = False  # is a finger currently touching the screen?
        self.touch_pos = (0, 0)  # current touch position on screen
        self.touch_start_pos = (0, 0)  # where the finger first touched
        self.touch_finger_id = None  # track which finger is the main one
        self.touch_btn_pressed = None  # which button is currently being pressed


# ============================================================
# HIT TESTING
# ============================================================


def touch_hit_button(tx, ty, ability_unlocked):
    """Check if a touch at (tx, ty) hits any on-screen button.

    Args:
        tx, ty: touch position in screen coordinates
        ability_unlocked: list of booleans from AbilityManager

    Returns:
        The action string, or None if no button was hit.
    """
    for label, bx, by, br, action in TOUCH_BUTTONS:
        dx = tx - bx
        dy = ty - by
        if dx * dx + dy * dy <= (br + 8) * (br + 8):
            return action

    # Ability buttons only shown if the ability is unlocked
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            dx = tx - bx
            dy = ty - by
            if dx * dx + dy * dy <= (br + 8) * (br + 8):
                return action

    return None


# ============================================================
# DRAWING
# ============================================================


def draw_touch_buttons(
    surface,
    touch_state,
    ability_unlocked,
    inside_building,
    interior_x,
    interior_y,
    cam_x,
    cam_y,
):
    """Draw the on-screen touch buttons and the move-target indicator.

    Args:
        surface: pygame Surface to draw onto
        touch_state: TouchState instance
        ability_unlocked: list of booleans from AbilityManager
        inside_building: the current Building if indoors, else None
        interior_x, interior_y: player interior coordinates
        cam_x, cam_y: current camera offset
    """
    btn_font = pygame.font.Font(None, 24)

    # --- Standard buttons ---
    for label, bx, by, br, action in TOUCH_BUTTONS:
        btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
        pressed = touch_state.touch_btn_pressed == action
        if pressed:
            pygame.draw.circle(btn_surf, (255, 255, 255, 160), (br + 1, br + 1), br)
        else:
            pygame.draw.circle(btn_surf, (255, 255, 255, 70), (br + 1, br + 1), br)
        pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
        surface.blit(btn_surf, (bx - br - 1, by - br - 1))
        txt = btn_font.render(label, True, WHITE)
        surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # --- Ability buttons (only if unlocked) ---
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
            pressed = touch_state.touch_btn_pressed == action
            colors = [
                (100, 180, 255, 100),
                (180, 100, 255, 100),
                (100, 255, 100, 100),
            ]
            bg_color = colors[i] if i < len(colors) else (255, 255, 255, 70)
            if pressed:
                bg_color = (bg_color[0], bg_color[1], bg_color[2], 200)
            pygame.draw.circle(btn_surf, bg_color, (br + 1, br + 1), br)
            pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
            surface.blit(btn_surf, (bx - br - 1, by - br - 1))
            txt = btn_font.render(label, True, WHITE)
            surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # --- Move target indicator ---
    if touch_state.touch_move_target is not None:
        tgt_x, tgt_y = touch_state.touch_move_target
        if inside_building is not None:
            # Interior coords → screen coords
            icam_x = interior_x - SCREEN_WIDTH // 2
            icam_y = interior_y - SCREEN_HEIGHT // 2
            sx = int(tgt_x - icam_x)
            sy = int(tgt_y - icam_y)
        else:
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
# EVENT HANDLING
# ============================================================


def handle_touch_event(
    event,
    touch_state,
    ability_unlocked,
    inside_building,
    interior_x,
    interior_y,
    cam_x,
    cam_y,
    shop_open,
):
    """Process a single pygame touch/mouse event and update TouchState.

    Returns a list of (pygame.KEYDOWN, key) tuples for actions that should
    be simulated as keyboard events, or an empty list.

    Args:
        event: the pygame event
        touch_state: TouchState instance (mutated in place)
        ability_unlocked: ability unlock list from AbilityManager
        inside_building: current Building or None
        interior_x, interior_y: interior player coords
        cam_x, cam_y: camera offset
        shop_open: whether the shop is open

    Returns:
        list of pygame.K_* key constants to simulate as KEYDOWN events
    """
    simulated_keys = []

    if event.type == pygame.FINGERDOWN:
        touch_state.touch_active = True
        tx = int(event.x * SCREEN_WIDTH)
        ty = int(event.y * SCREEN_HEIGHT)
        touch_state.touch_held = True
        touch_state.touch_pos = (tx, ty)
        touch_state.touch_start_pos = (tx, ty)
        touch_state.touch_finger_id = event.finger_id

        btn = touch_hit_button(tx, ty, ability_unlocked)
        if btn is not None:
            touch_state.touch_btn_pressed = btn
        else:
            touch_state.touch_btn_pressed = None
            if not shop_open:
                if inside_building is not None:
                    icam_x = interior_x - SCREEN_WIDTH // 2
                    icam_y = interior_y - SCREEN_HEIGHT // 2
                    touch_state.touch_move_target = (tx + icam_x, ty + icam_y)
                else:
                    touch_state.touch_move_target = (tx + cam_x, ty + cam_y)

    elif event.type == pygame.FINGERMOTION:
        if event.finger_id == touch_state.touch_finger_id:
            tx = int(event.x * SCREEN_WIDTH)
            ty = int(event.y * SCREEN_HEIGHT)
            touch_state.touch_pos = (tx, ty)

    elif event.type == pygame.FINGERUP:
        if event.finger_id == touch_state.touch_finger_id:
            tx = int(event.x * SCREEN_WIDTH)
            ty = int(event.y * SCREEN_HEIGHT)

            if touch_state.touch_btn_pressed is not None:
                btn = touch_hit_button(tx, ty, ability_unlocked)
                if btn == touch_state.touch_btn_pressed:
                    key = _action_to_key(btn)
                    if key is not None:
                        simulated_keys.append(key)

            touch_state.touch_held = False
            touch_state.touch_btn_pressed = None
            touch_state.touch_finger_id = None

    elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
        touch_state.touch_active = True
        tx, ty = event.pos
        touch_state.touch_held = True
        touch_state.touch_pos = (tx, ty)
        touch_state.touch_start_pos = (tx, ty)

        btn = touch_hit_button(tx, ty, ability_unlocked)
        if btn is not None:
            touch_state.touch_btn_pressed = btn
        else:
            touch_state.touch_btn_pressed = None
            if not shop_open:
                if inside_building is not None:
                    icam_x = interior_x - SCREEN_WIDTH // 2
                    icam_y = interior_y - SCREEN_HEIGHT // 2
                    touch_state.touch_move_target = (tx + icam_x, ty + icam_y)
                else:
                    touch_state.touch_move_target = (tx + cam_x, ty + cam_y)

    elif event.type == pygame.MOUSEMOTION and touch_state.touch_held:
        touch_state.touch_pos = event.pos

    elif event.type == pygame.MOUSEBUTTONUP and event.button == 1:
        tx, ty = event.pos
        if touch_state.touch_btn_pressed is not None:
            btn = touch_hit_button(tx, ty, ability_unlocked)
            if btn == touch_state.touch_btn_pressed:
                key = _action_to_key(btn)
                if key is not None:
                    simulated_keys.append(key)
        touch_state.touch_held = False
        touch_state.touch_btn_pressed = None

    return simulated_keys


def _action_to_key(action):
    """Map a button action string to a pygame key constant."""
    mapping = {
        "action_e": pygame.K_e,
        "action_o": pygame.K_o,
        "toggle_shop": pygame.K_TAB,
        "ability_f": pygame.K_f,
        "ability_i": pygame.K_i,
        "ability_g": pygame.K_g,
        "ability_b": pygame.K_b,
        "ability_t": pygame.K_t,
        "ability_q": pygame.K_q,
        "unstuck": pygame.K_u,
    }
    return mapping.get(action)
