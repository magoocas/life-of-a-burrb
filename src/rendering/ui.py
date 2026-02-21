"""
src/rendering/ui.py
HUD rendering: hearts, currencies, ability bars, prompts, title, death screen.
Extracted from game.py main loop, Phase 4.
"""

import math
import pygame

from src.constants import (
    WHITE,
    BLACK,
    YELLOW,
    BURRB_LIGHT_BLUE,
)
from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.biomes import (
    BIOME_CITY,
    BIOME_FOREST,
    BIOME_DESERT,
    BIOME_SNOW,
    BIOME_SWAMP,
    get_biome,
)

# Bounce/jump, BOUNCE_DURATION are referenced only for type info; passed as args.


def _font(size):
    """Create a font of the given size."""
    return pygame.font.Font(None, size)


# ---------------------------------------------------------------------------
# TITLE + MODE
# ---------------------------------------------------------------------------


def draw_title_and_mode(surface, inside_building):
    """Draw the game title and current mode indicator."""
    tf = _font(42)
    f = _font(28)
    title_text = tf.render("Life of a Burrb", True, WHITE)
    title_shadow = tf.render("Life of a Burrb", True, BLACK)
    surface.blit(title_shadow, (12, 12))
    surface.blit(title_text, (10, 10))

    if inside_building is not None:
        mode_text = f.render("[INSIDE]", True, YELLOW)
        mode_shadow = f.render("[INSIDE]", True, BLACK)
    else:
        mode_text = f.render("[TOP DOWN]", True, BURRB_LIGHT_BLUE)
        mode_shadow = f.render("[TOP DOWN]", True, BLACK)

    surface.blit(mode_shadow, (12, 42))
    surface.blit(mode_text, (10, 40))


# ---------------------------------------------------------------------------
# HEALTH BAR
# ---------------------------------------------------------------------------


def draw_health(surface, player_hp, MAX_HP):
    """Draw the heart health bar."""
    f = _font(28)
    hp_x = 10
    hp_y = 62
    hp_label = f.render("HP:", True, (255, 100, 100))
    hp_shadow = f.render("HP:", True, BLACK)
    surface.blit(hp_shadow, (hp_x + 1, hp_y + 1))
    surface.blit(hp_label, (hp_x, hp_y))
    for i in range(MAX_HP):
        heart_x = hp_x + 32 + i * 18
        heart_y = hp_y + 3
        if i < player_hp:
            # Full heart (red)
            pygame.draw.circle(surface, (220, 40, 40), (heart_x - 3, heart_y), 5)
            pygame.draw.circle(surface, (220, 40, 40), (heart_x + 3, heart_y), 5)
            pygame.draw.polygon(
                surface,
                (220, 40, 40),
                [
                    (heart_x - 7, heart_y + 1),
                    (heart_x, heart_y + 9),
                    (heart_x + 7, heart_y + 1),
                ],
            )
            # Shine
            pygame.draw.circle(surface, (255, 120, 120), (heart_x - 3, heart_y - 1), 2)
        else:
            # Empty heart (dark outline)
            pygame.draw.circle(surface, (80, 30, 30), (heart_x - 3, heart_y), 5, 1)
            pygame.draw.circle(surface, (80, 30, 30), (heart_x + 3, heart_y), 5, 1)
            pygame.draw.polygon(
                surface,
                (80, 30, 30),
                [
                    (heart_x - 7, heart_y + 1),
                    (heart_x, heart_y + 9),
                    (heart_x + 7, heart_y + 1),
                ],
                1,
            )


# ---------------------------------------------------------------------------
# HURT FLASH
# ---------------------------------------------------------------------------


def draw_hurt_flash(surface, hurt_timer):
    """Red vignette flash when the player takes damage."""
    if hurt_timer <= 0:
        return
    flash_alpha = int(150 * (hurt_timer / 20.0))
    flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
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
    surface.blit(flash_surf, (0, 0))


# ---------------------------------------------------------------------------
# DEATH SCREEN
# ---------------------------------------------------------------------------


def draw_death_screen(surface, death_timer):
    """Fade to black + 'You Died' text."""
    if death_timer <= 0:
        return
    fade_alpha = int(200 * (1.0 - death_timer / 120.0))
    death_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    death_surf.fill((0, 0, 0, min(200, fade_alpha)))
    surface.blit(death_surf, (0, 0))
    if death_timer < 90:
        death_font = _font(64)
        f = _font(28)
        dt_text = death_font.render("You Died!", True, (220, 40, 40))
        dt_shadow = death_font.render("You Died!", True, BLACK)
        dtx = SCREEN_WIDTH // 2 - dt_text.get_width() // 2
        dty = SCREEN_HEIGHT // 2 - dt_text.get_height() // 2
        surface.blit(dt_shadow, (dtx + 2, dty + 2))
        surface.blit(dt_text, (dtx, dty))
        if death_timer < 60:
            hint_text = f.render("Respawning at HOME...", True, (180, 180, 180))
            hx = SCREEN_WIDTH // 2 - hint_text.get_width() // 2
            surface.blit(hint_text, (hx, dty + 50))


# ---------------------------------------------------------------------------
# CURRENCIES
# ---------------------------------------------------------------------------


def draw_currencies(
    surface,
    chips_collected,
    berries_collected,
    gems_collected,
    snowflakes_collected,
    mushrooms_collected,
):
    """Display all non-zero currency counts in the top-right corner.
    Returns the y position below the last drawn currency (for stacking)."""
    f = _font(28)
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
            cur_text = f.render(cur_str, True, cur_color)
            cur_shadow = f.render(cur_str, True, BLACK)
            cur_x = SCREEN_WIDTH - cur_text.get_width() - 12
            surface.blit(cur_shadow, (cur_x + 1, currency_y + 1))
            surface.blit(cur_text, (cur_x, currency_y))
            currency_y += 18
    return currency_y


# ---------------------------------------------------------------------------
# ABILITY BARS
# ---------------------------------------------------------------------------


def draw_ability_bars(
    surface,
    currency_y,
    freeze_timer,
    invisible_timer,
    giant_timer,
    dash_active,
    bounce_timer,
    earthquake_timer,
    vine_trap_timer,
    camouflage_timer,
    sandstorm_timer,
    magnet_timer,
    fire_dash_active,
    blizzard_timer,
    snow_cloak_timer,
    swamp_monster_active,
    swamp_monster_timer,
    soda_cans,
    ability_unlocked,
    biome_ability_unlocked,
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
):
    """Draw active ability progress bars and passive badges."""
    f = _font(28)
    ability_y = currency_y + 4

    active_abilities = []
    if freeze_timer > 0:
        active_abilities.append(("FREEZE", (100, 180, 255), freeze_timer, 300))
    if invisible_timer > 0:
        active_abilities.append(("INVISIBLE", (180, 140, 255), invisible_timer, 300))
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
        max_timer = max(c["timer"] for c in soda_cans)
        active_abilities.append(
            (
                "SODA x" + str(len(soda_cans)),
                (200, 30, 30),
                max_timer,
                SODA_CAN_DURATION,
            )
        )

    for ab_name, ab_color, ab_timer, ab_max in active_abilities:
        bar_w = 90
        bar_h = 14
        bar_x = SCREEN_WIDTH - bar_w - 12
        bar_y = ability_y
        pygame.draw.rect(
            surface, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3
        )
        fill_w = int(bar_w * ab_timer / ab_max)
        pygame.draw.rect(
            surface, ab_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3
        )
        ab_txt = f.render(ab_name, True, WHITE)
        surface.blit(ab_txt, (bar_x - ab_txt.get_width() - 6, bar_y - 2))
        ability_y += 20

    # Passive ability badges
    passive_badges = []
    if ability_unlocked[1]:  # Super Speed
        passive_badges.append(("SPD", (100, 255, 100)))
    if ability_unlocked[2]:  # Mega Tongue
        passive_badges.append(("TNG", (255, 120, 160)))
    if ability_unlocked[0] and not ability_unlocked[1]:  # Dash (only if no super speed)
        passive_badges.append(("DSH", (255, 255, 100)))
    if biome_ability_unlocked[4]:  # Magnet (passive-ish)
        passive_badges.append(("MAG", (100, 150, 255)))

    if passive_badges:
        badge_x = SCREEN_WIDTH - 12
        for badge_name, badge_color in passive_badges:
            badge_txt = f.render(badge_name, True, badge_color)
            badge_x -= badge_txt.get_width() + 8
            surface.blit(badge_txt, (badge_x, ability_y))
        ability_y += 20

    return ability_y


# ---------------------------------------------------------------------------
# HELP TEXT / CONTROL HINTS
# ---------------------------------------------------------------------------


def draw_help_text(surface, inside_building):
    """Draw the control hint at the bottom of the screen."""
    f = _font(28)
    if inside_building is not None:
        help_msg = "Arrows/WASD walk  |  E take/exit  |  ESC quit"
    else:
        help_msg = "WASD walk | O tongue | 1 soda cans | E enter | TAB shop | ESC quit"
    help_text = f.render(help_msg, True, WHITE)
    help_shadow = f.render(help_msg, True, BLACK)
    surface.blit(help_shadow, (12, SCREEN_HEIGHT - 28))
    surface.blit(help_text, (10, SCREEN_HEIGHT - 30))


# ---------------------------------------------------------------------------
# INTERACTION PROMPTS
# ---------------------------------------------------------------------------


def draw_outdoor_prompts(surface, burrb_x, burrb_y, buildings, biome_collectibles):
    """Show 'Press E to enter' or biome collectible pickup prompts."""
    import math as _math

    f = _font(28)
    # Door prompt when near a building outside
    for b in buildings:
        door_cx = b.door_x + 8
        door_cy = b.door_y + 24
        dx = burrb_x - door_cx
        dy = burrb_y - door_cy
        dist = _math.sqrt(dx * dx + dy * dy)
        if dist < 30:
            prompt = f.render("Press E to enter", True, YELLOW)
            prompt_shadow = f.render("Press E to enter", True, BLACK)
            px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
            surface.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
            surface.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))
            return  # show only one prompt at a time

    # Biome collectible pickup prompt
    for coll in biome_collectibles:
        if coll[3]:
            continue
        cdx = burrb_x - coll[0]
        cdy = burrb_y - coll[1]
        cdist = _math.sqrt(cdx * cdx + cdy * cdy)
        if cdist < 30:
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
            prompt = f.render(pt, True, pc)
            prompt_shadow = f.render(pt, True, BLACK)
            px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
            surface.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
            surface.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))
            break


def draw_interior_prompts(
    surface, bld, interior_x, interior_y, closet_msg_timer, jumpscare_timer
):
    """Show interior interaction prompts (door, chips, closet, bed)."""
    import math as _math

    f = _font(28)

    tile = bld.interior_tile
    door_x = bld.interior_door_col * tile + tile // 2
    door_y = bld.interior_door_row * tile + tile // 2
    d_dx = interior_x - door_x
    d_dy = interior_y - door_y
    if _math.sqrt(d_dx * d_dx + d_dy * d_dy) < tile * 1.5:
        prompt = f.render("Press E to exit", True, YELLOW)
        prompt_shadow = f.render("Press E to exit", True, BLACK)
        px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
        surface.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
        surface.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))

    # Chip stealing prompt
    if not bld.chips_stolen and bld.chips_x > 0:
        chip_dx = interior_x - bld.chips_x
        chip_dy = interior_y - bld.chips_y
        chip_dist = _math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
        if chip_dist < 30:
            chip_prompt = f.render("Press E to take chips!", True, (255, 200, 50))
            chip_shadow = f.render("Press E to take chips!", True, BLACK)
            cpx = SCREEN_WIDTH // 2 - chip_prompt.get_width() // 2
            surface.blit(chip_shadow, (cpx + 1, SCREEN_HEIGHT // 2 + 71))
            surface.blit(chip_prompt, (cpx, SCREEN_HEIGHT // 2 + 70))

    # Closet prompt
    if not bld.closet_opened and bld.closet_x > 0:
        cl_dx = interior_x - bld.closet_x
        cl_dy = interior_y - bld.closet_y
        cl_dist = _math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
        if cl_dist < 30:
            cl_prompt = f.render("Press E to open closet!", True, (200, 170, 100))
            cl_shadow = f.render("Press E to open closet!", True, BLACK)
            clpx = SCREEN_WIDTH // 2 - cl_prompt.get_width() // 2
            surface.blit(cl_shadow, (clpx + 1, SCREEN_HEIGHT // 2 + 41))
            surface.blit(cl_prompt, (clpx, SCREEN_HEIGHT // 2 + 40))

    # Bed prompt
    if not bld.bed_shaken and bld.bed_x > 0:
        bed_dx = interior_x - bld.bed_x
        bed_dy = interior_y - bld.bed_y
        bed_dist = _math.sqrt(bed_dx * bed_dx + bed_dy * bed_dy)
        if bed_dist < 30:
            bed_prompt = f.render("Press E to shake bed!", True, (180, 140, 220))
            bed_shadow = f.render("Press E to shake bed!", True, BLACK)
            bpx = SCREEN_WIDTH // 2 - bed_prompt.get_width() // 2
            surface.blit(bed_shadow, (bpx + 1, SCREEN_HEIGHT // 2 + 11))
            surface.blit(bed_prompt, (bpx, SCREEN_HEIGHT // 2 + 10))

    # Monster warning
    if bld.monster_active:
        mon_text = f.render("SOMETHING CRAWLED OUT!", True, (200, 0, 200))
        mon_shadow = f.render("SOMETHING CRAWLED OUT!", True, BLACK)
        mpx = SCREEN_WIDTH // 2 - mon_text.get_width() // 2
        if (pygame.time.get_ticks() // 350) % 2 == 0:
            surface.blit(mon_shadow, (mpx + 1, 91))
            surface.blit(mon_text, (mpx, 90))

    # Found chips in closet message
    if closet_msg_timer > 0:
        found_text = f.render("Found 2 chips in the closet!", True, (100, 255, 100))
        found_shadow = f.render("Found 2 chips in the closet!", True, BLACK)
        ftx = SCREEN_WIDTH // 2 - found_text.get_width() // 2
        surface.blit(found_shadow, (ftx + 1, SCREEN_HEIGHT // 2 - 29))
        surface.blit(found_text, (ftx, SCREEN_HEIGHT // 2 - 30))

    # Resident angry warning
    if bld.resident_angry:
        warn_text = f.render("THE BURRB IS ANGRY!", True, (255, 60, 60))
        warn_shadow = f.render("THE BURRB IS ANGRY!", True, BLACK)
        wpx = SCREEN_WIDTH // 2 - warn_text.get_width() // 2
        if (pygame.time.get_ticks() // 400) % 2 == 0:
            surface.blit(warn_shadow, (wpx + 1, 71))
            surface.blit(warn_text, (wpx, 70))


# ---------------------------------------------------------------------------
# BIOME LABEL
# ---------------------------------------------------------------------------


def draw_biome_label(surface, burrb_x, burrb_y):
    """Show which biome the burrb is currently in."""
    f = _font(28)
    cur_biome = get_biome(burrb_x, burrb_y)
    biome_names = {
        BIOME_CITY: "City",
        BIOME_FOREST: "Forest",
        BIOME_DESERT: "Desert",
        BIOME_SNOW: "Snow",
        BIOME_SWAMP: "Swamp",
    }
    biome_label = f.render(biome_names[cur_biome], True, (255, 255, 255))
    biome_shadow = f.render(biome_names[cur_biome], True, (0, 0, 0))
    surface.blit(biome_shadow, (SCREEN_WIDTH - biome_label.get_width() - 11, 41))
    surface.blit(biome_label, (SCREEN_WIDTH - biome_label.get_width() - 12, 40))


# ---------------------------------------------------------------------------
# COLLECT MESSAGE
# ---------------------------------------------------------------------------


def draw_collect_message(surface, collect_msg_timer, collect_msg_text):
    """Floating 'Collected!' message that fades out."""
    if collect_msg_timer <= 0:
        return
    f = _font(28)
    msg_color = (100, 255, 100)
    msg = f.render(collect_msg_text, True, msg_color)
    msg_shadow = f.render(collect_msg_text, True, BLACK)
    mx = SCREEN_WIDTH // 2 - msg.get_width() // 2
    my = SCREEN_HEIGHT // 2 + 70 - (90 - collect_msg_timer) // 3
    surface.blit(msg_shadow, (mx + 1, my + 1))
    surface.blit(msg, (mx, my))


# ---------------------------------------------------------------------------
# SPAWN SQUARE
# ---------------------------------------------------------------------------


def draw_spawn_square(surface, SPAWN_RECT, SPAWN_SIZE, cam_x, cam_y):
    """Draw the HOME spawn square on the world."""
    sp_sx = SPAWN_RECT.x - cam_x
    sp_sy = SPAWN_RECT.y - cam_y
    if (
        sp_sx + SPAWN_SIZE > 0
        and sp_sx < SCREEN_WIDTH
        and sp_sy + SPAWN_SIZE > 0
        and sp_sy < SCREEN_HEIGHT
    ):
        pygame.draw.rect(
            surface,
            (140, 200, 120),
            (sp_sx, sp_sy, SPAWN_SIZE, SPAWN_SIZE),
            border_radius=8,
        )
        pygame.draw.rect(
            surface,
            (100, 160, 80),
            (sp_sx, sp_sy, SPAWN_SIZE, SPAWN_SIZE),
            3,
            border_radius=8,
        )
        home_font = pygame.font.Font(None, 22)
        home_text = home_font.render("HOME", True, (80, 130, 60))
        surface.blit(
            home_text,
            (
                sp_sx + SPAWN_SIZE // 2 - home_text.get_width() // 2,
                sp_sy + SPAWN_SIZE // 2 - home_text.get_height() // 2,
            ),
        )
