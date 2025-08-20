import librosa
import math

#//////////////////////Initial test/////////////////////////
filename = "src/audio/res/samples/PinkPanther_Piano_Only.mp3"
#filename = "src/audio/res/samples/wavSample.wav"
y, sr = librosa.load(filename, sr=None)
#print(y)
#print(sr)

tempo, beatFrames = librosa.beat.beat_track(y=y, sr=sr)
#beatTimes = librosa.frames_to_time(beatFrames, sr=sr)
#print(beatFrames)
#print(format(tempo))
#print(beatTimes)
audioBPM = math.ceil(tempo)
'''

#//////////////////////First version////////////////////////
from sound_to_midi.monophonic import wave_to_midi
from sound_to_midi.monophonic import midiutil


fileout = 'src/audio/res/samples/midiOutputs/testMidi.mid'
v
midi = wave_to_midi(y)
with open(fileout, 'wb') as f:
    midi.writeFile(f)
print("Finished")
'''

#//////////////////////Second version////////////////////////
chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr)
#chroma_cens = ((1,5,3),(4,5,6),(2,3,9))
noteTable = [] #the index is the timestamp and the value is the note
def whichNote(nbr: float):
    match nbr:
        case 0:
            return "C"
        case 1:
            return "C#"
        case 2:
            return "D"
        case 3:
            return "D#"
        case 4:
            return "E"
        case 5:
            return "F"
        case 6:
            return "F#"
        case 7:
            return "G"
        case 8:
            return "G#"
        case 9:
            return "A"
        case 10:
            return "A#"
        case 11:
            return "B"

for i in range(len(chroma_cens[0])):
    max = 0
    counter = 0
    for j in range(len(chroma_cens)):
        if(chroma_cens[j][i] > max):
            max = chroma_cens[j][i]
            counter += 1
        #t = max(chroma_cens[j][i])
    noteTable.append(whichNote(counter))

for i in noteTable:
    print(i)

midi = []

for i in noteTable:
    midi.append(librosa.note_to_midi(i))

'''
with open('src/audio/res/samples/midiOutputs/testMidi2.mid', 'wb') as f:
    midi.writeFile(f)
'''

from miditime.MIDITime import MIDITime

mymidi = MIDITime(audioBPM, 'src/audio/res/samples/midiOutputs/testMidi2.mid')

midiNotes = []
for i in range(len(midi)):
    midiNotes.append([i, midi[i], 127, 1])

mymidi.add_track(midiNotes)
mymidi.save_midi()

print("FINISHED")
