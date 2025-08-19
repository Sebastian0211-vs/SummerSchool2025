import pygame
import sys

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
    
    def draw_triangle(self):
        center_x = self.width // 2
        center_y = self.height // 2
        triangle_size = 50

        points = [
            (center_x, center_y - triangle_size),  # Top vertex
            (center_x - triangle_size, center_y + triangle_size),  # Bottom left
            (center_x + triangle_size, center_y + triangle_size)   # Bottom right
        ]
        
        pygame.draw.polygon(self.screen, (255, 255, 255), points)
    
    def run(self):
        # Main loop
        while self.running:
            # Handle pygame events
            for event in pygame.event.get():
                if event.type == pygame.QUIT:
                    self.running = False
            
            # Clear screen with black background
            self.screen.fill((0, 0, 0))
            # Draw the triangle shape
            self.draw_triangle()

            # Update the display
            pygame.display.flip()

            # Limit to 60 FPS
            self.clock.tick(60)
        
        # Clean up and exit correctly
        pygame.quit()
        sys.exit()
