"""
Car class for Life of a Burrb.
Cars drive along the city road grid, turning at intersections.
"""

import random

from src.constants import BLOCK_SIZE, ROAD_WIDTH
from src.biomes import CITY_X1, CITY_Y1, CITY_X2, CITY_Y2


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

        # Wrap around when leaving the city (cars loop within city)
        margin = 50
        if self.x > CITY_X2 + margin:
            self.x = CITY_X1 - margin
        elif self.x < CITY_X1 - margin:
            self.x = CITY_X2 + margin
        if self.y > CITY_Y2 + margin:
            self.y = CITY_Y1 - margin
        elif self.y < CITY_Y1 - margin:
            self.y = CITY_Y2 + margin

        # Check if we're at an intersection and maybe turn
        self.turn_cooldown -= 1
        if self.turn_cooldown <= 0:
            step = BLOCK_SIZE + ROAD_WIDTH
            # Are we near the center of an intersection?
            # Intersections happen where horizontal and vertical roads cross
            near_h_road = False
            near_v_road = False
            for bx in range(CITY_X1, CITY_X2 + step, step):
                road_x = bx + BLOCK_SIZE
                if abs(self.x - (road_x + ROAD_WIDTH // 2)) < 8:
                    near_v_road = True
                    break
            for by in range(CITY_Y1, CITY_Y2 + step, step):
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
CAR_COLORS = [
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


def spawn_cars():
    """Spawn cars on city roads. Returns a list of Car objects."""
    cars = []
    step = BLOCK_SIZE + ROAD_WIDTH

    # Cars on horizontal roads (city only)
    for by in range(CITY_Y1, CITY_Y2, step):
        road_y = by + BLOCK_SIZE + ROAD_WIDTH // 2
        # Spawn several cars per road
        num_cars = random.randint(2, 4)
        for _ in range(num_cars):
            cx = random.randint(CITY_X1 + 50, CITY_X2 - 50)
            # Drive on the right side of the road
            direction = random.choice([0, 2])  # right or left
            if direction == 0:
                cy = road_y + ROAD_WIDTH // 4  # right side (bottom lane)
            else:
                cy = road_y - ROAD_WIDTH // 4  # left side (top lane)
            color, detail, ctype = random.choice(CAR_COLORS)
            cars.append(Car(cx, cy, direction, color, detail, ctype))

    # Cars on vertical roads (city only)
    for bx in range(CITY_X1, CITY_X2, step):
        road_x = bx + BLOCK_SIZE + ROAD_WIDTH // 2
        num_cars = random.randint(2, 4)
        for _ in range(num_cars):
            cy = random.randint(CITY_Y1 + 50, CITY_Y2 - 50)
            direction = random.choice([1, 3])  # down or up
            if direction == 1:
                cx = road_x + ROAD_WIDTH // 4  # right side
            else:
                cx = road_x - ROAD_WIDTH // 4  # left side
            color, detail, ctype = random.choice(CAR_COLORS)
            cars.append(Car(cx, cy, direction, color, detail, ctype))

    return cars
