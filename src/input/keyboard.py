"""
Keyboard event handling.

handle_keydown() processes a single KEYDOWN event and returns a
KeyboardResult describing all the state changes that should be applied.
game.py applies those changes to its global state.
"""

import math
import random

import pygame

from src.constants import WORLD_WIDTH, WORLD_HEIGHT
from src.settings import SPAWN_X, SPAWN_Y
from src.systems.abilities import (
    ABILITIES,
    BIOME_ABILITIES,
    BOUNCE_DURATION,
    TELEPORT_DISTANCE,
    EARTHQUAKE_DURATION,
    EARTHQUAKE_RADIUS,
    VINE_TRAP_DURATION,
    VINE_TRAP_RADIUS,
    CAMOUFLAGE_DURATION,
    NATURE_HEAL_RADIUS,
    SANDSTORM_DURATION,
    SANDSTORM_RADIUS,
    MAGNET_DURATION,
    BLIZZARD_DURATION,
    BLIZZARD_RADIUS,
    SNOW_CLOAK_DURATION,
    POISON_CLOUD_DURATION,
    SWAMP_MONSTER_DURATION,
    SODA_CAN_DURATION,
    SODA_CAN_COOLDOWN_TIME,
)


# ============================================================
# RESULT DATACLASS (plain dict-based to avoid dataclass import overhead)
# ============================================================


class KeyboardResult:
    """Collects all state mutations requested by a single KEYDOWN event."""

    def __init__(self):
        # --- quit/shop ---
        self.quit = False
        self.close_shop = False
        self.toggle_shop = False

        # --- shop navigation (only if shop was open) ---
        self.shop_tab_delta = 0  # -1, +1 or 0
        self.shop_cursor_delta = 0  # -1, +1 or 0
        self.shop_buy = False  # RETURN pressed

        # --- unstuck ---
        self.unstuck = False

        # --- tongue ---
        self.shoot_tongue = False
        self.tongue_angle = 0.0

        # --- enter/exit building ---
        self.enter_building = False  # try to enter nearby building
        self.exit_building = False  # try to exit interior
        self.collect_item = False  # try to pick up biome collectible
        self.open_closet = False  # try to open closet
        self.steal_chips = False  # try to steal chip bag
        self.shake_bed = False  # try to shake bed

        # --- ability activations ---
        # Each flag means "activate this ability NOW if the conditions are met"
        self.activate_freeze = False
        self.activate_invisible = False
        self.activate_giant = False
        self.activate_bounce = False
        self.activate_teleport = False
        self.activate_earthquake = False
        self.activate_vine_trap = False
        self.activate_camouflage = False
        self.activate_nature_heal = False
        self.activate_sandstorm = False
        self.activate_magnet = False
        self.activate_fire_dash = False
        self.activate_ice_wall = False
        self.activate_blizzard = False
        self.activate_snow_cloak = False
        self.activate_poison_cloud = False
        self.activate_shadow_step = False
        self.activate_soda_cans = False
        self.activate_swamp_monster = False


def handle_keydown(
    event,
    shop_open,
    shop_tab,
    shop_cursor,
    abilities,
    chips_collected,
    berries_collected,
    gems_collected,
    snowflakes_collected,
    mushrooms_collected,
    inside_building,
    burrb_x,
    burrb_y,
    burrb_angle,
    facing_left,
    tongue_active,
    interior_x,
    interior_y,
    biome_collectibles,
    buildings,
    jumpscare_timer,
    biome_objects,
    trees,
    can_move_to_fn,
):
    """Process a pygame KEYDOWN event.

    Args:
        event: a pygame KEYDOWN event
        shop_open: bool — is the shop currently open?
        shop_tab: int — current shop tab (0-4)
        shop_cursor: int — current shop cursor row
        abilities: AbilityManager instance
        chips_collected: int
        berries_collected, gems_collected, snowflakes_collected, mushrooms_collected: int
        inside_building: Building or None
        burrb_x, burrb_y: player position
        burrb_angle: player angle (radians)
        facing_left: bool
        tongue_active: bool
        interior_x, interior_y: interior player position
        biome_collectibles: list of collectibles
        buildings: list of Building objects
        jumpscare_timer: int
        biome_objects: list of biome objects
        trees: list of (x, y, size) tuples
        can_move_to_fn: callable(x, y) -> bool for world collision

    Returns:
        KeyboardResult with all requested mutations.
    """
    from src.rendering.shop import get_shop_tab_info

    result = KeyboardResult()

    if event.key == pygame.K_ESCAPE:
        if shop_open:
            result.close_shop = True
        else:
            result.quit = True
        return result

    # TAB toggles shop
    if event.key == pygame.K_TAB:
        result.toggle_shop = True
        return result

    # --- SHOP NAVIGATION (only when shop is open) ---
    if shop_open:
        tab_abs, tab_cur, tab_name, _, _, _, tab_unlock, tab_indices = (
            get_shop_tab_info(
                shop_tab,
                ABILITIES,
                chips_collected,
                abilities.ability_unlocked,
                BIOME_ABILITIES,
                abilities.biome_ability_unlocked,
                berries_collected,
                gems_collected,
                snowflakes_collected,
                mushrooms_collected,
            )
        )
        if event.key == pygame.K_LEFT:
            result.shop_tab_delta = -1
        elif event.key == pygame.K_RIGHT:
            result.shop_tab_delta = 1
        elif event.key == pygame.K_UP:
            result.shop_cursor_delta = -1
        elif event.key == pygame.K_DOWN:
            result.shop_cursor_delta = 1
        elif event.key == pygame.K_RETURN:
            result.shop_buy = True
        # All other keys are ignored while shop is open
        return result

    # --- UNSTUCK ---
    if event.key == pygame.K_u:
        result.unstuck = True
        return result

    # --- TONGUE ---
    if event.key == pygame.K_o:
        if not tongue_active and inside_building is None:
            result.shoot_tongue = True
            result.tongue_angle = math.pi if facing_left else 0.0
        return result

    # --- ENTER / EXIT / INTERACT ---
    if event.key == pygame.K_e:
        if inside_building is None:
            result.enter_building = True
            result.collect_item = True  # also tries to collect nearby item
        else:
            result.open_closet = True
            result.steal_chips = True
            result.shake_bed = True
            result.exit_building = True
        return result

    # ============================================================
    # ABILITY KEYS
    # ============================================================

    if event.key == pygame.K_f:
        result.activate_freeze = True

    elif event.key == pygame.K_i:
        result.activate_invisible = True

    elif event.key == pygame.K_g:
        result.activate_giant = True

    elif event.key == pygame.K_b:
        result.activate_bounce = True

    elif event.key == pygame.K_t:
        result.activate_teleport = True

    elif event.key == pygame.K_q:
        result.activate_earthquake = True

    elif event.key == pygame.K_v:
        result.activate_vine_trap = True

    elif event.key == pygame.K_c:
        result.activate_camouflage = True

    elif event.key == pygame.K_h:
        result.activate_nature_heal = True

    elif event.key == pygame.K_n:
        result.activate_sandstorm = True

    elif event.key == pygame.K_m:
        result.activate_magnet = True

    elif event.key == pygame.K_r:
        result.activate_fire_dash = True

    elif event.key == pygame.K_l:
        result.activate_ice_wall = True

    elif event.key == pygame.K_z:
        result.activate_blizzard = True

    elif event.key == pygame.K_x:
        result.activate_snow_cloak = True

    elif event.key == pygame.K_p:
        result.activate_poison_cloud = True

    elif event.key == pygame.K_j:
        result.activate_shadow_step = True

    elif event.key == pygame.K_1:
        result.activate_soda_cans = True

    elif event.key == pygame.K_k:
        result.activate_swamp_monster = True

    return result
