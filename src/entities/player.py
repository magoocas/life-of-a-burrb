"""
Player class for Life of a Burrb.
Encapsulates all state belonging to the player-controlled burrb:
position, HP, movement, tongue, currencies, interior state, timers.
"""

from src.constants import WORLD_WIDTH, WORLD_HEIGHT
from src.settings import SPAWN_X, SPAWN_Y


# Health constant
MAX_HP = 5

# Hurt/invincibility timing
HURT_COOLDOWN_TIME = 60  # 1 second of invincibility after each hit


class Player:
    """
    The player-controlled burrb character.
    All mutable state for the burrb lives here so it can be passed
    around and reset cleanly (e.g. on death/respawn).
    """

    def __init__(self):
        # --- Position & movement ---
        self.x = float(WORLD_WIDTH // 2)
        self.y = float(WORLD_HEIGHT // 2)
        self.speed = 3
        self.facing_left = False
        self.walk_frame = 0
        self.is_walking = False
        self.angle = 0.0  # direction the burrb is looking (radians)

        # --- Health ---
        self.hp = MAX_HP
        self.hurt_timer = 0  # frames of red flash when hit
        self.hurt_cooldown = 0  # invincibility frames after a hit
        self.death_timer = 0  # frames of "you died" animation (0 = alive)

        # --- Tongue ---
        self.tongue_active = False
        self.tongue_length = 0.0
        self.tongue_max_length = 120.0
        self.tongue_speed = 8.0
        self.tongue_retracting = False
        self.tongue_angle = 0.0
        self.tongue_hit_npc = None  # visual feedback target

        # --- Building interior state ---
        self.inside_building = None  # Building object or None
        self.interior_x = 0.0
        self.interior_y = 0.0
        self.saved_outdoor_x = 0.0
        self.saved_outdoor_y = 0.0
        self.saved_outdoor_angle = 0.0

        # --- Currencies ---
        self.chips_collected = 2  # potato chips (city currency)
        self.berries_collected = 0  # forest currency
        self.gems_collected = 0  # desert currency
        self.snowflakes_collected = 0  # snow currency
        self.mushrooms_collected = 0  # swamp currency

    def respawn(self):
        """Reset the burrb to the spawn point after death."""
        self.x = float(SPAWN_X)
        self.y = float(SPAWN_Y)
        self.hp = MAX_HP
        self.hurt_timer = 0
        self.hurt_cooldown = 0
        self.death_timer = 0
        self.tongue_active = False
        self.tongue_length = 0.0
        self.tongue_retracting = False
        self.tongue_hit_npc = None
        self.inside_building = None
