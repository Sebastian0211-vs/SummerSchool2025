from .shape import *
from ..utils.geometry import *
import math


class Edelweiss(Shape):
    def __init__(
        self,
        center: Point,
        scale_factor=1.0,
        center_color=(255, 220, 100),
        petal_color=(255, 255, 255),
    ):
        super().__init__(center, petal_color)
        self.scale_factor = scale_factor
        self.center_color = center_color
        self.petal_color = petal_color
        self._create_edelweiss()

    def _create_edelweiss(self):
        # Clean edelweiss design with consistent proportions
        BASE_SIZE = 20 * self.scale_factor

        # Multiple small yellow circles for authentic edelweiss center
        self.flower_centers = []

        # Central circle
        main_center = Circle(
            Point(self.center.x, self.center.y),
            radius=BASE_SIZE * 0.3,
            color=self.center_color,
            num_triangles=12,
        )
        self.flower_centers.append(main_center)

        # Yellow pistils
        center_ring_angles = [i * 60 for i in range(6)]
        for angle in center_ring_angles:
            angle_rad = math.radians(angle)
            circle_distance = BASE_SIZE * 0.5
            circle_x = self.center.x + circle_distance * math.cos(angle_rad)
            circle_y = self.center.y + circle_distance * math.sin(angle_rad)

            small_center = Circle(
                Point(circle_x, circle_y),
                radius=BASE_SIZE * 0.2,
                color=self.center_color,
                num_triangles=8,
            )
            self.flower_centers.append(small_center)

        # Symmetrical white petals arranged in a star pattern
        self.petals = []
        petal_angles = [i * 45 for i in range(8)]

        for i, angle in enumerate(petal_angles):
            angle_rad = math.radians(angle)

            if i % 2 == 0:  # Long petals (main directions)
                petal_length = BASE_SIZE * 2.2
                petal_width = BASE_SIZE * 0.4
            else:  # Short petals (diagonal directions)
                petal_length = BASE_SIZE * 1.4
                petal_width = BASE_SIZE * 0.35

            # Compute coordinates
            distance_from_center = BASE_SIZE * 0.8 + petal_length / 2
            petal_x = self.center.x + distance_from_center * math.cos(angle_rad)
            petal_y = self.center.y + distance_from_center * math.sin(angle_rad)

            petal = Oval(
                Point(petal_x, petal_y),
                petal_width,
                petal_length,
                self.petal_color,
                num_triangles=12,
            )

            # Rotate petal to point outward
            petal.rotate(angle_rad + math.pi / 2)
            self.petals.append(petal)

        # Create smaller inner petals between main petals for fullness
        self.inner_petals = []
        inner_angles = [22.5 + i * 45 for i in range(8)]  # Offset by 22.5 degrees

        for angle in inner_angles:
            angle_rad = math.radians(angle)
            petal_length = BASE_SIZE * 0.9
            petal_width = BASE_SIZE * 0.25

            distance_from_center = BASE_SIZE * 0.9 + petal_length / 2
            petal_x = self.center.x + distance_from_center * math.cos(angle_rad)
            petal_y = self.center.y + distance_from_center * math.sin(angle_rad)

            inner_petal = Oval(
                Point(petal_x, petal_y),
                petal_width,
                petal_length,
                self.petal_color,
                num_triangles=8,
            )

            inner_petal.rotate(angle_rad + math.pi / 2)
            self.inner_petals.append(inner_petal)

        # Update shape attributs
        self.parts = [*self.petals, *self.inner_petals, *self.flower_centers]

        self.triangles = []
        for part in self.parts:
            self.triangles.extend(part.triangles)

        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_scale_factor(self, new_scale_factor):
        """Update the scale factor and recreate the edelweiss with new dimensions"""
        if self.scale_factor == new_scale_factor:
            return

        self.scale_factor = new_scale_factor
        self._create_edelweiss()

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)
