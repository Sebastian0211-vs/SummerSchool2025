import librosa
import math
import time

from sound_to_midi.monophonic import wave_to_midi
from sound_to_midi.monophonic import midiutil

'''
//////////////////////Initial test//////////////////////
'''
filename = 'src/audio/res/samples/SebPPp2.wav'
#filename = 'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
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
//////////////////////Other tests//////////////////////
'''




'''
////////////////////// //////////////////////
Using git's sound_to_midi that utilizes librosa
So attempting to improve it in order to have a
more accurate transposer.
'''
fileout = 'src/audio/res/midiOutputs/testPolyphony.mid'

timeStart = time.time()

midi = wave_to_midi(y, sr)
with open(fileout, 'wb') as f:
    midi.writeFile(f)

timeEnd = time.time() - timeStart

print("///////////////////FINISHED///////////////////")
print("In ", timeEnd, "seconds !")
