# -*- coding: utf-8 -*-

import numpy as np
import librosa
import librosa.feature.rhythm
import midiutil
import math
import matplotlib.pyplot as plt

# Only old utilized function with the polyphonic version
def pianoroll_to_midi(bpm: float, pianoroll: list) -> midiutil.MIDIFile():
    """
    Writes the contents of a pianoroll into a midi file.
    Uses midiutil for writing.

    Parameters
    ----------
    bpm: float

    pianoroll : list
        A pianoroll list as estimated by states_to_pianoroll().

    Returns
    -------
    None.

    """
    quarter_note = 60 / bpm

    onsets = np.array([p[0] for p in pianoroll])
    offsets = np.array([p[1] for p in pianoroll])

    onsets = onsets / quarter_note
    offsets = offsets / quarter_note
    durations = offsets - onsets

    midi = midiutil.MIDIFile(1)
    midi.addTempo(0, 0, bpm)

    for i, _ in enumerate(onsets):
        midi.addNote(
            0, 0, int(pianoroll[i][2]), onsets[i], durations[i], 100)

    return midi

#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#
#                                          Polyphonic update
#
#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#///////////////////////////////////////////////////////////////////////////////////////////////////////////
#I'm trying to combine ypin with chroma like I said to try and get chords through librosa's cqt functions
#////////HERE : ////////////////////////////////////////////////////////////////////////////////////////////

def prior_probabilities_hybrid(
        audio_signal: np.array,
        note_min: str,
        note_max: str,
        srate: int,
        frame_length: int,
        hop_length: int,
        pitch_acc: float,
        voiced_acc: float,
        onset_acc: float,
        spread: float,
        alpha: float) -> np.array:
    """
    Estimate prior probabilities by combining pyin (monophonic) and CQT (polyphonic).
    """
    fmin = librosa.note_to_hz(note_min)
    fmax = librosa.note_to_hz(note_max)
    midi_min = librosa.note_to_midi(note_min)
    midi_max = librosa.note_to_midi(note_max)
    n_notes = midi_max - midi_min + 1

    # ===== 1. PYIN =====
    pitch, voiced_flag, _ = librosa.pyin(
        y=audio_signal, fmin=fmin * 0.9, fmax=fmax * 1.1,
        sr=srate, frame_length=frame_length, win_length=int(frame_length / 2),
        hop_length=hop_length)
    tuning = librosa.pitch_tuning(pitch)
    f0_ = np.round(librosa.hz_to_midi(pitch - tuning)).astype(int)

    onsets = librosa.onset.onset_detect(
        y=audio_signal, sr=srate,
        hop_length=hop_length, backtrack=True)

    priors_pyin = np.ones((n_notes * 2 + 1, len(pitch)))
    for n_frame in range(len(pitch)):
        if not voiced_flag[n_frame]:
            priors_pyin[0, n_frame] = voiced_acc
        else:
            priors_pyin[0, n_frame] = 1 - voiced_acc
        for j in range(n_notes):
            if n_frame in onsets:
                priors_pyin[(j * 2) + 1, n_frame] = onset_acc
            else:
                priors_pyin[(j * 2) + 1, n_frame] = 1 - onset_acc
            if j + midi_min == f0_[n_frame]:
                priors_pyin[(j * 2) + 2, n_frame] = pitch_acc
            elif np.abs(j + midi_min - f0_[n_frame]) == 1:
                priors_pyin[(j * 2) + 2, n_frame] = pitch_acc * spread
            else:
                priors_pyin[(j * 2) + 2, n_frame] = 1 - pitch_acc

    # ===== 2. CQT =====
    cqt = librosa.cqt(
        y=audio_signal, sr=srate, hop_length=hop_length,
        fmin=librosa.note_to_hz(note_min),
        n_bins=n_notes,
        bins_per_octave=12)
    
    cqt_mag = np.abs(cqt)
    priors_cqt = cqt_mag / (np.sum(cqt_mag, axis=0, keepdims=True) + 1e-6)

    priors_cqt_full = np.ones_like(priors_pyin)
    for j in range(n_notes):
        priors_cqt_full[(j * 2) + 1, :] = priors_cqt[j, :]
        priors_cqt_full[(j * 2) + 2, :] = priors_cqt[j, :]
    priors_cqt_full[0, :] = 1 - np.max(priors_cqt, axis=0)

    # ===== 3. Fuse =====
    priors = alpha * priors_cqt_full + (1 - alpha) * priors_pyin

    return priors



def priors_to_pianoroll(priors: np.ndarray, note_min: str, hop_time: float, threshold: float = 0.3):
    """
    Convert priors into polyphonic piano roll by thresholding each note independently.
    """
    midi_min = librosa.note_to_midi(note_min)
    n_states, n_frames = priors.shape
    n_notes = (n_states - 1) // 2

    output = []
    active_notes = {}

    for t in range(n_frames):
        active_now = []
        for j in range(n_notes):
            sustain_prob = priors[(j * 2) + 2, t]
            if sustain_prob > threshold:
                midi_note = j + midi_min
                active_now.append(midi_note)
                if midi_note not in active_notes:
                    active_notes[midi_note] = t * hop_time

        ended = [m for m in list(active_notes.keys()) if m not in active_now]
        for midi_note in ended:
            onset_time = active_notes[midi_note]
            offset_time = t * hop_time
            note_name = librosa.midi_to_note(midi_note)
            output.append([onset_time, offset_time, midi_note, note_name])
            del active_notes[midi_note]

    for midi_note, onset_time in active_notes.items():
        offset_time = n_frames * hop_time
        note_name = librosa.midi_to_note(midi_note)
        output.append([onset_time, offset_time, midi_note, note_name])

    return output


# Matplotlib graphs ALL GENERATED BY CHATGPT
def plot_priors(priors, note_min="A2", hop_time=0.01, title="Note Probabilities"):
    """
    Plot priors (probabilities per note per frame) as a heatmap.
    
    priors = np.ndarray of shape (2*n_notes+1, n_frames)
             from prior_probabilities_hybrid()
    """
    import matplotlib.pyplot as plt

    n_states, n_frames = priors.shape
    n_notes = (n_states - 1) // 2
    midi_min = librosa.note_to_midi(note_min)
    
    # We only keep sustain states (not onset/silence)
    sustain_priors = priors[2::2, :]  # every 2nd row starting at 2
    times = np.arange(n_frames) * hop_time
    midi_notes = np.arange(midi_min, midi_min + n_notes)

    plt.figure(figsize=(14, 6))
    plt.imshow(
        sustain_priors,
        aspect="auto",
        origin="lower",
        extent=[times[0], times[-1], midi_notes[0], midi_notes[-1]],
        cmap="magma"
    )
    plt.colorbar(label="Probability")
    plt.ylabel("MIDI note")
    plt.xlabel("Time (s)")
    plt.title(title)

    # Put note labels on y-axis
    yticks = midi_notes[::max(1, len(midi_notes)//20)]  # avoid too many labels
    plt.yticks(yticks, [librosa.midi_to_note(m) for m in yticks])

    plt.show()
def plot_pianoroll(pianoroll, note_min="A2", title="Detected Notes"):
    """
    Plot the detected pianoroll from priors_to_pianoroll().
    
    pianoroll = list of [onset_time, offset_time, midi_note, note_name]
    """
    fig, ax = plt.subplots(figsize=(12, 6))

    for onset, offset, midi_note, note_name in pianoroll:
        ax.plot([onset, offset], [midi_note, midi_note],
                linewidth=6, solid_capstyle="butt")

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("MIDI Note")
    ax.set_title(title)

    # Y-axis as note names
    all_notes = sorted(set([p[2] for p in pianoroll]))
    ax.set_yticks(all_notes)
    ax.set_yticklabels([librosa.midi_to_note(n) for n in all_notes])

    ax.grid(True, which="both", axis="x", linestyle="--", alpha=0.5)

    plt.show()


# Acts as the main of the code aswell as stores the CONSTANTS
def wave_to_midi_poly(
        audio_signal: np.array,
        srate: int = 44100,
        frame_length: int = 2048,   # good settings 1024
        hop_length: int = 512,      # good settings 128
        note_min: str = "A2",
        note_max: str = "B7",       # was E5
        pitch_acc: float = 0.9,     # was 0.9
        voiced_acc: float = 0.9,    # was 0.9
        onset_acc: float = 0.9,     # was 0.9
        spread: float = 0.2,
        alpha: float = 0.7,         # was 0.7
        threshold: float = 0.3) -> midiutil.MIDIFile: # Threshold was 0.3
    """
    Converts an audio signal to a polyphonic MIDI file using hybrid priors (pyin + CQT).
    """

    priors = prior_probabilities_hybrid(
        audio_signal,
        note_min,
        note_max,
        srate,
        frame_length,
        hop_length,
        pitch_acc,
        voiced_acc,
        onset_acc,
        spread,
        alpha
    )

    hop_time = hop_length / srate
    pianoroll = priors_to_pianoroll(priors, note_min, hop_time, threshold)

    plot_priors(priors, "A2", hop_time)     # detected notes graph plotting
    plot_pianoroll(pianoroll, "A2")         # midi pianoroll graph plotting
    
    bpm = librosa.feature.rhythm.tempo(y=audio_signal, sr=srate)
    midi = pianoroll_to_midi(bpm, pianoroll)

    return midi
