import pygame
import sys
import math
from .shape import Point, Square, Circle, Triangle, Rectangle, Oval
from .cow import Cow
from .mountains import MountainGenerator
from .icosphere import AudioIcosphereVisualizer
from .grass import GrassGenerator
from .soil import Soil

class AudioVisualizer:
    # Singleton: ensure only one instance of AudioVisualizer exists
    _instance = None

    def __new__(cls):
        # Create new instance only if one doesn't already exist
        if cls._instance is None:
            cls._instance = super(AudioVisualizer, cls).__new__(cls)
        return cls._instance

    def __init__(self):
        # Avoid reinitialization if one instance already exists
        if hasattr(self, "initialized"):
            return

        # Initialize pygame and create display window
        pygame.init()

        # Window
        pygame.display.set_caption("Summer school 01 Audio Visualizer")
        self.width = 1000
        self.height = 1000
        self.screen = pygame.display.set_mode((self.width, self.height))

        # Clock
        self.clock = pygame.time.Clock()

        # Mountains
        self.mountains = MountainGenerator((self.width, self.height))
        self.mountains.generate_all_layers()

        # Sun
        self.sun = AudioIcosphereVisualizer(
            (self.width, self.height),
            sensitivity=2.0,
            rotation_speed=0.5,
            fps=60,
            subdivisions=3,
            base_scale=350,
        )

        # Grass
        self.grass = GrassGenerator((self.width, self.height), 10000)
        self.grass.generate()

        # Soil
        self.soil = Soil((self.width, self.height), 20, 0.02)
        self.soil.generate()

        # Update state
        self.running = True
        self.initialized = True

        # Create shapes for rotation demo
        self.square1 = Square(
            Point(self.width // 2, self.height // 2), 80, (255, 255, 255)
        )  # White square rotating around its center
        self.circle2 = Circle(
            Point(self.width // 2 - 200, self.height // 2), 30, (255, 100, 100)
        )  # Red circle rotating around offset point

        # Create a triangle that rotates around its center
        triangle_center = Point(self.width // 2 + 200, self.height // 2)
        triangle_size = 60
        self.triangle3 = Triangle(
            Point(triangle_center.x, triangle_center.y - triangle_size),  # Top point
            Point(
                triangle_center.x - triangle_size * 0.3,
                triangle_center.y + triangle_size * 0.5,
            ),  # Bottom left
            Point(
                triangle_center.x + triangle_size * 0.866,
                triangle_center.y + triangle_size * 0.5,
            ),  # Bottom right
            (100, 255, 100),  # Green color
        )

        # Create a rectangle that changes dimensions
        self.rectangle4 = Rectangle(
            Point(self.width // 2 - 100, self.height // 2 + 200),
            60,
            100,  # height, width
            (100, 100, 255),  # Blue color
        )

        # Create an oval that morphs its radii
        self.oval5 = Oval(
            Point(self.width // 2 + 100, self.height // 2 + 200),
            50,
            30,  # rx, ry
            (255, 255, 100),  # Yellow color
        )

        # Pulsation variables for the circle
        self.base_radius = 30
        self.pulse_amplitude = 20  # How much bigger/smaller it gets
        self.pulse_speed = 0.05  # How fast it pulsates

        # Rectangle morphing variables
        self.base_width = 100
        self.base_height = 60
        self.morph_speed = 0.03

        # Oval morphing variables
        self.base_rx = 50
        self.base_ry = 30
        self.oval_speed = 0.04

        # Translation demo shape
        # Orbital circle: Circle that orbits around window center with varying distance
        self.orbital_circle = Circle(
            Point(self.width // 2, self.height // 2 - 100),
            25,
            color=(100, 255, 180),  # Light green
        )

        # Store window center for orbital calculations
        self.window_center = Point(self.width // 2, self.height // 2)

        # Store triangle's home position for vertical movement
        self.triangle_home = Point(self.triangle3.center.x, self.triangle3.center.y)

        # Add two cows - one facing right, one facing left
        self.cow_right = Cow(Point(self.width // 2 - 300, self.height // 2 - 300), facing_direction=1)
        self.cow_left = Cow(Point(self.width // 2 + 300, self.height // 2 - 300), facing_direction=-1)
        
        # Cow animation variables - restrict to 2/3 of screen
        screen_range = self.height * 2/3  # 2/3 of screen height
        start_y = self.height / 6  # Start at 1/6 from top
        self.cow_min_y = start_y
        self.cow_max_y = start_y + screen_range
        self.cow_speed = 0.002  # Speed of vertical movement

    def draw_squares(self):
        current_time = pygame.time.get_ticks()

        # Square 1: Rotate around its own center (white) - consistent rotation speed
        self.square1.rotate(current_time * 0.001)

        # Circle 2: Pulsate (grow and shrink) and rotate around offset point (red)
        pulse_factor = math.sin(
            current_time * self.pulse_speed / 100
        )  # Oscillates between -1 and 1
        new_radius = self.base_radius + self.pulse_amplitude * pulse_factor
        self.circle2.set_radius(max(5, new_radius))  # Ensure minimum radius of 5

        self.circle2.rotate(current_time * 0.0015, self.square1.center)

        # Triangle 3: Rotate around its own center + vertical movement (green)
        # Calculate desired vertical position
        vertical_offset = 80 * math.sin(current_time * 0.002)  # Moves up/down 80 pixels
        desired_y = self.triangle_home.y + vertical_offset

        # Calculate translation needed
        dy_triangle = desired_y - self.triangle3.center.y

        # Apply vertical translation if needed
        if abs(dy_triangle) > 0.1:
            self.triangle3.translate(0, dy_triangle)

        # Apply rotation around its own center
        self.triangle3.rotate(current_time * 0.001)

        # Rectangle 4: Morph width/height and rotate (blue)
        width_factor = math.sin(current_time * self.morph_speed / 100)
        height_factor = math.cos(current_time * self.morph_speed / 100)

        new_width = self.base_width + 40 * width_factor
        new_height = self.base_height + 30 * height_factor

        self.rectangle4.set_width(new_width)
        self.rectangle4.set_height(new_height)
        self.rectangle4.rotate(current_time * 0.00125)

        # Oval 5: Morph rx/ry and rotate (yellow)
        rx_factor = math.sin(current_time * self.oval_speed / 100)
        ry_factor = math.cos(
            current_time * self.oval_speed / 100 * 1.3
        )  # Different frequency

        new_rx = self.base_rx + 25 * rx_factor
        new_ry = self.base_ry + 20 * ry_factor

        self.oval5.set_rx(new_rx)
        self.oval5.set_ry(new_ry)
        self.oval5.rotate(current_time * 0.00175)

        # Translation animations
        self.animate_translations(current_time)



        # Draw points at 0°, 90°, 180° from circle's outerPoints
        #for angle, color in [(0, (255, 0, 0)), (180, (0, 255, 0)), (270, (0, 0, 255))]:
        #    if angle in self.cow_right.body.outerPoints:
        #        point = self.cow_right.body.outerPoints[angle]
        #        pygame.draw.circle(self.screen, color, (int(point.x), int(point.y)), 5)

        # Translation test: Draw triangle outer points to verify they update correctly
        triangle_points = ["a", "b", "c"]
        triangle_colors = [
            (255, 255, 0),
            (255, 0, 255),
            (0, 255, 255),
        ]  # Yellow, Magenta, Cyan
        #for point_key, color in zip(triangle_points, triangle_colors):
        #    if point_key in self.triangle3.outerPoints:
        #        point = self.triangle3.outerPoints[point_key]
        #        pygame.draw.circle(self.screen, color, (int(point.x), int(point.y)), 8)

        # Draw translation demo shape
        #self.orbital_circle.draw(self.screen)

        # Draw soil
        self.soil.draw(self.screen)

        # Draw grass
        self.grass.draw(self.screen)

        # Draw mountains
        self.mountains.draw(self.screen)        


        # Animate and draw both cows
        self.animate_cow(current_time, self.cow_right)
        self.animate_cow(current_time, self.cow_left, phase_offset=math.pi)  # Out of phase
        self.cow_right.draw(self.screen)
        self.cow_left.draw(self.screen)

        # Draw the sun
        self.sun.draw(self.screen)

    def animate_translations(self, time):
        """Handle translation animation for the orbital circle"""

        # Orbital circle: Orbits around window center with varying distance (even slower)
        orbit_angle = time * 0.0075  # Reduced by half to make it 2x slower
        orbit_distance = 150 + 50 * math.sin(
            time * 0.004
        )  # Reduced by half, distance varies between 100-200

        # Calculate desired orbital position
        orbit_x = self.window_center.x + orbit_distance * math.cos(orbit_angle)
        orbit_y = self.window_center.y + orbit_distance * math.sin(orbit_angle)

        # Calculate translation needed
        dx_orbital = orbit_x - self.orbital_circle.center.x
        dy_orbital = orbit_y - self.orbital_circle.center.y

        # Apply translation (smooth orbital motion)
        if abs(dx_orbital) > 0.1 or abs(dy_orbital) > 0.1:
            self.orbital_circle.translate(dx_orbital, dy_orbital)

        # Make the orbital circle rotate to align tracked points with the rotation center
        # Calculate angle from circle center to window center to align the tracked points
        angle_to_center = math.atan2(
            self.window_center.y - self.orbital_circle.center.y,
            self.window_center.x - self.orbital_circle.center.x,
        )
        self.orbital_circle.rotate(angle_to_center)

    def animate_cow(self, time, cow, phase_offset=0):
        """Handle cow animation with vertical movement and scale factor based on position"""
        
        # Calculate vertical position (oscillates between min and max Y)
        y_progress = (math.sin(time * self.cow_speed + phase_offset) + 1) / 2  # 0 to 1
        desired_y = self.cow_min_y + y_progress * (self.cow_max_y - self.cow_min_y)
        
        # Calculate translation needed
        dy = desired_y - cow.center.y
        
        # Apply translation if needed
        if abs(dy) > 0.1:
            cow.translate(0, dy)
        
        # Calculate scale factor based on Y position (0.6 at top, 1.5 at bottom)
        scale_factor = 0.6 + (1.5 - 0.6) * y_progress
        cow.set_scale_factor(scale_factor)
        
        # Walking animation
        walk_angle = time * 0.005
        cow.walk(walk_angle)

    def run(self):
        # Main loop
        while self.running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Clear screen with black background
            self.screen.fill((0, 0, 0))
            # Draw the rotating squares
            self.draw_squares()

            # Update the display
            pygame.display.flip()

            # Limit to 60 FPS
            self.clock.tick(60)

        # Clean up and exit correctly
        pygame.quit()
        sys.exit()
