import numpy as np
import librosa
import midiutil
import matplotlib.pyplot as plt
from librosa.feature.rhythm import tempo

def audio_to_midi_polyphonic(
    audio_signal: np.ndarray,
    srate: int = 44100,
    hop_length: int = 512,
    note_min: str = "A2",
    note_max: str = "B7",
    cqt_threshold: float = 0.6,
    min_note_duration: float = 0.15
) -> midiutil.MIDIFile:
    """
    Converts audio to polyphonic midi using librosa.cqt
    """
    # Calculates note range
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    n_notes = midi_max - midi_min + 1
    
    cqt = librosa.cqt(
        y=audio_signal, 
        sr=srate, 
        hop_length=hop_length,
        fmin=librosa.note_to_hz(note_min),
        n_bins=n_notes,
        bins_per_octave=12
    )
    
    # Converts the notes to magnitude and normalizes
    cqt_mag = np.abs(cqt)
    cqt_norm = cqt_mag / (np.max(cqt_mag, axis=0, keepdims=True) + 1e-8)
    
    # Converts to a pianoroll
    hop_time = hop_length / srate
    pianoroll = cqt_to_pianoroll(cqt_norm, midi_min, hop_time, cqt_threshold, min_note_duration)
    
    # Creates the midi file
    bpm = float(librosa.feature.rhythm.tempo(y=audio_signal, sr=srate)[0])
    midi_file = create_midi_file(pianoroll, bpm)
    
    return midi_file


def cqt_to_pianoroll(cqt_norm: np.ndarray, midi_min: int, hop_time: float, 
                     threshold: float, min_duration: float) -> list:
    """
    Converts normalized CQT to a pianoroll
    """
    n_notes, n_frames = cqt_norm.shape
    pianoroll = []
    active_notes = {}
    
    for frame in range(n_frames):
        current_time = frame * hop_time
        
        # Check which notes are active in this frame
        active_in_frame = set()
        for note_idx in range(n_notes):
            if cqt_norm[note_idx, frame] > threshold:
                midi_note = note_idx + midi_min
                active_in_frame.add(midi_note)
                
                # Start new note if not already active
                if midi_note not in active_notes:
                    active_notes[midi_note] = current_time
        
        # End notes that are no longer active
        ended_notes = set(active_notes.keys()) - active_in_frame
        for midi_note in ended_notes:
            onset_time = active_notes[midi_note]
            duration = current_time - onset_time
            
            # Only add notes that meet minimum duration
            if duration >= min_duration:
                pianoroll.append([onset_time, current_time, midi_note])
            
            del active_notes[midi_note]
    
    # Close remaining active notes
    final_time = n_frames * hop_time
    for midi_note, onset_time in active_notes.items():
        duration = final_time - onset_time
        if duration >= min_duration:
            pianoroll.append([onset_time, final_time, midi_note])
    
    return pianoroll


def create_midi_file(pianoroll: list, bpm: float) -> midiutil.MIDIFile:
    """
    Creates midi file from pianoroll
    """
    # Perchance they gonna give as an empty mp3 ??
    if not pianoroll:
        # Return empty MIDI file if no notes detected
        midi = midiutil.MIDIFile(1)
        midi.addTempo(0, 0, bpm)
        return midi
    
    # Convert times to MIDI beats
    beat_duration = 60.0 / bpm
    
    midi = midiutil.MIDIFile(1)
    midi.addTempo(0, 0, bpm)
    
    for onset_time, offset_time, midi_note in pianoroll:
        onset_beats = onset_time / beat_duration
        duration_beats = (offset_time - onset_time) / beat_duration
        
        midi.addNote(
            track=0,
            channel=0,
            pitch=int(midi_note),
            time=onset_beats,
            duration=duration_beats,
            volume=100
        )
    
    return midi


# PLOTS ALL AI GENERATED
def plot_analysis(audio_signal: np.ndarray, pianoroll: list, srate: int = 44100, 
                 hop_length: int = 512, note_min: str = "A2"):
    """
    Plot the analysis results: CQT spectrogram and detected notes.
    """
    # Compute CQT for visualization
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi("B7")  # Assuming same range
    n_notes = midi_max - midi_min + 1
    
    cqt = librosa.cqt(
        y=audio_signal,
        sr=srate,
        hop_length=hop_length,
        fmin=librosa.note_to_hz(note_min),
        n_bins=n_notes,
        bins_per_octave=12
    )
    
    cqt_db = librosa.amplitude_to_db(np.abs(cqt), ref=np.max)
    
    # Create subplots
    fig, (ax1, ax2) = plt.subplots(2, 1, figsize=(12, 8), sharex=True)
    
    # Plot CQT
    hop_time = hop_length / srate
    times = np.arange(cqt.shape[1]) * hop_time
    
    img = ax1.imshow(
        cqt_db,
        aspect='auto',
        origin='lower',
        extent=[times[0], times[-1], midi_min, midi_min + n_notes],
        cmap='magma'
    )
    ax1.set_ylabel('MIDI Note')
    ax1.set_title('CQT Spectrogram')
    plt.colorbar(img, ax=ax1, label='Magnitude (dB)')
    
    # Plot detected notes
    for onset, offset, midi_note in pianoroll:
        ax2.plot([onset, offset], [midi_note, midi_note], 
                linewidth=4, solid_capstyle='butt', alpha=0.8)
    
    ax2.set_xlabel('Time (s)')
    ax2.set_ylabel('MIDI Note')
    ax2.set_title('Detected Notes')
    ax2.grid(True, alpha=0.3)
    
    # Set y-axis labels to note names
    for ax in [ax1, ax2]:
        if pianoroll:  # Only if we have detected notes
            all_notes = sorted(set([p[2] for p in pianoroll]))
            sample_notes = all_notes[::max(1, len(all_notes)//10)]
            ax.set_yticks(sample_notes)
            ax.set_yticklabels([librosa.midi_to_note(n) for n in sample_notes])
    
    plt.tight_layout()
    plt.show()


def convertMp3ToMidi(filepath: str, plot_results: bool = True) -> midiutil.MIDIFile:
    """
    Main
    """
    audio, sr = librosa.load(filepath, sr=None)
    #audio = librosa.effects.preemphasis(audio)
    
    # Convert to midi
    midi_file = audio_to_midi_polyphonic(audio, sr)
    
    # Plot boolean
    if plot_results:
        # Recreate pianoroll for plotting (could be optimized by returning it)
        midi_min = librosa.note_to_midi("A2")
        midi_max = librosa.note_to_midi("B7")
        n_notes = midi_max - midi_min + 1
        
        cqt = librosa.cqt(
            y=audio, sr=sr, hop_length=512,
            fmin=librosa.note_to_hz("A2"), n_bins=n_notes, bins_per_octave=12
        )
        cqt_norm = np.abs(cqt) / (np.max(np.abs(cqt), axis=0, keepdims=True) + 1e-8)
        pianoroll = cqt_to_pianoroll(cqt_norm, midi_min, 512/sr, 0.3, 0.1)
        
        plot_analysis(audio, pianoroll, sr)
    
    return midi_file