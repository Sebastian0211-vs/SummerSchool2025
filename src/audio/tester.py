import librosa
import math

filename = 'src/audio/res/samples/PinkPanther_Both.mp3'
#filename = "src/audio/res/samples/wavSample.wav"
y, sr = librosa.load(filename, sr=None)
#print(y)
#print(sr)

tempo, beatFrames = librosa.beat.beat_track(y=y, sr=sr)
#beatTimes = librosa.frames_to_time(beatFrames, sr=sr)
#print(beatFrames)
#print(format(tempo))
#print(beatTimes)
audioBPM = (tempo)
print("This be my bpm estimate: ", audioBPM)