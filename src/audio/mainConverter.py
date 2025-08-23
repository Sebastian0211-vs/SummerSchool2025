import librosa
import math

from sound_to_midi.monophonic import wave_to_midi
from sound_to_midi.monophonic import midiutil

'''
//////////////////////Initial test//////////////////////
'''
filename = 'src/audio/res/samples/SebET.wav'
#srate = librosa.get_samplerate(filename)
y, sr = librosa.load(filename, sr=None)
#print("Nummer uno: ", y)
#print("Nummer due", sr)

tempo, beatFrames = librosa.beat.beat_track(y=y, sr=sr)
#beatTimes = librosa.frames_to_time(beatFrames, sr=sr)
#print(beatFrames)
#print(format(tempo))
#print(beatTimes)
audioBPM = math.ceil(tempo)
print("This be my bpm estimate: ", audioBPM)

'''
////////////////////// //////////////////////
Using git's sound_to_midi that utilizes librosa
So attempting to improve it in order to have a
more accurate transposer.
'''
fileout = 'src/audio/res/midiOutputs/Et2.mid'

midi = wave_to_midi(y, sr)
with open(fileout, 'wb') as f:
    midi.writeFile(f)

print("///////////////////FINISHED///////////////////")
