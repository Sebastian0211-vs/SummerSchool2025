import pygame
import sys
import random
from .shape import Point, Square

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
        if hasattr(self, 'initialized'):
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

        # Update state
        self.running = True
        self.initialized = True
        
        # Create squares for rotation demo
        self.square1 = Square(Point(self.width // 2, self.height // 2), 80, (255, 255, 255))  # White square rotating around its center
        self.square2 = Square(Point(self.width // 2 - 100, self.height // 2), 60, (255, 100, 100))  # Red square rotating around offset point
    
    def draw_squares(self):
        # Square 1: Rotate around its own center (white) - no origin specified = uses center
        self.square1.rotate(self.square1.current_rotation + 0.02)
        
        # Square 2: Grow by random amount and rotate around offset point (red)
        growth = random.uniform(0.1, 2.0)  # Random growth between 0.1 and 2.0 pixels
        new_size = self.square2.size + growth
        self.square2.set_size(new_size)
        
        offset_point = Point(self.square2.center.x + 100, self.square2.center.y)
        self.square2.rotate(self.square2.current_rotation + 0.03, offset_point)
        
        # Draw both squares using their draw method
        self.square1.draw(self.screen)
        self.square2.draw(self.screen)
    
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
