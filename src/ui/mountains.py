import pygame
import random
import math

# Initialize pygame
pygame.init()

# Screen settings
WIDTH = 1920
HEIGHT = 1080
screen = pygame.display.set_mode((WIDTH, HEIGHT))
pygame.display.set_caption("Multi-layer mountains made of triangles")

# Colors
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
# Colors for different layers (from far to near)
MOUNTAIN_COLORS = [
    (180, 200, 220),  # farthest layer — very light
    (140, 170, 200),  # middle-far layer — light
    (106, 137, 167)   # nearest layer — base color
]
TRIANGLE_OUTLINE = (60, 60, 60)


class MountainLayer:
    def __init__(self, layer_index, base_horizon_y):
        self.layer_index = layer_index
        # Each farther layer is slightly higher (reduced offset)
        self.horizon_y = base_horizon_y + layer_index * 15
        self.mountain_points = []
        self.triangles = []
        self.color = MOUNTAIN_COLORS[layer_index]

        # Triangle size decreases for farther layers
        self.triangle_size = 20 - layer_index * 2

        # NOTE: triangle_size must stay > 0; if you add more layers, clamp this value.

    def generate_mountain_outline(self):
        """Generate a zig-zag mountain outline (polyline)."""
        self.mountain_points = []

        # Start at the left edge at the horizon level
        self.mountain_points.append((0, self.horizon_y))

        x = 0
        while x < WIDTH:
            # Random segment width (larger for farther layers)
            segment_width = random.randint(60 + self.layer_index * 20, 180 + self.layer_index * 30)
            # Random peak height (smaller for farther layers)
            max_peak_height = 300 - self.layer_index * 50
            min_peak_height = 80 - self.layer_index * 10
            peak_height = random.randint(min_peak_height, max_peak_height)
            peak_y = self.horizon_y - peak_height

            # Add peak (move half segment)
            x += segment_width // 2
            if x < WIDTH:
                self.mountain_points.append((x, peak_y))

            # Add descent (move the other half)
            x += segment_width // 2
            if x < WIDTH:
                valley_height = random.randint(30, max(30, peak_height // 2))
                valley_y = self.horizon_y - valley_height
                self.mountain_points.append((x, valley_y))

        # Finish at the right edge
        self.mountain_points.append((WIDTH, self.horizon_y))

        # NOTE: mountain_points is a polyline that always begins and ends on horizon_y.
        # This makes interpolation straightforward when querying the outline.

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
            x1, y1 = self.mountain_points[i]
            x2, y2 = self.mountain_points[i + 1]

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
            x1, y1 = self.mountain_points[i]
            x2, y2 = self.mountain_points[i + 1]

            if x1 <= x <= x2:
                if x2 - x1 != 0:
                    return y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                else:
                    return y1
        # If x is outside known points, return horizon as fallback
        return self.horizon_y

    def generate_triangles(self):
        """Generate triangles and clamp their vertices so they stay between outline and horizon."""
        self.triangles = []

        triangle_height = self.triangle_size * math.sqrt(3) / 2
        int_triangle_height = int(round(triangle_height))
        if int_triangle_height <= 0:
            int_triangle_height = 1  # safety clamp

        # NOTE: we generate a triangular grid (two triangles per cell: up and down).
        # We step y by the triangle height and x by triangle_size, offsetting every other row.
        for y in range(-self.triangle_size, HEIGHT + self.triangle_size, int_triangle_height):
            for x in range(-self.triangle_size, WIDTH + self.triangle_size, self.triangle_size):
                # Offset every other row for a staggered (hex-like) tiling
                x_offset = self.triangle_size // 2 if ((y // int_triangle_height) % 2) == 0 else 0
                x_pos = x + x_offset

                # Upward-pointing triangle
                tri_up = [
                    (x_pos, y),
                    (x_pos + self.triangle_size // 2, y - triangle_height),
                    (x_pos + self.triangle_size, y)
                ]
                # Downward-pointing triangle
                tri_down = [
                    (x_pos, y),
                    (x_pos + self.triangle_size // 2, y + triangle_height),
                    (x_pos + self.triangle_size, y)
                ]

                for triangle in (tri_up, tri_down):
                    # If at least one vertex is inside the mountain area, include triangle (then clamp)
                    in_mountain = any(self.point_in_mountain(vx, vy) for vx, vy in triangle)

                    if in_mountain:
                        vertices = []
                        for vx, vy in triangle:
                            # Clamp vertically: top boundary = outline (mountain_y), bottom = horizon_y
                            mountain_y = self.get_mountain_y_at_x(vx)
                            vy_clamped = max(mountain_y, min(vy, self.horizon_y))

                            # Clamp horizontally to screen and round to integers for pygame
                            vx_clamped = int(round(max(0, min(WIDTH, vx))))
                            vy_clamped = int(round(max(0, min(HEIGHT, vy_clamped))))
                            vertices.append((vx_clamped, vy_clamped))

                        # Validate non-degenerate triangle (area check)
                        if len(vertices) == 3:
                            area = abs((vertices[1][0] - vertices[0][0]) * (vertices[2][1] - vertices[0][1]) -
                                       (vertices[2][0] - vertices[0][0]) * (vertices[1][1] - vertices[0][1]))
                            if area > 1:
                                self.triangles.append(vertices)

        # NOTE: This approach ensures triangles that cross the outline are trimmed to the mountain's fill,
        # producing a mosaic-like mountain surface.

    def draw(self, screen):
        """Draw the mountain layer to the screen using the precomputed triangles."""
        # Draw triangles
        for triangle in self.triangles:
            # Slight color variation per triangle to add visual richness
            color_variation = random.randint(-15, 15)
            color = (
                max(0, min(255, self.color[0] + color_variation)),
                max(0, min(255, self.color[1] + color_variation)),
                max(0, min(255, self.color[2] + color_variation))
            )

            pygame.draw.polygon(screen, color, triangle)
            # Thinner outlines for far layers (example: draw outlines only for nearest)
            outline_width = 1 if self.layer_index == 2 else 0
            if outline_width > 0:
                pygame.draw.polygon(screen, TRIANGLE_OUTLINE, triangle, outline_width)


class MountainGenerator:
    def __init__(self):
        # Base horizon Y — adjust this to move all mountain layers up/down.
        # Smaller values move mountains higher on screen (y increases downward).
        self.base_horizon_y = HEIGHT // 3

        # Create three mountain layers (indices 0..2, from far to near)
        self.layers = [
            MountainLayer(0, self.base_horizon_y),  # farthest
            MountainLayer(1, self.base_horizon_y),  # middle
            MountainLayer(2, self.base_horizon_y)   # nearest
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
        # Fill background
        screen.fill(WHITE)

        # Draw layers from farthest to nearest so nearer ones appear on top
        for layer in self.layers:
            layer.draw(screen)


def main():
    clock = pygame.time.Clock()
    mountain_gen = MountainGenerator()

    # Generate mountains initially
    mountain_gen.generate_all_layers()

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_SPACE:
                    # Regenerate mountains on SPACE
                    mountain_gen.generate_all_layers()

        # Draw scene
        mountain_gen.draw(screen)

        pygame.display.flip()
        clock.tick(2)  # NOTE: low FPS so generation changes are visible; increase for smoother animation

    pygame.quit()


if __name__ == "__main__":
    main()
