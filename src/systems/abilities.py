"""
Ability system for Life of a Burrb.

AbilityManager owns all ability state: unlock flags, timers, cooldowns,
and per-frame update logic for all 21 abilities (9 chip + 12 biome).
"""

import math
import random

from src.constants import WORLD_WIDTH, WORLD_HEIGHT


# ── Ability definitions ──────────────────────────────────────────────────────

ABILITIES = [
    ("Dash", 2, "SHIFT", "Zoom forward super fast!"),
    ("Super Speed", 3, "SHIFT hold", "Run way faster!"),
    ("Mega Tongue", 3, "auto", "Tongue reaches 2x farther!"),
    ("Freeze", 4, "F", "Freeze all nearby burrbs!"),
    ("Invisibility", 5, "I", "Turn invisible for 5 sec!"),
    ("Giant Mode", 6, "G", "Become HUGE for 8 sec!"),
    ("Bounce", 4, "B", "Jump over buildings!"),
    ("Teleport", 5, "T", "Warp forward instantly!"),
    ("Earthquake", 7, "Q", "Stun everything nearby!"),
]

BIOME_ABILITIES = [
    # --- Forest abilities (berries) ---
    ("Vine Trap", 3, "V", "Trap nearby burrbs in vines!", "berry"),
    ("Camouflage", 4, "C", "Blend into the ground!", "berry"),
    ("Nature Heal", 5, "H", "Push enemies away!", "berry"),
    # --- Desert abilities (gems) ---
    ("Sandstorm", 4, "N", "Blind all nearby burrbs!", "gem"),
    ("Magnet", 3, "M", "Pull collectibles toward you!", "gem"),
    ("Fire Dash", 5, "R", "Dash with a trail of fire!", "gem"),
    # --- Snow abilities (snowflakes) ---
    ("Ice Wall", 3, "L", "Create a wall of ice!", "snowflake"),
    ("Blizzard", 5, "Z", "Freeze AND push burrbs!", "snowflake"),
    ("Snow Cloak", 4, "X", "Roll fast as a snowball!", "snowflake"),
    # --- Swamp abilities (mushrooms) ---
    ("Poison Cloud", 3, "P", "Leave a toxic cloud!", "mushroom"),
    ("Shadow Step", 4, "J", "Teleport to nearest shadow!", "mushroom"),
    ("Swamp Monster", 6, "K", "Summon a monster ally!", "mushroom"),
]

# Duration constants (frames at 60 FPS)
BOUNCE_DURATION = 45
TELEPORT_DISTANCE = 200
EARTHQUAKE_DURATION = 240
EARTHQUAKE_RADIUS = 300

VINE_TRAP_DURATION = 240
VINE_TRAP_RADIUS = 200
CAMOUFLAGE_DURATION = 300
NATURE_HEAL_RADIUS = 250
SANDSTORM_DURATION = 240
SANDSTORM_RADIUS = 300
MAGNET_DURATION = 300
MAGNET_RADIUS = 400
BLIZZARD_DURATION = 180
BLIZZARD_RADIUS = 250
SNOW_CLOAK_DURATION = 300
POISON_CLOUD_DURATION = 360
POISON_CLOUD_RADIUS = 60
SWAMP_MONSTER_DURATION = 600
SWAMP_MONSTER_SPEED = 2.0
SWAMP_MONSTER_RADIUS = 300
SODA_CAN_DURATION = 480
SODA_CAN_SPEED = 2.8
SODA_CAN_RADIUS = 250
SODA_CAN_COOLDOWN_TIME = 300


class AbilityManager:
    """Holds state and runs per-frame updates for all abilities."""

    def __init__(self):
        # Unlock state
        self.ability_unlocked = [False] * len(ABILITIES)
        self.biome_ability_unlocked = [False] * len(BIOME_ABILITIES)

        # Chip abilities
        self.dash_cooldown = 0
        self.dash_active = 0
        self.freeze_timer = 0
        self.invisible_timer = 0
        self.giant_timer = 0
        self.giant_scale = 1.0
        self.bounce_timer = 0
        self.bounce_cooldown = 0
        self.bounce_height = 0.0
        self.teleport_cooldown = 0
        self.teleport_flash = 0
        self.earthquake_timer = 0
        self.earthquake_cooldown = 0
        self.earthquake_shake = 0

        # Biome abilities
        self.vine_trap_timer = 0
        self.vine_trap_cooldown = 0
        self.camouflage_timer = 0
        self.nature_heal_timer = 0
        self.nature_heal_cooldown = 0
        self.sandstorm_timer = 0
        self.sandstorm_cooldown = 0
        self.magnet_timer = 0
        self.magnet_cooldown = 0
        self.fire_dash_active = 0
        self.fire_dash_cooldown = 0
        self.fire_trail = []  # list of [x, y, timer]
        self.ice_wall_cooldown = 0
        self.ice_walls = []  # list of [x, y, timer]
        self.blizzard_timer = 0
        self.blizzard_cooldown = 0
        self.snow_cloak_timer = 0
        self.snow_cloak_cooldown = 0
        self.poison_clouds = []  # list of [x, y, timer]
        self.poison_cooldown = 0
        self.shadow_step_cooldown = 0
        self.swamp_monster_active = False
        self.swamp_monster_x = 0.0
        self.swamp_monster_y = 0.0
        self.swamp_monster_timer = 0
        self.swamp_monster_walk = 0

        # Soda cans (free starter ability)
        self.soda_cans = []  # list of dicts
        self.soda_can_cooldown = 0

    # ── Helpers ──────────────────────────────────────────────────────────────

    def _countdown(self, attr):
        """Decrement a timer attribute if > 0."""
        val = getattr(self, attr)
        if val > 0:
            setattr(self, attr, val - 1)

    # ── Per-frame update ─────────────────────────────────────────────────────

    def update(self, burrb_x, burrb_y, npcs, biome_collectibles, inside_building, keys):
        """Run all ability timers and AI for one frame.

        `keys` is the result of pygame.key.get_pressed().
        Returns speed_mult (float) that should modify player speed.
        """
        # ---- Chip ability timers ----
        self._countdown("dash_cooldown")
        self._countdown("dash_active")
        self._countdown("freeze_timer")
        self._countdown("invisible_timer")
        self._countdown("giant_timer")

        # Bounce
        if self.bounce_timer > 0:
            self.bounce_timer -= 1
            t = self.bounce_timer / BOUNCE_DURATION
            self.bounce_height = math.sin(t * math.pi) * 80
        else:
            self.bounce_height = 0.0
        self._countdown("bounce_cooldown")

        self._countdown("teleport_cooldown")
        self._countdown("teleport_flash")

        # Earthquake
        if self.earthquake_timer > 0:
            self.earthquake_timer -= 1
            if self.earthquake_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock":
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        self._countdown("earthquake_cooldown")
        self._countdown("earthquake_shake")

        # Smooth giant scale
        target_giant = 2.5 if self.giant_timer > 0 else 1.0
        self.giant_scale += (target_giant - self.giant_scale) * 0.15

        # ---- Biome ability timers ----

        # Vine trap
        if self.vine_trap_timer > 0:
            self.vine_trap_timer -= 1
            if self.vine_trap_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        self._countdown("vine_trap_cooldown")

        self._countdown("camouflage_timer")
        self._countdown("nature_heal_timer")
        self._countdown("nature_heal_cooldown")

        # Sandstorm
        if self.sandstorm_timer > 0:
            self.sandstorm_timer -= 1
            if self.sandstorm_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed < 0.5:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        self._countdown("sandstorm_cooldown")

        # Magnet - pull uncollected biome collectibles toward player
        if self.magnet_timer > 0:
            self.magnet_timer -= 1
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
        self._countdown("magnet_cooldown")

        # Fire dash
        if self.fire_dash_active > 0:
            self.fire_dash_active -= 1
            if inside_building is None:
                self.fire_trail.append([burrb_x, burrb_y, 60])
        self._countdown("fire_dash_cooldown")
        # Age fire trail
        for ft in self.fire_trail:
            ft[2] -= 1
        self.fire_trail = [ft for ft in self.fire_trail if ft[2] > 0]
        # Fire damages NPCs
        for ft in self.fire_trail:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                fd = math.sqrt((npc.x - ft[0]) ** 2 + (npc.y - ft[1]) ** 2)
                if fd < 15 and fd > 1:
                    npc.x += ((npc.x - ft[0]) / fd) * 5
                    npc.y += ((npc.y - ft[1]) / fd) * 5

        # Ice walls
        for iw in self.ice_walls:
            iw[2] -= 1
        self.ice_walls = [iw for iw in self.ice_walls if iw[2] > 0]
        self._countdown("ice_wall_cooldown")
        # Ice walls block NPCs
        for iw in self.ice_walls:
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                wd = math.sqrt((npc.x - iw[0]) ** 2 + (npc.y - iw[1]) ** 2)
                if wd < 20 and wd > 1:
                    npc.x += ((npc.x - iw[0]) / wd) * 3
                    npc.y += ((npc.y - iw[1]) / wd) * 3

        # Blizzard
        if self.blizzard_timer > 0:
            self.blizzard_timer -= 1
            if self.blizzard_timer <= 0:
                for npc in npcs:
                    if npc.npc_type != "rock" and npc.speed == 0.0:
                        npc.speed = random.uniform(0.5, 1.5)
                        npc.dir_timer = random.randint(30, 120)
        self._countdown("blizzard_cooldown")
        self._countdown("snow_cloak_timer")
        self._countdown("snow_cloak_cooldown")

        # Poison clouds
        for pc in self.poison_clouds:
            pc[2] -= 1
            for npc in npcs:
                if npc.npc_type == "rock":
                    continue
                pd = math.sqrt((npc.x - pc[0]) ** 2 + (npc.y - pc[1]) ** 2)
                if pd < POISON_CLOUD_RADIUS and pd > 1:
                    npc.x += ((npc.x - pc[0]) / pd) * 2
                    npc.y += ((npc.y - pc[1]) / pd) * 2
        self.poison_clouds = [pc for pc in self.poison_clouds if pc[2] > 0]
        self._countdown("poison_cooldown")
        self._countdown("shadow_step_cooldown")

        # Swamp monster AI
        if self.swamp_monster_active:
            self.swamp_monster_timer -= 1
            self.swamp_monster_walk += 1
            if self.swamp_monster_timer <= 0:
                self.swamp_monster_active = False
            else:
                nearest_npc = None
                nearest_dist = SWAMP_MONSTER_RADIUS
                for npc in npcs:
                    if npc.npc_type == "rock":
                        continue
                    md = math.sqrt(
                        (npc.x - self.swamp_monster_x) ** 2
                        + (npc.y - self.swamp_monster_y) ** 2
                    )
                    if md < nearest_dist:
                        nearest_dist = md
                        nearest_npc = npc
                if nearest_npc is not None:
                    md = nearest_dist
                    if md > 1:
                        self.swamp_monster_x += (
                            (nearest_npc.x - self.swamp_monster_x) / md
                        ) * SWAMP_MONSTER_SPEED
                        self.swamp_monster_y += (
                            (nearest_npc.y - self.swamp_monster_y) / md
                        ) * SWAMP_MONSTER_SPEED
                    if md < 20 and md > 1:
                        nearest_npc.x += (
                            (nearest_npc.x - self.swamp_monster_x) / md
                        ) * 8
                        nearest_npc.y += (
                            (nearest_npc.y - self.swamp_monster_y) / md
                        ) * 8
                else:
                    fd = math.sqrt(
                        (burrb_x - self.swamp_monster_x) ** 2
                        + (burrb_y - self.swamp_monster_y) ** 2
                    )
                    if fd > 50 and fd > 1:
                        self.swamp_monster_x += (
                            (burrb_x - self.swamp_monster_x) / fd
                        ) * SWAMP_MONSTER_SPEED
                        self.swamp_monster_y += (
                            (burrb_y - self.swamp_monster_y) / fd
                        ) * SWAMP_MONSTER_SPEED

        # Soda can AI
        self._countdown("soda_can_cooldown")
        for can in self.soda_cans:
            can["timer"] -= 1
            can["walk"] += 1
            if can["attack_cd"] > 0:
                can["attack_cd"] -= 1
        self.soda_cans = [c for c in self.soda_cans if c["timer"] > 0]
        for can in self.soda_cans:
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
                if md < 14 and can["attack_cd"] <= 0:
                    nearest_npc.hp -= 1
                    nearest_npc.hurt_flash = 15
                    can["attack_cd"] = 30
                    if md > 1:
                        nearest_npc.x += ((nearest_npc.x - can["x"]) / md) * 10
                        nearest_npc.y += ((nearest_npc.y - can["y"]) / md) * 10
                        nearest_npc.x = max(30, min(WORLD_WIDTH - 30, nearest_npc.x))
                        nearest_npc.y = max(30, min(WORLD_HEIGHT - 30, nearest_npc.y))
                    if nearest_npc.hp <= 0:
                        nearest_npc.alive = False
            else:
                fd = math.sqrt((burrb_x - can["x"]) ** 2 + (burrb_y - can["y"]) ** 2)
                if fd > 40 and fd > 1:
                    can["x"] += ((burrb_x - can["x"]) / fd) * SODA_CAN_SPEED
                    can["y"] += ((burrb_y - can["y"]) / fd) * SODA_CAN_SPEED

        # ---- Speed multiplier ----
        import pygame  # local import to avoid circular issues at module level

        speed_mult = 1.0
        if self.ability_unlocked[1] and keys[pygame.K_LSHIFT]:
            speed_mult = 2.2
        # Dash activation
        if self.ability_unlocked[0] and not self.ability_unlocked[1]:
            if (
                keys[pygame.K_LSHIFT]
                and self.dash_cooldown <= 0
                and self.dash_active <= 0
            ):
                self.dash_active = 12
                self.dash_cooldown = 45
        if self.ability_unlocked[0] and self.ability_unlocked[1]:
            if (
                keys[pygame.K_LSHIFT]
                and self.dash_cooldown <= 0
                and self.dash_active <= 0
            ):
                self.dash_active = 12
                self.dash_cooldown = 45
        if self.dash_active > 0:
            speed_mult = max(speed_mult, 4.0)
        if self.fire_dash_active > 0:
            speed_mult = max(speed_mult, 5.0)
        if self.snow_cloak_timer > 0:
            speed_mult = max(speed_mult, 3.0)
        if self.giant_timer > 0:
            speed_mult *= 0.8

        return speed_mult

    # ── Activation helpers called from input handling ─────────────────────────

    def activate_freeze(self):
        if self.ability_unlocked[3] and self.freeze_timer <= 0:
            self.freeze_timer = 300

    def activate_invisible(self):
        if self.ability_unlocked[4] and self.invisible_timer <= 0:
            self.invisible_timer = 300

    def activate_giant(self):
        if self.ability_unlocked[5] and self.giant_timer <= 0:
            self.giant_timer = 480

    def activate_bounce(self, inside_building):
        if (
            self.ability_unlocked[6]
            and self.bounce_timer <= 0
            and self.bounce_cooldown <= 0
            and inside_building is None
        ):
            self.bounce_timer = BOUNCE_DURATION
            self.bounce_cooldown = 60

    def activate_teleport(
        self, burrb_x, burrb_y, burrb_angle, inside_building, buildings
    ):
        """Attempt a teleport. Returns (new_x, new_y) or (burrb_x, burrb_y) unchanged."""
        from src.systems.collision import can_move_to as _can_move_to

        if not (
            self.ability_unlocked[7]
            and self.teleport_cooldown <= 0
            and inside_building is None
        ):
            return burrb_x, burrb_y
        tp_x = burrb_x + math.cos(burrb_angle) * TELEPORT_DISTANCE
        tp_y = burrb_y + math.sin(burrb_angle) * TELEPORT_DISTANCE
        tp_x = max(30, min(WORLD_WIDTH - 30, tp_x))
        tp_y = max(30, min(WORLD_HEIGHT - 30, tp_y))
        if not _can_move_to(tp_x, tp_y, buildings):
            for shrink in range(1, 10):
                shorter = TELEPORT_DISTANCE * (1.0 - shrink * 0.1)
                test_x = burrb_x + math.cos(burrb_angle) * shorter
                test_y = burrb_y + math.sin(burrb_angle) * shorter
                test_x = max(30, min(WORLD_WIDTH - 30, test_x))
                test_y = max(30, min(WORLD_HEIGHT - 30, test_y))
                if _can_move_to(test_x, test_y, buildings):
                    tp_x = test_x
                    tp_y = test_y
                    break
            else:
                tp_x = burrb_x
                tp_y = burrb_y
        self.teleport_cooldown = 90
        self.teleport_flash = 15
        return tp_x, tp_y

    def activate_earthquake(self, burrb_x, burrb_y, npcs, cars, inside_building):
        if not (
            self.ability_unlocked[8]
            and self.earthquake_timer <= 0
            and self.earthquake_cooldown <= 0
            and inside_building is None
        ):
            return
        self.earthquake_timer = EARTHQUAKE_DURATION
        self.earthquake_cooldown = 360
        self.earthquake_shake = 30
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

    def activate_vine_trap(self, burrb_x, burrb_y, npcs, inside_building):
        if not (
            self.biome_ability_unlocked[0]
            and self.vine_trap_timer <= 0
            and self.vine_trap_cooldown <= 0
            and inside_building is None
        ):
            return
        self.vine_trap_timer = VINE_TRAP_DURATION
        self.vine_trap_cooldown = 300
        for npc in npcs:
            if npc.npc_type == "rock":
                continue
            vd = math.sqrt((npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2)
            if vd < VINE_TRAP_RADIUS:
                npc.speed = 0.0
                npc.dir_timer = VINE_TRAP_DURATION

    def activate_camouflage(self):
        if self.biome_ability_unlocked[1] and self.camouflage_timer <= 0:
            self.camouflage_timer = CAMOUFLAGE_DURATION

    def activate_nature_heal(self, burrb_x, burrb_y, npcs, inside_building):
        if not (
            self.biome_ability_unlocked[2]
            and self.nature_heal_timer <= 0
            and self.nature_heal_cooldown <= 0
            and inside_building is None
        ):
            return
        self.nature_heal_timer = 30
        self.nature_heal_cooldown = 300
        for npc in npcs:
            if npc.npc_type == "rock":
                continue
            hd = math.sqrt((npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2)
            if hd < NATURE_HEAL_RADIUS and hd > 1:
                push_str = 40
                npc.x += ((npc.x - burrb_x) / hd) * push_str
                npc.y += ((npc.y - burrb_y) / hd) * push_str

    def activate_sandstorm(self, burrb_x, burrb_y, npcs, inside_building):
        if not (
            self.biome_ability_unlocked[3]
            and self.sandstorm_timer <= 0
            and self.sandstorm_cooldown <= 0
            and inside_building is None
        ):
            return
        self.sandstorm_timer = SANDSTORM_DURATION
        self.sandstorm_cooldown = 360
        for npc in npcs:
            if npc.npc_type == "rock":
                continue
            sd = math.sqrt((npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2)
            if sd < SANDSTORM_RADIUS:
                npc.speed = 0.3
                npc.dir_timer = SANDSTORM_DURATION

    def activate_magnet(self):
        if (
            self.biome_ability_unlocked[4]
            and self.magnet_timer <= 0
            and self.magnet_cooldown <= 0
        ):
            self.magnet_timer = MAGNET_DURATION
            self.magnet_cooldown = 360

    def activate_fire_dash(self, inside_building):
        if (
            self.biome_ability_unlocked[5]
            and self.fire_dash_active <= 0
            and self.fire_dash_cooldown <= 0
            and inside_building is None
        ):
            self.fire_dash_active = 20
            self.fire_dash_cooldown = 90

    def activate_ice_wall(self, burrb_x, burrb_y, burrb_angle, inside_building):
        if not (
            self.biome_ability_unlocked[6]
            and self.ice_wall_cooldown <= 0
            and inside_building is None
        ):
            return
        self.ice_wall_cooldown = 180
        perp = burrb_angle + math.pi / 2
        wall_dist = 40
        cx = burrb_x + math.cos(burrb_angle) * wall_dist
        cy = burrb_y + math.sin(burrb_angle) * wall_dist
        for seg in range(-2, 3):
            wx = cx + math.cos(perp) * seg * 25
            wy = cy + math.sin(perp) * seg * 25
            self.ice_walls.append([wx, wy, 480])

    def activate_blizzard(self, burrb_x, burrb_y, npcs, inside_building):
        if not (
            self.biome_ability_unlocked[7]
            and self.blizzard_timer <= 0
            and self.blizzard_cooldown <= 0
            and inside_building is None
        ):
            return
        self.blizzard_timer = BLIZZARD_DURATION
        self.blizzard_cooldown = 360
        for npc in npcs:
            if npc.npc_type == "rock":
                continue
            bd = math.sqrt((npc.x - burrb_x) ** 2 + (npc.y - burrb_y) ** 2)
            if bd < BLIZZARD_RADIUS:
                npc.speed = 0.0
                npc.dir_timer = BLIZZARD_DURATION
                if bd > 1:
                    npc.x += ((npc.x - burrb_x) / bd) * 25
                    npc.y += ((npc.y - burrb_y) / bd) * 25

    def activate_snow_cloak(self):
        if (
            self.biome_ability_unlocked[8]
            and self.snow_cloak_timer <= 0
            and self.snow_cloak_cooldown <= 0
        ):
            self.snow_cloak_timer = SNOW_CLOAK_DURATION
            self.snow_cloak_cooldown = 360

    def activate_poison_cloud(self, burrb_x, burrb_y, inside_building):
        if (
            self.biome_ability_unlocked[9]
            and self.poison_cooldown <= 0
            and inside_building is None
        ):
            self.poison_cooldown = 240
            self.poison_clouds.append([burrb_x, burrb_y, POISON_CLOUD_DURATION])

    def activate_shadow_step(
        self, burrb_x, burrb_y, biome_objects, trees, inside_building
    ):
        """Returns (new_x, new_y) after teleporting to nearest shadow, or current pos."""
        if not (
            self.biome_ability_unlocked[10]
            and self.shadow_step_cooldown <= 0
            and inside_building is None
        ):
            return burrb_x, burrb_y
        self.shadow_step_cooldown = 120
        best_dist = 999999
        best_x, best_y = burrb_x, burrb_y
        for ox, oy, okind, osize in biome_objects:
            if okind in ("dead_tree", "snow_tree", "cactus"):
                sd = math.sqrt((ox - burrb_x) ** 2 + (oy - burrb_y) ** 2)
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
            self.teleport_flash = 15  # reuse flash effect
            return best_x, best_y
        return burrb_x, burrb_y

    def activate_swamp_monster(self, burrb_x, burrb_y, inside_building):
        if (
            self.biome_ability_unlocked[11]
            and not self.swamp_monster_active
            and inside_building is None
        ):
            self.swamp_monster_active = True
            self.swamp_monster_x = burrb_x + 30
            self.swamp_monster_y = burrb_y + 30
            self.swamp_monster_timer = SWAMP_MONSTER_DURATION
            self.swamp_monster_walk = 0

    def activate_soda_cans(self, burrb_x, burrb_y, inside_building):
        if (
            len(self.soda_cans) == 0
            and self.soda_can_cooldown <= 0
            and inside_building is None
        ):
            for i in range(3):
                angle = i * (2 * math.pi / 3)
                sx = burrb_x + math.cos(angle) * 25
                sy = burrb_y + math.sin(angle) * 25
                self.soda_cans.append(
                    {
                        "x": sx,
                        "y": sy,
                        "timer": SODA_CAN_DURATION,
                        "walk": 0,
                        "attack_cd": 0,
                    }
                )
            self.soda_can_cooldown = SODA_CAN_COOLDOWN_TIME
