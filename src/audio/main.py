import time
from mp3_to_midi_converter import convertMp3ToMidi

filename =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
#filename  =  'src/audio/res/samples/Seb/trumpet 1.wav'
fileout   =  'src/audio/res/midiOutputs/Rtest.mid'

chooseYourChallenger = 1
showGraphs = False

match chooseYourChallenger:
    case 1:
        midi = convertMp3ToMidi(filename, showGraphs)
        with open(fileout, 'wb') as f:
                midi.writeFile(f)
    case 2:
        all_premade_filepaths     =    ['src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3',
                                        'src/audio/res/samples/premade/PinkPanther_Trumpet_Only.mp3',
                                        'src/audio/res/samples/premade/Ecossaise_Piano.mp3',
                                        'src/audio/res/samples/premade/Ecossaise_Trumpet.mp3']
        all_midi_output_filepaths =    ['src/audio/res/midiOutputs/ARV1PPp.mid',
                                        'src/audio/res/midiOutputs/ARV1PPt.mid',
                                        'src/audio/res/midiOutputs/ARV1Ep.mid',
                                        'src/audio/res/midiOutputs/ARV1Et.mid']

        for i in range(len(all_premade_filepaths)):
            midi = convertMp3ToMidi(all_premade_filepaths[i], showGraphs)
            with open(all_midi_output_filepaths[i], 'wb') as f:
                midi.writeFile(f)

print("FINISHED")