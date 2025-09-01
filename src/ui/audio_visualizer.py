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

        # Init fixed flower map for all possible notes
        self.flower_note_map = {}
        unique_piano_notes = set(note.pitch for note in self.piano_notes)
        for i, note_pitch in enumerate(unique_piano_notes):
            # Create flower randomly in the grass
            grass_top = 950
            grass_bottom = self.height * (1 / 3) + 50
            x = random.randint(50, 950)
            y = random.randint(int(grass_bottom), int(grass_top))

            flower = Edelweiss(Point(x, y), scale_factor=0.25)
            self.flower_note_map[note_pitch] = flower

        # Update state
        self.running = True
        self.initialized = True

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

                self._update_static_flower_states(active_piano_notes)

            # TODO: Trumpet animation

    # Update all mapped flowers based on active notes
    def _update_static_flower_states(self, active_notes):
        active_pitches = {note.pitch for note in active_notes}

        for note_pitch, flower in self.flower_note_map.items():
            if note_pitch in active_pitches:
                note = next(note for note in active_notes if note.pitch == note_pitch)
                flower.update_by_note(note, 0)
            else:
                flower.set_petal_color((255, 255, 255))  # White color if no animation

    def _draw_shapes(self):
        # Draw the sky
        self.screen.fill((135, 206, 235))

        # Draw background
        self.ground.draw(self.screen)
        self.grass.draw(self.screen)
        self.sun.draw(self.screen)
        self.mountains.draw(self.screen)

        # Draw mapped flowers first
        for flower in self.flower_note_map.values():
            flower.draw(self.screen)

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
