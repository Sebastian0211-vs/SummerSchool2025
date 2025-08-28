import time
from mp3_to_midi_converter import proceed

filename =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
fileout  =  'src/audio/res/midiOutputs/RV0.mid'

PPp      =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
PPt      =  'src/audio/res/samples/premade/PinkPanther_Trumpet_Only.mp3'

midi = proceed(filename, False)
with open(fileout, 'wb') as f:
    midi.writeFile(f)

print("FINISHED")