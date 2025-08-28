import time
from soundToMidiLocalLibrary.sound_to_midi.mainOptimised import proceed

filename =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
fileout  =  'src/audio/res/midiOutputs/testClaudePolyphony.mid'

PPp      =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
PPt      =  'src/audio/res/samples/premade/PinkPanther_Trumpet_Only.mp3'

midi = proceed(PPt, False)
with open(fileout, 'wb') as f:
    midi.writeFile(f)

print("FINISHED")