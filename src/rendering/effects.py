"""
src/rendering/effects.py
Ability visual effects and tongue rendering.
Extracted from game.py main loop, Phase 4.

All draw functions take the screen surface plus whatever game state they need.
"""

import math
import pygame

from src.settings import SCREEN_WIDTH, SCREEN_HEIGHT
from src.constants import WORLD_WIDTH, WORLD_HEIGHT


# ---------------------------------------------------------------------------
# TONGUE
# ---------------------------------------------------------------------------


def draw_tongue(
    surface, burrb_x, burrb_y, cam_x, cam_y, tongue_active, tongue_length, tongue_angle
):
    """Draw the tongue in top-down mode."""
    if not tongue_active or tongue_length <= 0:
        return
    burrb_sx = burrb_x - cam_x
    burrb_sy = burrb_y - cam_y
    tip_sx = burrb_sx + math.cos(tongue_angle) * tongue_length
    tip_sy = burrb_sy + math.sin(tongue_angle) * tongue_length
    # Tongue is pink/red, gets thicker near the base
    # Base (thick part)
    pygame.draw.line(
        surface,
        (220, 80, 100),
        (int(burrb_sx), int(burrb_sy)),
        (int(tip_sx), int(tip_sy)),
        4,
    )
    # Center line (lighter pink)
    pygame.draw.line(
        surface,
        (255, 140, 160),
        (int(burrb_sx), int(burrb_sy)),
        (int(tip_sx), int(tip_sy)),
        2,
    )
    # Tongue tip (round blob)
    pygame.draw.circle(
        surface,
        (220, 60, 80),
        (int(tip_sx), int(tip_sy)),
        5,
    )
    pygame.draw.circle(
        surface,
        (255, 120, 140),
        (int(tip_sx), int(tip_sy)),
        3,
    )


# ---------------------------------------------------------------------------
# STANDARD ABILITY EFFECTS
# ---------------------------------------------------------------------------


def draw_teleport_flash(surface, burrb_x, burrb_y, cam_x, cam_y, teleport_flash):
    """Teleport flash effect."""
    if teleport_flash <= 0:
        return
    flash_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    flash_alpha = int(200 * (teleport_flash / 15))
    pygame.draw.circle(
        flash_surf,
        (100, 200, 255, flash_alpha),
        (int(burrb_x - cam_x), int(burrb_y - cam_y)),
        int(60 + (15 - teleport_flash) * 10),
    )
    surface.blit(flash_surf, (0, 0))


def draw_earthquake_shockwave(
    surface, burrb_x, burrb_y, cam_x, cam_y, earthquake_shake
):
    """Earthquake expanding ring shockwave."""
    if earthquake_shake <= 0:
        return
    eq_sx = int(burrb_x - cam_x)
    eq_sy = int(burrb_y - cam_y)
    ring_radius = int((30 - earthquake_shake) * 12)
    ring_alpha = int(180 * (earthquake_shake / 30))
    eq_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    pygame.draw.circle(
        eq_surf,
        (200, 150, 50, ring_alpha),
        (eq_sx, eq_sy),
        ring_radius,
        max(3, 8 - (30 - earthquake_shake) // 4),
    )
    # Inner dust cloud
    if earthquake_shake > 15:
        inner_r = ring_radius // 2
        pygame.draw.circle(
            eq_surf,
            (180, 160, 100, ring_alpha // 2),
            (eq_sx, eq_sy),
            inner_r,
        )
    surface.blit(eq_surf, (0, 0))


def draw_dash_trail(surface, burrb_x, burrb_y, cam_x, cam_y, burrb_angle, dash_active):
    """Dash trail effect."""
    if dash_active <= 0:
        return
    burrb_sx = int(burrb_x - cam_x)
    burrb_sy = int(burrb_y - cam_y)
    for trail_i in range(3):
        trail_offset = (trail_i + 1) * 8
        trail_alpha = 120 - trail_i * 40
        trail_x = burrb_sx - int(math.cos(burrb_angle) * trail_offset)
        trail_y = burrb_sy - int(math.sin(burrb_angle) * trail_offset)
        trail_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.rect(
            trail_surf,
            (60, 150, 220, trail_alpha),
            (0, 0, 16, 16),
            border_radius=4,
        )
        surface.blit(trail_surf, (trail_x - 8, trail_y - 8))


def draw_freeze_overlay(surface, cam_x, cam_y, npcs, freeze_timer):
    """Blue ice overlay on all frozen NPCs."""
    if freeze_timer <= 0:
        return
    for npc in npcs:
        if npc.npc_type == "rock":
            continue
        npc_sx = int(npc.x - cam_x)
        npc_sy = int(npc.y - cam_y)
        if -20 < npc_sx < SCREEN_WIDTH + 20 and -20 < npc_sy < SCREEN_HEIGHT + 20:
            ice_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            ice_alpha = 100 + int(math.sin(freeze_timer * 0.1) * 40)
            pygame.draw.rect(
                ice_surf,
                (100, 180, 255, ice_alpha),
                (0, 0, 20, 20),
                border_radius=4,
            )
            # Little ice sparkles
            for sp in range(3):
                spx = 4 + sp * 6
                spy = 3 + (sp % 2) * 10
                pygame.draw.circle(ice_surf, (200, 230, 255, 180), (spx, spy), 2)
            surface.blit(ice_surf, (npc_sx - 10, npc_sy - 10))


def draw_bounce_shadow(
    surface, burrb_x, burrb_y, cam_x, cam_y, bounce_timer, bounce_height
):
    """Shadow on ground when the burrb is bouncing."""
    if bounce_timer <= 0:
        return
    shadow_sx = int(burrb_x - cam_x)
    shadow_sy = int(burrb_y - cam_y)
    shadow_w = int(16 * (1.0 - bounce_height / 120))
    shadow_h = max(2, shadow_w // 3)
    shadow_surf = pygame.Surface((shadow_w * 2, shadow_h * 2), pygame.SRCALPHA)
    shadow_alpha = int(80 * (1.0 - bounce_height / 120))
    pygame.draw.ellipse(
        shadow_surf,
        (0, 0, 0, shadow_alpha),
        (0, 0, shadow_w * 2, shadow_h * 2),
    )
    surface.blit(shadow_surf, (shadow_sx - shadow_w, shadow_sy - shadow_h))


# ---------------------------------------------------------------------------
# BIOME ABILITY EFFECTS
# ---------------------------------------------------------------------------


def draw_vine_trap(surface, cam_x, cam_y, npcs, vine_trap_timer):
    """Green vine circles around trapped NPCs."""
    if vine_trap_timer <= 0:
        return
    vt_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    vt_alpha = min(150, vine_trap_timer * 3)
    for npc in npcs:
        if npc.npc_type == "rock":
            continue
        if npc.speed == 0.0:
            nsx = int(npc.x - cam_x)
            nsy = int(npc.y - cam_y)
            if -30 < nsx < SCREEN_WIDTH + 30 and -30 < nsy < SCREEN_HEIGHT + 30:
                pygame.draw.circle(vt_surf, (30, 180, 30, vt_alpha), (nsx, nsy), 14, 3)
                pygame.draw.circle(
                    vt_surf, (60, 220, 60, vt_alpha // 2), (nsx, nsy), 18, 2
                )
    surface.blit(vt_surf, (0, 0))


def draw_camouflage(
    surface, burrb_x, burrb_y, cam_x, cam_y, bounce_y_offset, camouflage_timer
):
    """Green leaf pattern overlay on the burrb area."""
    if camouflage_timer <= 0:
        return
    camo_surf = pygame.Surface((30, 30), pygame.SRCALPHA)
    camo_alpha = min(140, camouflage_timer * 3)
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y + bounce_y_offset)
    t_val = pygame.time.get_ticks() * 0.003
    for li in range(5):
        lx = 15 + int(math.sin(t_val + li * 1.2) * 8)
        ly = 15 + int(math.cos(t_val + li * 0.9) * 8)
        pygame.draw.circle(camo_surf, (40, 160, 40, camo_alpha), (lx, ly), 5)
    surface.blit(camo_surf, (bsx - 15, bsy - 15))


def draw_nature_heal(surface, burrb_x, burrb_y, cam_x, cam_y, nature_heal_timer):
    """Expanding green ring for Nature Heal."""
    if nature_heal_timer <= 0:
        return
    nh_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    nh_r = int((30 - nature_heal_timer) * 10)
    nh_alpha = int(180 * (nature_heal_timer / 30))
    pygame.draw.circle(
        nh_surf,
        (80, 255, 80, nh_alpha),
        (int(burrb_x - cam_x), int(burrb_y - cam_y)),
        nh_r,
        4,
    )
    surface.blit(nh_surf, (0, 0))


def draw_sandstorm(surface, burrb_x, burrb_y, cam_x, cam_y, sandstorm_timer):
    """Swirling sand particles for Sandstorm."""
    if sandstorm_timer <= 0:
        return
    ss_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    ss_alpha = min(80, sandstorm_timer)
    ss_surf.fill((220, 190, 120, ss_alpha // 3))
    t_val = pygame.time.get_ticks() * 0.001
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y)
    for si in range(20):
        sa = t_val * 3 + si * 0.3
        sr = 40 + si * 12
        sx_p = bsx + int(math.cos(sa) * sr)
        sy_p = bsy + int(math.sin(sa) * sr)
        pygame.draw.circle(ss_surf, (200, 170, 100, ss_alpha), (sx_p, sy_p), 3)
    surface.blit(ss_surf, (0, 0))


def draw_magnet(
    surface,
    burrb_x,
    burrb_y,
    cam_x,
    cam_y,
    biome_collectibles,
    magnet_timer,
    MAGNET_RADIUS,
):
    """Blue pull lines toward burrb for Magnet ability."""
    if magnet_timer <= 0:
        return
    mg_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    mg_alpha = min(120, magnet_timer * 2)
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y)
    for coll in biome_collectibles:
        if coll[3]:
            continue
        mdist = math.sqrt((burrb_x - coll[0]) ** 2 + (burrb_y - coll[1]) ** 2)
        if mdist < MAGNET_RADIUS:
            cx = int(coll[0] - cam_x)
            cy = int(coll[1] - cam_y)
            pygame.draw.line(
                mg_surf, (100, 150, 255, mg_alpha), (bsx, bsy), (cx, cy), 1
            )
    surface.blit(mg_surf, (0, 0))


def draw_fire_trail(surface, cam_x, cam_y, fire_trail):
    """Orange/red flames on the ground."""
    for ft in fire_trail:
        ftx = int(ft[0] - cam_x)
        fty = int(ft[1] - cam_y)
        if -20 < ftx < SCREEN_WIDTH + 20 and -20 < fty < SCREEN_HEIGHT + 20:
            ft_alpha = min(200, ft[2] * 5)
            ft_surf = pygame.Surface((20, 20), pygame.SRCALPHA)
            pygame.draw.circle(ft_surf, (255, 100, 20, ft_alpha), (10, 10), 8)
            pygame.draw.circle(ft_surf, (255, 200, 50, ft_alpha // 2), (10, 8), 5)
            surface.blit(ft_surf, (ftx - 10, fty - 10))


def draw_fire_dash_trail(
    surface, burrb_x, burrb_y, cam_x, cam_y, burrb_angle, fire_dash_active
):
    """Fire trail on the burrb during a Fire Dash."""
    if fire_dash_active <= 0:
        return
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y)
    for ti in range(3):
        to = (ti + 1) * 8
        ta = 160 - ti * 50
        tx_p = bsx - int(math.cos(burrb_angle) * to)
        ty_p = bsy - int(math.sin(burrb_angle) * to)
        t_surf = pygame.Surface((16, 16), pygame.SRCALPHA)
        pygame.draw.rect(t_surf, (255, 120, 30, ta), (0, 0, 16, 16), border_radius=4)
        surface.blit(t_surf, (tx_p - 8, ty_p - 8))


def draw_ice_walls(surface, cam_x, cam_y, ice_walls):
    """Blue-white ice wall blocks."""
    for iw in ice_walls:
        iwx = int(iw[0] - cam_x)
        iwy = int(iw[1] - cam_y)
        if -30 < iwx < SCREEN_WIDTH + 30 and -30 < iwy < SCREEN_HEIGHT + 30:
            iw_alpha = min(200, iw[2])
            iw_surf = pygame.Surface((22, 22), pygame.SRCALPHA)
            pygame.draw.rect(
                iw_surf,
                (150, 200, 255, iw_alpha),
                (0, 0, 22, 22),
                border_radius=4,
            )
            pygame.draw.rect(
                iw_surf,
                (200, 230, 255, iw_alpha),
                (3, 3, 16, 16),
                border_radius=3,
            )
            pygame.draw.rect(
                iw_surf,
                (100, 160, 220, iw_alpha),
                (0, 0, 22, 22),
                2,
                border_radius=4,
            )
            surface.blit(iw_surf, (iwx - 11, iwy - 11))


def draw_blizzard(surface, burrb_x, burrb_y, cam_x, cam_y, blizzard_timer):
    """Swirling snow + blue overlay for Blizzard."""
    if blizzard_timer <= 0:
        return
    bz_surf = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    bz_alpha = min(60, blizzard_timer)
    bz_surf.fill((180, 200, 255, bz_alpha // 3))
    t_val = pygame.time.get_ticks() * 0.002
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y)
    for si in range(15):
        sa = t_val * 4 + si * 0.4
        sr = 30 + si * 14
        sx_p = bsx + int(math.cos(sa) * sr)
        sy_p = bsy + int(math.sin(sa) * sr)
        pygame.draw.circle(bz_surf, (230, 240, 255, bz_alpha * 2), (sx_p, sy_p), 3)
    surface.blit(bz_surf, (0, 0))


def draw_snow_cloak(
    surface, burrb_x, burrb_y, cam_x, cam_y, bounce_y_offset, snow_cloak_timer
):
    """Draw the burrb as a rolling snowball during Snow Cloak."""
    if snow_cloak_timer <= 0:
        return
    sc_roll = pygame.time.get_ticks() * 0.01
    bsx = int(burrb_x - cam_x)
    bsy = int(burrb_y - cam_y + bounce_y_offset)
    pygame.draw.circle(surface, (230, 235, 245), (bsx, bsy), 12)
    pygame.draw.circle(surface, (210, 220, 235), (bsx, bsy), 12, 2)
    # Rolling detail lines
    for ri in range(3):
        ra = sc_roll + ri * 2.1
        rx = bsx + int(math.cos(ra) * 6)
        ry = bsy + int(math.sin(ra) * 6)
        pygame.draw.circle(surface, (200, 210, 225), (rx, ry), 2)


def draw_poison_clouds(surface, cam_x, cam_y, poison_clouds, POISON_CLOUD_RADIUS):
    """Green toxic clouds."""
    for pc in poison_clouds:
        pcx = int(pc[0] - cam_x)
        pcy = int(pc[1] - cam_y)
        if -80 < pcx < SCREEN_WIDTH + 80 and -80 < pcy < SCREEN_HEIGHT + 80:
            pc_alpha = min(120, pc[2] // 2)
            pc_surf = pygame.Surface(
                (POISON_CLOUD_RADIUS * 2 + 20, POISON_CLOUD_RADIUS * 2 + 20),
                pygame.SRCALPHA,
            )
            cx = POISON_CLOUD_RADIUS + 10
            cy = POISON_CLOUD_RADIUS + 10
            t_val = pygame.time.get_ticks() * 0.002
            # Multiple overlapping circles for cloud effect
            for ci in range(5):
                ca = t_val + ci * 1.3
                cr = POISON_CLOUD_RADIUS // 2 + int(math.sin(ca) * 10)
                cox = cx + int(math.cos(ca * 0.7) * 15)
                coy = cy + int(math.sin(ca * 0.5) * 15)
                pygame.draw.circle(pc_surf, (40, 180, 40, pc_alpha), (cox, coy), cr)
            surface.blit(
                pc_surf,
                (
                    pcx - POISON_CLOUD_RADIUS - 10,
                    pcy - POISON_CLOUD_RADIUS - 10,
                ),
            )


def draw_swamp_monster(
    surface,
    cam_x,
    cam_y,
    swamp_monster_active,
    swamp_monster_x,
    swamp_monster_y,
    swamp_monster_walk,
    inside_building,
):
    """Draw the swamp monster ally."""
    if not swamp_monster_active or inside_building is not None:
        return
    smx = int(swamp_monster_x - cam_x)
    smy = int(swamp_monster_y - cam_y)
    if -40 < smx < SCREEN_WIDTH + 40 and -40 < smy < SCREEN_HEIGHT + 40:
        # Dark green body
        pygame.draw.ellipse(surface, (30, 100, 40), (smx - 12, smy - 8, 24, 16))
        # Eyes (red and glowing)
        pygame.draw.circle(surface, (255, 50, 50), (smx - 5, smy - 6), 3)
        pygame.draw.circle(surface, (255, 50, 50), (smx + 5, smy - 6), 3)
        pygame.draw.circle(surface, (255, 150, 150), (smx - 5, smy - 6), 1)
        pygame.draw.circle(surface, (255, 150, 150), (smx + 5, smy - 6), 1)
        # 4 legs
        leg_off = math.sin(swamp_monster_walk * 0.3) * 3
        pygame.draw.line(
            surface,
            (20, 80, 30),
            (smx - 8, smy + 4),
            (smx - 12, smy + 10 + leg_off),
            2,
        )
        pygame.draw.line(
            surface,
            (20, 80, 30),
            (smx + 8, smy + 4),
            (smx + 12, smy + 10 - leg_off),
            2,
        )
        pygame.draw.line(
            surface,
            (20, 80, 30),
            (smx - 4, smy + 6),
            (smx - 6, smy + 12 - leg_off),
            2,
        )
        pygame.draw.line(
            surface,
            (20, 80, 30),
            (smx + 4, smy + 6),
            (smx + 6, smy + 12 + leg_off),
            2,
        )


def draw_soda_cans(surface, cam_x, cam_y, soda_cans, inside_building):
    """Draw soda can monsters."""
    if not soda_cans or inside_building is not None:
        return
    for can in soda_cans:
        cx = int(can["x"] - cam_x)
        cy = int(can["y"] - cam_y)
        if cx < -30 or cx > SCREEN_WIDTH + 30 or cy < -30 or cy > SCREEN_HEIGHT + 30:
            continue
        wf = can["walk"]
        leg_off = math.sin(wf * 0.4) * 2

        # Tiny legs (2 on each side, animated!)
        pygame.draw.line(
            surface,
            (60, 60, 60),
            (cx - 4, cy + 7),
            (cx - 6, cy + 11 + leg_off),
            2,
        )
        pygame.draw.line(
            surface,
            (60, 60, 60),
            (cx + 4, cy + 7),
            (cx + 6, cy + 11 - leg_off),
            2,
        )

        # Soda can body (red cylinder shape)
        pygame.draw.rect(
            surface, (200, 30, 30), (cx - 5, cy - 8, 10, 16), border_radius=3
        )
        # Silver top and bottom (like a real can)
        pygame.draw.rect(
            surface,
            (180, 180, 190),
            (cx - 5, cy - 8, 10, 3),
            border_radius=2,
        )
        pygame.draw.rect(
            surface,
            (180, 180, 190),
            (cx - 5, cy + 5, 10, 3),
            border_radius=2,
        )
        # White label stripe
        pygame.draw.rect(surface, (240, 240, 240), (cx - 4, cy - 2, 8, 4))
        # Outline
        pygame.draw.rect(
            surface,
            (120, 15, 15),
            (cx - 5, cy - 8, 10, 16),
            1,
            border_radius=3,
        )

        # Angry face on the can!
        # Eyes (little white dots with black pupils)
        pygame.draw.circle(surface, (255, 255, 255), (cx - 2, cy - 4), 2)
        pygame.draw.circle(surface, (255, 255, 255), (cx + 2, cy - 4), 2)
        pygame.draw.circle(surface, (0, 0, 0), (cx - 2, cy - 4), 1)
        pygame.draw.circle(surface, (0, 0, 0), (cx + 2, cy - 4), 1)
        # Angry eyebrows
        pygame.draw.line(surface, (0, 0, 0), (cx - 4, cy - 7), (cx - 1, cy - 6), 1)
        pygame.draw.line(surface, (0, 0, 0), (cx + 4, cy - 7), (cx + 1, cy - 6), 1)
        # Grumpy mouth
        pygame.draw.line(surface, (0, 0, 0), (cx - 2, cy + 2), (cx + 2, cy + 2), 1)
