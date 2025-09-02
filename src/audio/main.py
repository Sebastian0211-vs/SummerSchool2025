import time
from mp3_to_midi_converter import convertMp3ToMidi
from claudeAiComparisonAlgo import compare_midi_files

#filename  =  'src/audio/res/samples/premade/PinkPanther_Piano_Only.mp3'
#fileout   =  'src/audio/res/midiOutputs/test.mid'
#filename  =  'src/audio/res/samples/sons finax/Gamme_Piano.mp3'
#fileout   =  'src/audio/res/midiOutputs/GammePiano.mid'

trumpetFileName = 'src/audio/res/samples/sons finax/Gamme_Trumpet.mp3'
pianoFileName = 'src/audio/res/samples/sons finax/Gamme_Piano.mp3'
fileout = 'src/audio/res/midiOutputs/midi.mid'

chooseYourChallenger = 666
showGraphs = False

match chooseYourChallenger:

    case 666:
        midi = convertMp3ToMidi(trumpetFileName, pianoFileName)
        with open(fileout, 'wb') as f:
            midi.writeFile(f)
        '''
    # Produce midi files
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
    case 3:
        all_final_premade_filepaths     =    ['src/audio/res/samples/sons finax/Gamme_Piano.mp3',
                                        'src/audio/res/samples/sons finax/Gamme_Trumpet.mp3',
                                        'src/audio/res/samples/sons finax/SSB_Piano.mp3',
                                        'src/audio/res/samples/sons finax/SSB_Trumpet.mp3',
                                        'src/audio/res/samples/sons finax/SuperMario_Piano.mp3',
                                        'src/audio/res/samples/sons finax/SuperMario_Trumpet.mp3']
        all_final_midi_output_filepaths =    ['src/audio/res/midiOutputs/GammePiano.mid',
                                        'src/audio/res/midiOutputs/GammeTrumpet.mid',
                                        'src/audio/res/midiOutputs/SSBPiano.mid',
                                        'src/audio/res/midiOutputs/SSBTrumpet.mid',
                                        'src/audio/res/midiOutputs/SuperMarioPiano.mid',
                                        'src/audio/res/midiOutputs/SuperMarioTrumpet.mid']

        for i in range(len(all_final_premade_filepaths)):
            midi = convertMp3ToMidi(all_final_premade_filepaths[i], showGraphs)
            with open(all_final_midi_output_filepaths[i], 'wb') as f:
                midi.writeFile(f)
    case 4:
        all_final_premade_filepaths     =    ['src/audio/res/samples/sons finax/Gamme_Piano.mp3',
                                        'src/audio/res/samples/sons finax/Gamme_Trumpet.mp3']
        all_final_midi_output_filepaths =    ['src/audio/res/midiOutputs/GammePiano.mid',
                                        'src/audio/res/midiOutputs/GammeTrumpet.mid',
                                        'src/audio/res/midiOutputs/SSBPiano.mid']

        for i in range(len(all_final_premade_filepaths)):
            midi = convertMp3ToMidi(all_final_premade_filepaths[i], showGraphs)
            with open(all_final_midi_output_filepaths[i], 'wb') as f:
                midi.writeFile(f)
    case 5:
        all_final_premade_filepaths     =    ['src/audio/res/samples/sons finax/SSB_Piano.mp3',
                                        'src/audio/res/samples/sons finax/SSB_Trumpet.mp3']
        all_final_midi_output_filepaths =    ['src/audio/res/midiOutputs/SSBPiano.mid',
                                        'src/audio/res/midiOutputs/SSBTrumpet.mid']

        for i in range(len(all_final_premade_filepaths)):
            midi = convertMp3ToMidi(all_final_premade_filepaths[i], showGraphs)
            with open(all_final_midi_output_filepaths[i], 'wb') as f:
                midi.writeFile(f)
    case 6:
        all_final_premade_filepaths     =    ['src/audio/res/samples/sons finax/SuperMario_Piano.mp3',
                                        'src/audio/res/samples/sons finax/SuperMario_Trumpet.mp3']
        all_final_midi_output_filepaths =    ['src/audio/res/midiOutputs/SuperMarioPiano.mid',
                                        'src/audio/res/midiOutputs/SuperMarioTrumpet.mid']

        for i in range(len(all_final_premade_filepaths)):
            midi = convertMp3ToMidi(all_final_premade_filepaths[i], showGraphs)
            with open(all_final_midi_output_filepaths[i], 'wb') as f:
                midi.writeFile(f)



    # Produce results
    case 101:
        #Results = compare_midi_files('src/audio/res/samples/midi files to compare/PinkPantherPiano.mid', 'src/audio/res/midiOutputs/versions/Revamped/R2/ARV1PPp.mid')
        resultsGammePiano = compare_midi_files('src/audio/res/samples/midi files to compare/GammePiano.mid', 'src/audio/res/midiOutputs/GammePiano.mid')
        resultsGammeTrumpet = compare_midi_files('src/audio/res/samples/midi files to compare/GammeTrumpet.mid', 'src/audio/res/midiOutputs/GammeTrumpet.mid')
        resultsSSBPiano = compare_midi_files('src/audio/res/samples/midi files to compare/SSBPiano.mid', 'src/audio/res/midiOutputs/SSBPiano.mid')
        resultsSSBTrumpet = compare_midi_files('src/audio/res/samples/midi files to compare/SSBTrumpet.mid', 'src/audio/res/midiOutputs/SSBTrumpet.mid')
        resultsSuperMarioPiano = compare_midi_files('src/audio/res/samples/midi files to compare/SuperMarioPiano.mid', 'src/audio/res/midiOutputs/SuperMarioPiano.mid')
        resultsSuperMarioTrumpet = compare_midi_files('src/audio/res/samples/midi files to compare/SuperMarioTrumpet.mid', 'src/audio/res/midiOutputs/SuperMarioTrumpet.mid')
    case 102:
        resultGamme = compare_midi_files('src/audio/res/samples/midi files to compare/Gamme.mid', 'src/audio/res/midiOutputs/Gamme.mid')
        resultsSSB = compare_midi_files('src/audio/res/samples/midi files to compare/SSB.mid', 'src/audio/res/midiOutputs/SSB.mid')
        resultsSuperMario = compare_midi_files('src/audio/res/samples/midi files to compare/SuperMario.mid', 'src/audio/res/midiOutputs/SuperMario.mid')
                '''
    

print("FINISHED")