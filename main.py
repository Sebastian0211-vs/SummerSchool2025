from src.midi.models import Note
from src.midi.parser import parse_midi
import os
from src.ui.audio_visualizer import AudioVisualizer
from src.audio.AudioSplitter_v1 import AudioSplit


from src.ui.audio_visualizer import AudioVisualizer

def main():

    visualizer = AudioVisualizer()
    visualizer.run()

    # res_dir = os.path.dirname(os.path.abspath(__file__))
    # res_dir = os.path.join(res_dir, "ressources")
    # input_file_mp3 = os.path.join(res_dir, "MP3", "Ecossaise_Both.mp3")
    # piano_wav_out = os.path.join(res_dir, "temp", "piano.wav")
    # trumpet_wav_out = os.path.join(res_dir, "temp", "trumpet.wav")
    #
    # print("Input file:", input_file_mp3)
    # print("Piano output file:", piano_wav_out)
    # print("Trumpet output file:", trumpet_wav_out)
    #
    # AudioSplit(input_file_mp3, piano_wav_out, trumpet_wav_out)


if __name__ == "__main__":
    main()
