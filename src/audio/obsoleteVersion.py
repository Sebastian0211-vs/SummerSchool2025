import librosa
import math

#//////////////////////Initial test/////////////////////////
filename = "src/audio/res/samples/PinkPanther_Trumpet_Only.mp3"
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

midi = wave_to_midi(y)
with open(fileout, 'wb') as f:
    midi.writeFile(f)
print("Finished")
'''

#//////////////////////Second version////////////////////////
chroma_cens = librosa.feature.chroma_cens(y=y, sr=sr)
#chroma_cens = ((1,5,3),(4,5,6),(2,3,9))
midiTable = [] #the index is the timestamp and the value is the note
def whichNote(nbr: float):
    match nbr:
        case 0:
            return "C4"
        case 1:
            return "C#4"
        case 2:
            return "D4"
        case 3:
            return "D#4"
        case 4:
            return "E4"
        case 5:
            return "F4"
        case 6:
            return "F#4"
        case 7:
            return "G4"
        case 8:
            return "G#4"
        case 9:
            return "A4"
        case 10:
            return "A#4"
        case 11:
            return "B4"

'''
Gets the strongest note on the chroma_cens chart for each time stamp and 
puts it in a table, where it is converted beforehand into midi notes
thanks to librosa's note_to_midi
'''
for i in range(len(chroma_cens[0])):
    max1 = 0
    max2 = 0
    max3 = 0
    max4 = 0
    max5 = 0
    counter = 0
    for j in range(len(chroma_cens)):
        if(chroma_cens[j][i] > max1):
            #max5 = max4
            #max4 = max3
            #max3 = max2
            max2 = max1
            max1 = chroma_cens[j][i]
            counter += 1
    midiTable.append(librosa.note_to_midi(whichNote((counter-1)%12)))


'''
Prepares the formatting for the save of the midi file thanks to miditime.
Here it counts how many times a midi note appears consecutivly so it can
be played for x amount of beats instead of once every beat which causes
a stutter effect. miditime has the x amount of beats functionnality.
'''
#for i in midiTable:
#    print(i)

'''
Counts the amount of consecutive appearances of a same midi note and puts
it in a new list with the note and it's occurences.
Ex: [3,3,1,2,2,2,2] gives [[3,2][1,1][2,4]]
'''
def count_consecutive(nums):
    if not nums:
        return []

    result = []
    current = nums[0]
    count = 1

    for num in nums[1:]:
        if num == current:
            count += 1
        else:
            result.append([current, count])
            current = num
            count = 1

    # Append the last group
    result.append([current, count])
    return result

midi = count_consecutive(midiTable)
#print(midi)

from miditime.MIDITime import MIDITime
mymidi = MIDITime(audioBPM, 'src/audio/res/samples/midiOutputs/testMidi2.mid')

midiNotes = []
timeStamp = 0
for i in range(len(midi)):
    midiNotes.append([timeStamp, midi[i][0], 127, midi[i][1]])
    timeStamp += midi[i][1]

mymidi.add_track(midiNotes)
mymidi.save_midi()

print("FINISHED")
