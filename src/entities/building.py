"""
Building class for Life of a Burrb.
Each building has a randomly-generated interior with furniture,
a resident burrb sitting on a sofa, a closet, and a bed.
"""

import random
import pygame

from src.constants import BLACK, BROWN, YELLOW


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
    BED = 7

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

        # Bed! Every house has a bed. Shake it and maybe a monster appears!
        self.bed_x = 0.0  # pixel position of bed center
        self.bed_y = 0.0
        self.bed_shaken = False  # has the bed been shaken?
        self.bed_monster = False  # did a monster come out?

        # The 6-legged monster that might live under the bed!
        self.monster_active = False  # is the monster chasing the player?
        self.monster_x = 0.0
        self.monster_y = 0.0
        self.monster_speed = 2.2  # faster than the resident!
        self.monster_walk_frame = 0

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

        # Find the bed position
        for row in range(self.interior_h):
            for col in range(self.interior_w):
                if self.interior[row][col] == self.BED:
                    self.bed_x = col * tile + tile // 2
                    self.bed_y = row * tile + tile // 2
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

        # === BED ===
        # Every house has a bed against the right wall!
        # Shake it and maybe a 6-legged monster crawls out...
        bed_row = rng.randint(3, self.interior_h - 4)
        bed_col = self.interior_w - 2  # against the right wall
        # Make sure we don't overwrite something important
        if grid[bed_row][bed_col] != self.FLOOR:
            bed_col = 1  # try the left wall instead
        if grid[bed_row][bed_col] == self.FLOOR:
            grid[bed_row][bed_col] = self.BED

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
