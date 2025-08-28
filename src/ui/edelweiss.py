from .shape import *
from ..utils.geometry import *
import math
import random


class Edelweiss(Shape):
    def __init__(
        self,
        center: Point,
        scale_factor=1.0,
        pistils_color=(255, 255, 0),
        petals_color=(255, 255, 255),
    ):
        super().__init__(center)
        self.center = center
        self.scale_factor = scale_factor
        self.pistils_color = pistils_color
        self.petals_color = petals_color

        self._create_edelweiss()

    def _create_edelweiss(self):

        # Flower Configuration
        INNER_RADIUS = 10 * self.scale_factor
        BIG_PETALS_WIDTH = 10 * self.scale_factor
        BIG_PETALS_HEIGHT = 30 * self.scale_factor
        SMALL_PETALS_WIDTH = 10 * self.scale_factor
        SMALL_PETALS_HEIGHT = 16 * self.scale_factor

        self.inner_circle = Circle(
            Point(self.center.x, self.center.y),
            radius=INNER_RADIUS,
            color=self.petals_color,
        )

        self.main_pistil = Circle(
            Point(self.center.x, self.center.y),
            radius=INNER_RADIUS / 2,
            color=self.petals_color,
        )

        # Create small pistils with random positions in 6 sectors
        self.pistils = []

        sectors = [
            (0, 60),  # Sector 1: 0-60 degrees
            (60, 120),  # Sector 2: 60-120 degrees
            (120, 180),  # Sector 3: 120-180 degrees
            (180, 240),  # Sector 4: 180-240 degrees
            (240, 300),  # Sector 5: 240-300 degrees
            (300, 360),  # Sector 6: 300-360 degrees
        ]

        for start_angle, end_angle in sectors:
            # Generate random angle within this sector
            random_angle = random.uniform(start_angle, end_angle)

            # Calculate pistil position
            angle_rad = math.radians(random_angle)
            petal_x = self.inner_circle.center.x + (INNER_RADIUS / 2) * math.cos(
                angle_rad
            )
            petal_y = self.inner_circle.center.y + (INNER_RADIUS / 2) * math.sin(
                angle_rad
            )

            pistil = Circle(
                Point(petal_x, petal_y),
                INNER_RADIUS / 4,
                self.pistils_color,
            )

            self.pistils.append(pistil)

        # Create big petals with slight random variations
        self.big_petals = []
        for angle in [0, 90, 180, 270]:
            angle_rad = math.radians(angle)
            size_variation = random.uniform(0.8, 1.2)
            angle_offset = random.uniform(-15, 15)
            adjusted_angle = angle_rad + math.radians(angle_offset)

            petal_x = self.inner_circle.outerPoints[angle].x + (
                BIG_PETALS_HEIGHT / 2
            ) * math.cos(adjusted_angle)
            petal_y = self.inner_circle.outerPoints[angle].y + (
                BIG_PETALS_HEIGHT / 2
            ) * math.sin(adjusted_angle)

            big_petal = Oval(
                Point(petal_x, petal_y),
                (BIG_PETALS_WIDTH / 2) * size_variation,
                (BIG_PETALS_HEIGHT / 2) * size_variation,
                self.petals_color,
            )
            big_petal.rotate(adjusted_angle + math.pi / 2)
            self.big_petals.append(big_petal)

        # Create small petals
        self.small_petals = []
        for angle in [24, 66, 114, 156, 204, 246, 294, 336]:
            # Calculate petal position extending outward from circle
            angle_rad = math.radians(angle)
            petal_x = self.inner_circle.outerPoints[angle].x + (
                SMALL_PETALS_HEIGHT / 2
            ) * math.cos(angle_rad)
            petal_y = self.inner_circle.outerPoints[angle].y + (
                SMALL_PETALS_HEIGHT / 2
            ) * math.sin(angle_rad)

            small_petal = Oval(
                Point(petal_x, petal_y),
                SMALL_PETALS_WIDTH / 2,
                SMALL_PETALS_HEIGHT / 2,
                self.petals_color,
            )
            # Rotate petal to align with radial direction
            small_petal.rotate(angle_rad + math.pi / 2)
            self.small_petals.append(small_petal)

        self.parts = [
            self.inner_circle,
            self.main_pistil,
            *self.big_petals,
            *self.small_petals,
            *self.pistils,
        ]

        # Update triangles
        self.triangles = []
        for part in self.parts:
            self.triangles.extend(part.triangles)

    def set_scale_factor(self, new_scale_factor):
        """Update the scale factor and recreate the edelweiss with new dimensions"""
        if self.scale_factor == new_scale_factor:
            return

        self.scale_factor = new_scale_factor
        self._create_edelweiss()

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)
