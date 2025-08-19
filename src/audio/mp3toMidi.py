import librosa

filename = "src/audio/res/samples/PinkPanther_Trumpet_Only.mp3"
#filename = "src/audio/res/samples/wavSample.wav"
#y, sr = librosa.load(filename)
#print(y)
#print(sr)

#tempo, beatFrames = librosa.beat.beat_track(y=y, sr=sr)
#beatTimes = librosa.frames_to_time(beatFrames, sr=sr)
#print(beatFrames)
#print(format(tempo))
#print(beatTimes)


from sound_to_midi.monophonic import wave_to_midi
from sound_to_midi.monophonic import midiutil

fileout = 'src/audio/res/midiOutputs/testMidi.mid'

y, sr = librosa.load(filename, sr=None)
midi = wave_to_midi(y)
with open(fileout, 'wb') as f:
    midi.writeFile(f)
print("Finished")
