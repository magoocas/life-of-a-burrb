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

# --- Refactored imports (Phase 3) ---
from src.world.generator import generate_world

# --- Refactored imports (Phase 4) ---
from src.rendering.world import (
    draw_road_grid,
    draw_tree,
    draw_biome_object,
    draw_biome_collectible,
    draw_biome_ground,
)
from src.rendering.entities import (
    draw_burrb,
    draw_npc_topdown,
    draw_car_topdown,
)
from src.rendering.interior import draw_interior_topdown
from src.rendering.effects import (
    draw_tongue,
    draw_teleport_flash,
    draw_earthquake_shockwave,
    draw_dash_trail,
    draw_freeze_overlay,
    draw_bounce_shadow,
    draw_vine_trap,
    draw_camouflage,
    draw_nature_heal,
    draw_sandstorm,
    draw_magnet,
    draw_fire_trail,
    draw_fire_dash_trail,
    draw_ice_walls,
    draw_blizzard,
    draw_snow_cloak,
    draw_poison_clouds,
    draw_swamp_monster,
    draw_soda_cans,
)
from src.rendering.ui import (
    draw_title_and_mode,
    draw_health,
    draw_hurt_flash,
    draw_death_screen,
    draw_currencies,
    draw_ability_bars,
    draw_help_text,
    draw_outdoor_prompts,
    draw_interior_prompts,
    draw_biome_label,
    draw_collect_message,
    draw_spawn_square,
)
from src.rendering.shop import draw_shop, get_shop_tab_info
from src.rendering.jumpscare import draw_jumpscare

# --- Refactored imports (Phase 5) ---
from src.systems.collision import (
    can_move_to as _collision_can_move_to,
    can_move_interior,
    get_nearby_door_building as _get_nearby_door_building,
    is_at_interior_door,
)
from src.systems.camera import update_camera
from src.systems.combat import (
    update_tongue as _update_tongue,
    update_npc_attacks,
    update_death_and_respawn,
)
from src.systems.abilities import AbilityManager
from src.systems.shop import try_buy_ability

# --- Refactored imports (Phase 6) ---
from src.input.touch import (
    TouchState,
    TOUCH_BUTTONS,
    TOUCH_ABILITY_BUTTONS,
    TOUCH_BTN_RADIUS,
    touch_hit_button as _touch_hit_button,
    draw_touch_buttons as _draw_touch_buttons,
    handle_touch_event,
)
from src.input.keyboard import handle_keydown, KeyboardResult

# Initialize pygame - this starts up the game engine
pygame.init()

# Screen setup
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Life of a Burrb")

# Clock controls how fast the game runs (frames per second)
clock = pygame.time.Clock()


# ============================================================
# WORLD GENERATION (Phase 3 refactor)
# ============================================================
# All world generation is in src/world/generator.py.
# generate_world() returns a WorldData object with all objects.
_world = generate_world()
buildings = _world.buildings
trees = _world.trees
parks = _world.parks
biome_objects = _world.biome_objects
biome_collectibles = _world.biome_collectibles
npcs = _world.npcs
cars = _world.cars


# ============================================================
# DRAW FUNCTIONS (Phase 4: moved to src/rendering/)
# ============================================================
# draw_road_grid, draw_tree, draw_biome_object, draw_biome_collectible,
# draw_biome_ground → src/rendering/world.py
# draw_burrb, draw_npc_topdown, draw_car_topdown → src/rendering/entities.py
# draw_interior_topdown → src/rendering/interior.py
# draw_jumpscare → src/rendering/jumpscare.py
# draw_shop, get_shop_tab_info → src/rendering/shop.py
# Ability/tongue visual effects → src/rendering/effects.py
# HUD → src/rendering/ui.py


# ============================================================
# INTERIOR DRAWING AND COLLISION (Phase 5: delegating to src/systems/collision.py)
# ============================================================


def can_move_to(x, y):
    """Wrapper: check world-space movement (delegates to systems/collision.py)."""
    return _collision_can_move_to(x, y, buildings)


def get_nearby_door_building(bx, by):
    """Wrapper: find building near door (delegates to systems/collision.py)."""
    return _get_nearby_door_building(bx, by, buildings)


# (draw_interior_topdown and draw_jumpscare moved to src/rendering/ - Phase 4)
# (can_move_interior and is_at_interior_door imported from src/systems/collision - Phase 5)

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
# ABILITIES! (Phase 5: managed by AbilityManager in src/systems/abilities.py)
# ============================================================
# You can spend potato chips to unlock awesome new powers!
# Ability definitions and constants live in src/systems/abilities.py.
# The AbilityManager instance below owns all state and per-frame updates.

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
    MAGNET_RADIUS,
    BLIZZARD_DURATION,
    BLIZZARD_RADIUS,
    SNOW_CLOAK_DURATION,
    POISON_CLOUD_DURATION,
    POISON_CLOUD_RADIUS,
    SWAMP_MONSTER_DURATION,
    SWAMP_MONSTER_SPEED,
    SWAMP_MONSTER_RADIUS,
    SODA_CAN_DURATION,
    SODA_CAN_SPEED,
    SODA_CAN_RADIUS,
    SODA_CAN_COOLDOWN_TIME,
)

# Single instance that owns all ability state
abilities = AbilityManager()

# The shop menu
shop_open = False  # is the shop screen showing?
shop_cursor = 0  # which ability is highlighted in the shop

# The shop now has tabs! LEFT/RIGHT arrows switch between tabs.
shop_tab = 0  # 0=chips, 1=berries, 2=gems, 3=snowflakes, 4=mushrooms

# Fonts used by draw_touch_buttons (touch controls UI)
# All other font usage is in src/rendering/ui.py and src/rendering/shop.py

# ============================================================
# TOUCH CONTROLS (Phase 6: moved to src/input/touch.py)
# ============================================================
# Touch support for phones, tablets, and touchscreen computers!
# Tap the screen to move, use on-screen buttons for actions.
# Touch is auto-detected: buttons appear when you touch the screen.
#
# TOUCH_BUTTONS, TOUCH_ABILITY_BUTTONS, TOUCH_BTN_RADIUS, touch_hit_button,
# draw_touch_buttons, and handle_touch_event are all in src/input/touch.py.

touch = TouchState()  # all touch state lives here (Phase 6)


# (can_move_to moved to src/systems/collision.py - Phase 5)


async def main():
    """Main game loop, async for Pygbag web support."""
    global running, burrb_x, burrb_y, burrb_angle, facing_left
    global walk_frame, is_walking
    global shop_open, shop_cursor
    global inside_building, interior_x, interior_y
    global saved_outdoor_x, saved_outdoor_y, saved_outdoor_angle
    global tongue_active, tongue_length, tongue_retracting
    global tongue_angle, tongue_hit_npc
    # (ability state is now managed by the `abilities` AbilityManager object)
    global chips_collected
    global berries_collected, gems_collected, snowflakes_collected, mushrooms_collected
    global shop_tab
    global jumpscare_timer, jumpscare_frame, closet_msg_timer, scare_level
    global collect_msg_timer, collect_msg_text
    global cam_x, cam_y
    global player_hp, hurt_timer, hurt_cooldown, death_timer
    # (touch state is now managed by the `touch` TouchState object - Phase 6)

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
                # --- Phase 6: delegate to src/input/keyboard.handle_keydown ---
                kb = handle_keydown(
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
                    can_move_to,
                )

                # Apply result: quit / shop
                if kb.quit:
                    running = False
                    continue
                if kb.close_shop:
                    shop_open = False
                    continue
                if kb.toggle_shop:
                    shop_open = not shop_open
                    shop_cursor = 0
                    continue

                # Apply result: shop navigation (only when shop is open)
                if shop_open:
                    if kb.shop_tab_delta:
                        shop_tab = (shop_tab + kb.shop_tab_delta) % 5
                        shop_cursor = 0
                    if kb.shop_cursor_delta:
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
                        tab_len = len(tab_abs)
                        shop_cursor = (shop_cursor + kb.shop_cursor_delta) % tab_len
                    if kb.shop_buy:
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
                        if shop_tab == 0:
                            cost = ABILITIES[shop_cursor][1]
                            if (
                                not abilities.ability_unlocked[shop_cursor]
                                and chips_collected >= cost
                            ):
                                chips_collected -= cost
                                abilities.ability_unlocked[shop_cursor] = True
                        else:
                            cost = tab_abs[shop_cursor][1]
                            real_idx = tab_indices[shop_cursor]
                            if (
                                not abilities.biome_ability_unlocked[real_idx]
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
                                abilities.biome_ability_unlocked[real_idx] = True
                    continue  # skip all other game input when shop is open

                # Apply result: unstuck
                if kb.unstuck:
                    if inside_building is not None:
                        burrb_x = saved_outdoor_x
                        burrb_y = saved_outdoor_y
                        burrb_angle = saved_outdoor_angle
                        inside_building = None
                        touch.touch_move_target = None
                    else:
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
                                touch.touch_move_target = None
                                break

                # Apply result: tongue
                if kb.shoot_tongue:
                    tongue_active = True
                    tongue_length = 0.0
                    tongue_retracting = False
                    tongue_hit_npc = None
                    tongue_angle = kb.tongue_angle

                # Apply result: enter/exit/interact
                if kb.enter_building and inside_building is None:
                    nearby = get_nearby_door_building(burrb_x, burrb_y)
                    if nearby is not None:
                        inside_building = nearby
                        saved_outdoor_x = burrb_x
                        saved_outdoor_y = burrb_y
                        saved_outdoor_angle = burrb_angle
                        interior_x = float(nearby.spawn_x)
                        interior_y = float(nearby.spawn_y)
                        burrb_angle = math.pi * 1.5
                        touch.touch_move_target = None
                    elif kb.collect_item:
                        for coll in biome_collectibles:
                            if coll[3]:
                                continue
                            cdx = burrb_x - coll[0]
                            cdy = burrb_y - coll[1]
                            cdist = math.sqrt(cdx * cdx + cdy * cdy)
                            if cdist < 30:
                                coll[3] = True
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
                                collect_msg_timer = 90
                                break

                if kb.open_closet and inside_building is not None:
                    bld = inside_building
                    if (
                        not bld.closet_opened
                        and bld.closet_x > 0
                        and jumpscare_timer <= 0
                    ):
                        cl_dx = interior_x - bld.closet_x
                        cl_dy = interior_y - bld.closet_y
                        cl_dist = math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
                        if cl_dist < 30:
                            bld.closet_opened = True
                            if random.random() < 0.1:
                                bld.closet_jumpscare = True
                                scare_level += 1
                                jumpscare_timer = JUMPSCARE_DURATION + scare_level * 60
                                jumpscare_frame = 0
                            else:
                                chips_collected += 2
                                closet_msg_timer = 120

                if kb.steal_chips and inside_building is not None:
                    bld = inside_building
                    if not bld.chips_stolen and bld.chips_x > 0:
                        chip_dx = interior_x - bld.chips_x
                        chip_dy = interior_y - bld.chips_y
                        chip_dist = math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
                        if chip_dist < 30:
                            bld.chips_stolen = True
                            bld.resident_angry = True
                            chips_collected += 1

                if kb.shake_bed and inside_building is not None:
                    bld = inside_building
                    if not bld.bed_shaken and bld.bed_x > 0:
                        bed_dx = interior_x - bld.bed_x
                        bed_dy = interior_y - bld.bed_y
                        bed_dist = math.sqrt(bed_dx * bed_dx + bed_dy * bed_dy)
                        if bed_dist < 30:
                            bld.bed_shaken = True
                            if random.random() < 0.3:
                                bld.bed_monster = True
                                bld.monster_active = True
                                bld.monster_x = bld.bed_x
                                bld.monster_y = bld.bed_y

                if kb.exit_building and inside_building is not None:
                    if is_at_interior_door(inside_building, interior_x, interior_y):
                        burrb_x = saved_outdoor_x
                        burrb_y = saved_outdoor_y
                        burrb_angle = saved_outdoor_angle
                        inside_building = None
                        touch.touch_move_target = None

                # --- Ability activations ---

                if kb.activate_freeze:
                    if abilities.ability_unlocked[3] and abilities.freeze_timer <= 0:
                        abilities.freeze_timer = 300

                if kb.activate_invisible:
                    if abilities.ability_unlocked[4] and abilities.invisible_timer <= 0:
                        abilities.invisible_timer = 300

                if kb.activate_giant:
                    if abilities.ability_unlocked[5] and abilities.giant_timer <= 0:
                        abilities.giant_timer = 480

                if kb.activate_bounce:
                    if (
                        abilities.ability_unlocked[6]
                        and abilities.bounce_timer <= 0
                        and abilities.bounce_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.bounce_timer = BOUNCE_DURATION
                        abilities.bounce_cooldown = 60

                if kb.activate_teleport:
                    if (
                        abilities.ability_unlocked[7]
                        and abilities.teleport_cooldown <= 0
                        and inside_building is None
                    ):
                        tp_x = burrb_x + math.cos(burrb_angle) * TELEPORT_DISTANCE
                        tp_y = burrb_y + math.sin(burrb_angle) * TELEPORT_DISTANCE
                        tp_x = max(30, min(WORLD_WIDTH - 30, tp_x))
                        tp_y = max(30, min(WORLD_HEIGHT - 30, tp_y))
                        if not can_move_to(tp_x, tp_y):
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
                                tp_x = burrb_x
                                tp_y = burrb_y
                        burrb_x = tp_x
                        burrb_y = tp_y
                        abilities.teleport_cooldown = 90
                        abilities.teleport_flash = 15

                if kb.activate_earthquake:
                    if (
                        abilities.ability_unlocked[8]
                        and abilities.earthquake_timer <= 0
                        and abilities.earthquake_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.earthquake_timer = EARTHQUAKE_DURATION
                        abilities.earthquake_cooldown = 360
                        abilities.earthquake_shake = 30
                        for npc in npcs:
                            if npc.npc_type == "rock":
                                continue
                            eq_dx = npc.x - burrb_x
                            eq_dy = npc.y - burrb_y
                            eq_dist = math.sqrt(eq_dx * eq_dx + eq_dy * eq_dy)
                            if eq_dist < EARTHQUAKE_RADIUS:
                                if eq_dist > 1:
                                    npc.x += (eq_dx / eq_dist) * 20
                                    npc.y += (eq_dy / eq_dist) * 20
                                npc.dir_timer = EARTHQUAKE_DURATION
                                npc.speed = 0.0
                        for car in cars:
                            eq_dx = car.x - burrb_x
                            eq_dy = car.y - burrb_y
                            eq_dist = math.sqrt(eq_dx * eq_dx + eq_dy * eq_dy)
                            if eq_dist < EARTHQUAKE_RADIUS:
                                car.speed = 0.0

                if kb.activate_vine_trap:
                    if (
                        abilities.biome_ability_unlocked[0]
                        and abilities.vine_trap_timer <= 0
                        and abilities.vine_trap_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.vine_trap_timer = VINE_TRAP_DURATION
                        abilities.vine_trap_cooldown = 300
                        for npc in npcs:
                            if npc.npc_type == "rock":
                                continue
                            vd = math.sqrt(
                                (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                            )
                            if vd < VINE_TRAP_RADIUS:
                                npc.speed = 0.0
                                npc.dir_timer = VINE_TRAP_DURATION

                if kb.activate_camouflage:
                    if (
                        abilities.biome_ability_unlocked[1]
                        and abilities.camouflage_timer <= 0
                    ):
                        abilities.camouflage_timer = CAMOUFLAGE_DURATION

                if kb.activate_nature_heal:
                    if (
                        abilities.biome_ability_unlocked[2]
                        and abilities.nature_heal_timer <= 0
                        and abilities.nature_heal_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.nature_heal_timer = 30
                        abilities.nature_heal_cooldown = 300
                        for npc in npcs:
                            if npc.npc_type == "rock":
                                continue
                            hd = math.sqrt(
                                (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                            )
                            if hd < NATURE_HEAL_RADIUS and hd > 1:
                                npc.x += ((npc.x - burrb_x) / hd) * 40
                                npc.y += ((npc.y - burrb_y) / hd) * 40

                if kb.activate_sandstorm:
                    if (
                        abilities.biome_ability_unlocked[3]
                        and abilities.sandstorm_timer <= 0
                        and abilities.sandstorm_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.sandstorm_timer = SANDSTORM_DURATION
                        abilities.sandstorm_cooldown = 360
                        for npc in npcs:
                            if npc.npc_type == "rock":
                                continue
                            sd = math.sqrt(
                                (npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2
                            )
                            if sd < SANDSTORM_RADIUS:
                                npc.speed = 0.3
                                npc.dir_timer = SANDSTORM_DURATION

                if kb.activate_magnet:
                    if (
                        abilities.biome_ability_unlocked[4]
                        and abilities.magnet_timer <= 0
                        and abilities.magnet_cooldown <= 0
                    ):
                        abilities.magnet_timer = MAGNET_DURATION
                        abilities.magnet_cooldown = 360

                if kb.activate_fire_dash:
                    if (
                        abilities.biome_ability_unlocked[5]
                        and abilities.fire_dash_active <= 0
                        and abilities.fire_dash_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.fire_dash_active = 20
                        abilities.fire_dash_cooldown = 90

                if kb.activate_ice_wall:
                    if (
                        abilities.biome_ability_unlocked[6]
                        and abilities.ice_wall_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.ice_wall_cooldown = 180
                        perp = burrb_angle + math.pi / 2
                        wall_dist = 40
                        cx = burrb_x + math.cos(burrb_angle) * wall_dist
                        cy = burrb_y + math.sin(burrb_angle) * wall_dist
                        for seg in range(-2, 3):
                            wx = cx + math.cos(perp) * seg * 25
                            wy = cy + math.sin(perp) * seg * 25
                            abilities.ice_walls.append([wx, wy, 480])

                if kb.activate_blizzard:
                    if (
                        abilities.biome_ability_unlocked[7]
                        and abilities.blizzard_timer <= 0
                        and abilities.blizzard_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.blizzard_timer = BLIZZARD_DURATION
                        abilities.blizzard_cooldown = 360
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

                if kb.activate_snow_cloak:
                    if (
                        abilities.biome_ability_unlocked[8]
                        and abilities.snow_cloak_timer <= 0
                        and abilities.snow_cloak_cooldown <= 0
                    ):
                        abilities.snow_cloak_timer = SNOW_CLOAK_DURATION
                        abilities.snow_cloak_cooldown = 360

                if kb.activate_poison_cloud:
                    if (
                        abilities.biome_ability_unlocked[9]
                        and abilities.poison_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.poison_cooldown = 240
                        abilities.poison_clouds.append(
                            [burrb_x, burrb_y, POISON_CLOUD_DURATION]
                        )

                if kb.activate_shadow_step:
                    if (
                        abilities.biome_ability_unlocked[10]
                        and abilities.shadow_step_cooldown <= 0
                        and inside_building is None
                    ):
                        abilities.shadow_step_cooldown = 120
                        best_dist = 999999
                        best_x, best_y = burrb_x, burrb_y
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
                            sd = math.sqrt((tx - burrb_x) ** 2 + (ty - burrb_y) ** 2)
                            if 50 < sd < 500 and sd < best_dist:
                                best_dist = sd
                                best_x = tx + 20
                                best_y = ty + 20
                        if best_dist < 999999:
                            burrb_x = best_x
                            burrb_y = best_y
                            abilities.teleport_flash = 15

                if kb.activate_soda_cans:
                    if (
                        len(abilities.soda_cans) == 0
                        and abilities.soda_can_cooldown <= 0
                        and inside_building is None
                    ):
                        for i in range(3):
                            angle = i * (2 * math.pi / 3)
                            sx = burrb_x + math.cos(angle) * 25
                            sy = burrb_y + math.sin(angle) * 25
                            abilities.soda_cans.append(
                                {
                                    "x": sx,
                                    "y": sy,
                                    "timer": SODA_CAN_DURATION,
                                    "walk": 0,
                                    "attack_cd": 0,
                                }
                            )
                        abilities.soda_can_cooldown = SODA_CAN_COOLDOWN_TIME

                if kb.activate_swamp_monster:
                    if (
                        abilities.biome_ability_unlocked[11]
                        and not abilities.swamp_monster_active
                        and inside_building is None
                    ):
                        abilities.swamp_monster_active = True
                        abilities.swamp_monster_x = burrb_x + 30
                        abilities.swamp_monster_y = burrb_y + 30
                        abilities.swamp_monster_timer = SWAMP_MONSTER_DURATION
                        abilities.swamp_monster_walk = 0

            # === TOUCH / MOUSE INPUT (Phase 6: delegated to src/input/touch.py) ===
            simulated_keys = handle_touch_event(
                event,
                touch,
                abilities.ability_unlocked,
                inside_building,
                interior_x,
                interior_y,
                cam_x,
                cam_y,
                shop_open,
            )
            for key in simulated_keys:
                pygame.event.post(pygame.event.Event(pygame.KEYDOWN, key=key))

        # Handle touch input for the shop (tap abilities to select/buy)
        if shop_open and touch.touch_active and touch.touch_held:
            tx, ty = touch.touch_pos
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
                        touch.touch_held = False
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
                                if (
                                    not abilities.ability_unlocked[i]
                                    and chips_collected >= cost
                                ):
                                    chips_collected -= cost
                                    abilities.ability_unlocked[i] = True
                            else:
                                cost = tab_abs[i][1]
                                real_idx = tab_indices[i]
                                if (
                                    not abilities.biome_ability_unlocked[real_idx]
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
                                    abilities.biome_ability_unlocked[real_idx] = True
                        else:
                            shop_cursor = i
                        touch.touch_held = False
                        break


        # Skip movement and updates when shop is open (game is paused)
        if shop_open:
            draw_shop(
                screen,
                shop_tab,
                shop_cursor,
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
            if touch.touch_active:
                _draw_touch_buttons(screen, touch, abilities.ability_unlocked,
                                    inside_building, interior_x, interior_y, cam_x, cam_y)
            pygame.display.flip()
            clock.tick(FPS)
            await asyncio.sleep(0)
            continue

        # --- ABILITY TIMERS ---
        # Count down all active ability timers each frame
        if abilities.dash_cooldown > 0:
            abilities.dash_cooldown -= 1
        if abilities.dash_active > 0:
            abilities.dash_active -= 1
        if abilities.freeze_timer > 0:
            abilities.freeze_timer -= 1
        if abilities.invisible_timer > 0:
            abilities.invisible_timer -= 1
        if abilities.giant_timer > 0:
            abilities.giant_timer -= 1
        if jumpscare_timer > 0:
            jumpscare_timer -= 1
            jumpscare_frame += 1
        if closet_msg_timer > 0:
            closet_msg_timer -= 1
        if collect_msg_timer > 0:
            collect_msg_timer -= 1
        # Smoothly grow/shrink for giant mode
        target_giant = 2.5 if abilities.giant_timer > 0 else 1.0
        abilities.giant_scale += (target_giant - abilities.giant_scale) * 0.15

        # Bounce timer and height (smooth arc using sine!)
        if abilities.bounce_timer > 0:
            abilities.bounce_timer -= 1
            # Sine curve: goes up then comes back down smoothly
            t = abilities.bounce_timer / BOUNCE_DURATION  # 1.0 -> 0.0
            abilities.bounce_height = math.sin(t * math.pi) * 80  # max 80 pixels high
        else:
            abilities.bounce_height = 0.0
        if abilities.bounce_cooldown > 0:
            abilities.bounce_cooldown -= 1

        # Teleport cooldown and flash
        if abilities.teleport_cooldown > 0:
            abilities.teleport_cooldown -= 1
        if abilities.teleport_flash > 0:
            abilities.teleport_flash -= 1

        # Earthquake timers
        if abilities.earthquake_timer > 0:
            abilities.earthquake_timer -= 1
            # When earthquake ends, unstun NPCs and cars
            if abilities.earthquake_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock":
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
                for car in cars:
                    if car.speed == 0.0:
                        car.speed = random.uniform(1.2, 2.5)
        if abilities.earthquake_cooldown > 0:
            abilities.earthquake_cooldown -= 1
        if abilities.earthquake_shake > 0:
            abilities.earthquake_shake -= 1

        # --- BIOME ABILITY TIMERS ---
        if abilities.vine_trap_timer > 0:
            abilities.vine_trap_timer -= 1
            # When vine trap ends, unstun NPCs
            if abilities.vine_trap_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if abilities.vine_trap_cooldown > 0:
            abilities.vine_trap_cooldown -= 1
        if abilities.camouflage_timer > 0:
            abilities.camouflage_timer -= 1
        if abilities.nature_heal_timer > 0:
            abilities.nature_heal_timer -= 1
        if abilities.nature_heal_cooldown > 0:
            abilities.nature_heal_cooldown -= 1
        if abilities.sandstorm_timer > 0:
            abilities.sandstorm_timer -= 1
            if abilities.sandstorm_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed < 0.5:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if abilities.sandstorm_cooldown > 0:
            abilities.sandstorm_cooldown -= 1
        if abilities.magnet_timer > 0:
            abilities.magnet_timer -= 1
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
        if abilities.magnet_cooldown > 0:
            abilities.magnet_cooldown -= 1
        if abilities.fire_dash_active > 0:
            abilities.fire_dash_active -= 1
            # Drop fire particles behind the burrb
            if inside_building is None:
                abilities.fire_trail.append([burrb_x, burrb_y, 60])  # lasts 1 second
        if abilities.fire_dash_cooldown > 0:
            abilities.fire_dash_cooldown -= 1
        # Update fire trail
        for ft in abilities.fire_trail:
            ft[2] -= 1
        abilities.fire_trail = [ft for ft in abilities.fire_trail if ft[2] > 0]
        # Fire damages NPCs that walk through it!
        for ft in abilities.fire_trail:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                fd = math.sqrt((npc.x - ft[0]) ** 2 + (npc.y - ft[1]) ** 2)
                if fd < 15 and fd > 1:
                    # Push NPC away from fire
                    npc.x += ((npc.x - ft[0]) / fd) * 5
                    npc.y += ((npc.y - ft[1]) / fd) * 5
        # Update ice walls
        for iw in abilities.ice_walls:
            iw[2] -= 1
        abilities.ice_walls = [iw for iw in abilities.ice_walls if iw[2] > 0]
        if abilities.ice_wall_cooldown > 0:
            abilities.ice_wall_cooldown -= 1
        # Ice walls block NPCs
        for iw in abilities.ice_walls:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                wd = math.sqrt((npc.x - iw[0]) ** 2 + (npc.y - iw[1]) ** 2)
                if wd < 20 and wd > 1:
                    # Push NPC away from wall
                    npc.x += ((npc.x - iw[0]) / wd) * 3
                    npc.y += ((npc.y - iw[1]) / wd) * 3
        if abilities.blizzard_timer > 0:
            abilities.blizzard_timer -= 1
            if abilities.blizzard_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        if abilities.blizzard_cooldown > 0:
            abilities.blizzard_cooldown -= 1
        if abilities.snow_cloak_timer > 0:
            abilities.snow_cloak_timer -= 1
        if abilities.snow_cloak_cooldown > 0:
            abilities.snow_cloak_cooldown -= 1
        # Update poison clouds
        for pc in abilities.poison_clouds:
            pc[2] -= 1
            # Push NPCs away from poison
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                pd = math.sqrt((npc.x - pc[0]) ** 2 + (npc.y - pc[1]) ** 2)
                if pd < POISON_CLOUD_RADIUS and pd > 1:
                    npc.x += ((npc.x - pc[0]) / pd) * 2
                    npc.y += ((npc.y - pc[1]) / pd) * 2
        abilities.poison_clouds = [pc for pc in abilities.poison_clouds if pc[2] > 0]
        if abilities.poison_cooldown > 0:
            abilities.poison_cooldown -= 1
        if abilities.shadow_step_cooldown > 0:
            abilities.shadow_step_cooldown -= 1
        # Swamp monster AI
        if abilities.swamp_monster_active:
            abilities.swamp_monster_timer -= 1
            abilities.swamp_monster_walk += 1
            if abilities.swamp_monster_timer <= 0:
                abilities.swamp_monster_active = False
            else:
                # Find nearest NPC and chase it
                nearest_npc = None
                nearest_dist = SWAMP_MONSTER_RADIUS
                for npc in npcs:
                    if npc.npc_type == "rock":
                        continue
                    md = math.sqrt(
                        (npc.x - abilities.swamp_monster_x) ** 2
                        + (npc.y - abilities.swamp_monster_y) ** 2
                    )
                    if md < nearest_dist:
                        nearest_dist = md
                        nearest_npc = npc
                if nearest_npc is not None:
                    md = nearest_dist
                    if md > 1:
                        abilities.swamp_monster_x += (
                            (nearest_npc.x - abilities.swamp_monster_x) / md
                        ) * SWAMP_MONSTER_SPEED
                        abilities.swamp_monster_y += (
                            (nearest_npc.y - abilities.swamp_monster_y) / md
                        ) * SWAMP_MONSTER_SPEED
                    # Push NPC away on contact
                    if md < 20 and md > 1:
                        nearest_npc.x += (
                            (nearest_npc.x - abilities.swamp_monster_x) / md
                        ) * 8
                        nearest_npc.y += (
                            (nearest_npc.y - abilities.swamp_monster_y) / md
                        ) * 8
                else:
                    # No NPC nearby, follow the burrb
                    fd = math.sqrt(
                        (burrb_x - abilities.swamp_monster_x) ** 2
                        + (burrb_y - abilities.swamp_monster_y) ** 2
                    )
                    if fd > 50 and fd > 1:
                        abilities.swamp_monster_x += (
                            (burrb_x - abilities.swamp_monster_x) / fd
                        ) * SWAMP_MONSTER_SPEED
                        abilities.swamp_monster_y += (
                            (burrb_y - abilities.swamp_monster_y) / fd
                        ) * SWAMP_MONSTER_SPEED

        # Soda can monster AI!
        if abilities.soda_can_cooldown > 0:
            abilities.soda_can_cooldown -= 1
        for can in abilities.soda_cans:
            can["timer"] -= 1
            can["walk"] += 1
            if can["attack_cd"] > 0:
                can["attack_cd"] -= 1
        # Remove expired soda cans
        abilities.soda_cans = [c for c in abilities.soda_cans if c["timer"] > 0]
        # Each soda can chases the nearest NPC and bites it!
        for can in abilities.soda_cans:
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
        if abilities.ability_unlocked[1] and keys[pygame.K_LSHIFT]:
            speed_mult = 2.2
        # Dash: press SHIFT for a burst (ability index 0)
        # Dash activates when SHIFT is pressed and we have the dash ability
        if abilities.ability_unlocked[0] and not abilities.ability_unlocked[1]:
            # Only dash if super speed is NOT unlocked (otherwise SHIFT = super speed)
            if (
                keys[pygame.K_LSHIFT]
                and abilities.dash_cooldown <= 0
                and abilities.dash_active <= 0
            ):
                abilities.dash_active = 12  # 12 frames of dash burst
                abilities.dash_cooldown = 45  # cooldown before next dash
        # If BOTH dash and super speed are unlocked, SHIFT = super speed,
        # and dash triggers automatically when you start running fast
        if abilities.ability_unlocked[0] and abilities.ability_unlocked[1]:
            if (
                keys[pygame.K_LSHIFT]
                and abilities.dash_cooldown <= 0
                and abilities.dash_active <= 0
            ):
                abilities.dash_active = 12
                abilities.dash_cooldown = 45
        if abilities.dash_active > 0:
            speed_mult = max(speed_mult, 4.0)  # dash is faster than super speed
        # Fire Dash: even faster than regular dash with fire!
        if abilities.fire_dash_active > 0:
            speed_mult = max(speed_mult, 5.0)
        # Snow Cloak: rolling snowball is fast!
        if abilities.snow_cloak_timer > 0:
            speed_mult = max(speed_mult, 3.0)
        # Giant mode makes you a little slower (you're big!)
        if abilities.giant_timer > 0:
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
            touch.touch_move_target = None

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
        if dx == 0 and dy == 0 and touch.touch_move_target is not None and touch.touch_active:
            target_x, target_y = touch.touch_move_target
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
                touch.touch_move_target = None

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
            if abilities.bounce_timer > 0:
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
            if abilities.invisible_timer > 0 or abilities.camouflage_timer > 0:
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
            and abilities.invisible_timer <= 0
            and abilities.camouflage_timer <= 0
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
        if abilities.freeze_timer <= 0:
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
        effective_tongue_max = tongue_max_length * (
            2.0 if abilities.ability_unlocked[2] else 1.0
        )
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
        if abilities.earthquake_shake > 0:
            cam_x += random.randint(-6, 6)
            cam_y += random.randint(-6, 6)

        # --- DRAWING ---
        if inside_building is not None:
            # ========== INSIDE A BUILDING ==========
            # Top-down inside the building
            draw_interior_topdown(
                screen, inside_building, interior_x, interior_y, facing_left, walk_frame
            )

            # Interior interaction prompts (src/rendering/ui.py)
            draw_interior_prompts(
                screen,
                inside_building,
                interior_x,
                interior_y,
                closet_msg_timer,
                jumpscare_timer,
            )

        else:
            # ========== TOP-DOWN MODE (the original view) ==========
            # Fill the background with biome colors
            draw_biome_ground(screen, cam_x, cam_y)

            # Draw the spawn square (a nice clear area where you start!)
            draw_spawn_square(screen, SPAWN_RECT, SPAWN_SIZE, cam_x, cam_y)

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

            # Freeze overlay on all frozen NPCs
            draw_freeze_overlay(screen, cam_x, cam_y, npcs, abilities.freeze_timer)

            # Bounce: draw a shadow on the ground when airborne!
            draw_bounce_shadow(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                abilities.bounce_timer,
                abilities.bounce_height,
            )

            # Bounce height offset for drawing the burrb
            bounce_y_offset = -abilities.bounce_height  # negative = up on screen

            # Draw the burrb (with Giant Mode and Invisibility effects!)
            if abilities.giant_scale > 1.05 or abilities.invisible_timer > 0:
                # Draw to a temp surface so we can scale/alpha it
                temp_size = int(60 * abilities.giant_scale)
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
                if abilities.giant_scale > 1.05:
                    new_w = int(temp_size * abilities.giant_scale)
                    new_h = int(temp_size * abilities.giant_scale)
                    temp_surf = pygame.transform.scale(temp_surf, (new_w, new_h))
                else:
                    new_w = temp_size
                    new_h = temp_size
                # Invisibility = semi-transparent + blue tint
                if abilities.invisible_timer > 0:
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

            # --- ABILITY VISUAL EFFECTS (src/rendering/effects.py) ---
            draw_teleport_flash(
                screen, burrb_x, burrb_y, cam_x, cam_y, abilities.teleport_flash
            )
            draw_earthquake_shockwave(
                screen, burrb_x, burrb_y, cam_x, cam_y, abilities.earthquake_shake
            )
            draw_dash_trail(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                burrb_angle,
                abilities.dash_active,
            )
            draw_vine_trap(screen, cam_x, cam_y, npcs, abilities.vine_trap_timer)
            draw_camouflage(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                bounce_y_offset,
                abilities.camouflage_timer,
            )
            draw_nature_heal(
                screen, burrb_x, burrb_y, cam_x, cam_y, abilities.nature_heal_timer
            )
            draw_sandstorm(
                screen, burrb_x, burrb_y, cam_x, cam_y, abilities.sandstorm_timer
            )
            draw_magnet(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                biome_collectibles,
                abilities.magnet_timer,
                MAGNET_RADIUS,
            )
            draw_fire_trail(screen, cam_x, cam_y, abilities.fire_trail)
            draw_fire_dash_trail(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                burrb_angle,
                abilities.fire_dash_active,
            )
            draw_ice_walls(screen, cam_x, cam_y, abilities.ice_walls)
            draw_blizzard(
                screen, burrb_x, burrb_y, cam_x, cam_y, abilities.blizzard_timer
            )
            draw_snow_cloak(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                bounce_y_offset,
                abilities.snow_cloak_timer,
            )
            draw_poison_clouds(
                screen, cam_x, cam_y, abilities.poison_clouds, POISON_CLOUD_RADIUS
            )
            draw_swamp_monster(
                screen,
                cam_x,
                cam_y,
                abilities.swamp_monster_active,
                abilities.swamp_monster_x,
                abilities.swamp_monster_y,
                abilities.swamp_monster_walk,
                inside_building,
            )
            draw_soda_cans(screen, cam_x, cam_y, abilities.soda_cans, inside_building)
            draw_tongue(
                screen,
                burrb_x,
                burrb_y,
                cam_x,
                cam_y,
                tongue_active,
                tongue_length,
                tongue_angle,
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

        # --- UI overlay (shown in both modes, src/rendering/ui.py) ---
        draw_title_and_mode(screen, inside_building)
        draw_health(screen, player_hp, MAX_HP)
        draw_hurt_flash(screen, hurt_timer)
        draw_death_screen(screen, death_timer)
        currency_y = draw_currencies(
            screen,
            chips_collected,
            berries_collected,
            gems_collected,
            snowflakes_collected,
            mushrooms_collected,
        )
        draw_ability_bars(
            screen,
            currency_y,
            abilities.freeze_timer,
            abilities.invisible_timer,
            abilities.giant_timer,
            abilities.dash_active,
            abilities.bounce_timer,
            abilities.earthquake_timer,
            abilities.vine_trap_timer,
            abilities.camouflage_timer,
            abilities.sandstorm_timer,
            abilities.magnet_timer,
            abilities.fire_dash_active,
            abilities.blizzard_timer,
            abilities.snow_cloak_timer,
            abilities.swamp_monster_active,
            abilities.swamp_monster_timer,
            abilities.soda_cans,
            abilities.ability_unlocked,
            abilities.biome_ability_unlocked,
            BOUNCE_DURATION,
            EARTHQUAKE_DURATION,
            VINE_TRAP_DURATION,
            CAMOUFLAGE_DURATION,
            SANDSTORM_DURATION,
            MAGNET_DURATION,
            BLIZZARD_DURATION,
            SNOW_CLOAK_DURATION,
            SWAMP_MONSTER_DURATION,
            SODA_CAN_DURATION,
        )
        draw_help_text(screen, inside_building)
        if inside_building is None:
            draw_outdoor_prompts(
                screen, burrb_x, burrb_y, buildings, biome_collectibles
            )
            draw_biome_label(screen, burrb_x, burrb_y)
        draw_collect_message(screen, collect_msg_timer, collect_msg_text)

        # Draw touch buttons (only if touch has been used)
        if touch.touch_active:
            _draw_touch_buttons(screen, touch, abilities.ability_unlocked,
                                inside_building, interior_x, interior_y, cam_x, cam_y)

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
