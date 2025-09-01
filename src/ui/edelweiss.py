from .shape import *
from ..utils.geometry import *
from ..midi.models import Note
import math
import time


class Edelweiss(Shape):
    def __init__(
        self,
        center: Point,
        scale_factor=1.0,
        center_color=(255, 220, 100),
        petal_color=(255, 255, 255),
    ):
        super().__init__(center, petal_color)

        # Shape construction
        self.scale_factor = scale_factor
        self.center_color = center_color
        self.petal_color = petal_color
        self.default_center_color = center_color
        self.default_petal_color = petal_color

        # Animation
        self.last_note_name = None
        self.rotation_direction = 1

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

            # Compute points
            circle_distance = BASE_SIZE * 0.5
            circle_x = self.center.x + circle_distance * math.cos(angle_rad)
            circle_y = self.center.y + circle_distance * math.sin(angle_rad)

            for layer in range(2):
                scale = 1.0 - layer * 0.2

                brightness_factor = 1.0 - layer * 0.16
                color = tuple(
                    int(c * brightness_factor) for c in self.center_color
                )  # Gradiant color

                # All pistils shared the same points bug radius is based on a scaling layer
                small_center = Circle(
                    Point(circle_x, circle_y),
                    radius=BASE_SIZE * 0.2 * scale,
                    color=color,
                    num_triangles=8,
                )
                self.flower_centers.append(small_center)

        # Symmetrical white petals arranged in a star pattern
        self.petals = []
        petal_angles = [i * 45 for i in range(8)]

        for i, angle in enumerate(petal_angles):
            angle_rad = math.radians(angle)

            if i % 2 == 0:
                # Big petals 0 90 180 270
                petal_length = BASE_SIZE * 2.2
                petal_width = BASE_SIZE * 0.4
            else:
                # Small petals ...
                petal_length = BASE_SIZE * 1.4
                petal_width = BASE_SIZE * 0.35

            # Compute points
            distance_from_center = BASE_SIZE * 0.8 + petal_length / 2
            petal_x = self.center.x + distance_from_center * math.cos(angle_rad)
            petal_y = self.center.y + distance_from_center * math.sin(angle_rad)

            for layer in range(3):
                scale = 1.0 - layer * 0.15

                # Color will be set by _apply_petal_layering
                layer_petal = Oval(
                    Point(petal_x, petal_y),
                    petal_width * scale,
                    petal_length * scale,
                    self.petal_color,  # Temporary color
                    num_triangles=12,
                )
                layer_petal.rotate(angle_rad + math.pi / 2)
                self.petals.append(layer_petal)

        # Create smaller inner petals between main petals for fullness
        self.inner_petals = []
        inner_angles = [22.5 + i * 45 for i in range(8)]

        for angle in inner_angles:
            angle_rad = math.radians(angle)
            petal_length = BASE_SIZE * 0.9
            petal_width = BASE_SIZE * 0.25

            # Compute points
            distance_from_center = BASE_SIZE * 0.9 + petal_length / 2
            petal_x = self.center.x + distance_from_center * math.cos(angle_rad)
            petal_y = self.center.y + distance_from_center * math.sin(angle_rad)

            for layer in range(2):
                scale = 1.0 - layer * 0.2

                # Color will be set by _apply_petal_layering
                inner_petal = Oval(
                    Point(petal_x, petal_y),
                    petal_width * scale,
                    petal_length * scale,
                    self.petal_color,  # Temporary color
                    num_triangles=8,
                )
                inner_petal.rotate(angle_rad + math.pi / 2)
                self.inner_petals.append(inner_petal)

        # Apply proper layering to petals
        self._apply_petal_layering(self.petal_color)

        # Update shape attributs
        self.parts = [*self.petals, *self.inner_petals, *self.flower_centers]

        self.triangles = []
        for part in self.parts:
            self.triangles.extend(part.triangles)

        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def _apply_petal_layering(self, base_color):
        """Apply layering colors to all petals"""

        # Update main petals with layering (3 layers each)
        petal_index = 0
        for _ in range(8):  # 8 main petal positions
            for layer in range(3):  # 3 layers per petal
                brightness_factor = 1.0 - layer * 0.12
                layered_color = tuple(int(c * brightness_factor) for c in base_color)
                if petal_index < len(self.petals):
                    self.petals[petal_index].color = layered_color
                petal_index += 1

        # Update inner petals with layering (2 layers each)
        inner_petal_index = 0
        for _ in range(8):  # 8 inner petal positions
            for layer in range(2):  # 2 layers per inner petal
                brightness_factor = 1.0 - layer * 0.16
                layered_color = tuple(int(c * brightness_factor) for c in base_color)
                if inner_petal_index < len(self.inner_petals):
                    self.inner_petals[inner_petal_index].color = layered_color
                inner_petal_index += 1

    def set_scale_factor(self, new_scale_factor):
        """Update the scale factor and recreate the edelweiss with new dimensions"""
        if self.scale_factor == new_scale_factor:
            return

        self.scale_factor = new_scale_factor
        self._create_edelweiss()

    def set_petal_color(self, new_color):
        """Update the color of all petals with proper layering"""
        self.petal_color = new_color
        self._apply_petal_layering(new_color)

    def update_by_note(self, note, rotation_speed=0):
        """Convert MIDI pitch to color"""

        # Enhanced vibrant colors for each note in chromatic scale
        note_colors = [
            (255, 20, 60),  # C - Crimson Red
            (255, 100, 0),  # C# - Bright Orange
            (255, 215, 0),  # D - Gold
            (173, 255, 47),  # D# - Green Yellow
            (50, 205, 50),  # E - Lime Green
            (0, 255, 127),  # F - Spring Green
            (64, 224, 208),  # F# - Turquoise
            (30, 144, 255),  # G - Dodger Blue
            (138, 43, 226),  # G# - Blue Violet
            (186, 85, 211),  # A - Medium Orchid
            (255, 20, 147),  # A# - Deep Pink
            (255, 105, 180),  # B - Hot Pink
        ]

        # Get base color for the note
        base_color = note_colors[note.pitch % 12]
        self.set_petal_color(base_color)

        # Change rotation direction only when note name changes
        current_note_name = note.pitch % 12
        if self.last_note_name != current_note_name:
            self.rotation_direction *= -1
            self.last_note_name = current_note_name

        # Update rotation angle with current direction
        self.current_rotation += rotation_speed * self.rotation_direction
        self.rotate(self.current_rotation, self.center)

    def draw(self, screen):
        for part in self.parts:
            part.draw(screen)
