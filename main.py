from src.midi.models import Note
from src.midi.parser import parse_midi
import os
import pygame
from src.ui.audio_visualizer import AudioVisualizer
from src.audio.AudioSplitter_v1 import AudioSplit
from src.audio.audiosplitter_v2 import separate_two_harmonic_sources


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

    res_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(res_dir, "ressources")
    input_file_mp3 = os.path.join(res_dir, "MP3", "Ecossaise_Both.mp3")
    piano_wav_out = os.path.join(res_dir, "temp", "piano.wav")
    trumpet_wav_out = os.path.join(res_dir, "temp", "trumpet.wav")

    print("Input file:", input_file_mp3)
    print("Piano output file:", piano_wav_out)
    print("Trumpet output file:", trumpet_wav_out)

    AudioSplit(input_file_mp3,
               piano_wav_out,
               trumpet_wav_out,
               aggressiveness=0.9,      # pousse la séparation
               debug_dir="debug_run_v5"     # dossier où sauver les spectrogrammes/masks
)
    #separate_two_harmonic_sources(input_file_mp3, piano_wav_out, trumpet_wav_out)


if __name__ == "__main__":
    main()
