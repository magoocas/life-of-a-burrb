"""
Life of a Burrb
A burrb is a bird-like animal that walks around an open world city.
Use arrow keys or WASD to move around!
"""

import pygame
import math
import random

# Initialize pygame - this starts up the game engine
pygame.init()

# Screen settings
SCREEN_WIDTH = 900
SCREEN_HEIGHT = 700
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption("Life of a Burrb")

# Clock controls how fast the game runs (frames per second)
clock = pygame.time.Clock()
FPS = 60

# Colors - these are (Red, Green, Blue) values from 0-255
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
DARK_GRAY = (80, 80, 80)
GRAY = (150, 150, 150)
LIGHT_GRAY = (200, 200, 200)
GREEN = (80, 180, 80)
DARK_GREEN = (50, 140, 50)
BROWN = (139, 90, 43)
SKY_BLUE = (135, 200, 235)
YELLOW = (255, 220, 50)
SIDEWALK = (210, 200, 185)
ROAD_COLOR = (60, 60, 60)
ROAD_LINE = (220, 210, 50)

# Burrb colors (matching the drawing!)
BURRB_BLUE = (60, 150, 220)
BURRB_LIGHT_BLUE = (100, 180, 240)
BURRB_DARK_BLUE = (30, 100, 170)
BURRB_ORANGE = (230, 160, 30)
BURRB_EYE = (20, 40, 80)

# ============================================================
# WORLD MAP
# ============================================================
# The world is much bigger than the screen - that's what makes
# it "open world"! The camera follows the burrb around.
WORLD_WIDTH = 3200
WORLD_HEIGHT = 3200

# City grid settings
BLOCK_SIZE = 200  # each city block is 200x200 pixels (smaller = denser city)
ROAD_WIDTH = 70  # wider roads for more cement
SIDEWALK_WIDTH = 24  # wider sidewalks


# ============================================================
# BUILDINGS
# ============================================================
# We'll randomly generate buildings in each city block
class Building:
    """A building in the city. Each one has a random size and color."""

    # Interior tile types
    FLOOR = 0
    WALL = 1
    FURNITURE = 2
    DOOR_TILE = 3
    SOFA = 4
    TV = 5
    CLOSET = 6

    def __init__(self, x, y, w, h, color, roof_color):
        self.x = x
        self.y = y
        self.w = w
        self.h = h
        self.color = color
        self.roof_color = roof_color
        # Random windows
        self.windows = []
        win_cols = max(1, w // 30)
        win_rows = max(1, h // 35)
        for row in range(win_rows):
            for col in range(win_cols):
                wx = x + 12 + col * (w - 20) // max(1, win_cols)
                wy = y + 12 + row * (h - 20) // max(1, win_rows)
                # Some windows are lit (yellow), some are dark
                lit = random.random() > 0.3
                self.windows.append((wx, wy, lit))
        # Door
        self.door_x = x + w // 2 - 8
        self.door_y = y + h - 24

        # === INTERIOR ===
        # Each building has a room inside! The interior is a grid
        # of tiles: floor, walls, and furniture.
        # Interior size is always the same so it feels like a
        # proper room inside, regardless of building outer size.
        self.interior_w = 20  # grid width in tiles
        self.interior_h = 16  # grid height in tiles
        self.interior_tile = 24  # pixels per tile
        self.interior = self._generate_interior()

        # Interior colors (based on building color, but lighter for floors)
        self.floor_color = (
            min(255, color[0] + 80),
            min(255, color[1] + 80),
            min(255, color[2] + 60),
        )
        self.wall_interior_color = (
            max(0, color[0] - 20),
            max(0, color[1] - 20),
            max(0, color[2] - 20),
        )
        self.furniture_color = (139, 90, 43)  # wood brown

        # Door position inside (bottom center)
        self.interior_door_col = self.interior_w // 2
        self.interior_door_row = self.interior_h - 1

        # Burrb spawn position when entering (just inside the door)
        self.spawn_x = (
            self.interior_door_col * self.interior_tile + self.interior_tile // 2
        )
        self.spawn_y = (
            self.interior_door_row - 1
        ) * self.interior_tile + self.interior_tile // 2

        # === RESIDENT BURRB (lives in this building!) ===
        # Every building has a burrb sitting on the sofa watching TV
        # and eating potato chips. If you steal their chips, they get
        # mad and chase you!
        rng_resident = random.Random(self.x * 777 + self.y * 333)
        resident_colors = [
            ((220, 80, 80), (180, 50, 50)),  # red
            ((80, 200, 80), (40, 150, 40)),  # green
            ((220, 180, 50), (180, 140, 30)),  # yellow
            ((200, 100, 200), (160, 60, 160)),  # purple
            ((220, 140, 60), (180, 100, 30)),  # orange
            ((220, 100, 160), (180, 60, 120)),  # pink
            ((100, 220, 200), (60, 180, 160)),  # teal
        ]
        rc = rng_resident.choice(resident_colors)
        self.resident_color = rc[0]
        self.resident_detail = rc[1]
        # Resident sits on the sofa (pixel position set after interior gen)
        self.resident_x = 0.0
        self.resident_y = 0.0
        self.resident_angry = False  # are they chasing you?
        self.resident_speed = 1.8
        self.resident_walk_frame = 0

        # Potato chips!
        self.chips_x = 0.0
        self.chips_y = 0.0
        self.chips_stolen = False  # did the player take the chips?

        # Closet! Every house has a closet. Open it for chips... or a scare!
        self.closet_opened = False  # has the closet been opened?
        self.closet_x = 0.0  # pixel position of closet center
        self.closet_y = 0.0
        self.closet_jumpscare = False  # was this closet a jump scare?

        # Find the sofa position to place the resident and chips
        tile = self.interior_tile
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.SOFA:
                    # Put resident on the sofa
                    self.resident_x = col * tile + tile // 2
                    self.resident_y = row * tile + tile // 2
                    # Put chips right next to the sofa
                    self.chips_x = (col + 1) * tile + tile // 2
                    self.chips_y = row * tile + tile // 2
                    break
            else:
                continue
            break

        # Find the closet position
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.CLOSET:
                    self.closet_x = col * tile + tile // 2
                    self.closet_y = row * tile + tile // 2
                    break
            else:
                continue
            break

    def _generate_interior(self):
        """
        Generate the interior room layout!
        Uses the building's position as a random seed so each
        building always has the same interior.
        """
        rng = random.Random(self.x * 1000 + self.y)
        grid = []
        for row in range(self.interior_h):
            grid_row = []
            for col in range(self.interior_w):
                # Walls around the edges
                if row == 0 or col == 0 or col == self.interior_w - 1:
                    grid_row.append(self.WALL)
                elif row == self.interior_h - 1:
                    # Bottom wall with door opening in the center
                    if col == self.interior_w // 2:
                        grid_row.append(self.DOOR_TILE)
                    else:
                        grid_row.append(self.WALL)
                else:
                    grid_row.append(self.FLOOR)
            grid.append(grid_row)

        # Add furniture randomly!
        # Tables (2x1 or 1x2 blocks)
        num_tables = rng.randint(1, 3)
        for _ in range(num_tables):
            tr = rng.randint(3, self.interior_h - 4)
            tc = rng.randint(3, self.interior_w - 4)
            if grid[tr][tc] == self.FLOOR:
                grid[tr][tc] = self.FURNITURE
                # Make some tables 2 tiles
                if rng.random() > 0.5 and tc + 1 < self.interior_w - 1:
                    if grid[tr][tc + 1] == self.FLOOR:
                        grid[tr][tc + 1] = self.FURNITURE

        # Shelves along walls (but not blocking the door)
        num_shelves = rng.randint(2, 5)
        for _ in range(num_shelves):
            side = rng.choice(["top", "left", "right"])
            if side == "top":
                sc = rng.randint(2, self.interior_w - 3)
                if grid[1][sc] == self.FLOOR:
                    grid[1][sc] = self.FURNITURE
            elif side == "left":
                sr = rng.randint(2, self.interior_h - 3)
                if grid[sr][1] == self.FLOOR:
                    grid[sr][1] = self.FURNITURE
            elif side == "right":
                sr = rng.randint(2, self.interior_h - 3)
                if grid[sr][self.interior_w - 2] == self.FLOOR:
                    grid[sr][self.interior_w - 2] = self.FURNITURE

        # A counter/bar (horizontal line of furniture)
        if rng.random() > 0.4:
            counter_row = rng.randint(4, self.interior_h - 5)
            counter_start = rng.randint(3, self.interior_w // 2 - 1)
            counter_len = rng.randint(3, 6)
            for c in range(
                counter_start, min(self.interior_w - 2, counter_start + counter_len)
            ):
                if grid[counter_row][c] == self.FLOOR:
                    grid[counter_row][c] = self.FURNITURE

        # === LIVING ROOM SETUP ===
        # Every building has a TV against the top wall and a sofa
        # facing it! A burrb sits on the sofa eating potato chips.

        # TV goes against the top wall (row 1), near the right side
        tv_col = self.interior_w - 5
        tv_row = 1
        # Clear space for TV (overwrite any shelf that might be there)
        grid[tv_row][tv_col] = self.TV

        # Sofa goes 3 rows below the TV (facing it)
        sofa_row = tv_row + 3
        sofa_col = tv_col
        # Sofa is 2 tiles wide
        if grid[sofa_row][sofa_col] == self.FLOOR:
            grid[sofa_row][sofa_col] = self.SOFA
        if sofa_col + 1 < self.interior_w - 1:
            if grid[sofa_row][sofa_col + 1] == self.FLOOR:
                grid[sofa_row][sofa_col + 1] = self.SOFA

        # === CLOSET ===
        # Every house has a closet against the left wall!
        # Open it to find chips... or get jump scared!
        closet_row = rng.randint(3, self.interior_h - 4)
        closet_col = 1  # against the left wall
        # Make sure we don't overwrite something important
        if grid[closet_row][closet_col] != self.FLOOR:
            # Try the right wall instead
            closet_col = self.interior_w - 2
        if grid[closet_row][closet_col] == self.FLOOR:
            grid[closet_row][closet_col] = self.CLOSET

        return grid

    def draw(self, surface, cam_x, cam_y):
        sx = self.x - cam_x
        sy = self.y - cam_y
        # Main building (rounded corners for a smoother look)
        br = min(8, self.w // 6, self.h // 6)
        pygame.draw.rect(
            surface, self.color, (sx, sy, self.w, self.h), border_radius=br
        )
        # Outline
        pygame.draw.rect(surface, BLACK, (sx, sy, self.w, self.h), 2, border_radius=br)
        # Roof accent
        pygame.draw.rect(
            surface, self.roof_color, (sx + 2, sy, self.w - 4, 6), border_radius=3
        )
        # Windows
        for wx, wy, lit in self.windows:
            wsx = wx - cam_x
            wsy = wy - cam_y
            color = (255, 240, 150) if lit else (80, 90, 110)
            pygame.draw.rect(surface, color, (wsx, wsy, 14, 14), border_radius=3)
            pygame.draw.rect(
                surface, (40, 40, 40), (wsx, wsy, 14, 14), 1, border_radius=3
            )
            # Window cross
            pygame.draw.line(
                surface, (40, 40, 40), (wsx + 7, wsy + 2), (wsx + 7, wsy + 12), 1
            )
            pygame.draw.line(
                surface, (40, 40, 40), (wsx + 2, wsy + 7), (wsx + 12, wsy + 7), 1
            )
        # Door
        dx = self.door_x - cam_x
        dy = self.door_y - cam_y
        pygame.draw.rect(surface, BROWN, (dx, dy, 16, 24), border_radius=3)
        pygame.draw.rect(surface, (80, 50, 20), (dx, dy, 16, 24), 1, border_radius=3)
        # Doorknob
        pygame.draw.circle(surface, YELLOW, (dx + 12, dy + 14), 2)

    def get_rect(self):
        return pygame.Rect(self.x, self.y, self.w, self.h)


# ============================================================
# GENERATE THE CITY
# ============================================================
buildings = []
trees = []
# Building color palettes (Super Mario 3D World style - bright candy colors!)
building_colors = [
    ((255, 100, 100), (220, 60, 60)),  # bright red
    ((100, 200, 255), (60, 160, 220)),  # sky blue
    ((255, 220, 80), (220, 180, 40)),  # sunny yellow
    ((160, 255, 130), (110, 220, 80)),  # lime green
    ((255, 160, 200), (220, 120, 160)),  # bubblegum pink
    ((200, 140, 255), (160, 100, 220)),  # lavender purple
    ((255, 180, 100), (220, 140, 60)),  # tangerine orange
    ((255, 255, 200), (220, 220, 160)),  # cream/vanilla
    ((180, 240, 255), (140, 200, 220)),  # ice blue
    ((255, 140, 140), (220, 100, 100)),  # coral
    ((140, 255, 200), (100, 220, 160)),  # mint green
    ((255, 200, 255), (220, 160, 220)),  # light purple/pink
]

random.seed(42)  # Same city every time you play

# Create city blocks in a grid pattern
for bx in range(0, WORLD_WIDTH, BLOCK_SIZE + ROAD_WIDTH):
    for by in range(0, WORLD_HEIGHT, BLOCK_SIZE + ROAD_WIDTH):
        # Each block gets 3-6 buildings (more packed!)
        num_buildings = random.randint(3, 6)
        for _ in range(num_buildings):
            bw = random.randint(30, 80)  # smaller buildings
            bh = random.randint(30, 70)
            # Place building within the block (with sidewalk margin)
            margin = SIDEWALK_WIDTH + 2
            max_x = bx + BLOCK_SIZE - bw - margin
            max_y = by + BLOCK_SIZE - bh - margin
            if max_x <= bx + margin or max_y <= by + margin:
                continue
            px = random.randint(bx + margin, max_x)
            py = random.randint(by + margin, max_y)

            # Check overlap with existing buildings (tighter spacing)
            new_rect = pygame.Rect(px - 2, py - 2, bw + 4, bh + 4)
            overlap = False
            for b in buildings:
                if new_rect.colliderect(b.get_rect()):
                    overlap = True
                    break
            if not overlap:
                color, roof_color = random.choice(building_colors)
                buildings.append(Building(px, py, bw, bh, color, roof_color))

        # Fewer trees in the city (more urban)
        for _ in range(random.randint(0, 1)):
            margin = SIDEWALK_WIDTH + 8
            tx = random.randint(bx + margin, bx + BLOCK_SIZE - margin)
            ty = random.randint(by + margin, by + BLOCK_SIZE - margin)
            # Don't place on buildings
            tree_rect = pygame.Rect(tx - 8, ty - 8, 16, 16)
            overlap = any(tree_rect.colliderect(b.get_rect()) for b in buildings)
            if not overlap:
                trees.append((tx, ty, random.randint(12, 22)))


# ============================================================
# PARKS - a few open green areas
# ============================================================
parks = []
for _ in range(3):
    px = random.randint(200, WORLD_WIDTH - 400)
    py = random.randint(200, WORLD_HEIGHT - 400)
    pw = random.randint(120, 220)
    ph = random.randint(120, 220)
    parks.append(pygame.Rect(px, py, pw, ph))
    # Remove buildings that overlap with parks
    buildings = [
        b
        for b in buildings
        if not pygame.Rect(px - 10, py - 10, pw + 20, ph + 20).colliderect(b.get_rect())
    ]
    # Add extra trees in parks
    for _ in range(8):
        tx = random.randint(px + 20, px + pw - 20)
        ty = random.randint(py + 20, py + ph - 20)
        trees.append((tx, ty, random.randint(14, 24)))


# ============================================================
# NPCs - Other animals and humans walking around the city!
# ============================================================
# "NPC" stands for Non-Player Character. These are characters
# that the computer controls, not you. They wander around the
# city on their own, making it feel alive!
#
# Each NPC has a "type" which determines what it looks like:
#   - "burrb"  = another burrb (different colors!)
#   - "human"  = a person walking around
#   - "cat"    = a little cat
#   - "dog"    = a dog


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

    def update(self):
        """Move the NPC around. This is its simple 'brain'."""
        # Rocks don't move! They just sit there being a rock.
        if self.npc_type == "rock":
            return

        self.walk_frame += 1

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


# Spawn NPCs throughout the city!
npcs = []

# NPC color palettes - ALL burrbs now! Every color EXCEPT light blue
# because light blue is the player's color.
burrb_colors = [
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

# Place NPCs on roads and sidewalks where they can walk freely
# They're ALL burrbs - a whole city of burrbs!
for _ in range(30):
    # Pick a random spot in the world
    nx = random.randint(100, WORLD_WIDTH - 100)
    ny = random.randint(100, WORLD_HEIGHT - 100)

    # Make sure they don't spawn inside a building
    spawn_rect = pygame.Rect(nx - 10, ny - 10, 20, 20)
    in_building = any(spawn_rect.colliderect(b.get_rect()) for b in buildings)
    if in_building:
        continue

    color, detail = random.choice(burrb_colors)
    npcs.append(NPC(nx, ny, "burrb", color, detail))


# ============================================================
# CARS - vehicles driving on the roads!
# ============================================================
# Cars drive along the road grid. They go in one direction
# (horizontal or vertical) and when they reach an intersection,
# they might turn or keep going straight.


class Car:
    """A car that drives along the roads."""

    def __init__(self, x, y, direction, color, detail_color, car_type):
        self.x = x
        self.y = y
        # direction: 0=right, 1=down, 2=left, 3=up
        self.direction = direction
        self.color = color
        self.detail_color = detail_color
        self.car_type = car_type  # "sedan", "truck", "taxi", "sport"
        self.speed = random.uniform(1.2, 2.5)
        # How long until we check for a turn at an intersection
        self.turn_cooldown = 0

    def update(self):
        """Move the car along the road."""
        # Move in current direction
        if self.direction == 0:  # right
            self.x += self.speed
        elif self.direction == 1:  # down
            self.y += self.speed
        elif self.direction == 2:  # left
            self.x -= self.speed
        elif self.direction == 3:  # up
            self.y -= self.speed

        # Wrap around when leaving the world (cars loop around)
        margin = 50
        if self.x > WORLD_WIDTH + margin:
            self.x = -margin
        elif self.x < -margin:
            self.x = WORLD_WIDTH + margin
        if self.y > WORLD_HEIGHT + margin:
            self.y = -margin
        elif self.y < -margin:
            self.y = WORLD_HEIGHT + margin

        # Check if we're at an intersection and maybe turn
        self.turn_cooldown -= 1
        if self.turn_cooldown <= 0:
            step = BLOCK_SIZE + ROAD_WIDTH
            # Are we near the center of an intersection?
            # Intersections happen where horizontal and vertical roads cross
            near_h_road = False
            near_v_road = False
            for bx in range(0, WORLD_WIDTH + step, step):
                road_x = bx + BLOCK_SIZE
                if abs(self.x - (road_x + ROAD_WIDTH // 2)) < 8:
                    near_v_road = True
                    break
            for by in range(0, WORLD_HEIGHT + step, step):
                road_y = by + BLOCK_SIZE
                if abs(self.y - (road_y + ROAD_WIDTH // 2)) < 8:
                    near_h_road = True
                    break

            if near_h_road and near_v_road:
                # At an intersection! Maybe turn
                choice = random.random()
                if choice < 0.3:
                    # Turn right
                    self.direction = (self.direction + 1) % 4
                    self.turn_cooldown = 60
                elif choice < 0.5:
                    # Turn left
                    self.direction = (self.direction - 1) % 4
                    self.turn_cooldown = 60
                else:
                    # Keep going straight
                    self.turn_cooldown = 30


# Car color palettes
car_colors = [
    ((200, 40, 40), (150, 30, 30), "sedan"),  # red sedan
    ((40, 80, 180), (30, 60, 140), "sedan"),  # blue sedan
    ((60, 60, 60), (40, 40, 40), "sedan"),  # black sedan
    ((220, 220, 220), (180, 180, 180), "sedan"),  # white sedan
    ((40, 140, 60), (30, 100, 40), "sedan"),  # green sedan
    ((255, 200, 0), (200, 160, 0), "taxi"),  # yellow taxi
    ((255, 200, 0), (200, 160, 0), "taxi"),  # yellow taxi (more taxis!)
    ((120, 80, 50), (90, 60, 35), "truck"),  # brown truck
    ((80, 80, 100), (60, 60, 80), "truck"),  # gray truck
    ((200, 50, 50), (160, 30, 30), "sport"),  # red sports car
    ((50, 50, 200), (30, 30, 160), "sport"),  # blue sports car
    ((240, 140, 20), (200, 110, 10), "sport"),  # orange sports car
]

# Spawn cars on roads
cars = []
step = BLOCK_SIZE + ROAD_WIDTH

# Cars on horizontal roads
for by in range(0, WORLD_HEIGHT, step):
    road_y = by + BLOCK_SIZE + ROAD_WIDTH // 2
    # Spawn several cars per road
    num_cars = random.randint(2, 4)
    for _ in range(num_cars):
        cx = random.randint(50, WORLD_WIDTH - 50)
        # Drive on the right side of the road
        direction = random.choice([0, 2])  # right or left
        if direction == 0:
            cy = road_y + ROAD_WIDTH // 4  # right side (bottom lane)
        else:
            cy = road_y - ROAD_WIDTH // 4  # left side (top lane)
        color, detail, ctype = random.choice(car_colors)
        cars.append(Car(cx, cy, direction, color, detail, ctype))

# Cars on vertical roads
for bx in range(0, WORLD_WIDTH, step):
    road_x = bx + BLOCK_SIZE + ROAD_WIDTH // 2
    num_cars = random.randint(2, 4)
    for _ in range(num_cars):
        cy = random.randint(50, WORLD_HEIGHT - 50)
        direction = random.choice([1, 3])  # down or up
        if direction == 1:
            cx = road_x + ROAD_WIDTH // 4  # right side
        else:
            cx = road_x - ROAD_WIDTH // 4  # left side
        color, detail, ctype = random.choice(car_colors)
        cars.append(Car(cx, cy, direction, color, detail, ctype))


# ============================================================
# COLLISION GRID (for raycasting)
# ============================================================
# For first-person mode, we need a grid version of the world.
# Think of it like graph paper laid over the city - each tiny
# square is either "wall" (part of a building) or "empty".
# When we shoot rays in first person, they step through this
# grid to find walls quickly.

TILE_SIZE = 16  # each grid cell is 16x16 pixels
GRID_W = WORLD_WIDTH // TILE_SIZE
GRID_H = WORLD_HEIGHT // TILE_SIZE

# Create the grid - None means empty, a color tuple means wall
world_grid = [[None] * GRID_W for _ in range(GRID_H)]

# Fill in the grid from buildings
for b in buildings:
    # Figure out which grid cells this building covers
    col_start = max(0, b.x // TILE_SIZE)
    col_end = min(GRID_W, (b.x + b.w) // TILE_SIZE + 1)
    row_start = max(0, b.y // TILE_SIZE)
    row_end = min(GRID_H, (b.y + b.h) // TILE_SIZE + 1)
    for row in range(row_start, row_end):
        for col in range(col_start, col_end):
            world_grid[row][col] = b.color

# Also mark the world edges as walls so rays don't go forever
for col in range(GRID_W):
    world_grid[0][col] = DARK_GRAY
    world_grid[GRID_H - 1][col] = DARK_GRAY
for row in range(GRID_H):
    world_grid[row][0] = DARK_GRAY
    world_grid[row][GRID_W - 1] = DARK_GRAY


# ============================================================
# DRAW FUNCTIONS
# ============================================================
def draw_road_grid(surface, cam_x, cam_y):
    """Draw the roads between city blocks."""
    # Horizontal roads
    for by in range(0, WORLD_HEIGHT + BLOCK_SIZE, BLOCK_SIZE + ROAD_WIDTH):
        road_y = by + BLOCK_SIZE
        ry = road_y - cam_y
        # Road surface
        pygame.draw.rect(surface, ROAD_COLOR, (-cam_x, ry, WORLD_WIDTH, ROAD_WIDTH))
        # Center line (dashed)
        center_y = ry + ROAD_WIDTH // 2
        for dx in range(0, WORLD_WIDTH, 40):
            lx = dx - cam_x
            pygame.draw.rect(surface, ROAD_LINE, (lx, center_y - 1, 20, 3))
        # Sidewalks
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (-cam_x, ry - SIDEWALK_WIDTH, WORLD_WIDTH, SIDEWALK_WIDTH),
        )
        pygame.draw.rect(
            surface, SIDEWALK, (-cam_x, ry + ROAD_WIDTH, WORLD_WIDTH, SIDEWALK_WIDTH)
        )

    # Vertical roads
    for bx in range(0, WORLD_WIDTH + BLOCK_SIZE, BLOCK_SIZE + ROAD_WIDTH):
        road_x = bx + BLOCK_SIZE
        rx = road_x - cam_x
        pygame.draw.rect(surface, ROAD_COLOR, (rx, -cam_y, ROAD_WIDTH, WORLD_HEIGHT))
        # Center line
        center_x = rx + ROAD_WIDTH // 2
        for dy in range(0, WORLD_HEIGHT, 40):
            ly = dy - cam_y
            pygame.draw.rect(surface, ROAD_LINE, (center_x - 1, ly, 3, 20))
        # Sidewalks
        pygame.draw.rect(
            surface,
            SIDEWALK,
            (rx - SIDEWALK_WIDTH, -cam_y, SIDEWALK_WIDTH, WORLD_HEIGHT),
        )
        pygame.draw.rect(
            surface, SIDEWALK, (rx + ROAD_WIDTH, -cam_y, SIDEWALK_WIDTH, WORLD_HEIGHT)
        )


def draw_tree(surface, x, y, size, cam_x, cam_y):
    """Draw a tree at the given world position."""
    sx = x - cam_x
    sy = y - cam_y
    # Trunk (slightly tapered using a polygon for smoothness)
    pygame.draw.polygon(
        surface,
        BROWN,
        [
            (sx - 2, sy + size // 3),
            (sx + 2, sy + size // 3),
            (sx + 3, sy + size // 2),
            (sx - 3, sy + size // 2),
        ],
    )
    # Leaves (multiple overlapping circles for a bushy, round canopy)
    r = size // 2
    leaf_y = sy - size // 4
    pygame.draw.circle(surface, DARK_GREEN, (sx, leaf_y), r)
    pygame.draw.circle(surface, GREEN, (sx - r // 3, leaf_y - r // 4), r - 1)
    pygame.draw.circle(surface, GREEN, (sx + r // 3, leaf_y + r // 5), r - 2)
    pygame.draw.circle(surface, (90, 190, 70), (sx - r // 4, leaf_y - r // 3), r // 2)
    pygame.draw.circle(surface, (100, 200, 80), (sx + r // 5, leaf_y - r // 2), r // 3)


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


# ============================================================
# FIRST PERSON RAYCASTING
# ============================================================
# This is the Doom-style 3D renderer! Here's how it works:
#
# Imagine you're the Burrb, looking forward. You shoot out
# hundreds of invisible "rays" in a fan shape from your eyes.
# Each ray travels forward until it hits a wall (building).
#
# - If a ray hits something CLOSE, we draw a TALL stripe
# - If a ray hits something FAR, we draw a SHORT stripe
#
# All these stripes side by side create the illusion of 3D!
#
# This is called "raycasting" and it's exactly how the
# original Doom and Wolfenstein 3D games worked in the 1990s.

FOV = math.pi / 3  # 60 degrees - how wide the burrb can see
HALF_FOV = FOV / 2
# How many rays to cast - one per pixel for smooth walls!
# (We used to do 1 per 2 pixels, but that looked blocky)
NUM_RAYS = SCREEN_WIDTH
RAY_STEP = FOV / NUM_RAYS
MAX_DEPTH = 800  # how far rays can travel (in pixels)

# Sky colors for gradient (Super Mario 3D World style - bright and cheerful!)
SKY_TOP = (30, 120, 255)  # vivid blue at the top
SKY_BOTTOM = (140, 210, 255)  # light sky blue at the horizon
# Ground colors for gradient (bright green grass, like Mario games!)
GROUND_TOP = (60, 180, 50)  # darker green at horizon
GROUND_BOTTOM = (100, 220, 70)  # bright cheerful green close up


def draw_first_person(surface, px, py, angle):
    """
    Draw the world from the Burrb's eyes using raycasting!

    px, py  = Burrb's position in the world (in pixels)
    angle   = direction the Burrb is looking (in radians)

    Returns a "depth buffer" - a list with one number per screen column.
    Each number is how far away the wall is at that column. NPCs and
    cars use this to know when they should be hidden behind a wall!
    """
    # Depth buffer: one entry per screen column, starts at max distance
    depth_buffer = [MAX_DEPTH] * SCREEN_WIDTH

    # --- SKY (Super Mario 3D World style - bright blue with fluffy clouds!) ---
    half_h = SCREEN_HEIGHT // 2
    for y in range(half_h):
        t = y / half_h
        r = int(SKY_TOP[0] + (SKY_BOTTOM[0] - SKY_TOP[0]) * t)
        g = int(SKY_TOP[1] + (SKY_BOTTOM[1] - SKY_TOP[1]) * t)
        b = int(SKY_TOP[2] + (SKY_BOTTOM[2] - SKY_TOP[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Fluffy clouds! (drawn on top of the sky gradient)
    # The clouds scroll slowly based on the player's angle to feel alive
    cloud_offset = angle * 80  # clouds drift as you turn
    cloud_data = [
        (150, 60, 90, 30),  # (x_base, y, width, height)
        (400, 40, 110, 35),
        (650, 70, 80, 25),
        (250, 90, 100, 28),
        (800, 55, 95, 32),
        (50, 45, 70, 22),
        (520, 80, 85, 26),
    ]
    for cx_base, cy, cw, ch in cloud_data:
        # Clouds wrap around the screen as you turn
        cx = int((cx_base - cloud_offset) % (SCREEN_WIDTH + 200) - 100)
        # Main cloud body (overlapping white circles for puffy look)
        cloud_white = (255, 255, 255)
        cloud_shadow = (220, 235, 255)
        # Bottom shadow
        pygame.draw.ellipse(surface, cloud_shadow, (cx - cw // 2, cy + ch // 4, cw, ch))
        # Main puffs
        pygame.draw.ellipse(surface, cloud_white, (cx - cw // 2, cy, cw, ch))
        pygame.draw.ellipse(
            surface,
            cloud_white,
            (cx - cw // 3, cy - ch // 3, int(cw * 0.6), int(ch * 0.8)),
        )
        pygame.draw.ellipse(
            surface,
            cloud_white,
            (cx + cw // 8, cy - ch // 4, int(cw * 0.5), int(ch * 0.7)),
        )

    # --- GROUND (bright green grass with Mario-style stripes!) ---
    for y in range(half_h, SCREEN_HEIGHT):
        t = (y - half_h) / half_h
        r = int(GROUND_TOP[0] + (GROUND_BOTTOM[0] - GROUND_TOP[0]) * t)
        g = int(GROUND_TOP[1] + (GROUND_BOTTOM[1] - GROUND_TOP[1]) * t)
        b = int(GROUND_TOP[2] + (GROUND_BOTTOM[2] - GROUND_TOP[2]) * t)
        # Add subtle grass stripes (alternating lighter/darker green)
        # Stripes get wider near the bottom (perspective!)
        stripe_width = max(2, int(3 + t * 12))
        if ((y + int(angle * 20)) // stripe_width) % 2 == 0:
            r = min(255, r + 12)
            g = min(255, g + 15)
            b = min(255, b + 5)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # --- CAST RAYS ---
    # We shoot one ray for every 2 columns of pixels on screen.
    # Each ray starts at the burrb and travels in a slightly
    # different direction, fanning out across the field of view.

    ray_angle = angle - HALF_FOV  # start from left side of view

    for ray_num in range(NUM_RAYS):
        # --- DDA RAYCASTING ALGORITHM ---
        # "DDA" stands for Digital Differential Analyzer.
        # It's a clever way to step through the grid, cell by cell,
        # following the ray's direction. Instead of moving the ray
        # by tiny steps (slow!), DDA jumps from grid line to grid line.

        ra = ray_angle
        sin_a = math.sin(ra)
        cos_a = math.cos(ra)

        # Avoid division by zero
        if abs(cos_a) < 0.00001:
            cos_a = 0.00001
        if abs(sin_a) < 0.00001:
            sin_a = 0.00001

        # Which grid cell are we starting in?
        map_x = int(px) // TILE_SIZE
        map_y = int(py) // TILE_SIZE

        # --- Check VERTICAL grid lines (left/right walls) ---
        # How far is it between vertical grid lines along this ray?
        delta_dist_x = abs(TILE_SIZE / cos_a)
        # Are we going left or right?
        if cos_a > 0:
            step_x = 1
            side_dist_x = (map_x * TILE_SIZE + TILE_SIZE - px) / abs(cos_a)
        else:
            step_x = -1
            side_dist_x = (px - map_x * TILE_SIZE) / abs(cos_a)

        # --- Check HORIZONTAL grid lines (top/bottom walls) ---
        delta_dist_y = abs(TILE_SIZE / sin_a)
        if sin_a > 0:
            step_y = 1
            side_dist_y = (map_y * TILE_SIZE + TILE_SIZE - py) / abs(sin_a)
        else:
            step_y = -1
            side_dist_y = (py - map_y * TILE_SIZE) / abs(sin_a)

        # Step through the grid until we hit a wall or go too far
        hit = False
        hit_side = 0  # 0 = hit a vertical wall, 1 = hit a horizontal wall
        dist = 0
        wall_color = GRAY

        for _ in range(64):  # max 64 steps (safety limit)
            # Jump to the next grid line (whichever is closer)
            if side_dist_x < side_dist_y:
                dist = side_dist_x
                side_dist_x += delta_dist_x
                map_x += step_x
                hit_side = 0
            else:
                dist = side_dist_y
                side_dist_y += delta_dist_y
                map_y += step_y
                hit_side = 1

            # Did the ray leave the grid?
            if map_x < 0 or map_x >= GRID_W or map_y < 0 or map_y >= GRID_H:
                dist = MAX_DEPTH
                break

            # Did the ray hit a wall?
            cell = world_grid[map_y][map_x]
            if cell is not None:
                wall_color = cell
                hit = True
                break

        if dist <= 0:
            dist = 0.1

        # --- FISHEYE CORRECTION ---
        # Without this, walls would look curved/bulgy in the middle
        # of the screen. We fix it by adjusting the distance based on
        # the angle difference between this ray and where we're looking.
        corrected_dist = dist * math.cos(ra - angle)
        if corrected_dist <= 0:
            corrected_dist = 0.1

        # --- CALCULATE WALL HEIGHT ---
        # Closer walls = taller, farther walls = shorter
        # The constant (20000) controls how tall walls look overall
        wall_height = min(SCREEN_HEIGHT, 20000 / corrected_dist)

        # Where to draw this wall stripe on screen
        wall_top = half_h - wall_height / 2
        wall_bottom = half_h + wall_height / 2

        # --- WALL_X: where on the wall surface did the ray hit? ---
        # This gives us a number from 0.0 to 1.0 that tells us
        # how far across the wall tile the ray landed. We need this
        # to know where to draw windows, spikes, and other details.
        if hit_side == 0:
            # Hit a vertical wall - use Y position to find wall_x
            wall_x = (py + dist * sin_a) % TILE_SIZE / TILE_SIZE
        else:
            # Hit a horizontal wall - use X position to find wall_x
            wall_x = (px + dist * cos_a) % TILE_SIZE / TILE_SIZE

        # --- SHADING (Mario 3D World style - bright and cheerful!) ---
        # In Mario games, things don't get super dark in the distance.
        # We keep everything bright and colorful with gentle shading.
        shade = max(0.55, 1.0 - corrected_dist / MAX_DEPTH * 0.5)
        if hit_side == 1:
            shade *= 0.88  # subtle side shading (not too dark!)

        # Apply shading to the wall color (stays bright!)
        r = min(255, int(wall_color[0] * shade))
        g = min(255, int(wall_color[1] * shade))
        b = min(255, int(wall_color[2] * shade))
        shaded_color = (r, g, b)

        # Roof color - slightly different hue, not much darker
        # (Mario roofs are colorful, not gloomy!)
        roof_shade = shade * 0.85
        roof_r = min(255, int(wall_color[0] * roof_shade))
        roof_g = min(255, int(wall_color[1] * roof_shade))
        roof_b = min(255, int(wall_color[2] * roof_shade))
        roof_color = (roof_r, roof_g, roof_b)

        # Bright white highlight for the top edge of walls (cartoon outline!)
        highlight_color = (
            min(255, int(wall_color[0] * shade + 60)),
            min(255, int(wall_color[1] * shade + 60)),
            min(255, int(wall_color[2] * shade + 60)),
        )

        # Store wall distance in the depth buffer for this column
        if 0 <= ray_num < SCREEN_WIDTH:
            depth_buffer[ray_num] = corrected_dist

        # --- DRAW THE WALL STRIPE (Super Mario 3D World style!) ---
        # Bright, colorful, cartoon-like buildings with round rooftops,
        # cute windows, and cheerful doors!
        screen_x = ray_num
        if hit:
            # === ROUNDED ROOFTOP ===
            # Mario-style buildings have smooth, rounded tops!
            # We use a sine wave to make gentle bumps along the roof.
            bump_freq = 2.0  # gentle bumps per tile
            bump_wave = (math.sin(wall_x * bump_freq * math.pi * 2) + 1.0) * 0.5
            bump_max = wall_height * 0.10  # 10% of wall height
            bump_h = bump_wave * bump_max

            # Draw the roof bump (brighter than the wall, not darker!)
            if bump_h > 1:
                bump_top = int(wall_top - bump_h)
                pygame.draw.rect(
                    surface, roof_color, (screen_x, bump_top, 1, int(bump_h))
                )

            # === BRIGHT HIGHLIGHT LINE at the top ===
            # Mario buildings have a bright edge along the top - cartoon style!
            highlight_h = max(2, int(wall_height * 0.04))
            pygame.draw.rect(
                surface, highlight_color, (screen_x, int(wall_top), 1, highlight_h)
            )

            # === MAIN WALL ===
            # Bright, saturated wall in the building's candy color
            main_top = int(wall_top) + highlight_h
            main_h = int(wall_height) - highlight_h
            if main_h > 0:
                pygame.draw.rect(surface, shaded_color, (screen_x, main_top, 1, main_h))

            # === BOTTOM EDGE (dark outline for cartoon look) ===
            # A thin dark line at the very bottom of the wall
            if wall_height > 20:
                bot_h = max(1, int(wall_height * 0.02))
                bot_y = int(wall_top + wall_height - bot_h)
                dark_edge = (
                    max(0, shaded_color[0] - 50),
                    max(0, shaded_color[1] - 50),
                    max(0, shaded_color[2] - 50),
                )
                pygame.draw.rect(surface, dark_edge, (screen_x, bot_y, 1, bot_h))

            # === CUTE WINDOWS (Mario-style!) ===
            # Bright, cheerful windows with white frames
            win_width = 0.09
            win_positions = [0.25, 0.5, 0.75]
            in_window_col = False
            for wp in win_positions:
                if abs(wall_x - wp) < win_width:
                    in_window_col = True
                    break

            if in_window_col and wall_height > 30:
                num_win_rows = min(3, max(1, int(wall_height / 50)))
                win_h = max(4, int(wall_height * 0.09))

                for wi in range(num_win_rows):
                    win_zone_top = wall_top + wall_height * 0.15
                    win_zone_bottom = wall_top + wall_height * 0.70
                    win_zone_h = win_zone_bottom - win_zone_top
                    if num_win_rows == 1:
                        wy = win_zone_top + win_zone_h * 0.4
                    else:
                        wy = win_zone_top + (win_zone_h * wi / (num_win_rows))

                    # Mario windows are bright sky blue or warm yellow!
                    window_id = int(wall_x * 10) + wi * 7
                    if window_id % 3 != 0:
                        # Bright sky-blue window (daytime!)
                        win_color = (
                            min(255, int(180 * shade)),
                            min(255, int(230 * shade)),
                            min(255, int(255 * shade)),
                        )
                    else:
                        # Warm yellow/lit window
                        win_color = (
                            min(255, int(255 * shade)),
                            min(255, int(240 * shade)),
                            min(255, int(150 * shade)),
                        )

                    pygame.draw.rect(surface, win_color, (screen_x, int(wy), 1, win_h))

                    # White window frame edge (at left/right of window)
                    if (
                        abs(wall_x - win_positions[0]) < 0.01
                        or abs(wall_x - win_positions[1]) < 0.01
                        or abs(wall_x - win_positions[2]) < 0.01
                    ):
                        frame_white = (
                            min(255, int(255 * shade)),
                            min(255, int(255 * shade)),
                            min(255, int(255 * shade)),
                        )
                        pygame.draw.rect(
                            surface, frame_white, (screen_x, int(wy), 1, win_h)
                        )

            # === CHEERFUL DOOR (Mario-style!) ===
            # Bright colored doors with a round top feel
            if wall_height > 60 and corrected_dist < 300:
                hit_world_x = px + dist * cos_a
                hit_world_y = py + dist * sin_a

                cell_cx = map_x * TILE_SIZE + TILE_SIZE // 2
                cell_cy = map_y * TILE_SIZE + TILE_SIZE // 2
                for bld in buildings:
                    if (
                        bld.x <= cell_cx < bld.x + bld.w
                        and bld.y <= cell_cy < bld.y + bld.h
                    ):
                        if hit_side == 0:
                            face_pos = (hit_world_y - bld.y) / bld.h
                        else:
                            face_pos = (hit_world_x - bld.x) / bld.w

                        if 0.35 < face_pos < 0.65:
                            door_h = max(8, int(wall_height * 0.40))
                            door_top = int(wall_top + wall_height - door_h)

                            # Bright colorful door (warm brown with a hint of color)
                            door_color = (
                                min(255, int(180 * shade)),
                                min(255, int(120 * shade)),
                                min(255, int(60 * shade)),
                            )
                            pygame.draw.rect(
                                surface, door_color, (screen_x, door_top, 1, door_h)
                            )

                            # White door frame (cartoon outline!)
                            frame_color = (
                                min(255, int(240 * shade)),
                                min(255, int(240 * shade)),
                                min(255, int(230 * shade)),
                            )
                            frame_h = max(1, door_h // 12)
                            pygame.draw.rect(
                                surface,
                                frame_color,
                                (screen_x, door_top, 1, frame_h),
                            )

                            # Round top of door (lighter arc)
                            arc_zone = 0.04
                            if abs(face_pos - 0.5) < arc_zone:
                                pygame.draw.rect(
                                    surface,
                                    frame_color,
                                    (screen_x, door_top - frame_h, 1, frame_h * 2),
                                )

                            # Big bright doorknob (gold star!)
                            if 0.46 < face_pos < 0.54:
                                knob_y = door_top + door_h * 2 // 3
                                knob_color = (
                                    min(255, int(255 * shade)),
                                    min(255, int(220 * shade)),
                                    min(255, int(50 * shade)),
                                )
                                pygame.draw.rect(
                                    surface,
                                    knob_color,
                                    (screen_x, int(knob_y), 1, max(2, door_h // 6)),
                                )
                        break

        # Move to the next ray
        ray_angle += RAY_STEP

    return depth_buffer


def draw_minimap(surface, px, py, angle):
    """
    Draw a tiny top-down map in the corner during first person mode.
    This helps you not get lost! You can see where you are and
    which direction you're looking.
    """
    map_size = 140
    map_scale = 0.02  # how zoomed out the minimap is
    map_x = SCREEN_WIDTH - map_size - 10
    map_y = 10
    map_cx = map_x + map_size // 2
    map_cy = map_y + map_size // 2

    # Semi-transparent background
    map_surface = pygame.Surface((map_size, map_size))
    map_surface.fill((30, 100, 30))
    map_surface.set_alpha(180)
    surface.blit(map_surface, (map_x, map_y))

    # Draw buildings on minimap
    view_range = map_size / map_scale / 2  # how far we can see on the map
    for b in buildings:
        # Position relative to the burrb
        bx_rel = (b.x - px) * map_scale
        by_rel = (b.y - py) * map_scale
        bw = max(2, int(b.w * map_scale))
        bh = max(2, int(b.h * map_scale))
        sx = int(map_cx + bx_rel)
        sy = int(map_cy + by_rel)
        # Only draw if on the minimap
        if (
            map_x < sx + bw
            and sx < map_x + map_size
            and map_y < sy + bh
            and sy < map_y + map_size
        ):
            # Clip to minimap bounds
            draw_rect = pygame.Rect(sx, sy, bw, bh)
            draw_rect = draw_rect.clip(pygame.Rect(map_x, map_y, map_size, map_size))
            pygame.draw.rect(surface, (255, 200, 150), draw_rect)

    # Draw NPCs on minimap as tiny colored dots
    for npc in npcs:
        nx_rel = (npc.x - px) * map_scale
        ny_rel = (npc.y - py) * map_scale
        nsx = int(map_cx + nx_rel)
        nsy = int(map_cy + ny_rel)
        if map_x < nsx < map_x + map_size and map_y < nsy < map_y + map_size:
            pygame.draw.circle(surface, npc.color, (nsx, nsy), 2)

    # Draw cars on minimap as tiny colored rectangles
    for car in cars:
        cx_rel = (car.x - px) * map_scale
        cy_rel = (car.y - py) * map_scale
        csx = int(map_cx + cx_rel)
        csy = int(map_cy + cy_rel)
        if map_x < csx < map_x + map_size and map_y < csy < map_y + map_size:
            pygame.draw.rect(surface, car.color, (csx - 1, csy - 1, 3, 3))

    # Draw the Burrb as a dot in the center
    pygame.draw.circle(surface, BURRB_BLUE, (map_cx, map_cy), 3)

    # Draw a line showing which direction you're looking
    look_len = 12
    look_x = int(map_cx + math.cos(angle) * look_len)
    look_y = int(map_cy + math.sin(angle) * look_len)
    pygame.draw.line(surface, BURRB_ORANGE, (map_cx, map_cy), (look_x, look_y), 2)

    # Draw FOV cone lines
    left_angle = angle - HALF_FOV
    right_angle = angle + HALF_FOV
    fov_len = 20
    lx = int(map_cx + math.cos(left_angle) * fov_len)
    ly = int(map_cy + math.sin(left_angle) * fov_len)
    rx = int(map_cx + math.cos(right_angle) * fov_len)
    ry = int(map_cy + math.sin(right_angle) * fov_len)
    pygame.draw.line(surface, (180, 255, 100), (map_cx, map_cy), (lx, ly), 1)
    pygame.draw.line(surface, (180, 255, 100), (map_cx, map_cy), (rx, ry), 1)

    # Border
    pygame.draw.rect(surface, WHITE, (map_x, map_y, map_size, map_size), 1)


# ============================================================
# NPC DRAWING FUNCTIONS
# ============================================================


def draw_npc_topdown(surface, npc, cam_x, cam_y):
    """
    Draw an NPC in top-down mode. Each type looks different:
    - Burrbs are small squares with spikes
    - Humans are circles with a body rectangle
    - Cats are small ovals with pointy ears
    - Dogs are ovals with a tail
    """
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
        # Eye
        eye_x = sx + 2
        pygame.draw.circle(surface, npc.detail_color, (eye_x, sy - 2), 2)
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


def draw_npcs_first_person(surface, px, py, angle, npc_list, depth_buffer):
    """
    Draw NPCs in first person mode as "billboards" - flat images
    that always face toward you, with REAL 3D depth testing!

    This works like Doom: we draw each NPC onto a temporary surface,
    then copy it to the screen column by column, but ONLY for columns
    where the NPC is closer than the wall. This means NPCs properly
    disappear behind buildings instead of floating on top!

    The depth_buffer is a list of wall distances (one per screen column)
    from the raycaster. If an NPC is farther than the wall at a given
    column, that column of the NPC doesn't get drawn.
    """
    half_h = SCREEN_HEIGHT // 2

    # We need to sort NPCs by distance (farthest first) so close
    # ones draw on top of far ones. This is called the "painter's
    # algorithm" - paint the back first, then paint over it.
    npc_draws = []

    for npc in npc_list:
        # Vector from player to NPC
        dx = npc.x - px
        dy = npc.y - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 10 or dist > MAX_DEPTH:
            continue  # too close or too far

        # What angle is this NPC at, relative to where we're looking?
        npc_angle = math.atan2(dy, dx)
        angle_diff = npc_angle - angle

        # Normalize angle difference to -pi to pi
        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        # Is the NPC within our field of view? (with some margin)
        if abs(angle_diff) > HALF_FOV + 0.2:
            continue  # behind us or too far to the side

        npc_draws.append((dist, angle_diff, npc))

    # Sort: farthest first (so close ones draw on top)
    npc_draws.sort(key=lambda x: -x[0])

    for dist, angle_diff, npc in npc_draws:
        # Project onto screen X position
        # angle_diff of 0 = center of screen
        # angle_diff of -HALF_FOV = left edge
        # angle_diff of +HALF_FOV = right edge
        screen_x = int(SCREEN_WIDTH / 2 + (angle_diff / HALF_FOV) * SCREEN_WIDTH / 2)

        # Size based on distance (closer = bigger)
        sprite_height = min(SCREEN_HEIGHT, 12000 / dist)
        sprite_width = sprite_height * 0.6

        # Where to draw on screen (centered at feet level)
        sprite_top = int(half_h - sprite_height * 0.3)
        sprite_bottom = int(half_h + sprite_height * 0.7)
        sprite_left = int(screen_x - sprite_width / 2)

        sw = int(sprite_width)
        sh = int(sprite_height)
        if sw < 2 or sh < 2:
            continue  # too small to draw

        # Quick check: is EVERY column of this sprite behind a wall?
        # If so, skip drawing entirely (saves time!)
        all_hidden = True
        for col in range(max(0, sprite_left), min(SCREEN_WIDTH, sprite_left + sw)):
            if dist < depth_buffer[col]:
                all_hidden = False
                break
        if all_hidden:
            continue

        # === RENDER NPC TO A TEMPORARY SURFACE ===
        # We draw the NPC onto a small offscreen surface first,
        # then copy it column-by-column with depth testing.
        # The "colorkey" trick makes the background transparent.
        TRANSPARENT = (255, 0, 255)  # magenta = see-through
        npc_surf = pygame.Surface((sw, sh))
        npc_surf.fill(TRANSPARENT)
        npc_surf.set_colorkey(TRANSPARENT)

        # All drawing coordinates are LOCAL to npc_surf (0,0 is top-left)
        local_cx = sw // 2  # center X of the sprite surface

        # Distance shading (farther = darker)
        shade = max(0.55, 1.0 - dist / MAX_DEPTH * 0.5)

        # Apply shading to colors
        r = min(255, int(npc.color[0] * shade))
        g = min(255, int(npc.color[1] * shade))
        b = min(255, int(npc.color[2] * shade))
        body_color = (r, g, b)

        dr = min(255, int(npc.detail_color[0] * shade))
        dg = min(255, int(npc.detail_color[1] * shade))
        db = min(255, int(npc.detail_color[2] * shade))
        detail_color = (dr, dg, db)

        outline = (
            max(0, int(30 * shade)),
            max(0, int(30 * shade)),
            max(0, int(30 * shade)),
        )

        # Leg animation
        leg_kick = math.sin(npc.walk_frame * 0.3) * sh * 0.05

        if npc.npc_type == "burrb":
            # === BURRB SPRITE ===
            body_h = int(sh * 0.5)
            body_w = int(sw * 0.9)
            body_top_l = int(sh * 0.2)
            body_left_l = local_cx - body_w // 2

            # Legs
            leg_x1 = local_cx - body_w // 4
            leg_x2 = local_cx + body_w // 4
            leg_top_l = body_top_l + body_h
            leg_len = max(2, int(sh * 0.2))
            lw = max(1, sw // 12)
            pygame.draw.line(
                npc_surf,
                outline,
                (leg_x1, leg_top_l),
                (int(leg_x1 + leg_kick), leg_top_l + leg_len),
                lw,
            )
            pygame.draw.line(
                npc_surf,
                outline,
                (leg_x2, leg_top_l),
                (int(leg_x2 - leg_kick), leg_top_l + leg_len),
                lw,
            )

            # Body (square with rounded corners)
            if body_w > 4 and body_h > 4:
                pygame.draw.rect(
                    npc_surf,
                    body_color,
                    (body_left_l, body_top_l, body_w, body_h),
                    border_radius=max(1, sw // 8),
                )
                pygame.draw.rect(
                    npc_surf,
                    outline,
                    (body_left_l, body_top_l, body_w, body_h),
                    1,
                    border_radius=max(1, sw // 8),
                )

            # Spikes on top
            num_spikes = 4
            for i in range(num_spikes):
                spike_x = body_left_l + int(body_w * (i + 0.5) / num_spikes)
                spike_h = max(2, int(sh * 0.12))
                if i % 2 == 0:
                    spike_h = int(spike_h * 1.3)
                pygame.draw.polygon(
                    npc_surf,
                    body_color,
                    [
                        (spike_x - max(1, sw // 10), body_top_l),
                        (spike_x, body_top_l - spike_h),
                        (spike_x + max(1, sw // 10), body_top_l),
                    ],
                )

            # Eye (teardrop)
            eye_x = local_cx + body_w // 6
            eye_y = body_top_l + body_h // 4
            eye_r = max(1, sw // 8)
            pygame.draw.circle(npc_surf, outline, (eye_x, eye_y), eye_r)
            if eye_r > 1:
                pygame.draw.circle(
                    npc_surf,
                    (255, 255, 255),
                    (eye_x - eye_r // 3, eye_y - eye_r // 3),
                    max(1, eye_r // 3),
                )

            # Beak
            beak_w = max(2, int(sw * 0.3))
            beak_x = local_cx + body_w // 2
            beak_y = body_top_l + body_h // 3
            orange_shaded = (
                min(255, int(230 * shade)),
                min(255, int(160 * shade)),
                min(255, int(30 * shade)),
            )
            pygame.draw.polygon(
                npc_surf,
                orange_shaded,
                [
                    (beak_x, beak_y - max(1, sh // 20)),
                    (beak_x + beak_w, beak_y),
                    (beak_x, beak_y + max(1, sh // 20)),
                ],
            )

        elif npc.npc_type == "human":
            # === HUMAN SPRITE ===
            head_r = max(2, int(sw * 0.25))
            head_y = head_r + 2
            pygame.draw.circle(npc_surf, body_color, (local_cx, head_y), head_r)
            pygame.draw.circle(npc_surf, outline, (local_cx, head_y), head_r, 1)
            if head_r > 3:
                pygame.draw.circle(
                    npc_surf,
                    outline,
                    (local_cx - head_r // 3, head_y - 1),
                    max(1, head_r // 4),
                )
                pygame.draw.circle(
                    npc_surf,
                    outline,
                    (local_cx + head_r // 3, head_y - 1),
                    max(1, head_r // 4),
                )

            # Body (shirt)
            torso_top = head_y + head_r
            torso_h = max(3, int(sh * 0.3))
            torso_w = max(3, int(sw * 0.6))
            pygame.draw.rect(
                npc_surf,
                detail_color,
                (local_cx - torso_w // 2, torso_top, torso_w, torso_h),
            )
            pygame.draw.rect(
                npc_surf,
                outline,
                (local_cx - torso_w // 2, torso_top, torso_w, torso_h),
                1,
            )

            # Arms
            arm_w = max(1, sw // 10)
            arm_len = max(2, int(sh * 0.15))
            arm_swing = leg_kick * 0.7
            pygame.draw.line(
                npc_surf,
                body_color,
                (local_cx - torso_w // 2, torso_top + 2),
                (
                    int(local_cx - torso_w // 2 - arm_w * 2),
                    int(torso_top + arm_len + arm_swing),
                ),
                arm_w,
            )
            pygame.draw.line(
                npc_surf,
                body_color,
                (local_cx + torso_w // 2, torso_top + 2),
                (
                    int(local_cx + torso_w // 2 + arm_w * 2),
                    int(torso_top + arm_len - arm_swing),
                ),
                arm_w,
            )

            # Legs (pants - darker)
            leg_top_l = torso_top + torso_h
            leg_len = max(3, int(sh * 0.25))
            leg_w = max(1, sw // 8)
            pants_color = (
                max(0, int(40 * shade)),
                max(0, int(40 * shade)),
                max(0, int(60 * shade)),
            )
            pygame.draw.line(
                npc_surf,
                pants_color,
                (local_cx - torso_w // 4, leg_top_l),
                (int(local_cx - torso_w // 4 + leg_kick), leg_top_l + leg_len),
                leg_w,
            )
            pygame.draw.line(
                npc_surf,
                pants_color,
                (local_cx + torso_w // 4, leg_top_l),
                (int(local_cx + torso_w // 4 - leg_kick), leg_top_l + leg_len),
                leg_w,
            )

        elif npc.npc_type == "cat":
            # === CAT SPRITE ===
            body_h = max(3, int(sh * 0.25))
            body_w = max(4, int(sw * 0.7))
            body_top_l = int(sh * 0.45)

            # Body (oval)
            pygame.draw.ellipse(
                npc_surf,
                body_color,
                (local_cx - body_w // 2, body_top_l, body_w, body_h),
            )
            pygame.draw.ellipse(
                npc_surf,
                outline,
                (local_cx - body_w // 2, body_top_l, body_w, body_h),
                1,
            )

            # Head
            head_r = max(2, int(sw * 0.22))
            head_x = local_cx
            head_y = body_top_l - head_r + 2
            pygame.draw.circle(npc_surf, body_color, (head_x, head_y), head_r)
            pygame.draw.circle(npc_surf, outline, (head_x, head_y), head_r, 1)

            # Pointy ears!
            ear_h = max(2, int(sh * 0.1))
            pygame.draw.polygon(
                npc_surf,
                body_color,
                [
                    (head_x - head_r, head_y - head_r // 2),
                    (head_x - head_r // 2, head_y - head_r - ear_h),
                    (head_x, head_y - head_r // 2),
                ],
            )
            pygame.draw.polygon(
                npc_surf,
                body_color,
                [
                    (head_x, head_y - head_r // 2),
                    (head_x + head_r // 2, head_y - head_r - ear_h),
                    (head_x + head_r, head_y - head_r // 2),
                ],
            )

            # Eyes (glowing!)
            if head_r > 2:
                eye_color = (
                    min(255, int(200 * shade)),
                    min(255, int(220 * shade)),
                    min(255, int(50 * shade)),
                )
                pygame.draw.circle(
                    npc_surf,
                    eye_color,
                    (head_x - head_r // 3, head_y),
                    max(1, head_r // 3),
                )
                pygame.draw.circle(
                    npc_surf,
                    eye_color,
                    (head_x + head_r // 3, head_y),
                    max(1, head_r // 3),
                )

            # Tail (curvy!)
            tail_wave = math.sin(npc.walk_frame * 0.15) * max(2, sw // 5)
            tail_x = local_cx - body_w // 2
            pygame.draw.line(
                npc_surf,
                body_color,
                (tail_x, body_top_l + body_h // 2),
                (int(tail_x - sw * 0.3), int(body_top_l - sh * 0.1 + tail_wave)),
                max(1, sw // 10),
            )

            # Legs (thin)
            leg_len = max(2, int(sh * 0.12))
            lw = max(1, sw // 12)
            pygame.draw.line(
                npc_surf,
                outline,
                (local_cx - body_w // 3, body_top_l + body_h),
                (local_cx - body_w // 3, body_top_l + body_h + leg_len),
                lw,
            )
            pygame.draw.line(
                npc_surf,
                outline,
                (local_cx + body_w // 3, body_top_l + body_h),
                (local_cx + body_w // 3, body_top_l + body_h + leg_len),
                lw,
            )

        elif npc.npc_type == "dog":
            # === DOG SPRITE ===
            body_h = max(3, int(sh * 0.28))
            body_w = max(5, int(sw * 0.8))
            body_top_l = int(sh * 0.38)

            # Body (oval, slightly bigger than cat)
            pygame.draw.ellipse(
                npc_surf,
                body_color,
                (local_cx - body_w // 2, body_top_l, body_w, body_h),
            )
            pygame.draw.ellipse(
                npc_surf,
                outline,
                (local_cx - body_w // 2, body_top_l, body_w, body_h),
                1,
            )

            # Head
            head_r = max(3, int(sw * 0.25))
            head_x = local_cx + body_w // 4
            head_y = body_top_l - head_r // 2
            pygame.draw.circle(npc_surf, body_color, (head_x, head_y), head_r)
            pygame.draw.circle(npc_surf, outline, (head_x, head_y), head_r, 1)

            # Snout
            snout_w = max(2, int(sw * 0.18))
            snout_h = max(2, int(sh * 0.06))
            pygame.draw.ellipse(
                npc_surf,
                detail_color,
                (head_x + head_r // 2, head_y - snout_h // 2, snout_w, snout_h),
            )
            # Nose
            pygame.draw.circle(
                npc_surf,
                outline,
                (head_x + head_r // 2 + snout_w, head_y),
                max(1, sw // 15),
            )

            # Eye
            if head_r > 3:
                pygame.draw.circle(
                    npc_surf,
                    outline,
                    (head_x - head_r // 4, head_y - head_r // 4),
                    max(1, head_r // 4),
                )

            # Floppy ear
            ear_w = max(2, int(sw * 0.12))
            ear_h = max(2, int(sh * 0.1))
            pygame.draw.ellipse(
                npc_surf,
                detail_color,
                (head_x - head_r // 2, head_y - head_r, ear_w, ear_h),
            )

            # Tail (wagging!)
            tail_wave = math.sin(npc.walk_frame * 0.2) * max(2, sw // 4)
            tail_x = local_cx - body_w // 2
            pygame.draw.line(
                npc_surf,
                body_color,
                (tail_x, body_top_l + body_h // 3),
                (int(tail_x - sw * 0.25), int(body_top_l - sh * 0.08 + tail_wave)),
                max(1, sw // 8),
            )

            # Legs
            leg_len = max(2, int(sh * 0.15))
            lw = max(1, sw // 10)
            pygame.draw.line(
                npc_surf,
                outline,
                (local_cx - body_w // 3, body_top_l + body_h),
                (int(local_cx - body_w // 3 + leg_kick), body_top_l + body_h + leg_len),
                lw,
            )
            pygame.draw.line(
                npc_surf,
                outline,
                (local_cx + body_w // 4, body_top_l + body_h),
                (int(local_cx + body_w // 4 - leg_kick), body_top_l + body_h + leg_len),
                lw,
            )

        elif npc.npc_type == "rock":
            # === ROCK SPRITE (petrified NPC!) ===
            # A lumpy gray boulder sitting on the ground
            rock_w = int(sw * 0.8)
            rock_h = int(sh * 0.5)
            rock_top_l = int(sh * 0.4)
            rock_left_l = local_cx - rock_w // 2

            # Main rock body (big ellipse)
            pygame.draw.ellipse(
                npc_surf,
                body_color,
                (rock_left_l, rock_top_l, rock_w, rock_h),
            )
            # Upper bump (smaller overlapping ellipse)
            bump_w = int(rock_w * 0.6)
            bump_h = int(rock_h * 0.5)
            pygame.draw.ellipse(
                npc_surf,
                detail_color,
                (local_cx - bump_w // 2, rock_top_l - bump_h // 2, bump_w, bump_h),
            )
            # Small top bump
            tiny_w = int(rock_w * 0.35)
            tiny_h = int(rock_h * 0.3)
            pygame.draw.ellipse(
                npc_surf,
                body_color,
                (
                    local_cx - tiny_w // 2,
                    rock_top_l - bump_h // 2 - tiny_h // 3,
                    tiny_w,
                    tiny_h,
                ),
            )
            # Cracks
            crack_color = (
                max(0, int(50 * shade)),
                max(0, int(50 * shade)),
                max(0, int(45 * shade)),
            )
            if rock_w > 8:
                pygame.draw.line(
                    npc_surf,
                    crack_color,
                    (local_cx - rock_w // 4, rock_top_l + rock_h // 4),
                    (local_cx, rock_top_l + rock_h * 3 // 4),
                    1,
                )
                pygame.draw.line(
                    npc_surf,
                    crack_color,
                    (local_cx + rock_w // 6, rock_top_l + rock_h // 6),
                    (local_cx + rock_w // 3, rock_top_l + rock_h // 2),
                    1,
                )
            # Outline
            pygame.draw.ellipse(
                npc_surf,
                outline,
                (rock_left_l, rock_top_l, rock_w, rock_h),
                1,
            )
            # Highlight
            hl_color = (
                min(255, int(170 * shade)),
                min(255, int(170 * shade)),
                min(255, int(160 * shade)),
            )
            hl_r = max(1, rock_w // 8)
            pygame.draw.circle(
                npc_surf,
                hl_color,
                (local_cx - rock_w // 5, rock_top_l + rock_h // 4),
                hl_r,
            )

        # === DEPTH-TESTED BLIT ===
        # This is the 3D magic! Instead of just slapping the sprite
        # onto the screen, we copy it column by column, checking the
        # depth buffer each time. If the wall at that column is closer
        # than the NPC, we skip that column (the NPC is hidden behind
        # the wall). This makes NPCs properly disappear behind buildings!
        for col in range(sw):
            screen_col = sprite_left + col
            # Skip columns outside the screen
            if screen_col < 0 or screen_col >= SCREEN_WIDTH:
                continue
            # The 3D depth test: is the NPC closer than the wall here?
            if dist < depth_buffer[screen_col]:
                # Yes! Draw this column of the sprite
                surface.blit(
                    npc_surf,
                    (screen_col, sprite_top),
                    area=pygame.Rect(col, 0, 1, sh),
                )


# ============================================================
# CAR DRAWING (top-down and first-person)
# ============================================================


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
            wy = int(sx - hh + 2)
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


def draw_cars_first_person(surface, px, py, angle, car_list, depth_buffer):
    """
    Draw cars in first person mode as billboard sprites with 3D depth testing!
    Same technique as NPCs - render to temp surface, then blit column by column
    checking the depth buffer so cars hide behind walls properly.
    """
    half_h = SCREEN_HEIGHT // 2

    car_draws = []

    for car in car_list:
        dx = car.x - px
        dy = car.y - py
        dist = math.sqrt(dx * dx + dy * dy)

        if dist < 10 or dist > MAX_DEPTH:
            continue

        car_angle = math.atan2(dy, dx)
        angle_diff = car_angle - angle

        while angle_diff > math.pi:
            angle_diff -= 2 * math.pi
        while angle_diff < -math.pi:
            angle_diff += 2 * math.pi

        if abs(angle_diff) > HALF_FOV + 0.2:
            continue

        car_draws.append((dist, angle_diff, car))

    # Sort farthest first (painter's algorithm)
    car_draws.sort(key=lambda x: -x[0])

    for dist, angle_diff, car in car_draws:
        screen_x = int(SCREEN_WIDTH / 2 + (angle_diff / HALF_FOV) * SCREEN_WIDTH / 2)

        # Cars are bigger than NPCs
        sprite_height = min(SCREEN_HEIGHT, 10000 / dist)
        sprite_width = sprite_height * 1.2

        # Cars sit on the ground
        sprite_top = int(half_h - sprite_height * 0.2)
        sprite_bottom = int(half_h + sprite_height * 0.8)
        sprite_left = int(screen_x - sprite_width / 2)

        sw = int(sprite_width)
        sh = int(sprite_height)
        if sw < 3 or sh < 3:
            continue

        # Quick check: is every column behind a wall?
        all_hidden = True
        for col in range(max(0, sprite_left), min(SCREEN_WIDTH, sprite_left + sw)):
            if dist < depth_buffer[col]:
                all_hidden = False
                break
        if all_hidden:
            continue

        # Render car to temp surface
        TRANSPARENT = (255, 0, 255)
        car_surf = pygame.Surface((sw, sh))
        car_surf.fill(TRANSPARENT)
        car_surf.set_colorkey(TRANSPARENT)

        local_cx = sw // 2

        # Distance shading
        shade = max(0.55, 1.0 - dist / MAX_DEPTH * 0.5)

        r = min(255, int(car.color[0] * shade))
        g = min(255, int(car.color[1] * shade))
        b = min(255, int(car.color[2] * shade))
        body_color = (r, g, b)

        dr = min(255, int(car.detail_color[0] * shade))
        dg = min(255, int(car.detail_color[1] * shade))
        db = min(255, int(car.detail_color[2] * shade))
        detail_color = (dr, dg, db)

        outline = (
            max(0, int(30 * shade)),
            max(0, int(30 * shade)),
            max(0, int(30 * shade)),
        )

        # --- Draw car onto temp surface ---
        # All coordinates are local (0,0 = top-left of car_surf)
        local_bottom = sh
        local_top = 0

        # Body (main rectangle)
        body_h = int(sh * 0.5)
        body_w = sw
        body_top_l = local_bottom - body_h
        body_rect = pygame.Rect(0, body_top_l, body_w, body_h)
        pygame.draw.rect(car_surf, body_color, body_rect, border_radius=3)

        # Cabin/roof
        cabin_h = int(sh * 0.3)
        cabin_w = int(sw * 0.6)
        cabin_left_l = local_cx - cabin_w // 2
        cabin_top_l = body_top_l - cabin_h
        cabin_rect = pygame.Rect(cabin_left_l, cabin_top_l, cabin_w, cabin_h)
        pygame.draw.rect(car_surf, detail_color, cabin_rect, border_radius=3)

        # Windows
        win_color = (
            min(255, int(160 * shade)),
            min(255, int(200 * shade)),
            min(255, int(230 * shade)),
        )
        win_margin = max(1, cabin_w // 8)
        win_rect = pygame.Rect(
            cabin_left_l + win_margin,
            cabin_top_l + max(1, cabin_h // 4),
            cabin_w - win_margin * 2,
            cabin_h - max(2, cabin_h // 3),
        )
        pygame.draw.rect(car_surf, win_color, win_rect, border_radius=2)

        # Window divider
        if sw > 15:
            pygame.draw.line(
                car_surf,
                detail_color,
                (local_cx, cabin_top_l + max(1, cabin_h // 4)),
                (local_cx, cabin_top_l + cabin_h - max(1, cabin_h // 4)),
                max(1, sw // 20),
            )

        # Wheels
        wheel_r = max(2, body_h // 4)
        wheel_y_l = local_bottom
        left_wheel_x = body_w // 5
        right_wheel_x = body_w * 4 // 5
        pygame.draw.circle(car_surf, (20, 20, 20), (left_wheel_x, wheel_y_l), wheel_r)
        pygame.draw.circle(car_surf, (20, 20, 20), (right_wheel_x, wheel_y_l), wheel_r)
        hub_r = max(1, wheel_r // 2)
        pygame.draw.circle(car_surf, (120, 120, 120), (left_wheel_x, wheel_y_l), hub_r)
        pygame.draw.circle(car_surf, (120, 120, 120), (right_wheel_x, wheel_y_l), hub_r)

        # Headlights
        hl_size = max(2, body_w // 10)
        hl_color = (
            min(255, int(255 * shade)),
            min(255, int(255 * shade)),
            min(255, int(180 * shade)),
        )
        pygame.draw.rect(
            car_surf, hl_color, (1, body_top_l + body_h // 4, hl_size, hl_size)
        )
        pygame.draw.rect(
            car_surf,
            hl_color,
            (body_w - hl_size - 1, body_top_l + body_h // 4, hl_size, hl_size),
        )

        # Taillights
        tl_color = (min(255, int(200 * shade)), 0, 0)
        pygame.draw.rect(
            car_surf, tl_color, (1, body_top_l + body_h * 2 // 3, hl_size, hl_size)
        )
        pygame.draw.rect(
            car_surf,
            tl_color,
            (body_w - hl_size - 1, body_top_l + body_h * 2 // 3, hl_size, hl_size),
        )

        # Taxi sign
        if car.car_type == "taxi" and sw > 10:
            sign_w = max(4, cabin_w // 3)
            sign_h = max(2, cabin_h // 3)
            sign_color = (
                min(255, int(255 * shade)),
                min(255, int(255 * shade)),
                min(255, int(100 * shade)),
            )
            pygame.draw.rect(
                car_surf,
                sign_color,
                (local_cx - sign_w // 2, cabin_top_l - sign_h, sign_w, sign_h),
                border_radius=2,
            )

        # Truck cargo
        if car.car_type == "truck":
            cargo_h = int(sh * 0.15)
            cargo_w = int(sw * 0.4)
            cargo_left_l = body_w // 2
            pygame.draw.rect(
                car_surf,
                detail_color,
                (cargo_left_l, body_top_l - cargo_h, cargo_w, cargo_h + body_h),
                border_radius=2,
            )

        # Sport stripe
        if car.car_type == "sport" and sw > 12:
            stripe_shade = min(255, int(255 * shade))
            pygame.draw.line(
                car_surf,
                (stripe_shade, stripe_shade, stripe_shade),
                (3, body_top_l + body_h // 2),
                (body_w - 3, body_top_l + body_h // 2),
                max(1, body_h // 8),
            )

        # Outlines
        pygame.draw.rect(car_surf, outline, body_rect, 1, border_radius=3)
        pygame.draw.rect(car_surf, outline, cabin_rect, 1, border_radius=3)

        # === DEPTH-TESTED BLIT (same as NPCs) ===
        for col in range(sw):
            screen_col = sprite_left + col
            if screen_col < 0 or screen_col >= SCREEN_WIDTH:
                continue
            if dist < depth_buffer[screen_col]:
                surface.blit(
                    car_surf,
                    (screen_col, sprite_top),
                    area=pygame.Rect(col, 0, 1, sh),
                )


# ============================================================
# INTERIOR DRAWING AND COLLISION
# ============================================================


def can_move_interior(bld, x, y):
    """Check if the burrb can move to (x,y) inside a building."""
    tile = bld.interior_tile
    # Check a small rect around the burrb
    for check_x, check_y in [
        (x - 6, y - 6),
        (x + 6, y - 6),
        (x - 6, y + 6),
        (x + 6, y + 6),
    ]:
        col = int(check_x) // tile
        row = int(check_y) // tile
        if row < 0 or row >= bld.interior_h or col < 0 or col >= bld.interior_w:
            return False
        cell = bld.interior[row][col]
        if cell in (Building.WALL, Building.FURNITURE, Building.TV, Building.CLOSET):
            return False
    return True


def get_nearby_door_building(bx, by):
    """Check if the burrb is near any building's door (outside)."""
    for b in buildings:
        # Door center position
        door_cx = b.door_x + 8
        door_cy = b.door_y + 24  # bottom of door
        dx = bx - door_cx
        dy = by - door_cy
        dist = math.sqrt(dx * dx + dy * dy)
        if dist < 30:
            return b
    return None


def is_at_interior_door(bld, x, y):
    """Check if the burrb is near the door inside a building."""
    tile = bld.interior_tile
    door_x = bld.interior_door_col * tile + tile // 2
    door_y = bld.interior_door_row * tile + tile // 2
    dx = x - door_x
    dy = y - door_y
    return math.sqrt(dx * dx + dy * dy) < tile * 1.5


def draw_interior_topdown(surface, bld, px, py):
    """
    Draw the inside of a building in top-down mode!
    The interior fills the whole screen so it feels like
    you've gone inside.
    """
    tile = bld.interior_tile
    total_w = bld.interior_w * tile
    total_h = bld.interior_h * tile

    # Camera offset to center on the player
    cam_x = px - SCREEN_WIDTH // 2
    cam_y = py - SCREEN_HEIGHT // 2

    # Background
    screen.fill((40, 35, 30))

    # Draw the interior grid
    for row in range(bld.interior_h):
        for col in range(bld.interior_w):
            sx = col * tile - cam_x
            sy = row * tile - cam_y

            # Skip if off screen
            if (
                sx + tile < 0
                or sx > SCREEN_WIDTH
                or sy + tile < 0
                or sy > SCREEN_HEIGHT
            ):
                continue

            cell = bld.interior[row][col]

            if cell == Building.FLOOR or cell == Building.DOOR_TILE:
                # Floor tiles (checkerboard pattern for texture)
                if (row + col) % 2 == 0:
                    floor_c = bld.floor_color
                else:
                    floor_c = (
                        max(0, bld.floor_color[0] - 15),
                        max(0, bld.floor_color[1] - 15),
                        max(0, bld.floor_color[2] - 15),
                    )
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))

                # Door tile gets a special marker
                if cell == Building.DOOR_TILE:
                    pygame.draw.rect(
                        surface, BROWN, (sx + 2, sy + 2, tile - 4, tile - 4)
                    )
                    pygame.draw.rect(
                        surface, (100, 60, 30), (sx + 2, sy + 2, tile - 4, tile - 4), 1
                    )
                    # "EXIT" hint
                    if tile > 16:
                        exit_font = pygame.font.Font(None, 16)
                        exit_text = exit_font.render("EXIT", True, YELLOW)
                        surface.blit(exit_text, (sx + 2, sy + tile // 2 - 4))

            elif cell == Building.WALL:
                # Walls
                pygame.draw.rect(surface, bld.wall_interior_color, (sx, sy, tile, tile))
                pygame.draw.rect(surface, BLACK, (sx, sy, tile, tile), 1)

            elif cell == Building.FURNITURE:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # Furniture on top (brown wooden look)
                margin = 2
                pygame.draw.rect(
                    surface,
                    bld.furniture_color,
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    (100, 60, 25),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    1,
                    border_radius=2,
                )
                # Wood grain lines
                for i in range(2, tile - 4, 5):
                    pygame.draw.line(
                        surface,
                        (120, 75, 35),
                        (sx + margin + 1, sy + margin + i),
                        (sx + tile - margin - 1, sy + margin + i),
                        1,
                    )

            elif cell == Building.SOFA:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # Blue sofa cushion!
                margin = 2
                pygame.draw.rect(
                    surface,
                    (80, 120, 200),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=4,
                )
                # Sofa back (darker blue strip at top)
                pygame.draw.rect(
                    surface,
                    (60, 90, 160),
                    (sx + margin, sy + margin, tile - margin * 2, 6),
                    border_radius=2,
                )
                # Cushion line
                pygame.draw.line(
                    surface,
                    (70, 105, 180),
                    (sx + tile // 2, sy + margin + 6),
                    (sx + tile // 2, sy + tile - margin),
                    1,
                )
                # Outline
                pygame.draw.rect(
                    surface,
                    (40, 60, 120),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    1,
                    border_radius=4,
                )

            elif cell == Building.TV:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                # TV screen (dark rectangle with bright image)
                margin = 3
                # TV body
                pygame.draw.rect(
                    surface,
                    (30, 30, 30),
                    (sx + margin, sy + margin, tile - margin * 2, tile - margin * 2),
                    border_radius=2,
                )
                # Screen (bright blue-ish glow - it's on!)
                pygame.draw.rect(
                    surface,
                    (100, 180, 255),
                    (
                        sx + margin + 2,
                        sy + margin + 2,
                        tile - margin * 2 - 4,
                        tile - margin * 2 - 4,
                    ),
                    border_radius=1,
                )
                # Little stand at the bottom
                pygame.draw.rect(
                    surface,
                    (50, 50, 50),
                    (sx + tile // 2 - 3, sy + tile - margin, 6, 2),
                )

            elif cell == Building.CLOSET:
                # Draw floor underneath
                floor_c = bld.floor_color
                pygame.draw.rect(surface, floor_c, (sx, sy, tile, tile))
                margin = 2
                if bld.closet_opened:
                    # Open closet - dark inside with door swung open
                    pygame.draw.rect(
                        surface,
                        (40, 28, 18),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        border_radius=1,
                    )
                    # Open door (thin strip on the right side)
                    pygame.draw.rect(
                        surface,
                        (160, 110, 60),
                        (sx + tile - margin - 4, sy + margin, 4, tile - margin * 2),
                    )
                else:
                    # Closed closet - wooden double doors
                    pygame.draw.rect(
                        surface,
                        (160, 110, 60),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        border_radius=2,
                    )
                    # Door line down the middle
                    pygame.draw.line(
                        surface,
                        (120, 80, 40),
                        (sx + tile // 2, sy + margin),
                        (sx + tile // 2, sy + tile - margin),
                        1,
                    )
                    # Two little doorknobs
                    pygame.draw.circle(
                        surface, (200, 180, 50), (sx + tile // 2 - 3, sy + tile // 2), 2
                    )
                    pygame.draw.circle(
                        surface, (200, 180, 50), (sx + tile // 2 + 3, sy + tile // 2), 2
                    )
                    # Outline
                    pygame.draw.rect(
                        surface,
                        (100, 65, 30),
                        (
                            sx + margin,
                            sy + margin,
                            tile - margin * 2,
                            tile - margin * 2,
                        ),
                        1,
                        border_radius=2,
                    )

    # Draw the resident burrb (sitting or chasing!)
    if bld.resident_x > 0:
        res_sx = int(bld.resident_x - cam_x)
        res_sy = int(bld.resident_y - cam_y)
        if -30 < res_sx < SCREEN_WIDTH + 30 and -30 < res_sy < SCREEN_HEIGHT + 30:
            res_color = bld.resident_color
            res_detail = bld.resident_detail
            size = 16
            if not bld.resident_angry:
                # Sitting on sofa - draw facing the TV (upward)
                # Body
                pygame.draw.rect(
                    surface,
                    res_color,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    BLACK,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    1,
                    border_radius=2,
                )
                # Eye (looking at TV)
                pygame.draw.circle(surface, res_detail, (res_sx + 2, res_sy - 3), 2)
                # Spikes
                for i in range(3):
                    spike_x = res_sx - 4 + i * 4
                    pygame.draw.polygon(
                        surface,
                        res_color,
                        [
                            (spike_x - 1, res_sy - size // 2),
                            (spike_x, res_sy - size // 2 - 5),
                            (spike_x + 1, res_sy - size // 2),
                        ],
                    )
            else:
                # ANGRY! Chasing the player!
                # Body (slightly red-tinted from anger)
                angry_color = (
                    min(255, res_color[0] + 40),
                    max(0, res_color[1] - 20),
                    max(0, res_color[2] - 20),
                )
                # Walking animation
                leg_off = math.sin(bld.resident_walk_frame * 0.3) * 3
                # Legs
                pygame.draw.line(
                    surface,
                    BLACK,
                    (res_sx - 3, res_sy + size // 2),
                    (res_sx - 3 + leg_off, res_sy + size // 2 + 6),
                    2,
                )
                pygame.draw.line(
                    surface,
                    BLACK,
                    (res_sx + 3, res_sy + size // 2),
                    (res_sx + 3 - leg_off, res_sy + size // 2 + 6),
                    2,
                )
                # Body
                pygame.draw.rect(
                    surface,
                    angry_color,
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    border_radius=2,
                )
                pygame.draw.rect(
                    surface,
                    (180, 30, 30),
                    (res_sx - size // 2, res_sy - size // 2, size, size),
                    1,
                    border_radius=2,
                )
                # Angry eyes (X shaped!)
                pygame.draw.line(
                    surface, (200, 0, 0), (res_sx, res_sy - 4), (res_sx + 4, res_sy), 2
                )
                pygame.draw.line(
                    surface, (200, 0, 0), (res_sx + 4, res_sy - 4), (res_sx, res_sy), 2
                )
                # Angry spikes (pointier)
                for i in range(3):
                    spike_x = res_sx - 4 + i * 4
                    pygame.draw.polygon(
                        surface,
                        angry_color,
                        [
                            (spike_x - 1, res_sy - size // 2),
                            (spike_x, res_sy - size // 2 - 7),
                            (spike_x + 1, res_sy - size // 2),
                        ],
                    )

    # Draw the potato chips (if not stolen!)
    if not bld.chips_stolen and bld.chips_x > 0:
        chip_sx = int(bld.chips_x - cam_x)
        chip_sy = int(bld.chips_y - cam_y)
        if -20 < chip_sx < SCREEN_WIDTH + 20 and -20 < chip_sy < SCREEN_HEIGHT + 20:
            # Chip bag (small orange/yellow rectangle)
            pygame.draw.rect(
                surface,
                (220, 160, 30),
                (chip_sx - 5, chip_sy - 6, 10, 12),
                border_radius=2,
            )
            # Red stripe on bag
            pygame.draw.rect(
                surface,
                (200, 40, 40),
                (chip_sx - 5, chip_sy - 2, 10, 4),
            )
            # "C" for chips
            pygame.draw.rect(
                surface,
                (255, 220, 80),
                (chip_sx - 3, chip_sy - 5, 6, 3),
                border_radius=1,
            )
            # Outline
            pygame.draw.rect(
                surface,
                (150, 100, 20),
                (chip_sx - 5, chip_sy - 6, 10, 12),
                1,
                border_radius=2,
            )

    # Draw the burrb inside
    burrb_sx = px - cam_x
    burrb_sy = py - cam_y
    # Use the regular burrb drawing function with adjusted coordinates
    draw_burrb(surface, px, py, cam_x, cam_y, facing_left, walk_frame)


def draw_interior_first_person(surface, bld, px, py, angle):
    """
    Draw the inside of a building in first person mode!
    Uses raycasting just like outside, but on the building's
    interior grid instead of the world grid.
    """
    tile = bld.interior_tile
    half_h = SCREEN_HEIGHT // 2

    # Ceiling gradient (indoor lighting)
    ceil_top = (60, 55, 50)
    ceil_bot = (120, 110, 100)
    for y in range(half_h):
        t = y / half_h
        r = int(ceil_top[0] + (ceil_bot[0] - ceil_top[0]) * t)
        g = int(ceil_top[1] + (ceil_bot[1] - ceil_top[1]) * t)
        b = int(ceil_top[2] + (ceil_bot[2] - ceil_top[2]) * t)
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Floor gradient
    floor_top_c = (
        max(0, bld.floor_color[0] - 40),
        max(0, bld.floor_color[1] - 40),
        max(0, bld.floor_color[2] - 40),
    )
    floor_bot_c = bld.floor_color
    for y in range(half_h, SCREEN_HEIGHT):
        t = (y - half_h) / half_h
        r = int(floor_top_c[0] + (floor_bot_c[0] - floor_top_c[0]) * t)
        g = int(floor_top_c[1] + (floor_bot_c[1] - floor_top_c[1]) * t)
        b = int(floor_bot_c[2] + (floor_bot_c[2] - floor_top_c[2]) * t)
        # Clamp values
        r = max(0, min(255, r))
        g = max(0, min(255, g))
        b = max(0, min(255, b))
        pygame.draw.line(surface, (r, g, b), (0, y), (SCREEN_WIDTH, y))

    # Raycast through the interior grid
    ray_angle = angle - HALF_FOV

    for ray_num in range(NUM_RAYS):
        ra = ray_angle
        sin_a = math.sin(ra)
        cos_a = math.cos(ra)
        if abs(cos_a) < 0.00001:
            cos_a = 0.00001
        if abs(sin_a) < 0.00001:
            sin_a = 0.00001

        map_x = int(px) // tile
        map_y = int(py) // tile

        delta_dist_x = abs(tile / cos_a)
        if cos_a > 0:
            step_x = 1
            side_dist_x = (map_x * tile + tile - px) / abs(cos_a)
        else:
            step_x = -1
            side_dist_x = (px - map_x * tile) / abs(cos_a)

        delta_dist_y = abs(tile / sin_a)
        if sin_a > 0:
            step_y = 1
            side_dist_y = (map_y * tile + tile - py) / abs(sin_a)
        else:
            step_y = -1
            side_dist_y = (py - map_y * tile) / abs(sin_a)

        hit = False
        hit_side = 0
        dist = 0
        hit_type = Building.WALL

        for _ in range(40):
            if side_dist_x < side_dist_y:
                dist = side_dist_x
                side_dist_x += delta_dist_x
                map_x += step_x
                hit_side = 0
            else:
                dist = side_dist_y
                side_dist_y += delta_dist_y
                map_y += step_y
                hit_side = 1

            if (
                map_x < 0
                or map_x >= bld.interior_w
                or map_y < 0
                or map_y >= bld.interior_h
            ):
                dist = 400
                break

            cell = bld.interior[map_y][map_x]
            if cell in (
                Building.WALL,
                Building.FURNITURE,
                Building.SOFA,
                Building.TV,
                Building.CLOSET,
            ):
                hit_type = cell
                hit = True
                break

        if dist <= 0:
            dist = 0.1

        corrected_dist = dist * math.cos(ra - angle)
        if corrected_dist <= 0:
            corrected_dist = 0.1

        wall_height = min(SCREEN_HEIGHT, 12000 / corrected_dist)
        wall_top = half_h - wall_height / 2

        shade = max(0.3, 1.0 - corrected_dist / 400)
        if hit_side == 1:
            shade *= 0.8

        screen_x = ray_num

        if hit:
            if hit_type == Building.WALL:
                base = bld.wall_interior_color
            elif hit_type == Building.SOFA:
                base = (80, 120, 200)  # blue sofa
            elif hit_type == Building.TV:
                base = (30, 30, 30)  # dark TV screen
            elif hit_type == Building.CLOSET:
                if bld.closet_opened:
                    base = (60, 40, 25)  # dark open closet
                else:
                    base = (160, 110, 60)  # wooden closet door
            else:
                base = bld.furniture_color

            r = min(255, int(base[0] * shade))
            g = min(255, int(base[1] * shade))
            b = min(255, int(base[2] * shade))
            pygame.draw.rect(
                surface, (r, g, b), (screen_x, int(wall_top), 1, int(wall_height))
            )

            # TV screen glow (bright blue-white in the middle)
            if hit_type == Building.TV and wall_height > 10:
                glow_h = int(wall_height * 0.6)
                glow_top = int(wall_top + wall_height * 0.15)
                glow_color = (
                    min(255, int(150 * shade)),
                    min(255, int(200 * shade)),
                    min(255, int(255 * shade)),
                )
                pygame.draw.rect(surface, glow_color, (screen_x, glow_top, 1, glow_h))

            # Door tile gets a special brown color
            if map_y == bld.interior_door_row and map_x == bld.interior_door_col:
                dr = min(255, int(160 * shade))
                dg = min(255, int(100 * shade))
                db = min(255, int(40 * shade))
                pygame.draw.rect(
                    surface,
                    (dr, dg, db),
                    (screen_x, int(wall_top), 1, int(wall_height)),
                )

        ray_angle += RAY_STEP

    # --- Draw resident burrb and chips as billboards in first person! ---
    # This works like outdoor NPC rendering: calculate angle to object,
    # project onto screen, draw a scaled sprite.
    half_h = SCREEN_HEIGHT // 2

    def _draw_interior_billboard(obj_x, obj_y, draw_func, sprite_w, sprite_h):
        """Helper to draw an object as a billboard in interior first person."""
        # Vector from player to object
        dx_obj = obj_x - px
        dy_obj = obj_y - py
        obj_dist = math.sqrt(dx_obj * dx_obj + dy_obj * dy_obj)
        if obj_dist < 1:
            return  # too close, skip
        # Angle to the object
        obj_angle = math.atan2(dy_obj, dx_obj)
        # Angle difference from view direction
        diff = obj_angle - angle
        # Normalize to -pi..pi
        while diff > math.pi:
            diff -= 2 * math.pi
        while diff < -math.pi:
            diff += 2 * math.pi
        # Only draw if within FOV (plus a little margin)
        if abs(diff) > HALF_FOV + 0.15:
            return
        # Project to screen x
        screen_x = int(SCREEN_WIDTH / 2 + diff * SCREEN_WIDTH / FOV)
        # Perspective-corrected distance
        corrected = obj_dist * math.cos(diff)
        if corrected < 1:
            corrected = 1
        # Scale based on distance
        scale = 8000 / corrected
        sw = max(4, int(sprite_w * scale / 100))
        sh = max(4, int(sprite_h * scale / 100))
        # Screen position (centered)
        sx = screen_x - sw // 2
        sy = half_h - sh // 2 + int(sh * 0.1)  # slightly below center (on floor)
        # Call the draw function
        draw_func(surface, sx, sy, sw, sh, corrected)

    # Draw the resident burrb in first person!
    if bld.resident_x > 0:

        def _draw_resident_fp(surf, sx, sy, sw, sh, dist):
            shade = max(0.3, 1.0 - dist / 400)
            rc = bld.resident_color
            rd = bld.resident_detail
            if not bld.resident_angry:
                # Normal resident - colored body
                body_color = (
                    int(rc[0] * shade),
                    int(rc[1] * shade),
                    int(rc[2] * shade),
                )
                pygame.draw.rect(surf, body_color, (sx, sy, sw, sh), border_radius=2)
                # Eye
                eye_r = max(1, sw // 6)
                pygame.draw.circle(
                    surf,
                    (int(rd[0] * shade), int(rd[1] * shade), int(rd[2] * shade)),
                    (sx + sw // 2 + eye_r, sy + sh // 3),
                    eye_r,
                )
                # Spikes on top
                for i in range(3):
                    spike_x = sx + sw // 4 + i * (sw // 4)
                    pygame.draw.polygon(
                        surf,
                        body_color,
                        [
                            (spike_x - 1, sy),
                            (spike_x, sy - max(2, sh // 4)),
                            (spike_x + 1, sy),
                        ],
                    )
            else:
                # ANGRY resident - red tinted, X eyes!
                angry_c = (
                    min(255, int((rc[0] + 40) * shade)),
                    max(0, int((rc[1] - 20) * shade)),
                    max(0, int((rc[2] - 20) * shade)),
                )
                pygame.draw.rect(surf, angry_c, (sx, sy, sw, sh), border_radius=2)
                # Red outline
                pygame.draw.rect(
                    surf,
                    (int(180 * shade), int(30 * shade), int(30 * shade)),
                    (sx, sy, sw, sh),
                    max(1, sw // 8),
                    border_radius=2,
                )
                # X eyes
                ex = sx + sw // 2
                ey = sy + sh // 3
                er = max(2, sw // 5)
                red_eye = (int(200 * shade), 0, 0)
                pygame.draw.line(
                    surf, red_eye, (ex - er, ey - er), (ex + er, ey + er), 2
                )
                pygame.draw.line(
                    surf, red_eye, (ex + er, ey - er), (ex - er, ey + er), 2
                )
                # Angry spikes (pointier)
                for i in range(3):
                    spike_x = sx + sw // 4 + i * (sw // 4)
                    pygame.draw.polygon(
                        surf,
                        angry_c,
                        [
                            (spike_x - 1, sy),
                            (spike_x, sy - max(3, sh // 3)),
                            (spike_x + 1, sy),
                        ],
                    )
                # Walking legs
                if bld.resident_walk_frame > 0:
                    leg_off = int(
                        math.sin(bld.resident_walk_frame * 0.3) * max(2, sw // 5)
                    )
                    leg_color = (int(40 * shade), int(40 * shade), int(40 * shade))
                    pygame.draw.line(
                        surf,
                        leg_color,
                        (sx + sw // 3, sy + sh),
                        (sx + sw // 3 + leg_off, sy + sh + max(2, sh // 3)),
                        max(1, sw // 8),
                    )
                    pygame.draw.line(
                        surf,
                        leg_color,
                        (sx + 2 * sw // 3, sy + sh),
                        (sx + 2 * sw // 3 - leg_off, sy + sh + max(2, sh // 3)),
                        max(1, sw // 8),
                    )

        _draw_interior_billboard(
            bld.resident_x, bld.resident_y, _draw_resident_fp, 16, 16
        )

    # Draw the chip bag in first person!
    if not bld.chips_stolen and bld.chips_x > 0:

        def _draw_chips_fp(surf, sx, sy, sw, sh, dist):
            shade = max(0.3, 1.0 - dist / 400)
            # Orange/yellow chip bag
            bag_color = (int(220 * shade), int(160 * shade), int(30 * shade))
            pygame.draw.rect(surf, bag_color, (sx, sy, sw, sh), border_radius=2)
            # Red stripe
            stripe_h = max(1, sh // 3)
            stripe_y = sy + sh // 3
            pygame.draw.rect(
                surf,
                (int(200 * shade), int(40 * shade), int(40 * shade)),
                (sx, stripe_y, sw, stripe_h),
            )
            # Outline
            pygame.draw.rect(
                surf,
                (int(150 * shade), int(100 * shade), int(20 * shade)),
                (sx, sy, sw, sh),
                1,
                border_radius=2,
            )

        _draw_interior_billboard(bld.chips_x, bld.chips_y, _draw_chips_fp, 10, 12)


def draw_jumpscare(surface, frame):
    """
    Draw a TERRIFYING birb jump scare!
    A scary birb bursts out with its mouth wide open showing
    sharp bloody teeth. The screen shakes and flashes!
    """
    sw = SCREEN_WIDTH
    sh = SCREEN_HEIGHT

    # Screen flash effect (red flash at the start!)
    if frame < 8:
        flash_alpha = max(0, 255 - frame * 32)
        flash_surf = pygame.Surface((sw, sh))
        flash_surf.fill((200, 0, 0))
        flash_surf.set_alpha(flash_alpha)
        surface.blit(flash_surf, (0, 0))

    # Screen shake
    shake_x = random.randint(-8, 8) if frame < 60 else 0
    shake_y = random.randint(-8, 8) if frame < 60 else 0

    # The scary birb grows from center, reaching full size quickly
    grow = min(1.0, frame / 12.0)
    size = int(350 * grow)
    if size < 10:
        return

    # Center of the birb face
    cx = sw // 2 + shake_x
    cy = sh // 2 + shake_y - 20

    # Dark background overlay
    dark = pygame.Surface((sw, sh))
    dark.fill((10, 0, 0))
    dark.set_alpha(200)
    surface.blit(dark, (0, 0))

    # === THE SCARY BIRB ===
    # Body (big dark shape)
    body_w = size
    body_h = int(size * 1.1)
    body_color = (40, 35, 50)
    pygame.draw.ellipse(
        surface,
        body_color,
        (cx - body_w // 2, cy - body_h // 3, body_w, body_h),
    )

    # Spiky hair on top (jagged, scary!)
    spike_base_y = cy - body_h // 3
    num_spikes = 7
    for i in range(num_spikes):
        spike_x = cx - size // 3 + i * (size * 2 // 3) // max(1, num_spikes - 1)
        spike_h = random.randint(size // 5, size // 3)
        spike_w = size // 10
        pygame.draw.polygon(
            surface,
            (20, 15, 30),
            [
                (spike_x - spike_w, spike_base_y + 5),
                (spike_x + random.randint(-3, 3), spike_base_y - spike_h),
                (spike_x + spike_w, spike_base_y + 5),
            ],
        )

    # EYES - big, angry, glowing red!
    eye_y = cy + size // 12
    eye_spacing = size // 4
    eye_size = size // 6

    # Left eye (angry red glow)
    pygame.draw.circle(surface, (180, 0, 0), (cx - eye_spacing, eye_y), eye_size + 4)
    pygame.draw.circle(surface, (255, 20, 20), (cx - eye_spacing, eye_y), eye_size)
    # Tiny pupil (makes it scarier)
    pygame.draw.circle(surface, (0, 0, 0), (cx - eye_spacing, eye_y), eye_size // 3)
    # Angry eyebrow
    pygame.draw.line(
        surface,
        (20, 10, 10),
        (cx - eye_spacing - eye_size, eye_y - eye_size - 4),
        (cx - eye_spacing + eye_size, eye_y - eye_size + 6),
        max(2, size // 40),
    )

    # Right eye
    pygame.draw.circle(surface, (180, 0, 0), (cx + eye_spacing, eye_y), eye_size + 4)
    pygame.draw.circle(surface, (255, 20, 20), (cx + eye_spacing, eye_y), eye_size)
    pygame.draw.circle(surface, (0, 0, 0), (cx + eye_spacing, eye_y), eye_size // 3)
    # Angry eyebrow
    pygame.draw.line(
        surface,
        (20, 10, 10),
        (cx + eye_spacing - eye_size, eye_y - eye_size + 6),
        (cx + eye_spacing + eye_size, eye_y - eye_size - 4),
        max(2, size // 40),
    )

    # === THE MOUTH - WIDE OPEN WITH SHARP BLOODY TEETH ===
    mouth_y = cy + size // 3
    mouth_w = int(size * 0.7)
    mouth_h = int(size * 0.45)

    # Mouth opening (dark gaping hole)
    pygame.draw.ellipse(
        surface,
        (30, 0, 0),
        (cx - mouth_w // 2, mouth_y - mouth_h // 4, mouth_w, mouth_h),
    )
    # Inner mouth (red/dark red throat)
    inner_w = int(mouth_w * 0.7)
    inner_h = int(mouth_h * 0.6)
    pygame.draw.ellipse(
        surface,
        (100, 10, 10),
        (cx - inner_w // 2, mouth_y + mouth_h // 8, inner_w, inner_h),
    )

    # SHARP TEETH - TOP ROW
    num_teeth = 9
    tooth_w = mouth_w // (num_teeth + 1)
    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        # Teeth are triangular and jagged
        tooth_h = random.randint(size // 8, size // 5)
        # White-ish tooth with blood
        tooth_color = (240, 235, 220)
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2, mouth_y - mouth_h // 8),
                (tx + random.randint(-2, 2), mouth_y - mouth_h // 8 + tooth_h),
                (tx + tooth_w // 2, mouth_y - mouth_h // 8),
            ],
        )
        # Blood dripping from some teeth!
        if random.random() > 0.4:
            blood_len = random.randint(size // 12, size // 6)
            pygame.draw.line(
                surface,
                (180, 0, 0),
                (tx, mouth_y - mouth_h // 8 + tooth_h),
                (
                    tx + random.randint(-3, 3),
                    mouth_y - mouth_h // 8 + tooth_h + blood_len,
                ),
                max(1, size // 80),
            )

    # SHARP TEETH - BOTTOM ROW (pointing up)
    for i in range(num_teeth):
        tx = (
            cx
            - mouth_w // 2
            + tooth_w // 2
            + i * (mouth_w - tooth_w) // max(1, num_teeth - 1)
        )
        tooth_h = random.randint(size // 8, size // 5)
        tooth_color = (235, 230, 215)
        bottom_y = mouth_y + mouth_h - mouth_h // 4
        pygame.draw.polygon(
            surface,
            tooth_color,
            [
                (tx - tooth_w // 2, bottom_y),
                (tx + random.randint(-2, 2), bottom_y - tooth_h),
                (tx + tooth_w // 2, bottom_y),
            ],
        )
        # More blood!
        if random.random() > 0.5:
            blood_len = random.randint(size // 15, size // 8)
            pygame.draw.line(
                surface,
                (200, 10, 10),
                (tx, bottom_y - tooth_h),
                (tx + random.randint(-2, 2), bottom_y - tooth_h - blood_len),
                max(1, size // 80),
            )

    # Beak edges (orange beak outline around mouth area)
    beak_color = (200, 120, 20)
    # Upper beak
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 5, mouth_y - mouth_h // 2, mouth_w + 10, mouth_h // 2),
        0,
        math.pi,
        max(2, size // 50),
    )
    # Lower beak
    pygame.draw.arc(
        surface,
        beak_color,
        (cx - mouth_w // 2 - 5, mouth_y + mouth_h // 2, mouth_w + 10, mouth_h // 2),
        math.pi,
        math.pi * 2,
        max(2, size // 50),
    )

    # Blood splatter around the mouth
    for _ in range(8):
        bx = cx + random.randint(-mouth_w // 2, mouth_w // 2)
        by = mouth_y + random.randint(-mouth_h // 3, mouth_h)
        br = random.randint(2, max(3, size // 40))
        pygame.draw.circle(surface, (180, 0, 0), (bx, by), br)

    # Scary text that shakes!
    scare_font = pygame.font.Font(None, max(24, size // 4))
    scare_text = scare_font.render("AAAAAHHH!!!", True, (255, 30, 30))
    text_x = sw // 2 - scare_text.get_width() // 2 + random.randint(-5, 5)
    text_y = 40 + random.randint(-3, 3)
    # Shadow
    scare_shadow = scare_font.render("AAAAAHHH!!!", True, (80, 0, 0))
    surface.blit(scare_shadow, (text_x + 2, text_y + 2))
    surface.blit(scare_text, (text_x, text_y))

    # Second text at bottom
    if frame > 20:
        sub_font = pygame.font.Font(None, max(20, size // 6))
        sub_text = sub_font.render(
            "A BIRB WAS HIDING IN THE CLOSET!", True, (255, 100, 100)
        )
        sub_x = sw // 2 - sub_text.get_width() // 2 + random.randint(-3, 3)
        sub_y = sh - 80 + random.randint(-2, 2)
        surface.blit(sub_text, (sub_x, sub_y))


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

# First person mode!
# "angle" is the direction the burrb is looking, measured in
# radians. 0 = looking right, pi/2 = looking down, pi = left, etc.
# Think of it like a compass but using math angles.
first_person = False
burrb_angle = 0.0  # start facing right
turn_speed = 0.04  # how fast you rotate (radians per frame)

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
# hits an NPC, that NPC turns into a rock! Like a magic petrifying tongue.
tongue_active = False  # is the tongue currently shooting out?
tongue_length = 0.0  # how far the tongue has extended so far
tongue_max_length = 120.0  # max reach of the tongue
tongue_speed = 8.0  # how fast the tongue extends per frame
tongue_retracting = False  # is the tongue pulling back in?
tongue_angle = 0.0  # direction the tongue is going (radians)
tongue_hit_npc = None  # did we hit someone? (for visual feedback)

# Chip collecting!
# Every building has a bag of chips. Steal them all!
chips_collected = 0

# Jump scare from closets!
# When you open a closet and get unlucky, a scary birb jumps out!
jumpscare_timer = 0  # frames remaining for jump scare (0 = not active)
jumpscare_frame = 0  # animation frame counter for the scare
JUMPSCARE_DURATION = 90  # 1.5 seconds at 60fps
closet_msg_timer = 0  # frames to show "found chips!" message

# ============================================================
# ABILITIES!
# ============================================================
# You can spend potato chips to unlock awesome new powers!
# Each ability has a cost, an unlocked flag, and some have
# active timers (they only last a few seconds when used).
#
# Ability list:
#   DASH        - 2 chips - Press SHIFT to zoom forward!
#   SUPER SPEED - 3 chips - Hold SHIFT to run really fast!
#   MEGA TONGUE - 3 chips - Tongue reaches twice as far!
#   FREEZE      - 4 chips - Press F to freeze all nearby burrbs!
#   INVISIBILITY- 5 chips - Press I to become invisible!
#   GIANT MODE  - 6 chips - Press G to become HUGE!

# The shop menu
shop_open = False  # is the shop screen showing?
shop_cursor = 0  # which ability is highlighted in the shop

# Ability definitions: (name, cost, key_hint, description)
ABILITIES = [
    ("Dash", 2, "SHIFT", "Zoom forward super fast!"),
    ("Super Speed", 3, "SHIFT hold", "Run way faster!"),
    ("Mega Tongue", 3, "auto", "Tongue reaches 2x farther!"),
    ("Freeze", 4, "F", "Freeze all nearby burrbs!"),
    ("Invisibility", 5, "I", "Turn invisible for 5 sec!"),
    ("Giant Mode", 6, "G", "Become HUGE for 8 sec!"),
]

# Which abilities have been unlocked (bought with chips)
ability_unlocked = [False] * len(ABILITIES)

# Active ability timers (frames remaining, 0 = not active)
# Some abilities are always-on once unlocked (Mega Tongue, Super Speed),
# others are timed bursts.
dash_cooldown = 0  # frames until dash can be used again
dash_active = 0  # frames remaining in a dash burst
freeze_timer = 0  # frames remaining for freeze effect
invisible_timer = 0  # frames remaining for invisibility
giant_timer = 0  # frames remaining for giant mode
giant_scale = 1.0  # current size multiplier (smoothly grows/shrinks)

# Font for UI
font = pygame.font.Font(None, 28)
title_font = pygame.font.Font(None, 42)
shop_font = pygame.font.Font(None, 32)
shop_title_font = pygame.font.Font(None, 48)

# ============================================================
# TOUCH CONTROLS
# ============================================================
# Touch support for phones, tablets, and touchscreen computers!
# Tap the screen to move, use on-screen buttons for actions.
# Touch is auto-detected: buttons appear when you touch the screen.

touch_active = False  # has the player used touch? (shows buttons)
touch_move_target = None  # (x, y) world position to walk toward, or None
touch_held = False  # is a finger currently touching the screen?
touch_pos = (0, 0)  # current touch position on screen
touch_start_pos = (0, 0)  # where the finger first touched
touch_finger_id = None  # track which finger is the main one

# On-screen button layout (right side of screen)
# Each button: (label, center_x, center_y, radius, key_action)
TOUCH_BTN_RADIUS = 28
TOUCH_BTN_PAD = 8
_br = TOUCH_BTN_RADIUS
_bx = SCREEN_WIDTH - _br - 12  # right edge
_bx2 = _bx - _br * 2 - TOUCH_BTN_PAD  # second column from right

TOUCH_BUTTONS = [
    # Right column (main actions)
    ("E", _bx, SCREEN_HEIGHT - _br - 12, _br, "action_e"),
    ("O", _bx, SCREEN_HEIGHT - _br * 3 - 20, _br, "action_o"),
    # Second column
    ("VIEW", _bx2, SCREEN_HEIGHT - _br - 12, _br, "toggle_view"),
    ("SHOP", _bx2, SCREEN_HEIGHT - _br * 3 - 20, _br, "toggle_shop"),
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
]

touch_btn_pressed = None  # which button is currently being pressed


def touch_hit_button(tx, ty):
    """Check if a touch at (tx, ty) hits any on-screen button.
    Returns the action string or None."""
    for label, bx, by, br, action in TOUCH_BUTTONS:
        dx = tx - bx
        dy = ty - by
        if dx * dx + dy * dy <= (br + 8) * (br + 8):
            return action
    # Check ability buttons only if unlocked
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        # F=index 3, I=index 4, G=index 5
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            dx = tx - bx
            dy = ty - by
            if dx * dx + dy * dy <= (br + 8) * (br + 8):
                return action
    return None


def draw_touch_buttons(surface):
    """Draw the on-screen touch buttons."""
    btn_font = pygame.font.Font(None, 24)

    for label, bx, by, br, action in TOUCH_BUTTONS:
        # Button background (semi-transparent circle)
        btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
        pressed = touch_btn_pressed == action
        if pressed:
            pygame.draw.circle(btn_surf, (255, 255, 255, 160), (br + 1, br + 1), br)
        else:
            pygame.draw.circle(btn_surf, (255, 255, 255, 70), (br + 1, br + 1), br)
        pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
        surface.blit(btn_surf, (bx - br - 1, by - br - 1))
        # Label
        txt = btn_font.render(label, True, WHITE)
        surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # Ability buttons (only show if unlocked)
    for i, (label, bx, by, br, action) in enumerate(TOUCH_ABILITY_BUTTONS):
        ability_idx = i + 3
        if ability_idx < len(ability_unlocked) and ability_unlocked[ability_idx]:
            btn_surf = pygame.Surface((br * 2 + 2, br * 2 + 2), pygame.SRCALPHA)
            pressed = touch_btn_pressed == action
            # Color-code ability buttons
            colors = [(100, 180, 255, 100), (180, 100, 255, 100), (100, 255, 100, 100)]
            bg_color = colors[i] if i < len(colors) else (255, 255, 255, 70)
            if pressed:
                bg_color = (bg_color[0], bg_color[1], bg_color[2], 200)
            pygame.draw.circle(btn_surf, bg_color, (br + 1, br + 1), br)
            pygame.draw.circle(btn_surf, (255, 255, 255, 120), (br + 1, br + 1), br, 2)
            surface.blit(btn_surf, (bx - br - 1, by - br - 1))
            txt = btn_font.render(label, True, WHITE)
            surface.blit(txt, (bx - txt.get_width() // 2, by - txt.get_height() // 2))

    # Draw move target indicator if active (small pulsing circle)
    if touch_move_target is not None and not first_person:
        tgt_x, tgt_y = touch_move_target
        if inside_building is not None:
            # Interior coords to screen coords
            icam_x = interior_x - SCREEN_WIDTH // 2
            icam_y = interior_y - SCREEN_HEIGHT // 2
            sx = int(tgt_x - icam_x)
            sy = int(tgt_y - icam_y)
        else:
            # World coords to screen coords
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
# COLLISION - so the burrb can't walk through buildings
# ============================================================
def can_move_to(x, y):
    """Check if the burrb can move to position (x, y)."""
    # World boundaries
    if x < 20 or x > WORLD_WIDTH - 20 or y < 20 or y > WORLD_HEIGHT - 20:
        return False
    # Building collision (use a small rect around the burrb's feet)
    burrb_rect = pygame.Rect(x - 10, y + 5, 20, 14)
    for b in buildings:
        if burrb_rect.colliderect(b.get_rect()):
            return False
    return True


def draw_shop(surface):
    """
    Draw the ability shop screen!
    This is a cool menu where you spend your potato chips
    to unlock awesome new powers for your burrb.
    """
    # Dark semi-transparent overlay
    overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
    overlay.fill((0, 0, 0, 180))
    surface.blit(overlay, (0, 0))

    # Shop box
    box_w = 500
    box_h = 420
    box_x = (SCREEN_WIDTH - box_w) // 2
    box_y = (SCREEN_HEIGHT - box_h) // 2

    # Background with border
    pygame.draw.rect(
        surface, (40, 30, 60), (box_x, box_y, box_w, box_h), border_radius=12
    )
    pygame.draw.rect(
        surface, (100, 80, 160), (box_x, box_y, box_w, box_h), 3, border_radius=12
    )

    # Title
    title = shop_title_font.render("CHIP SHOP", True, (255, 220, 50))
    surface.blit(title, (box_x + box_w // 2 - title.get_width() // 2, box_y + 12))

    # Chip count
    chip_str = f"Your chips: {chips_collected}"
    chip_txt = shop_font.render(chip_str, True, (255, 200, 50))
    surface.blit(chip_txt, (box_x + box_w // 2 - chip_txt.get_width() // 2, box_y + 52))

    # Abilities list
    for i, (name, cost, key_hint, desc) in enumerate(ABILITIES):
        row_y = box_y + 90 + i * 52
        # Highlight selected row
        if i == shop_cursor:
            pygame.draw.rect(
                surface,
                (80, 60, 120),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                border_radius=6,
            )
            pygame.draw.rect(
                surface,
                (140, 120, 200),
                (box_x + 10, row_y - 4, box_w - 20, 48),
                2,
                border_radius=6,
            )

        # Already unlocked?
        if ability_unlocked[i]:
            name_color = (100, 220, 100)  # green = owned
            status = "OWNED"
            status_color = (100, 220, 100)
        elif chips_collected >= cost:
            name_color = (255, 255, 255)  # white = can buy
            status = f"{cost} chips"
            status_color = (255, 200, 50)
        else:
            name_color = (120, 120, 120)  # gray = too expensive
            status = f"{cost} chips"
            status_color = (150, 80, 80)

        # Name
        name_txt = shop_font.render(name, True, name_color)
        surface.blit(name_txt, (box_x + 24, row_y))

        # Key hint
        if ability_unlocked[i]:
            key_txt = font.render(f"[{key_hint}]", True, (150, 200, 150))
        else:
            key_txt = font.render(f"[{key_hint}]", True, (100, 100, 100))
        surface.blit(key_txt, (box_x + 24, row_y + 24))

        # Description
        desc_txt = font.render(desc, True, (180, 180, 200))
        surface.blit(desc_txt, (box_x + 140, row_y + 24))

        # Cost / status on the right
        cost_txt = shop_font.render(status, True, status_color)
        surface.blit(cost_txt, (box_x + box_w - cost_txt.get_width() - 20, row_y + 4))

    # Instructions at the bottom
    instr = font.render(
        "UP/DOWN select  |  ENTER buy  |  TAB close", True, (180, 180, 200)
    )
    surface.blit(
        instr, (box_x + box_w // 2 - instr.get_width() // 2, box_y + box_h - 30)
    )


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
            if event.key == pygame.K_ESCAPE:
                if shop_open:
                    shop_open = False
                else:
                    running = False

            # TAB opens/closes the chip shop!
            if event.key == pygame.K_TAB:
                shop_open = not shop_open
                shop_cursor = 0

            # When the shop is open, handle shop navigation
            if shop_open:
                if event.key == pygame.K_UP:
                    shop_cursor = (shop_cursor - 1) % len(ABILITIES)
                if event.key == pygame.K_DOWN:
                    shop_cursor = (shop_cursor + 1) % len(ABILITIES)
                if event.key == pygame.K_RETURN:
                    # Try to buy the selected ability!
                    cost = ABILITIES[shop_cursor][1]
                    if not ability_unlocked[shop_cursor] and chips_collected >= cost:
                        chips_collected -= cost
                        ability_unlocked[shop_cursor] = True
                # Skip all other game input when shop is open
                continue

            if event.key == pygame.K_SPACE:
                first_person = not first_person

            # Press O to shoot the tongue!
            if event.key == pygame.K_o:
                if not tongue_active and inside_building is None:
                    tongue_active = True
                    tongue_length = 0.0
                    tongue_retracting = False
                    tongue_hit_npc = None
                    # Tongue shoots in the direction the burrb is facing
                    if first_person:
                        tongue_angle = burrb_angle
                    else:
                        if facing_left:
                            tongue_angle = math.pi  # left
                        else:
                            tongue_angle = 0.0  # right

            # Press E to enter/exit buildings!
            if event.key == pygame.K_e:
                if inside_building is None:
                    # Try to enter a building (check if near a door)
                    nearby = get_nearby_door_building(burrb_x, burrb_y)
                    if nearby is not None:
                        inside_building = nearby
                        # Save outdoor position so we can come back
                        saved_outdoor_x = burrb_x
                        saved_outdoor_y = burrb_y
                        saved_outdoor_angle = burrb_angle
                        # Move burrb to interior spawn point
                        interior_x = float(nearby.spawn_x)
                        interior_y = float(nearby.spawn_y)
                        burrb_angle = math.pi * 1.5  # face upward (into the room)
                        touch_move_target = None  # clear touch target
                else:
                    # Try to open the closet!
                    bld = inside_building
                    if (
                        not bld.closet_opened
                        and bld.closet_x > 0
                        and jumpscare_timer <= 0
                    ):
                        cl_dx = interior_x - bld.closet_x
                        cl_dy = interior_y - bld.closet_y
                        cl_dist = math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
                        if cl_dist < 30:  # close enough to open!
                            bld.closet_opened = True
                            # 10% chance of jump scare, 90% chance of 2 chips!
                            if random.random() < 0.1:
                                # JUMP SCARE!
                                bld.closet_jumpscare = True
                                jumpscare_timer = JUMPSCARE_DURATION
                                jumpscare_frame = 0
                            else:
                                # Found 2 chips!
                                chips_collected += 2
                                closet_msg_timer = 120  # show message for 2 sec

                    # Try to steal the chips! (check if near the chip bag)
                    if not bld.chips_stolen and bld.chips_x > 0:
                        chip_dx = interior_x - bld.chips_x
                        chip_dy = interior_y - bld.chips_y
                        chip_dist = math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
                        if chip_dist < 30:  # close enough to grab!
                            bld.chips_stolen = True
                            bld.resident_angry = True  # uh oh!
                            chips_collected += 1

                    # Try to exit the building (check if near interior door)
                    if is_at_interior_door(inside_building, interior_x, interior_y):
                        # Put burrb back outside, just below the door
                        burrb_x = saved_outdoor_x
                        burrb_y = saved_outdoor_y
                        burrb_angle = saved_outdoor_angle
                        inside_building = None
                        touch_move_target = None  # clear touch target

            # --- ABILITY ACTIVATION KEYS ---

            # Press F to FREEZE all nearby burrbs!
            if event.key == pygame.K_f:
                if ability_unlocked[3] and freeze_timer <= 0:
                    freeze_timer = 300  # 5 seconds at 60fps

            # Press I to become INVISIBLE!
            if event.key == pygame.K_i:
                if ability_unlocked[4] and invisible_timer <= 0:
                    invisible_timer = 300  # 5 seconds

            # Press G to become GIANT!
            if event.key == pygame.K_g:
                if ability_unlocked[5] and giant_timer <= 0:
                    giant_timer = 480  # 8 seconds

        # === TOUCH / MOUSE INPUT ===
        # Handle finger touch events (phones/tablets) AND mouse clicks
        # (touchscreen laptops report mouse events for touch)
        if event.type == pygame.FINGERDOWN:
            touch_active = True
            tx = int(event.x * SCREEN_WIDTH)
            ty = int(event.y * SCREEN_HEIGHT)
            touch_held = True
            touch_pos = (tx, ty)
            touch_start_pos = (tx, ty)
            touch_finger_id = event.finger_id

            # Check if a button was pressed
            btn = touch_hit_button(tx, ty)
            if btn is not None:
                touch_btn_pressed = btn
            else:
                touch_btn_pressed = None
                # Tap to move! Convert screen position to world/interior position
                if not shop_open:
                    if inside_building is not None:
                        # Inside a building: figure out interior coords from screen
                        bld = inside_building
                        tile = bld.interior_tile
                        if first_person:
                            # In first-person interior, tapping doesn't set move target
                            pass
                        else:
                            # Top-down interior: screen is centered on burrb
                            icam_x = interior_x - SCREEN_WIDTH // 2
                            icam_y = interior_y - SCREEN_HEIGHT // 2
                            touch_move_target = (tx + icam_x, ty + icam_y)
                    elif first_person:
                        # First person outdoor: tap left/right to turn, upper to walk
                        pass  # handled in FINGERMOTION / held check
                    else:
                        # Top-down outdoor: convert screen coords to world coords
                        touch_move_target = (tx + cam_x, ty + cam_y)

        if event.type == pygame.FINGERMOTION:
            if event.finger_id == touch_finger_id:
                tx = int(event.x * SCREEN_WIDTH)
                ty = int(event.y * SCREEN_HEIGHT)
                touch_pos = (tx, ty)

        if event.type == pygame.FINGERUP:
            if event.finger_id == touch_finger_id:
                tx = int(event.x * SCREEN_WIDTH)
                ty = int(event.y * SCREEN_HEIGHT)

                # If a button was pressed, trigger its action on release
                if touch_btn_pressed is not None:
                    btn = touch_hit_button(tx, ty)
                    if btn == touch_btn_pressed:
                        # Trigger the button action!
                        if btn == "action_e":
                            # Simulate pressing E
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_e
                            )
                            pygame.event.post(fake_event)
                        elif btn == "action_o":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_o
                            )
                            pygame.event.post(fake_event)
                        elif btn == "toggle_view":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_SPACE
                            )
                            pygame.event.post(fake_event)
                        elif btn == "toggle_shop":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_TAB
                            )
                            pygame.event.post(fake_event)
                        elif btn == "ability_f":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_f
                            )
                            pygame.event.post(fake_event)
                        elif btn == "ability_i":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_i
                            )
                            pygame.event.post(fake_event)
                        elif btn == "ability_g":
                            fake_event = pygame.event.Event(
                                pygame.KEYDOWN, key=pygame.K_g
                            )
                            pygame.event.post(fake_event)

                touch_held = False
                touch_btn_pressed = None
                touch_finger_id = None

        # Also handle mouse clicks as touch (for touchscreen laptops)
        if event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
            touch_active = True
            tx, ty = event.pos
            touch_held = True
            touch_pos = (tx, ty)
            touch_start_pos = (tx, ty)

            btn = touch_hit_button(tx, ty)
            if btn is not None:
                touch_btn_pressed = btn
            else:
                touch_btn_pressed = None
                if not shop_open:
                    if inside_building is not None:
                        if not first_person:
                            icam_x = interior_x - SCREEN_WIDTH // 2
                            icam_y = interior_y - SCREEN_HEIGHT // 2
                            touch_move_target = (tx + icam_x, ty + icam_y)
                    elif not first_person:
                        touch_move_target = (tx + cam_x, ty + cam_y)

        if event.type == pygame.MOUSEMOTION and touch_held:
            touch_pos = event.pos

        if event.type == pygame.MOUSEBUTTONUP and event.button == 1:
            tx, ty = event.pos
            if touch_btn_pressed is not None:
                btn = touch_hit_button(tx, ty)
                if btn == touch_btn_pressed:
                    if btn == "action_e":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_e)
                        )
                    elif btn == "action_o":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_o)
                        )
                    elif btn == "toggle_view":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_SPACE)
                        )
                    elif btn == "toggle_shop":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_TAB)
                        )
                    elif btn == "ability_f":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_f)
                        )
                    elif btn == "ability_i":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_i)
                        )
                    elif btn == "ability_g":
                        pygame.event.post(
                            pygame.event.Event(pygame.KEYDOWN, key=pygame.K_g)
                        )
            touch_held = False
            touch_btn_pressed = None

    # Handle touch input for the shop (tap abilities to select/buy)
    if shop_open and touch_active and touch_held:
        tx, ty = touch_pos
        box_w = 500
        box_h = 420
        box_x = (SCREEN_WIDTH - box_w) // 2
        box_y = (SCREEN_HEIGHT - box_h) // 2
        # Check if tap is inside the shop box
        if box_x <= tx <= box_x + box_w:
            for i in range(len(ABILITIES)):
                row_y = box_y + 90 + i * 52
                if row_y - 4 <= ty <= row_y + 48:
                    if shop_cursor == i:
                        # Already selected - try to buy!
                        cost = ABILITIES[i][1]
                        if not ability_unlocked[i] and chips_collected >= cost:
                            chips_collected -= cost
                            ability_unlocked[i] = True
                    else:
                        shop_cursor = i
                    touch_held = False  # prevent repeated taps
                    break

    # Skip movement and updates when shop is open (game is paused)
    if shop_open:
        draw_shop(screen)
        if touch_active:
            draw_touch_buttons(screen)
        pygame.display.flip()
        clock.tick(FPS)
        continue

    # --- ABILITY TIMERS ---
    # Count down all active ability timers each frame
    if dash_cooldown > 0:
        dash_cooldown -= 1
    if dash_active > 0:
        dash_active -= 1
    if freeze_timer > 0:
        freeze_timer -= 1
    if invisible_timer > 0:
        invisible_timer -= 1
    if giant_timer > 0:
        giant_timer -= 1
    if jumpscare_timer > 0:
        jumpscare_timer -= 1
        jumpscare_frame += 1
    if closet_msg_timer > 0:
        closet_msg_timer -= 1
    # Smoothly grow/shrink for giant mode
    target_giant = 2.5 if giant_timer > 0 else 1.0
    giant_scale += (target_giant - giant_scale) * 0.15

    # --- MOVEMENT ---
    # Check which keys are currently held down
    keys = pygame.key.get_pressed()
    dx = 0
    dy = 0

    # Calculate speed multiplier from abilities!
    speed_mult = 1.0
    # Super Speed: hold SHIFT to go fast (ability index 1)
    if ability_unlocked[1] and keys[pygame.K_LSHIFT]:
        speed_mult = 2.2
    # Dash: press SHIFT for a burst (ability index 0)
    # Dash activates when SHIFT is pressed and we have the dash ability
    if ability_unlocked[0] and not ability_unlocked[1]:
        # Only dash if super speed is NOT unlocked (otherwise SHIFT = super speed)
        if keys[pygame.K_LSHIFT] and dash_cooldown <= 0 and dash_active <= 0:
            dash_active = 12  # 12 frames of dash burst
            dash_cooldown = 45  # cooldown before next dash
    # If BOTH dash and super speed are unlocked, SHIFT = super speed,
    # and dash triggers automatically when you start running fast
    if ability_unlocked[0] and ability_unlocked[1]:
        if keys[pygame.K_LSHIFT] and dash_cooldown <= 0 and dash_active <= 0:
            dash_active = 12
            dash_cooldown = 45
    if dash_active > 0:
        speed_mult = max(speed_mult, 4.0)  # dash is faster than super speed
    # Giant mode makes you a little slower (you're big!)
    if giant_timer > 0:
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
        touch_move_target = None

    if first_person:
        # FIRST PERSON CONTROLS:
        # Left/Right (or A/D) = TURN (rotate which way you're looking)
        # Up/Down (or W/S) = WALK forward/backward in the direction you face
        if keys[pygame.K_LEFT] or keys[pygame.K_a]:
            burrb_angle -= turn_speed
        if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
            burrb_angle += turn_speed

        # Forward/backward movement uses the angle to figure out
        # which direction to actually move in the world.
        # cos(angle) gives the X component, sin(angle) gives the Y component.
        if keys[pygame.K_UP] or keys[pygame.K_w]:
            dx = math.cos(burrb_angle) * current_speed
            dy = math.sin(burrb_angle) * current_speed
        if keys[pygame.K_DOWN] or keys[pygame.K_s]:
            dx = -math.cos(burrb_angle) * current_speed
            dy = -math.sin(burrb_angle) * current_speed

        # Keep angle in the range 0 to 2*pi (a full circle)
        burrb_angle = burrb_angle % (2 * math.pi)

        # Update facing_left for when we switch back to top-down
        facing_left = math.pi / 2 < burrb_angle < 3 * math.pi / 2
    else:
        # TOP-DOWN CONTROLS (the original controls):
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

        # Update the angle to match movement direction, so when you
        # switch to first person you're already looking the right way
        if dx != 0 or dy != 0:
            burrb_angle = math.atan2(dy, dx)

    # --- TOUCH MOVEMENT ---
    # If no keyboard input and we have a touch move target, walk toward it!
    if dx == 0 and dy == 0 and touch_move_target is not None and touch_active:
        target_x, target_y = touch_move_target
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
            if not first_person:
                facing_left = dx < 0
                burrb_angle = math.atan2(dy, dx)
            else:
                burrb_angle = math.atan2(tmy, tmx)
        else:
            # Arrived at target!
            touch_move_target = None

    # First-person touch: swipe to turn, hold upper screen to walk forward
    if touch_active and touch_held and first_person and touch_btn_pressed is None:
        tx, ty = touch_pos
        sx, sy = touch_start_pos
        # Horizontal swipe = turning
        swipe_dx = tx - sx
        if abs(swipe_dx) > 5:
            burrb_angle += swipe_dx * 0.003
            burrb_angle = burrb_angle % (2 * math.pi)
            facing_left = math.pi / 2 < burrb_angle < 3 * math.pi / 2
        # Tap in upper half of screen = walk forward
        if ty < SCREEN_HEIGHT * 0.5:
            dx = math.cos(burrb_angle) * current_speed
            dy = math.sin(burrb_angle) * current_speed

    # Try to move (check collisions) - works the same in both modes!
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
        if invisible_timer > 0:
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
        and invisible_timer <= 0
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

    # --- UPDATE NPCs ---
    # Every frame, each NPC takes a step and maybe changes direction
    # UNLESS they're frozen by the Freeze ability!
    if freeze_timer <= 0:
        for npc in npcs:
            npc.update()
    # (When frozen, NPCs just stand perfectly still - like statues!)

    # --- UPDATE CARS ---
    # Cars drive along roads every frame
    if inside_building is None:
        for car in cars:
            car.update()

    # --- UPDATE TONGUE ---
    # The tongue extends outward, checks if it hits any NPC,
    # then retracts back. If it hits an NPC, that NPC turns to stone!
    # Mega Tongue ability doubles the range!
    effective_tongue_max = tongue_max_length * (2.0 if ability_unlocked[2] else 1.0)
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
                if npc.npc_type == "rock":
                    continue  # already a rock, skip
                ddx = npc.x - tip_x
                ddy = npc.y - tip_y
                hit_dist = math.sqrt(ddx * ddx + ddy * ddy)
                if hit_dist < 16:  # close enough = hit!
                    # PETRIFY! Turn this NPC into a rock!
                    npc.npc_type = "rock"
                    npc.color = (120, 120, 110)  # gray rock color
                    npc.detail_color = (90, 90, 80)  # darker gray
                    npc.speed = 0  # rocks don't move
                    tongue_hit_npc = npc
                    tongue_retracting = True  # tongue snaps back
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

    # --- DRAWING ---
    if inside_building is not None:
        # ========== INSIDE A BUILDING ==========
        if first_person:
            # First person inside the building
            draw_interior_first_person(
                screen, inside_building, interior_x, interior_y, burrb_angle
            )
            # Beak at bottom
            beak_cx = SCREEN_WIDTH // 2
            beak_cy = SCREEN_HEIGHT - 50
            pygame.draw.polygon(
                screen,
                BURRB_ORANGE,
                [
                    (beak_cx - 12, beak_cy + 10),
                    (beak_cx, beak_cy - 8),
                    (beak_cx + 12, beak_cy + 10),
                ],
            )
            pygame.draw.polygon(
                screen,
                (200, 130, 20),
                [
                    (beak_cx - 12, beak_cy + 10),
                    (beak_cx, beak_cy - 8),
                    (beak_cx + 12, beak_cy + 10),
                ],
                2,
            )
        else:
            # Top-down inside the building
            draw_interior_topdown(screen, inside_building, interior_x, interior_y)

        # Door prompt if near interior door
        if is_at_interior_door(inside_building, interior_x, interior_y):
            prompt = font.render("Press E to exit", True, YELLOW)
            prompt_shadow = font.render("Press E to exit", True, BLACK)
            px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
            screen.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
            screen.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))

        # Chip stealing prompt if near the chip bag!
        bld = inside_building
        if not bld.chips_stolen and bld.chips_x > 0:
            chip_dx = interior_x - bld.chips_x
            chip_dy = interior_y - bld.chips_y
            chip_dist = math.sqrt(chip_dx * chip_dx + chip_dy * chip_dy)
            if chip_dist < 30:
                chip_prompt = font.render(
                    "Press E to take chips!", True, (255, 200, 50)
                )
                chip_shadow = font.render("Press E to take chips!", True, BLACK)
                cpx = SCREEN_WIDTH // 2 - chip_prompt.get_width() // 2
                screen.blit(chip_shadow, (cpx + 1, SCREEN_HEIGHT // 2 + 71))
                screen.blit(chip_prompt, (cpx, SCREEN_HEIGHT // 2 + 70))

        # Closet prompt if near the closet!
        if not bld.closet_opened and bld.closet_x > 0:
            cl_dx = interior_x - bld.closet_x
            cl_dy = interior_y - bld.closet_y
            cl_dist = math.sqrt(cl_dx * cl_dx + cl_dy * cl_dy)
            if cl_dist < 30:
                cl_prompt = font.render(
                    "Press E to open closet!", True, (200, 170, 100)
                )
                cl_shadow = font.render("Press E to open closet!", True, BLACK)
                clpx = SCREEN_WIDTH // 2 - cl_prompt.get_width() // 2
                screen.blit(cl_shadow, (clpx + 1, SCREEN_HEIGHT // 2 + 41))
                screen.blit(cl_prompt, (clpx, SCREEN_HEIGHT // 2 + 40))

        # "Found chips in closet!" message
        if closet_msg_timer > 0:
            found_text = font.render(
                "Found 2 chips in the closet!", True, (100, 255, 100)
            )
            found_shadow = font.render("Found 2 chips in the closet!", True, BLACK)
            ftx = SCREEN_WIDTH // 2 - found_text.get_width() // 2
            screen.blit(found_shadow, (ftx + 1, SCREEN_HEIGHT // 2 - 29))
            screen.blit(found_text, (ftx, SCREEN_HEIGHT // 2 - 30))

        # Warning text when resident is angry!
        if bld.resident_angry:
            warn_text = font.render("THE BURRB IS ANGRY!", True, (255, 60, 60))
            warn_shadow = font.render("THE BURRB IS ANGRY!", True, BLACK)
            wpx = SCREEN_WIDTH // 2 - warn_text.get_width() // 2
            # Make it flash by only showing every other half-second
            if (pygame.time.get_ticks() // 400) % 2 == 0:
                screen.blit(warn_shadow, (wpx + 1, 71))
                screen.blit(warn_text, (wpx, 70))

    elif first_person:
        # ========== FIRST PERSON MODE (Doom-style!) ==========
        # Draw the 3D raycasted view and get the depth buffer back
        depth_buf = draw_first_person(screen, burrb_x, burrb_y, burrb_angle)

        # Draw NPCs as billboard sprites in 3D with depth testing!
        # They properly hide behind walls now, just like in Doom!
        draw_npcs_first_person(screen, burrb_x, burrb_y, burrb_angle, npcs, depth_buf)

        # Draw cars as billboard sprites in 3D with depth testing!
        draw_cars_first_person(screen, burrb_x, burrb_y, burrb_angle, cars, depth_buf)

        # Draw the minimap in the corner so you don't get lost
        draw_minimap(screen, burrb_x, burrb_y, burrb_angle)

        # Draw a tiny burrb beak at the bottom of screen (like a nose)
        beak_cx = SCREEN_WIDTH // 2
        beak_cy = SCREEN_HEIGHT - 50
        pygame.draw.polygon(
            screen,
            BURRB_ORANGE,
            [
                (beak_cx - 12, beak_cy + 10),
                (beak_cx, beak_cy - 8),
                (beak_cx + 12, beak_cy + 10),
            ],
        )
        pygame.draw.polygon(
            screen,
            (200, 130, 20),
            [
                (beak_cx - 12, beak_cy + 10),
                (beak_cx, beak_cy - 8),
                (beak_cx + 12, beak_cy + 10),
            ],
            2,
        )

        # Draw the tongue in first-person mode!
        # It shoots out from the beak tip toward the center of the screen
        if tongue_active and tongue_length > 0:
            # Tongue goes from beak tip toward the center/horizon
            eff_tmax = tongue_max_length * (2.0 if ability_unlocked[2] else 1.0)
            t_progress = tongue_length / eff_tmax
            tongue_start_x = beak_cx
            tongue_start_y = beak_cy - 8  # tip of beak
            # Target: center of screen (horizon where it would hit something)
            tongue_target_x = SCREEN_WIDTH // 2
            tongue_target_y = SCREEN_HEIGHT // 2 - 30
            # Interpolate from beak to target based on progress
            tongue_end_x = int(
                tongue_start_x + (tongue_target_x - tongue_start_x) * t_progress
            )
            tongue_end_y = int(
                tongue_start_y + (tongue_target_y - tongue_start_y) * t_progress
            )
            # Tongue gets thinner as it extends further
            tongue_thick = max(2, int(6 * (1.0 - t_progress * 0.5)))
            # Main tongue
            pygame.draw.line(
                screen,
                (220, 80, 100),
                (tongue_start_x, tongue_start_y),
                (tongue_end_x, tongue_end_y),
                tongue_thick,
            )
            # Lighter center
            pygame.draw.line(
                screen,
                (255, 140, 160),
                (tongue_start_x, tongue_start_y),
                (tongue_end_x, tongue_end_y),
                max(1, tongue_thick - 2),
            )
            # Tip blob
            tip_r = max(3, int(6 * (1.0 - t_progress * 0.3)))
            pygame.draw.circle(
                screen, (220, 60, 80), (tongue_end_x, tongue_end_y), tip_r
            )
            pygame.draw.circle(
                screen, (255, 120, 140), (tongue_end_x, tongue_end_y), max(1, tip_r - 2)
            )

    else:
        # ========== TOP-DOWN MODE (the original view) ==========
        # Fill the background (cement/concrete color for the city)
        screen.fill((190, 185, 175))

        # Draw parks
        for park in parks:
            pr = pygame.Rect(park.x - cam_x, park.y - cam_y, park.w, park.h)
            pygame.draw.rect(screen, (100, 180, 80), pr, border_radius=12)
            pygame.draw.rect(screen, DARK_GREEN, pr, 2, border_radius=12)

        # Draw roads
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
            # Freeze effect: draw a blue ice overlay on frozen NPCs
            if freeze_timer > 0 and npc.npc_type != "rock":
                npc_sx = int(npc.x - cam_x)
                npc_sy = int(npc.y - cam_y)
                if (
                    -20 < npc_sx < SCREEN_WIDTH + 20
                    and -20 < npc_sy < SCREEN_HEIGHT + 20
                ):
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
                        pygame.draw.circle(
                            ice_surf, (200, 230, 255, 180), (spx, spy), 2
                        )
                    screen.blit(ice_surf, (npc_sx - 10, npc_sy - 10))

        # Draw the burrb (with Giant Mode and Invisibility effects!)
        if giant_scale > 1.05 or invisible_timer > 0:
            # Draw to a temp surface so we can scale/alpha it
            temp_size = int(60 * giant_scale)
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
            if giant_scale > 1.05:
                new_w = int(temp_size * giant_scale)
                new_h = int(temp_size * giant_scale)
                temp_surf = pygame.transform.scale(temp_surf, (new_w, new_h))
            else:
                new_w = temp_size
                new_h = temp_size
            # Invisibility = semi-transparent + blue tint
            if invisible_timer > 0:
                temp_surf.set_alpha(60)
            # Blit at the correct world position
            blit_x = int(burrb_x - cam_x - new_w // 2)
            blit_y = int(burrb_y - cam_y - new_h // 2)
            screen.blit(temp_surf, (blit_x, blit_y))
        else:
            draw_burrb(screen, burrb_x, burrb_y, cam_x, cam_y, facing_left, walk_frame)

        # Dash trail effect!
        if dash_active > 0:
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
                screen.blit(trail_surf, (trail_x - 8, trail_y - 8))

        # Draw the tongue in top-down mode!
        if tongue_active and tongue_length > 0:
            burrb_sx = burrb_x - cam_x
            burrb_sy = burrb_y - cam_y
            tip_sx = burrb_sx + math.cos(tongue_angle) * tongue_length
            tip_sy = burrb_sy + math.sin(tongue_angle) * tongue_length
            # Tongue is pink/red, gets thicker near the base
            # Base (thick part)
            pygame.draw.line(
                screen,
                (220, 80, 100),
                (int(burrb_sx), int(burrb_sy)),
                (int(tip_sx), int(tip_sy)),
                4,
            )
            # Center line (lighter pink)
            pygame.draw.line(
                screen,
                (255, 140, 160),
                (int(burrb_sx), int(burrb_sy)),
                (int(tip_sx), int(tip_sy)),
                2,
            )
            # Tongue tip (round blob)
            pygame.draw.circle(
                screen,
                (220, 60, 80),
                (int(tip_sx), int(tip_sy)),
                5,
            )
            pygame.draw.circle(
                screen,
                (255, 120, 140),
                (int(tip_sx), int(tip_sy)),
                3,
            )

        # Draw trees in front of burrb (if they're below it)
        for tx, ty, tsize in trees:
            if ty >= burrb_y:
                draw_tree(screen, tx, ty, tsize, cam_x, cam_y)

    # --- UI overlay (shown in both modes) ---
    # Game title
    title_text = title_font.render("Life of a Burrb", True, WHITE)
    title_shadow = title_font.render("Life of a Burrb", True, BLACK)
    screen.blit(title_shadow, (12, 12))
    screen.blit(title_text, (10, 10))

    # Mode indicator
    if inside_building is not None:
        mode_text = font.render("[INSIDE]", True, YELLOW)
        mode_shadow = font.render("[INSIDE]", True, BLACK)
        if first_person:
            help_msg = (
                "A/D turn, W/S walk  |  E take/exit  |  SPACE toggle view  |  ESC quit"
            )
        else:
            help_msg = (
                "Arrows/WASD walk  |  E take/exit  |  SPACE toggle view  |  ESC quit"
            )
    elif first_person:
        mode_text = font.render("[FIRST PERSON]", True, BURRB_ORANGE)
        mode_shadow = font.render("[FIRST PERSON]", True, BLACK)
        help_msg = "A/D turn, W/S walk  |  O tongue  |  E enter  |  TAB shop  |  SPACE top-down"
    else:
        mode_text = font.render("[TOP DOWN]", True, BURRB_LIGHT_BLUE)
        mode_shadow = font.render("[TOP DOWN]", True, BLACK)
        help_msg = "Arrows/WASD walk  |  O tongue  |  E enter  |  TAB shop  |  SPACE first person"

    screen.blit(mode_shadow, (12, 42))
    screen.blit(mode_text, (10, 40))

    # Chips collected counter!
    if chips_collected > 0:
        chip_str = f"Chips: {chips_collected}"
        chip_text = font.render(chip_str, True, (255, 200, 50))
        chip_shadow = font.render(chip_str, True, BLACK)
        chip_x_pos = SCREEN_WIDTH - chip_text.get_width() - 12
        screen.blit(chip_shadow, (chip_x_pos + 1, 12))
        screen.blit(chip_text, (chip_x_pos, 10))
        # Little chip bag icon next to the counter
        icon_x = chip_x_pos - 16
        pygame.draw.rect(screen, (220, 160, 30), (icon_x, 8, 12, 16), border_radius=2)
        pygame.draw.rect(screen, (200, 40, 40), (icon_x, 14, 12, 5))
        pygame.draw.rect(
            screen, (150, 100, 20), (icon_x, 8, 12, 16), 1, border_radius=2
        )

    # Active ability indicators (shown on the right side below chip counter)
    ability_y = 34
    # Show active timed abilities with remaining time bars
    active_abilities = []
    if freeze_timer > 0:
        active_abilities.append(("FREEZE", (100, 180, 255), freeze_timer, 300))
    if invisible_timer > 0:
        active_abilities.append(("INVISIBLE", (180, 140, 255), invisible_timer, 300))
    if giant_timer > 0:
        active_abilities.append(("GIANT", (255, 140, 60), giant_timer, 480))
    if dash_active > 0:
        active_abilities.append(("DASH!", (255, 255, 100), dash_active, 12))
    # Show always-on abilities as small badges
    passive_badges = []
    if ability_unlocked[1]:  # Super Speed
        passive_badges.append(("SPD", (100, 255, 100)))
    if ability_unlocked[2]:  # Mega Tongue
        passive_badges.append(("TNG", (255, 120, 160)))
    if ability_unlocked[0] and not ability_unlocked[1]:  # Dash (only if no super speed)
        passive_badges.append(("DSH", (255, 255, 100)))

    for ab_name, ab_color, ab_timer, ab_max in active_abilities:
        # Background bar
        bar_w = 90
        bar_h = 14
        bar_x = SCREEN_WIDTH - bar_w - 12
        bar_y = ability_y
        pygame.draw.rect(
            screen, (30, 30, 40), (bar_x, bar_y, bar_w, bar_h), border_radius=3
        )
        # Fill bar
        fill_w = int(bar_w * ab_timer / ab_max)
        pygame.draw.rect(
            screen, ab_color, (bar_x, bar_y, fill_w, bar_h), border_radius=3
        )
        # Label
        ab_txt = font.render(ab_name, True, WHITE)
        screen.blit(ab_txt, (bar_x - ab_txt.get_width() - 6, bar_y - 2))
        ability_y += 20

    # Passive ability badges
    if passive_badges:
        badge_x = SCREEN_WIDTH - 12
        for badge_name, badge_color in passive_badges:
            badge_txt = font.render(badge_name, True, badge_color)
            badge_x -= badge_txt.get_width() + 8
            screen.blit(badge_txt, (badge_x, ability_y))
        ability_y += 20

    # Mini instructions
    help_text = font.render(help_msg, True, WHITE)
    help_shadow = font.render(help_msg, True, BLACK)
    screen.blit(help_shadow, (12, SCREEN_HEIGHT - 28))
    screen.blit(help_text, (10, SCREEN_HEIGHT - 30))

    # Door prompt when near a building outside
    if inside_building is None:
        nearby = get_nearby_door_building(burrb_x, burrb_y)
        if nearby is not None:
            prompt = font.render("Press E to enter", True, YELLOW)
            prompt_shadow = font.render("Press E to enter", True, BLACK)
            px_pos = SCREEN_WIDTH // 2 - prompt.get_width() // 2
            screen.blit(prompt_shadow, (px_pos + 1, SCREEN_HEIGHT // 2 + 101))
            screen.blit(prompt, (px_pos, SCREEN_HEIGHT // 2 + 100))

    # Draw touch buttons (only if touch has been used)
    if touch_active:
        draw_touch_buttons(screen)

    # JUMP SCARE! Draw the scary birb on top of EVERYTHING!
    if jumpscare_timer > 0:
        draw_jumpscare(screen, jumpscare_frame)

    # Update the display (flip the "page" so we see what we just drew)
    pygame.display.flip()

    # Tick the clock - this keeps the game at 60 FPS
    clock.tick(FPS)

# Clean up when the game is done
pygame.quit()
