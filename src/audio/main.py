import librosa
import time
from soundToMidiLocalLibrary.sound_to_midi.main import wave_to_midi_poly

filename =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
fileout =   'src/audio/res/midiOutputs/testPolyphony.mid'

y, sr = librosa.load(filename, sr=None)
'''
Using git's sound_to_midi that utilizes librosa
So attempting to improve it in order to have a
more accurate transposer.
'''
timeStart = time.time()
midi = wave_to_midi_poly(y, sr)
with open(fileout, 'wb') as f:
    midi.writeFile(f)
timeEnd = time.time() - timeStart

print("/////////////FINISHED IN ", timeEnd/60, "MINUTES///////////////////")
