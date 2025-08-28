import random
from .shape import *

GROUND_COLORS = [(78, 65, 42), (115, 85, 55), (145, 105, 65)]  # Rich earth tones
STONE_COLOR = (125, 115, 95)


class Soil:
    def __init__(self, window_size, cell_size=25, stone_prob=0.05):

        self.width, self.height = window_size
        self.ground_height = int(self.height * 0.675)
        self.cell_size = cell_size
        self.stone_prob = stone_prob
        self.triangles = []

    def generate(self):
        self.triangles = []
        base_y = self.height
        top_y = self.height - self.ground_height

        # points network
        grid = []
        for y in range(top_y, base_y + self.cell_size, self.cell_size):
            row = []
            for x in range(0, self.width + self.cell_size, self.cell_size):

                jitter_x = random.randint(-4, 4)
                jitter_y = random.randint(-4, 4)
                row.append(Point(x + jitter_x, y + jitter_y))
            grid.append(row)

        rows = len(grid)
        cols = len(grid[0])

        # triangulation
        for i in range(rows - 1):
            for j in range(cols - 1):
                p1 = grid[i][j]
                p2 = grid[i][j + 1]
                p3 = grid[i + 1][j]
                p4 = grid[i + 1][j + 1]

                # choose the color, sometimes gray for a stone
                if random.random() < self.stone_prob:
                    color = STONE_COLOR
                else:
                    color = random.choice(GROUND_COLORS)

                # two triangles to make a square
                tri1 = Triangle(p1, p2, p3, color=color)
                tri2 = Triangle(p2, p4, p3, color=color)

                self.triangles.append(tri1)
                self.triangles.append(tri2)

    def draw(self, screen):
        for tri in self.triangles:
            tri.draw(screen)
