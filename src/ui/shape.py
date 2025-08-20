import math
import pygame


class Point:
    def __init__(self, x: float, y: float):
        self.x, self.y = x, y

    def __repr__(self):
        return f"(x:{self.x}, y:{self.y})"

    def rotate(self, angle: float, origin):
        # Distance between point and origin
        dist_x = self.x - origin.x
        dist_y = self.y - origin.y

        # Apply rotation
        cos_a = math.cos(angle)
        sin_a = math.sin(angle)
        rotated_x = dist_x * cos_a - dist_y * sin_a
        rotated_y = dist_x * sin_a + dist_y * cos_a

        # Update the point's coordinates
        self.x = rotated_x + origin.x
        self.y = rotated_y + origin.y

    def translate(self, dx: float, dy: float):
        """Translate the point by the given offset"""
        self.x += dx
        self.y += dy


class TrianglePrimitive:
    def __init__(self, a: Point, b: Point, c: Point):
        self.a, self.b, self.c = a, b, c

    def get_points(self) -> list[Point]:
        return [self.a, self.b, self.c]

    def draw(self, screen, color):
        points = [(p.x, p.y) for p in self.get_points()]
        pygame.draw.polygon(screen, color, points)

    def __repr__(self):
        return f"TrianglePrimitive: a:({self.a}), b:({self.b}), c:({self.c})"


# Shapes are exclusively made of triangle primitives
class Shape:
    def __init__(self, center: Point, color=(255, 255, 255)):
        self.center = center
        self.color = color  # RGB tuple
        self.triangles = []
        self.original_coords = []  # Store original coordinates

        # Rotation uses
        self.current_rotation = 0.0

    def get_triangles(self) -> list[TrianglePrimitive]:
        return self.triangles

    def rotate(self, angle: float, origin=None):
        """Set the angle we want to rotate. If no origin specified, rotate around shape's center"""
        if origin is None:
            origin = self.center

        self.current_rotation = angle % (math.pi * 2)

        # Update TrianglePrimitive's points
        for i, (orig_a, orig_b, orig_c) in enumerate(self.original_coords):
            triangle = self.triangles[i]

            # Reset existing Point
            triangle.a.x, triangle.a.y = orig_a
            triangle.b.x, triangle.b.y = orig_b
            triangle.c.x, triangle.c.y = orig_c

            # Apply rotation
            triangle.a.rotate(angle, origin)
            triangle.b.rotate(angle, origin)
            triangle.c.rotate(angle, origin)

    def translate(self, dx: float, dy: float):
        """Translate the shape by moving all triangles and updating center"""
        # Update center
        self.center.translate(dx, dy)

        # Update all triangle points
        for triangle in self.triangles:
            triangle.a.translate(dx, dy)
            triangle.b.translate(dx, dy)
            triangle.c.translate(dx, dy)

        # Update original coordinates to maintain correct rotation reference
        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def _apply_current_rotation(self) -> bool:
        """Apply current rotation without recreating objects"""
        if self.current_rotation != 0:
            self.rotate(self.current_rotation)
            return True
        return False

    def draw(self, screen):
        """Draw all the shape's triangles"""
        for triangle in self.triangles:
            triangle.draw(screen, self.color)


class Square(Shape):
    def __init__(self, center: Point, size: float, color=(255, 255, 255)):
        super().__init__(center, color)
        self.size = size
        self._create_triangles()

    def _create_triangles(self):
        """Create triangles based on current size and center"""
        half_size = self.size / 2
        top_left = Point(self.center.x - half_size, self.center.y - half_size)
        top_right = Point(self.center.x + half_size, self.center.y - half_size)
        bot_left = Point(self.center.x - half_size, self.center.y + half_size)
        bot_right = Point(self.center.x + half_size, self.center.y + half_size)

        self.triangles = [
            TrianglePrimitive(top_left, bot_left, bot_right),
            TrianglePrimitive(top_right, top_left, bot_right),
        ]

        # Store original coordinates
        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_size(self, new_size: float):
        """Update the square's size and recreate triangles"""
        if self.size != new_size:
            self.size = new_size
            self._create_triangles()

            # Reapply rotation
            self._apply_current_rotation()


class Circle(Shape):
    def __init__(self, center: Point, radius: float, color=(255, 255, 255)):
        super().__init__(center, color)
        self.radius = radius
        self._create_triangles()

    def _create_triangles(self):
        """Create triangles based on radius and center"""
        self.triangles = []
        TOTAL_TRIANGLES = 60

        for i in range(TOTAL_TRIANGLES):
            p1_angle = 2 * math.pi / TOTAL_TRIANGLES * i
            p2_angle = 2 * math.pi / TOTAL_TRIANGLES * (i + 1)

            self.triangles.append(
                TrianglePrimitive(
                    Point(self.center.x, self.center.y),
                    Point(
                        self.center.x + self.radius * math.cos(p1_angle),
                        self.center.y + self.radius * math.sin(p1_angle),
                    ),
                    Point(
                        self.center.x + self.radius * math.cos(p2_angle),
                        self.center.y + self.radius * math.sin(p2_angle),
                    ),
                )
            )

        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_radius(self, new_radius: float):
        """Update the circle's radius and recreate triangles"""
        if self.radius != new_radius:
            self.radius = new_radius
            self._create_triangles()

            # Reapply rotation
            self._apply_current_rotation()


class Triangle(Shape):
    def __init__(self, a: Point, b: Point, c: Point, color=(255, 255, 255)):
        # Calculate center as the centroid of the triangle
        center_x = (a.x + b.x + c.x) / 3
        center_y = (a.y + b.y + c.y) / 3
        center = Point(center_x, center_y)

        super().__init__(center, color)
        self.a, self.b, self.c = a, b, c
        self._create_triangles()

    def _create_triangles(self):
        """Create a single triangle from the three points"""
        self.triangles = [TrianglePrimitive(self.a, self.b, self.c)]
        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_points(self, a: Point, b: Point, c: Point):
        """Update the triangle's points and recreate triangle"""
        self.a, self.b, self.c = a, b, c

        # Update center
        self.center.x = (a.x + b.x + c.x) / 3
        self.center.y = (a.y + b.y + c.y) / 3

        self._create_triangles()

        # Reapply rotation
        self._apply_current_rotation()


class Oval(Shape):
    def __init__(self, center: Point, rx: float, ry: float, color=(255, 255, 255)):
        super().__init__(center, color)
        self.rx, self.ry = rx, ry

        self._create_triangles()

    def _create_triangles(self):
        """Create triangles based on rx, ry and center"""
        self.triangles = []
        TOTAL_TRIANGLES = 60

        for i in range(TOTAL_TRIANGLES):
            p1_angle = 2 * math.pi / TOTAL_TRIANGLES * i
            p2_angle = 2 * math.pi / TOTAL_TRIANGLES * (i + 1)

            self.triangles.append(
                TrianglePrimitive(
                    Point(self.center.x, self.center.y),
                    Point(
                        self.center.x + self.rx * math.cos(p1_angle),
                        self.center.y + self.ry * math.sin(p1_angle),
                    ),
                    Point(
                        self.center.x + self.rx * math.cos(p2_angle),
                        self.center.y + self.ry * math.sin(p2_angle),
                    ),
                )
            )

        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_rx(self, rx: float):
        if self.rx != rx:
            self.rx = rx
            self._create_triangles()

            # Reapply rotation
            self._apply_current_rotation()

    def set_ry(self, ry: float):
        if self.ry != ry:
            self.ry = ry
            self._create_triangles()

            # Reapply rotation
            self._apply_current_rotation()


class Rectangle(Shape):
    def __init__(
        self, center: Point, height: float, width: float, color=(255, 255, 255)
    ):
        super().__init__(center, color)
        self.width, self.height = width, height
        self._create_triangles()

    def _create_triangles(self):
        """Create triangles based on current width, height and center"""
        half_width = self.width / 2
        half_height = self.height / 2

        top_left = Point(self.center.x - half_width, self.center.y - half_height)
        top_right = Point(self.center.x + half_width, self.center.y - half_height)
        bot_left = Point(self.center.x - half_width, self.center.y + half_height)
        bot_right = Point(self.center.x + half_width, self.center.y + half_height)

        self.triangles = [
            TrianglePrimitive(top_left, bot_left, bot_right),
            TrianglePrimitive(top_right, top_left, bot_right),
        ]

        # Store original coordinates
        self.original_coords = [
            ((t.a.x, t.a.y), (t.b.x, t.b.y), (t.c.x, t.c.y)) for t in self.triangles
        ]

    def set_width(self, new_width: float):
        """Update the rectangle's width and recreate triangles"""
        self.width = new_width
        self._create_triangles()

        # Reapply rotation
        self._apply_current_rotation()

    def set_height(self, new_height: float):
        """Update the rectangle's height and recreate triangles"""
        self.height = new_height
        self._create_triangles()

        # Reapply rotation
        self._apply_current_rotation()
