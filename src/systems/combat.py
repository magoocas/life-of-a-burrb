"""
Combat system for Life of a Burrb.

Handles:
- Tongue mechanics (extend, hit detection, retract)
- NPC attack / damage to player
- Knockback for player and NPCs
- Death and respawn logic
"""

import math

from src.constants import WORLD_WIDTH, WORLD_HEIGHT
from src.settings import SPAWN_X, SPAWN_Y
from src.entities.player import MAX_HP, HURT_COOLDOWN_TIME


# ── Tongue ──────────────────────────────────────────────────────────────────


def update_tongue(
    tongue_active,
    tongue_length,
    tongue_retracting,
    tongue_hit_npc,
    tongue_angle,
    tongue_speed,
    tongue_max_length,
    mega_tongue_unlocked,
    burrb_x,
    burrb_y,
    npcs,
):
    """Advance the tongue by one frame.

    Returns updated (tongue_active, tongue_length, tongue_retracting,
    tongue_hit_npc).
    """
    if not tongue_active:
        return tongue_active, tongue_length, tongue_retracting, tongue_hit_npc

    effective_max = tongue_max_length * (2.0 if mega_tongue_unlocked else 1.0)

    if not tongue_retracting:
        tongue_length += tongue_speed
        if tongue_length >= effective_max:
            tongue_retracting = True

        # Check if tongue tip hit any NPC!
        tip_x = burrb_x + math.cos(tongue_angle) * tongue_length
        tip_y = burrb_y + math.sin(tongue_angle) * tongue_length
        for npc in npcs:
            if npc.npc_type == "rock" or not npc.alive:
                continue
            ddx = npc.x - tip_x
            ddy = npc.y - tip_y
            hit_dist = math.sqrt(ddx * ddx + ddy * ddy)
            if hit_dist < 16:  # close enough = hit!
                npc.hp -= 1
                npc.hurt_flash = 15
                tongue_hit_npc = npc
                tongue_retracting = True
                # Knock them back away from the player!
                if hit_dist > 1:
                    npc.x += (ddx / hit_dist) * 20
                    npc.y += (ddy / hit_dist) * 20
                    npc.x = max(30, min(WORLD_WIDTH - 30, npc.x))
                    npc.y = max(30, min(WORLD_HEIGHT - 30, npc.y))
                if npc.hp <= 0:
                    npc.alive = False
                break
    else:
        # Tongue is retracting
        tongue_length -= tongue_speed * 1.5
        if tongue_length <= 0:
            tongue_length = 0
            tongue_active = False
            tongue_hit_npc = None

    return tongue_active, tongue_length, tongue_retracting, tongue_hit_npc


# ── NPC Attacks on Player ────────────────────────────────────────────────────


def update_npc_attacks(
    burrb_x,
    burrb_y,
    npcs,
    player_hp,
    hurt_timer,
    hurt_cooldown,
    inside_building,
    death_timer,
):
    """Check if any aggressive NPC is attacking the player.

    Returns updated (burrb_x, burrb_y, player_hp, hurt_timer, hurt_cooldown).
    """
    if hurt_cooldown > 0:
        hurt_cooldown -= 1
    if hurt_timer > 0:
        hurt_timer -= 1

    if inside_building is not None or death_timer > 0:
        return burrb_x, burrb_y, player_hp, hurt_timer, hurt_cooldown

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
                player_hp -= 1
                hurt_timer = 20
                hurt_cooldown = HURT_COOLDOWN_TIME
                npc.attack_cooldown = 40
                # Knock the player back!
                if adist > 1:
                    burrb_x += (adx / adist) * 15
                    burrb_y += (ady / adist) * 15
                    burrb_x = max(20, min(WORLD_WIDTH - 20, burrb_x))
                    burrb_y = max(20, min(WORLD_HEIGHT - 20, burrb_y))

    return burrb_x, burrb_y, player_hp, hurt_timer, hurt_cooldown


# ── Death and Respawn ────────────────────────────────────────────────────────


def update_death_and_respawn(player_hp, death_timer, hurt_cooldown, hurt_timer):
    """Handle the death animation and respawn.

    Returns updated (burrb_x, burrb_y, player_hp, death_timer,
    hurt_cooldown, hurt_timer, respawned).
    respawned is True on the frame the player comes back to life.
    """
    new_x = None
    new_y = None
    respawned = False

    if player_hp <= 0 and death_timer <= 0:
        death_timer = 120  # 2 seconds of death animation
        player_hp = 0

    if death_timer > 0:
        death_timer -= 1
        if death_timer <= 0:
            # Respawn!
            player_hp = MAX_HP
            new_x = float(SPAWN_X)
            new_y = float(SPAWN_Y)
            hurt_cooldown = 120
            hurt_timer = 0
            respawned = True

    return new_x, new_y, player_hp, death_timer, hurt_cooldown, hurt_timer, respawned
