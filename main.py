import argparse

from src.midi.parser import parse_midi
import os
from src.ui.audio_visualizer import AudioVisualizer
from src.audio.AudioSplitter_v1 import AudioSplit
from src.audio.mp3_to_midi_converter import convertMp3ToMidi

def main():
    res_dir = os.path.dirname(os.path.abspath(__file__))
    res_dir = os.path.join(res_dir, "ressources")
    input_file_mp3 = os.path.join(res_dir, "MP3", "Final/SSB.mp3")
    piano_wav_out = os.path.join(res_dir, "temp", "piano.wav")
    trumpet_wav_out = os.path.join(res_dir, "temp", "trumpet.wav")

    ap = argparse.ArgumentParser(description="Audio to MIDI Converter")
    ap.add_argument("mp3_file", type=str, help="Path to the input MP3 file")

    # Note extraction
    midi_notes = {}
    project_root = os.path.dirname(os.path.abspath(__file__))
    midi_file_path = os.path.join(
        project_root, "ressources", "Midi", "Ecossaise_Beethoven.midi"
    )



    args = ap.parse_args()
    input_file_mp3 = args.mp3_file

    print("Starting audio separation...")
    AudioSplit(input_file_mp3,
               piano_wav_out,
               trumpet_wav_out,
               n_fft=4096,  # taille de la fenêtre FFT
               hop_length=1024,  # pas de la fenêtre FFT
               aggressiveness=0.8,  # pousse la séparation
               expand_piano=False,  # agrandit la plage de fréquences du piano
               debug_dir="debug_run_v5"  # dossier où sauver les spectrogrammes/masks
               )
    print("Audio separation completed.")
    print("Starting MP3 to MIDI conversion...")
    midi = convertMp3ToMidi(trumpet_wav_out, piano_wav_out)
    with open(midi_file_path, 'wb') as f:
        midi.writeFile(f)

    print("MP3 to MIDI conversion completed.")

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
    visualizer = AudioVisualizer(midi_notes=midi_notes, midi_file_path=input_file_mp3)
    print("Launching audio visualizer...")
    visualizer.run()






    #separate_two_harmonic_sources(input_file_mp3, piano_wav_out, trumpet_wav_out)


if __name__ == "__main__":
    main()
