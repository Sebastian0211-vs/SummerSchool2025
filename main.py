from src.midi.parser import parse_midi
import os
import pygame
from src.ui.audio_visualizer import AudioVisualizer


def main():

    # Note extraction
    midi_notes = {}
    project_root = os.path.dirname(os.path.abspath(__file__))
    midi_file_path = os.path.join(
        project_root, "ressources", "Midi", "Ecossaise_Beethoven.midi"
    )

    if os.path.exists(midi_file_path):
        try:
            midi_notes = parse_midi(midi_file_path)
        except Exception as e:
            midi_notes = {}
            exit(0)
    else:
        print(f"MIDI file not found at: {midi_file_path}")
        exit(0)

    # Visualizer load
    visualizer = AudioVisualizer(midi_notes=midi_notes, midi_file_path=midi_file_path)
    visualizer.run()


if __name__ == "__main__":
    main()
