import pygame
import sys
import math
from .shape import Point
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

        # Init background
        self.mountains = MountainGenerator((self.width, self.height))
        self.mountains.generate_all_layers()

        self.sun = AudioIcosphereVisualizer(
            (self.width, self.height),
            sensitivity=2.0,
            rotation_speed=0.5,
            fps=60,
            subdivisions=2,
            base_scale=250,
        )

        self.grass = GrassGenerator((self.width, self.height), 2000)
        self.grass.generate()

        self.soil = Soil((self.width, self.height), 40, 0.02)
        self.soil.generate()

        # Initialize cows
        self.cow1 = Cow(
            Point(self.width * 0.1, self.height * 0.85),
            color=(0, 0, 0),
            scale_factor=0.8,
            facing_direction=1,
        )
        self.cow2 = Cow(
            Point(self.width * 0.9, self.height * 0.9),
            color=(160, 82, 45),
            scale_factor=0.6,
            facing_direction=-1,
        )

        # Cow animation variables
        self.cow1_direction = -1
        self.cow2_direction = 1
        self.cow_speed = 10.0
        self.walk_angle = 0
        self.movement_top = self.height * (1 / 3)
        self.movement_bottom = self.height * 0.98

        # Update state
        self.running = True
        self.initialized = True

    def _update_shapes(self):
        # Update walk angle for animation
        self.walk_angle += 0.1

        # Move cows vertically
        self.cow1.center.y += self.cow1_direction * self.cow_speed
        self.cow2.center.y += self.cow2_direction * self.cow_speed

        # Reverse direction at movement boundaries
        if self.cow1.center.y <= self.movement_top:
            self.cow1_direction = 1
        elif self.cow1.center.y >= self.movement_bottom:
            self.cow1_direction = -1

        if self.cow2.center.y <= self.movement_top:
            self.cow2_direction = 1
        elif self.cow2.center.y >= self.movement_bottom:
            self.cow2_direction = -1

        # Apply depth effect by adjusting scale based on y position
        # Higher y values (lower on screen) = larger scale (closer)
        # Lower y values (higher on screen) = smaller scale (farther)
        depth_factor1 = 0.4 + (self.cow1.center.y / self.height) * 0.6
        depth_factor2 = 0.4 + (self.cow2.center.y / self.height) * 0.6

        self.cow1.set_scale_factor(depth_factor1)
        self.cow2.set_scale_factor(depth_factor2)

        # Apply walking animation
        self.cow1.walk(self.walk_angle)
        self.cow2.walk(self.walk_angle + math.pi)  # Offset walk cycle

    def _draw_shapes(self):
        # Draw the sky
        self.screen.fill((135, 206, 235))

        # Draw background
        self.soil.draw(self.screen)
        self.grass.draw(self.screen)
        self.sun.draw(self.screen)
        self.mountains.draw(self.screen)

        # Draw cows
        self.cow1.draw(self.screen)
        self.cow2.draw(self.screen)

    def run(self):
        # Main loop
        while self.running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False

            # Draw shapes and updating
            self._update_shapes()
            self._draw_shapes()
            pygame.display.flip()

            # Limit to 60 FPS
            self.clock.tick(60)

        # Clean up and exit correctly
        pygame.quit()
        sys.exit()
