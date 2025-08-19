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
    

class Triangle:
    def __init__(self, a: Point, b:Point, c:Point):
        self.a, self.b, self.c = a, b, c

    def get_point(self) -> list[Point]:
        return [self.a, self.b, self.c]

    def __repr__(self):
        return f"Triangle: a:({self.a}), b:({self.b}), c:({self.c})"
    
# Shapes are exclusively made of triangles
class Shape:
    def __init__(self, center: Point, color=(255, 255, 255)):
        self.center = center
        self.color = color  # RGB tuple
        self.triangles = []
        self.original_triangles = []  # Store original positions

        # Rotation uses
        self.current_rotation = 0.0
        self.rotation_origin = None
    
    def get_triangles(self) -> list[Triangle]:
        return self.triangles
    
    def rotate(self, angle: float, origin=None):
        """Set the angle we want to rotate. If no origin specified, rotate around shape's center"""
        if origin is None:
            origin = self.center
        
        self.current_rotation = angle
        self.rotation_origin = origin
        
        # Reset to original positions and apply rotation
        for i, original_triangle in enumerate(self.original_triangles):
            # Rectreate points after rotation transformation
            new_a = Point(original_triangle.a.x, original_triangle.a.y)
            new_b = Point(original_triangle.b.x, original_triangle.b.y)
            new_c = Point(original_triangle.c.x, original_triangle.c.y)
            
            # Apply rotation
            new_a.rotate(angle, origin)
            new_b.rotate(angle, origin)
            new_c.rotate(angle, origin)
            
            # Update current triangle
            self.triangles[i].a = new_a
            self.triangles[i].b = new_b
            self.triangles[i].c = new_c
    
    def draw(self, screen):
        """Draw all the shape's triangles"""
        
        for triangle in self.triangles:
            points = [(p.x, p.y) for p in triangle.get_point()]
            pygame.draw.polygon(screen, self.color, points)
    
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
            Triangle(top_left, bot_left, bot_right),
            Triangle(top_right, top_left, bot_right)
        ]
        
        # Store original positions for rotation reset
        self.original_triangles = [
            Triangle(Point(top_left.x, top_left.y), Point(bot_left.x, bot_left.y), Point(bot_right.x, bot_right.y)),
            Triangle(Point(top_right.x, top_right.y), Point(top_left.x, top_left.y), Point(bot_right.x, bot_right.y))
        ]
    
    def set_size(self, new_size: float):
        """Update the square's size and recreate triangles"""
        self.size = new_size
        self._create_triangles()

        # Update rotation too 
        if self.current_rotation != 0:
            self.rotate(self.current_rotation, self.rotation_origin)