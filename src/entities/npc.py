"""
NPC class for Life of a Burrb.
NPCs wander around the world. Aggressive burrbs will chase and attack the player!
"""

import math
import random
import pygame

from src.constants import WORLD_WIDTH, WORLD_HEIGHT
from src.settings import SPAWN_RECT


class NPC:
    """A character that wanders around the city."""

    def __init__(self, x, y, npc_type, color, detail_color):
        self.x = x
        self.y = y
        self.npc_type = npc_type  # "burrb", "human", "cat", "dog"
        self.color = color  # main body color
        self.detail_color = detail_color  # secondary color
        self.speed = random.uniform(0.5, 1.5)
        # Movement direction (in radians)
        self.angle = random.uniform(0, 2 * math.pi)
        # Timer to change direction randomly
        self.dir_timer = random.randint(60, 240)
        self.walk_frame = 0
        # Combat! Some burrbs are aggressive and will attack you!
        # About 40% of burrbs are mean. You can tell because they
        # have angry red eyes.
        self.aggressive = random.random() < 0.4
        self.chase_speed = random.uniform(2.0, 3.0)  # faster when chasing!
        self.chasing = False  # currently chasing the player?
        self.attack_cooldown = 0  # frames until they can hit you again
        # NPC health! Tongue hits hurt them instead of turning them to stone.
        self.hp = 3  # takes 3 tongue hits to knock out
        self.hurt_flash = 0  # frames of red flash when hit
        self.alive = True  # set to False when HP hits 0

    def update(self, player_x=0.0, player_y=0.0, buildings=None):
        """Move the NPC around. This is its simple 'brain'."""
        if buildings is None:
            buildings = []

        # Dead NPCs and rocks don't move!
        if not self.alive or self.npc_type == "rock":
            return

        self.walk_frame += 1
        if self.attack_cooldown > 0:
            self.attack_cooldown -= 1
        if self.hurt_flash > 0:
            self.hurt_flash -= 1

        # --- AGGRESSIVE CHASE BEHAVIOR ---
        # If this burrb is mean and the player is close enough,
        # it will chase you down and try to peck you!
        NPC_SIGHT_RANGE = 200  # how far they can see you
        NPC_LOSE_RANGE = 350  # how far before they give up chasing
        self.chasing = False

        if self.aggressive and self.npc_type == "burrb":
            dx_to_player = player_x - self.x
            dy_to_player = player_y - self.y
            dist_to_player = math.sqrt(dx_to_player**2 + dy_to_player**2)

            # Don't chase if player is in the spawn square (safe zone!)
            player_in_spawn = SPAWN_RECT.collidepoint(player_x, player_y)

            if dist_to_player < NPC_SIGHT_RANGE and not player_in_spawn:
                # CHASE THE PLAYER!
                self.chasing = True
                if dist_to_player > 1:
                    move_x = (dx_to_player / dist_to_player) * self.chase_speed
                    move_y = (dy_to_player / dist_to_player) * self.chase_speed
                    new_x = self.x + move_x
                    new_y = self.y + move_y

                    # Don't run into buildings
                    npc_rect = pygame.Rect(new_x - 6, new_y - 6, 12, 12)
                    blocked = False
                    for b in buildings:
                        if npc_rect.colliderect(b.get_rect()):
                            blocked = True
                            break
                    if new_x < 30 or new_x > WORLD_WIDTH - 30:
                        blocked = True
                    if new_y < 30 or new_y > WORLD_HEIGHT - 30:
                        blocked = True

                    if not blocked:
                        self.x = new_x
                        self.y = new_y
                    # Point toward the player
                    self.angle = math.atan2(dy_to_player, dx_to_player)
                return  # skip normal wandering while chasing

        # --- NORMAL WANDERING ---
        # Count down the direction timer
        self.dir_timer -= 1
        if self.dir_timer <= 0:
            # Pick a new random direction
            self.angle = random.uniform(0, 2 * math.pi)
            self.speed = random.uniform(0.5, 1.5)
            self.dir_timer = random.randint(60, 240)

        # Move in current direction
        new_x = self.x + math.cos(self.angle) * self.speed
        new_y = self.y + math.sin(self.angle) * self.speed

        # Check if they'd walk into a building
        npc_rect = pygame.Rect(new_x - 6, new_y - 6, 12, 12)
        blocked = False
        for b in buildings:
            if npc_rect.colliderect(b.get_rect()):
                blocked = True
                break

        # Stay inside the world
        if new_x < 30 or new_x > WORLD_WIDTH - 30:
            blocked = True
        if new_y < 30 or new_y > WORLD_HEIGHT - 30:
            blocked = True

        if blocked:
            # Turn around and try a new direction
            self.angle = random.uniform(0, 2 * math.pi)
            self.dir_timer = random.randint(30, 120)
        else:
            self.x = new_x
            self.y = new_y


# NPC color palettes - ALL burrbs now! Every color EXCEPT light blue
# because light blue is the player's color.
BURRB_COLORS = [
    ((220, 80, 80), (180, 50, 50)),  # red burrb
    ((80, 200, 80), (40, 150, 40)),  # green burrb
    ((220, 180, 50), (180, 140, 30)),  # yellow burrb
    ((200, 100, 200), (160, 60, 160)),  # purple burrb
    ((220, 140, 60), (180, 100, 30)),  # orange burrb
    ((60, 60, 60), (30, 30, 30)),  # dark/black burrb
    ((240, 240, 240), (200, 200, 200)),  # white burrb
    ((220, 100, 160), (180, 60, 120)),  # pink burrb
    ((160, 120, 60), (120, 80, 30)),  # brown burrb
    ((100, 220, 200), (60, 180, 160)),  # teal burrb
    ((180, 80, 80), (140, 40, 40)),  # dark red burrb
    ((100, 60, 160), (70, 30, 130)),  # indigo burrb
    ((220, 200, 160), (180, 160, 120)),  # cream burrb
    ((50, 120, 50), (30, 80, 30)),  # dark green burrb
    ((200, 60, 200), (160, 30, 160)),  # magenta burrb
]


def spawn_npcs(buildings, count=80):
    """Spawn NPCs throughout the world. Returns a list of NPC objects."""
    npcs = []
    for _ in range(count):
        # Pick a random spot in the world
        nx = random.randint(100, WORLD_WIDTH - 100)
        ny = random.randint(100, WORLD_HEIGHT - 100)

        # Make sure they don't spawn inside a building
        spawn_rect = pygame.Rect(nx - 10, ny - 10, 20, 20)
        in_building = any(spawn_rect.colliderect(b.get_rect()) for b in buildings)
        if in_building:
            continue

        color, detail = random.choice(BURRB_COLORS)
        npcs.append(NPC(nx, ny, "burrb", color, detail))

    return npcs
