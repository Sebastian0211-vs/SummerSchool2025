import librosa
import librosa.feature.rhythm


filename =  'src/audio/res/samples/SebPPp2.wav'
y, sr = librosa.load(filename, sr=None)
bpm = librosa.feature.rhythm.tempo(y=y, sr=sr)
