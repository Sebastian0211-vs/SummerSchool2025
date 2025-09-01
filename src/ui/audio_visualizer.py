import pygame
import sys
import math
import time
import os
import random
from .shape import Point, Rectangle
from .cow import Cow
from .edelweiss import Edelweiss
from .mountains import MountainGenerator
from .icosphere import AudioIcosphereVisualizer
from .grass import GrassGenerator


class AudioVisualizer:
    # Singleton: ensure only one instance of AudioVisualizer exists
    _instance = None

    def __new__(cls, midi_notes=None, midi_file_path=None):
        # Create new instance only if one doesn't already exist
        if cls._instance is None:
            cls._instance = super(AudioVisualizer, cls).__new__(cls)
        return cls._instance

    def __init__(self, midi_notes=None, midi_file_path=None):
        # Avoid reinitialization if one instance already exists
        if hasattr(self, "initialized"):
            return

        # Initialize pygame and create display window
        pygame.init()

        # Initialize mixer for MIDI playback
        try:
            pygame.mixer.init()
        except pygame.error as e:
            print(f"Audio initialization failed: {e}")
            print("Continuing in visual-only mode")

        # Window
        pygame.display.set_caption("Summer school 01 Audio Visualizer")
        self.width = 1000
        self.height = 1000
        self.screen = pygame.display.set_mode((self.width, self.height))

        # Clock
        self.clock = pygame.time.Clock()

        # MIDI
        self.midi_notes = midi_notes
        self.midi_file_path = midi_file_path
        self.trumpet_notes = self.midi_notes.get(0, [])
        self.piano_notes = self.midi_notes.get(1, [])
        self.midi_start_time = None

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

        self.ground_height = self.height * (2 / 3)
        ground_center_y = self.height - self.ground_height / 2
        self.ground = Rectangle(
            Point(self.width / 2, ground_center_y),
            self.ground_height,
            self.width,
            color=(101, 67, 33),
        )

        # Init cows
        self.cow1 = Cow(
            Point(self.width * 0.1, self.height * 0.85),
            color=(0, 0, 0),
            scale_factor=1,
            facing_direction=1,
        )
        self.cow2 = Cow(
            Point(self.width * 0.9, self.height * 0.9),
            color=(160, 82, 45),
            scale_factor=1,
            facing_direction=-1,
        )

        # Init main Edelweiss
        self.main_edelweiss = Edelweiss(
            Point(500, 500),
        )

        # Init 12 flowers - one per note section
        self.flowers = []
        self.create_flower_grid()

        # Update state
        self.running = True
        self.initialized = True

    def create_flower_grid(self):
        """Create 12 flowers, one for each note (0-11)"""
        section_width = self.width / 12
        base_y = self.height - 50

        for i in range(12):
            x_pos = section_width * i + section_width / 2
            flower = {
                "note_index": i,
                "base_y": base_y,
                "target_y": base_y,
                "current_note": None,
                "edelweiss": Edelweiss(
                    Point(x_pos, base_y),
                    scale_factor=0.5,
                ),
            }
            self.flowers.append(flower)

    def _update_shapes(self):
        # Update Interface based on notes
        if self.piano_notes or self.trumpet_notes:

            if self.midi_start_time is None:
                self.midi_start_time = time.time()

            # Calculate delta time
            current_midi_time = time.time() - self.midi_start_time

            # Piano animation
            active_piano_notes = [
                note
                for note in self.piano_notes
                if note.start_tick <= current_midi_time <= note.end_tick
            ]
            if active_piano_notes:
                latest_note = active_piano_notes[-1]
                self.main_edelweiss.update_by_note(latest_note, 0.2)

                self._update_flower_grid(active_piano_notes)

            # TODO: Trumpet animation

    def _update_flower_grid(self, active_notes):
        """Update 12 flowers based on note amplitudes with spinning and color changes"""

        # Reset all flowers - clear active notes
        for flower in self.flowers:
            flower["current_note"] = None
            flower["target_y"] = flower["base_y"]

        # Update flowers based on active notes
        for note in active_notes:
            note_index = note.pitch % 12
            flower = self.flowers[note_index]
            flower["current_note"] = note

            # Calculate amplitude based movement
            amplitude = note.velocity_on
            max_height = self.height / 3
            min_y = self.height - max_height

            # Normalize amplitude (0-127) to movement range
            y_offset = (amplitude / 127.0) * (flower["base_y"] - min_y)
            flower["target_y"] = flower["base_y"] - y_offset

        # Update all flowers (position, rotation, color)
        for flower in self.flowers:
            edelweiss = flower["edelweiss"]

            # Smooth position interpolation
            current_y = edelweiss.center.y
            target_y = flower["target_y"]
            dy = (target_y - current_y) * 0.1  # Smooth movement

            if abs(dy) > 0.1:
                edelweiss.translate(0, dy)

            # Handle spinning, color changes, and scaling during note duration
            if flower["current_note"]:

                amplitude = flower["current_note"].velocity_on
                base_scale = 0.6
                min_scale = 0.2

                scale_factor = base_scale - (amplitude / 127.0) * (
                    base_scale - min_scale
                )
                edelweiss.set_scale_factor(scale_factor)

                # Spin the flower and apply color changes
                edelweiss.update_by_note(flower["current_note"], 0.5)
            else:
                # Reset to base scale and white when no note is active
                edelweiss.set_scale_factor(0.5)
                edelweiss.set_petal_color((255, 255, 255))

    def _draw_shapes(self):
        # Draw the sky
        self.screen.fill((135, 206, 235))

        # Draw background
        self.ground.draw(self.screen)
        self.grass.draw(self.screen)
        self.sun.draw(self.screen)
        self.mountains.draw(self.screen)

        # Draw cows
        self.cow1.draw(self.screen)
        self.cow2.draw(self.screen)

        # Draw grid flowers
        for flower in self.flowers:
            flower["edelweiss"].draw(self.screen)

        # Draw main edelweiss (foreground)
        self.main_edelweiss.draw(self.screen)

    def run(self):
        # Start MIDI playback
        if self.midi_file_path and os.path.exists(self.midi_file_path):
            pygame.mixer.music.load(self.midi_file_path)
            pygame.mixer.music.play()

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
