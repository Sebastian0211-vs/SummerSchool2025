import random
from .shape import *

# Colors for the layers of a single blade of grass (from far to near)
BLADE_COLORS = [
    (140, 215, 140),
    (70, 170, 70),
    (25, 110, 25)
]


class GrassBlade:
    def __init__(self, x, y, base_height, base_width, scale=1.0):
        """
        The blade of grass consists of 3 layers.
        scale — size coefficient (for perspective).
        """
        self.x = x
        self.y = y
        self.base_height = int(base_height * scale)
        self.base_width = int(base_width * scale)
        self.triangles = []
        self.generate_layers()

    def generate_layers(self):
        self.triangles = []
        for i, color in enumerate(BLADE_COLORS):
            h = self.base_height + i * 6 + random.randint(-2, 2)
            w = self.base_width + i * 2
            tip_offset = random.randint(-w, w)

            p0 = Point(self.x - w // 2, self.y)          # left base
            p1 = Point(self.x + w // 2, self.y)          # right base
            p2 = Point(self.x + tip_offset, self.y - h)  # top

            # color variation
            var = random.randint(-15, 15)
            col = (
                max(0, min(255, color[0] + var)),
                max(0, min(255, color[1] + var)),
                max(0, min(255, color[2] + var))
            )

            self.triangles.append(Triangle(p0, p1, p2, color=col))

    def draw(self, screen):
        for tri in self.triangles:
            tri.draw(screen)


class GrassGenerator:
    def __init__(self, window_size, blade_count=300):
        self.width, self.height = window_size
        self.blade_count = blade_count
        self.blades = []

    def generate(self):
        self.blades = []
        for _ in range(self.blade_count):
            x = random.randint(0, self.width)
            y = random.randint(int(self.height * 0.325), self.height)  # draw starting from this pos y

            # perspective coeff: lower -> bigger
            t = (y - self.height * 0.4) / (self.height * 0.6)  # normalize between 0 and 1
            scale = 0.4 + t * 0.8  # from 0.4(highest point) to 1.2(lowest point)

            base_h = random.randint(15, 25)
            base_w = random.randint(4, 7)

            blade = GrassBlade(x, y, base_h, base_w, scale)
            self.blades.append(blade)

        # sort by y, so the furthest are being drawn before to avoid overlating
        self.blades.sort(key=lambda b: b.y)

    def draw(self, screen):
        for blade in self.blades:
            blade.draw(screen)
