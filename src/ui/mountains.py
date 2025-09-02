import math
import random

from .shape import Point, Triangle

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
        self.horizon_y = base_horizon_y
        self.mountain_points = []
        self.original_mountain_points = [] 
        self.triangles = []  # Will store Triangle objects
        self.color = MOUNTAIN_COLORS[layer_index]

        self.triangle_size = 40 - layer_index * 5

        # Optimization caches
        self._mountain_y_cache = {}  # Cache interpolated mountain heights
        self._cached_colors = []  # Pre-generate color variations

        # Animation properties
        self.peak_animations = {} 
        self.animation_decay = 0.88 
        self.max_bounce_height = 150 - layer_index * 20  
        
        # Optimization flags
        self.animation_dirty = False  
        self.last_frame_had_animation = False
        self.triangles_generation_cooldown = 0  
        

    def generate_mountain_outline(self):
        """Generate a zig-zag mountain outline (polyline)."""
        self.mountain_points = []
        self.original_mountain_points = []
        self._mountain_y_cache.clear()  # Clear cache when regenerating

        # Start at the left edge at the horizon level
        self.mountain_points.append(Point(0, self.horizon_y))
        self.original_mountain_points.append(Point(0, self.horizon_y))

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
                self.original_mountain_points.append(Point(x, peak_y))

            # Add descent (move the other half)
            x += segment_width // 2
            if x < self.width:
                valley_height = random.randint(30, max(30, peak_height // 2))
                valley_y = self.horizon_y - valley_height
                self.mountain_points.append(Point(x, valley_y))
                self.original_mountain_points.append(Point(x, valley_y))

        # Finish at the right edge
        self.mountain_points.append(Point(self.width, self.horizon_y))
        self.original_mountain_points.append(Point(self.width, self.horizon_y))

    def update_peak_animations(self, active_notes):
        has_active_notes = bool(active_notes)
        has_existing_animations = bool(self.peak_animations)
        
        if not has_active_notes and not has_existing_animations:
            self.animation_dirty = False
            return
        
        if self.triangles_generation_cooldown > 0:
            self.triangles_generation_cooldown -= 1
            
        self.animation_dirty = True
        
        peaks_to_remove = []
        for peak_idx in self.peak_animations:
            self.peak_animations[peak_idx] *= self.animation_decay
            if self.peak_animations[peak_idx] < 0.08:
                peaks_to_remove.append(peak_idx)
        
        for peak_idx in peaks_to_remove:
            del self.peak_animations[peak_idx]

        if active_notes:
            if not hasattr(self, '_cached_peak_points'):
                self._cached_peak_points = [i for i in range(1, len(self.original_mountain_points) - 1, 2)]
            
            peak_points = self._cached_peak_points
            
            if peak_points:
                for pitch, velocity in active_notes.items():
                    peak_idx = (pitch % len(peak_points))
                    actual_peak_idx = peak_points[peak_idx]
                    
                    animation_strength = velocity * self.max_bounce_height * 1.8
                    if actual_peak_idx in self.peak_animations:
                        self.peak_animations[actual_peak_idx] = max(
                            self.peak_animations[actual_peak_idx], 
                            animation_strength
                        )
                    else:
                        self.peak_animations[actual_peak_idx] = animation_strength

        if self.peak_animations:
            for peak_idx, bounce_offset in self.peak_animations.items():
                orig_point = self.original_mountain_points[peak_idx]
                self.mountain_points[peak_idx] = Point(orig_point.x, orig_point.y - bounce_offset)
            
            if not self.last_frame_had_animation:
                for i, orig_point in enumerate(self.original_mountain_points):
                    if i not in self.peak_animations:
                        self.mountain_points[i] = Point(orig_point.x, orig_point.y)
            
            self.last_frame_had_animation = True
        else:
            if self.last_frame_had_animation:
                self.mountain_points = [Point(p.x, p.y) for p in self.original_mountain_points]
            self.animation_dirty = False
            self.last_frame_had_animation = False

    def point_in_mountain(self, x, y):
        """Return whether the point (x,y) is inside the mountain area (between outline and horizon).
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
        """Return the outline y coordinate at a given x (linear interpolation)"""
        x_key = int(x)
        if not self.animation_dirty and x_key in self._mountain_y_cache:
            return self._mountain_y_cache[x_key]
            
        for i in range(len(self.mountain_points) - 1):
            x1, y1 = self.mountain_points[i].x, self.mountain_points[i].y
            x2, y2 = self.mountain_points[i + 1].x, self.mountain_points[i + 1].y

            if x1 <= x <= x2:
                if x2 - x1 != 0:
                    y_result = y1 + (y2 - y1) * (x - x1) / (x2 - x1)
                else:
                    y_result = y1
                    
                if not self.animation_dirty:
                    self._mountain_y_cache[x_key] = y_result
                return y_result
                
        # If x is outside known points, return horizon as fallback
        fallback = self.horizon_y
        if not self.animation_dirty:
            self._mountain_y_cache[x_key] = fallback
        return fallback

    def generate_triangles(self):
        """Generate triangles"""
        if self.animation_dirty:
            self._mountain_y_cache.clear()
        
        self.triangles = []

        triangle_height = self.triangle_size * math.sqrt(3) / 2
        int_triangle_height = int(round(triangle_height))
        if int_triangle_height <= 0:
            int_triangle_height = 1 
            
        # Pre-generate color variations for better performance
        if not self._cached_colors:
            self._pregenerate_colors()

        triangle_size_half = self.triangle_size // 2
        
        for y in range(-self.triangle_size, self.height + self.triangle_size, int_triangle_height):
            for x in range(-self.triangle_size, self.width + self.triangle_size, self.triangle_size):
                # Offset every other row for a staggered (hex-like) tiling
                x_offset = triangle_size_half if ((y // int_triangle_height) % 2) == 0 else 0
                x_pos = x + x_offset

                # Upward-pointing triangle
                tri_up = [
                    Point(x_pos, y),
                    Point(x_pos + triangle_size_half, y - triangle_height),
                    Point(x_pos + self.triangle_size, y)
                ]
                # Downward-pointing triangle
                tri_down = [
                    Point(x_pos, y),
                    Point(x_pos + triangle_size_half, y + triangle_height),
                    Point(x_pos + self.triangle_size, y)
                ]

                for triangle_points in (tri_up, tri_down):
                    min_y = min(p.y for p in triangle_points)
                    if min_y > self.horizon_y:
                        continue
                        
                    in_mountain = any(self.point_in_mountain(p.x, p.y) for p in triangle_points)

                    if in_mountain:
                        vertices = []
                        for p in triangle_points:
                            mountain_y = self.get_mountain_y_at_x(p.x)
                            vy_clamped = max(mountain_y, min(p.y, self.horizon_y))

                            vx_clamped = int(round(max(0, min(self.width, p.x))))
                            vy_clamped = int(round(max(0, min(self.height, vy_clamped))))
                            vertices.append(Point(vx_clamped, vy_clamped))

                        if len(vertices) == 3:
                            p0, p1, p2 = vertices
                            area = abs((p1.x - p0.x) * (p2.y - p0.y) -
                                       (p2.x - p0.x) * (p1.y - p0.y))
                            if area > 1:
                                # Use pre-generated color variation
                                color = random.choice(self._cached_colors)
                                
                                # Create Triangle object instead of storing raw vertices
                                triangle_obj = Triangle(vertices[0], vertices[1], vertices[2], color=color)
                                self.triangles.append(triangle_obj)
                                if self.layer_index == 2:
                                    triangle_outline_obj = Triangle(vertices[0], vertices[1], vertices[2], color=TRIANGLE_OUTLINE)
                                    self.triangles.append(triangle_outline_obj)
        
    def _pregenerate_colors(self, num_colors=30):
        """Pre-generate color variations to avoid repeated calculations"""
        self._cached_colors = []
        for _ in range(num_colors):
            color_variation = random.randint(-15, 15)
            color = (
                max(0, min(255, self.color[0] + color_variation)),
                max(0, min(255, self.color[1] + color_variation)),
                max(0, min(255, self.color[2] + color_variation))
            )
            self._cached_colors.append(color)

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
        self.base_horizon_y = self.height // 3

        # Create three mountain layers (from far to near)
        self.layers = [
            MountainLayer(self.width, self.height, 0, self.base_horizon_y),  # farthest
            MountainLayer(self.width, self.height, 1, self.base_horizon_y),  # middle
            MountainLayer(self.width, self.height, 2, self.base_horizon_y)  # nearest
        ]

        self._active_notes = {}


    def update_by_note(self, notes):

        self._active_notes = {}

        if not notes:
            for layer in self.layers:
                if layer.peak_animations: 
                    layer.update_peak_animations({})
                    if (layer.animation_dirty and 
                        (layer.layer_index == 2 or layer.triangles_generation_cooldown == 0)):
                        layer.generate_triangles()
            return

       
        for note in notes:
            vel_norm = float(note.velocity_on) / 127.0 if note.velocity_on > 0 else 0.0
            if vel_norm > 0:
                self._active_notes[note.pitch] = vel_norm

        for layer in self.layers:
            layer.update_peak_animations(self._active_notes)
            
            if (layer.animation_dirty and 
                (layer.layer_index == 2 or layer.triangles_generation_cooldown == 0)):
                layer.generate_triangles()

    def generate_all_layers(self):
        """Generate outline and triangles for every layer."""
        for layer in self.layers:
            layer.generate_mountain_outline()
            layer.generate_triangles()

    def draw(self, screen):
        """Draw all mountain layers to the screen (from far to near)."""
        for layer in self.layers:
            layer.draw(screen)
            