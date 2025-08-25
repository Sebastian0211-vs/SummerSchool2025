import math
import random

from .shape import *

# Colors for different layers (from far to near)
MOUNTAIN_COLORS = [
    (180, 200, 220),  # farthest layer — very light
    (140, 170, 200),  # middle-far layer — light
    (106, 137, 167)  # nearest layer — base color
]
TRIANGLE_OUTLINE = (60, 60, 60)


class MountainLayer:
    def __init__(self, width, height, layer_index, base_horizon_y):
        self.width = width
        self.height = height
        self.layer_index = layer_index
        # Each farther layer is slightly higher (reduced offset)
        self.horizon_y = base_horizon_y + layer_index * 15
        self.mountain_points = []
        self.triangles = []  # Will store Triangle objects
        self.color = MOUNTAIN_COLORS[layer_index]

        # Triangle size decreases for farther layers
        self.triangle_size = 20 - layer_index * 2

        # NOTE: triangle_size must stay > 0

    def generate_mountain_outline(self):
        """Generate a zig-zag mountain outline (polyline)."""
        self.mountain_points = []

        # Start at the left edge at the horizon level
        self.mountain_points.append(Point(0, self.horizon_y))

        x = 0
        while x < self.width:
            # Random segment width (larger for farther layers)
            segment_width = random.randint(60 + self.layer_index * 20, 180 + self.layer_index * 30)
            # Random peak height (smaller for farther layers)
            max_peak_height = 300 - self.layer_index * 50
            min_peak_height = 80 - self.layer_index * 10
            peak_height = random.randint(min_peak_height, max_peak_height)
            peak_y = self.horizon_y - peak_height

            # Add peak (move half segment)
            x += segment_width // 2
            if x < self.width:
                self.mountain_points.append(Point(x, peak_y))

            # Add descent (move the other half)
            x += segment_width // 2
            if x < self.width:
                valley_height = random.randint(30, max(30, peak_height // 2))
                valley_y = self.horizon_y - valley_height
                self.mountain_points.append(Point(x, valley_y))

        # Finish at the right edge
        self.mountain_points.append(Point(self.width, self.horizon_y))

        # NOTE: mountain_points is a polyline that always begins and ends on horizon_y.

    def point_in_mountain(self, x, y):
        """Return whether the point (x,y) is inside the mountain area (between outline and horizon).

        Important: in pygame y increases downward. horizon_y is the bottom boundary of the mountain.
        A point is inside if mountain_y <= y <= horizon_y.
        """
        # If point is below the horizon (larger y), it's outside the mountain.
        if y > self.horizon_y:
            return False

        # Find which outline segment contains x, then interpolate outline y.
        for i in range(len(self.mountain_points) - 1):
            x1, y1 = self.mountain_points[i].x, self.mountain_points[i].y
            x2, y2 = self.mountain_points[i + 1].x, self.mountain_points[i + 1].y

            if x1 <= x <= x2:
                # Interpolate outline height
                if x2 - x1 != 0:
                    mountain_y = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                else:
                    mountain_y = y1
                # Inside if between outline (top) and horizon (bottom)
                return mountain_y <= y <= self.horizon_y

        return False

    def get_mountain_y_at_x(self, x):
        """Return the outline y coordinate at a given x (linear interpolation)."""
        for i in range(len(self.mountain_points) - 1):
            x1, y1 = self.mountain_points[i].x, self.mountain_points[i].y
            x2, y2 = self.mountain_points[i + 1].x, self.mountain_points[i + 1].y

            if x1 <= x <= x2:
                if x2 - x1 != 0:
                    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                else:
                    return y1
        # If x is outside known points, return horizon as fallback
        return self.horizon_y

    def generate_triangles(self):
        """Generate triangles and clamp their vertices so they stay between outline and horizon."""
        self.triangles = []  # Will store Triangle objects

        triangle_height = self.triangle_size * math.sqrt(3) / 2
        int_triangle_height = int(round(triangle_height))
        if int_triangle_height <= 0:
            int_triangle_height = 1  # safety clamp

        # NOTE: we generate a triangular grid (two triangles per cell: up and down).
        # We step y by the triangle height and x by triangle_size, offsetting every other row.
        for y in range(-self.triangle_size, self.height + self.triangle_size, int_triangle_height):
            for x in range(-self.triangle_size, self.width + self.triangle_size, self.triangle_size):
                # Offset every other row for a staggered (hex-like) tiling
                x_offset = self.triangle_size // 2 if ((y // int_triangle_height) % 2) == 0 else 0
                x_pos = x + x_offset

                # Upward-pointing triangle
                tri_up = [
                    Point(x_pos, y),
                    Point(x_pos + self.triangle_size // 2, y - triangle_height),
                    Point(x_pos + self.triangle_size, y)
                ]
                # Downward-pointing triangle
                tri_down = [
                    Point(x_pos, y),
                    Point(x_pos + self.triangle_size // 2, y + triangle_height),
                    Point(x_pos + self.triangle_size, y)
                ]

                for triangle_points in (tri_up, tri_down):
                    # If at least one vertex is inside the mountain area, include triangle (then clamp)
                    in_mountain = any(self.point_in_mountain(p.x, p.y) for p in triangle_points)

                    if in_mountain:
                        vertices = []
                        for p in triangle_points:
                            # Clamp vertically: top boundary = outline (mountain_y), bottom = horizon_y
                            mountain_y = self.get_mountain_y_at_x(p.x)
                            vy_clamped = max(mountain_y, min(p.y, self.horizon_y))

                            # Clamp horizontally to screen and round to integers for pygame
                            vx_clamped = int(round(max(0, min(self.width, p.x))))
                            vy_clamped = int(round(max(0, min(self.height, vy_clamped))))
                            vertices.append(Point(vx_clamped, vy_clamped))

                        if len(vertices) == 3:
                            p0, p1, p2 = vertices
                            area = abs((p1.x - p0.x) * (p2.y - p0.y) -
                                       (p2.x - p0.x) * (p1.y - p0.y))
                            if area > 1:
                                color_variation = random.randint(-15, 15)
                                color = (
                                    max(0, min(255, self.color[0] + color_variation)),
                                    max(0, min(255, self.color[1] + color_variation)),
                                    max(0, min(255, self.color[2] + color_variation))
                                )
                                # Create Triangle object instead of storing raw vertices
                                triangle_obj = Triangle(vertices[0], vertices[1], vertices[2], color=color)
                                self.triangles.append(triangle_obj)
                                if self.layer_index == 2:
                                    triangle_outline_obj = Triangle(vertices[0], vertices[1], vertices[2], color=TRIANGLE_OUTLINE)
                                    self.triangles.append(triangle_outline_obj)

        # NOTE: This approach ensures triangles that cross the outline are trimmed to the mountain's fill,
        # producing a mosaic-like mountain surface.

    def draw(self, screen):
        if self.layer_index == 2:
            for i, triangle in enumerate(self.triangles):
                if i % 2 == 0:
                    triangle.draw(screen)
                else:
                    triangle.draw(screen, 1)
        else:
            for triangle in self.triangles:
                triangle.draw(screen)


class MountainGenerator:
    def __init__(self, window_size):
        self.width, self.height = window_size
        # Base horizon Y — adjust this to move all mountain layers up/down.
        # Smaller values move mountains higher on screen (y increases downward).
        self.base_horizon_y = self.height // 3

        # Create three mountain layers (from far to near)
        self.layers = [
            MountainLayer(self.width, self.height, 0, self.base_horizon_y),  # farthest
            MountainLayer(self.width, self.height, 1, self.base_horizon_y),  # middle
            MountainLayer(self.width, self.height, 2, self.base_horizon_y)  # nearest
        ]

        # NOTE: If you want interactive control over horizon, modify base_horizon_y
        # and call generate_all_layers() to regenerate outlines/triangles.

    def generate_all_layers(self):
        """Generate outline and triangles for every layer."""
        for layer in self.layers:
            layer.generate_mountain_outline()
            layer.generate_triangles()

    def draw(self, screen):
        """Draw all mountain layers to the screen (from far to near)."""

        # Draw layers from farthest to nearest so nearer ones appear on top
        for layer in self.layers:
            layer.draw(screen)
