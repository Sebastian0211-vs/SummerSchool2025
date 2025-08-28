# -*- coding: utf-8 -*-

import numpy as np
import librosa
import librosa.feature.rhythm
import midiutil
import math
import matplotlib.pyplot as plt
from scipy.ndimage import uniform_filter1d

def pianoroll_to_midi(bpm: float, pianoroll: list) -> midiutil.MIDIFile():
    """
    Writes the contents of a pianoroll into a midi file.
    Uses midiutil for writing.
    """
    if isinstance(bpm, np.ndarray):
        bpm = float(bpm[0])
    
    quarter_note = 60 / bpm

    onsets = np.array([p[0] for p in pianoroll])
    offsets = np.array([p[1] for p in pianoroll])

    onsets = onsets / quarter_note
    offsets = offsets / quarter_note
    durations = offsets - onsets

    midi = midiutil.MIDIFile(1)
    midi.addTempo(0, 0, bpm)

    for i, _ in enumerate(onsets):
        # Add minimum duration to prevent stuttering
        duration = max(durations[i], 0.1)
        midi.addNote(
            0, 0, int(pianoroll[i][2]), onsets[i], duration, 100)

    return midi

def smooth_priors(priors: np.ndarray, window_size: int = 5) -> np.ndarray:
    """
    Smoothing function aka temporal smoothing to reduce the stutter in the midi file.
    """
    smoothed = np.copy(priors)
    for i in range(priors.shape[0]):
        smoothed[i, :] = uniform_filter1d(priors[i, :], size=window_size, mode='constant')
    return smoothed

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

    # ===== 1. PYIN with better parameters =====
    pitch, voiced_flag, _ = librosa.pyin(
        y=audio_signal, 
        fmin=fmin * 0.9, 
        fmax=fmax * 1.1,
        sr=srate, 
        frame_length=frame_length, 
        win_length=frame_length // 4,  # Smaller window for better time resolution
        hop_length=hop_length,
        pad_mode='constant')
    
    # Improved tuning estimation
    tuning = librosa.pitch_tuning(pitch)
    f0_ = np.round(librosa.hz_to_midi(pitch - tuning)).astype(int)

    # Better onset detection with lower sensitivity
    onsets = librosa.onset.onset_detect(
        y=audio_signal, 
        sr=srate,
        hop_length=hop_length, 
        backtrack=True,
        delta=0.2,  # Higher threshold for onset detection
        wait=5)     # Minimum frames between onsets

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

    # ===== 2. Improved CQT for better chord detection =====
    cqt = librosa.cqt(
        y=audio_signal, 
        sr=srate, 
        hop_length=hop_length,
        fmin=librosa.note_to_hz(note_min),
        n_bins=n_notes,
        bins_per_octave=12,
        window='hann')  # Better window function
    
    cqt_mag = np.abs(cqt)
    
    # Apply harmonic filtering to reduce overtones
    # This helps with chord detection by reducing harmonic confusion
    cqt_filtered = np.copy(cqt_mag)
    for i in range(n_notes):
        # Suppress harmonics (octaves and fifths)
        if i + 12 < n_notes:  # Octave
            cqt_filtered[i, :] = np.maximum(0, cqt_mag[i, :] - 0.3 * cqt_mag[i + 12, :])
        if i + 7 < n_notes:   # Fifth
            cqt_filtered[i, :] = np.maximum(0, cqt_filtered[i, :] - 0.2 * cqt_mag[i + 7, :])
    
    # Normalize with better stability
    priors_cqt = cqt_filtered / (np.sum(cqt_filtered, axis=0, keepdims=True) + 1e-3)
    
    # Apply logarithmic scaling to compress dynamic range
    priors_cqt = np.log1p(priors_cqt * 10) / np.log1p(10)

    priors_cqt_full = np.ones_like(priors_pyin)
    for j in range(n_notes):
        priors_cqt_full[(j * 2) + 1, :] = priors_cqt[j, :]
        priors_cqt_full[(j * 2) + 2, :] = priors_cqt[j, :]
    priors_cqt_full[0, :] = 1 - np.max(priors_cqt, axis=0)

    # ===== 3. Fuse with smoothing =====
    priors = alpha * priors_cqt_full + (1 - alpha) * priors_pyin
    
    # Apply temporal smoothing to reduce jitter
    priors = smooth_priors(priors, window_size=3)
    
    return priors

def priors_to_pianoroll(priors: np.ndarray, note_min: str, hop_time: float, threshold: float = 0.5):
    """
    Convert priors into polyphonic piano roll with improved note handling.
    """
    midi_min = librosa.note_to_midi(note_min)
    n_states, n_frames = priors.shape
    n_notes = (n_states - 1) // 2

    output = []
    active_notes = {}
    
    # Minimum note duration to prevent stuttering (in frames)
    min_duration_frames = max(3, int(0.1 / hop_time))

    for t in range(n_frames):
        active_now = []
        for j in range(n_notes):
            sustain_prob = priors[(j * 2) + 2, t]
            
            # Use adaptive threshold based on frame energy
            frame_energy = np.sum(priors[2::2, t])
            adaptive_threshold = threshold * (1 + 0.2 * (1 - frame_energy))
            
            if sustain_prob > adaptive_threshold:
                midi_note = j + midi_min
                active_now.append(midi_note)
                if midi_note not in active_notes:
                    active_notes[midi_note] = t * hop_time

        # Only end notes that have been active for minimum duration
        ended = []
        for midi_note in list(active_notes.keys()):
            if midi_note not in active_now:
                duration_frames = t - (active_notes[midi_note] / hop_time)
                if duration_frames >= min_duration_frames:
                    ended.append(midi_note)
        
        for midi_note in ended:
            onset_time = active_notes[midi_note]
            offset_time = t * hop_time
            note_name = librosa.midi_to_note(midi_note)
            output.append([onset_time, offset_time, midi_note, note_name])
            del active_notes[midi_note]

    # Handle remaining active notes
    for midi_note, onset_time in active_notes.items():
        offset_time = n_frames * hop_time
        duration_frames = n_frames - (onset_time / hop_time)
        if duration_frames >= min_duration_frames:
            note_name = librosa.midi_to_note(midi_note)
            output.append([onset_time, offset_time, midi_note, note_name])

    return output

def plot_priors(priors, note_min="A2", hop_time=0.01, title="Note Probabilities"):
    """Plot priors with improved visualization."""
    n_states, n_frames = priors.shape
    n_notes = (n_states - 1) // 2
    midi_min = librosa.note_to_midi(note_min)
    
    sustain_priors = priors[2::2, :]
    times = np.arange(n_frames) * hop_time
    midi_notes = np.arange(midi_min, midi_min + n_notes)

    plt.figure(figsize=(14, 6))
    plt.imshow(
        sustain_priors,
        aspect="auto",
        origin="lower",
        extent=[times[0], times[-1], midi_notes[0], midi_notes[-1]],
        cmap="magma",
        vmin=0, vmax=1
    )
    plt.colorbar(label="Probability")
    plt.ylabel("MIDI note")
    plt.xlabel("Time (s)")
    plt.title(title)

    yticks = midi_notes[::max(1, len(midi_notes)//20)]
    plt.yticks(yticks, [librosa.midi_to_note(m) for m in yticks])
    plt.tight_layout()
    plt.show()
def plot_pianoroll(pianoroll, note_min="A2", title="Detected Notes"):
    """Plot pianoroll with color coding for different notes."""
    if not pianoroll:
        print("No notes detected in pianoroll")
        return
        
    fig, ax = plt.subplots(figsize=(12, 6))
    
    colors = plt.cm.tab10(np.linspace(0, 1, 10))
    
    for i, (onset, offset, midi_note, note_name) in enumerate(pianoroll):
        color = colors[i % len(colors)]
        ax.plot([onset, offset], [midi_note, midi_note],
                linewidth=6, solid_capstyle="butt", color=color)

    ax.set_xlabel("Time (s)")
    ax.set_ylabel("MIDI Note")
    ax.set_title(title)

    all_notes = sorted(set([p[2] for p in pianoroll]))
    if all_notes:
        ax.set_yticks(all_notes)
        ax.set_yticklabels([librosa.midi_to_note(n) for n in all_notes])

    ax.grid(True, which="both", axis="x", linestyle="--", alpha=0.5)
    plt.tight_layout()
    plt.show()

def wave_to_midi_poly(
        audio_signal: np.array,
        srate: int = 44100,
        frame_length: int = 1024,      # Reduced for better time resolution
        hop_length: int = 256,         # Reduced for better time resolution
        note_min: str = "A2",
        note_max: str = "B7",
        pitch_acc: float = 0.9,
        voiced_acc: float = 0.9,
        onset_acc: float = 0.9,        # Much lower to prevent stuttering
        spread: float = 0.2,
        alpha: float = 0.6,            # Favor CQT slightly for chord detection
        threshold: float = 0.9) -> midiutil.MIDIFile:  # Higher threshold
    """
    Converts an audio signal to a polyphonic MIDI file with improved stability.
    """
    
    # Preprocess audio: normalize and apply gentle filtering
    audio_signal = librosa.util.normalize(audio_signal)
    
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
    
    plot_priors(priors, note_min, hop_time)
    plot_pianoroll(pianoroll, note_min)
    
    # Improved BPM detection
    tempo = librosa.feature.rhythm.tempo(
        y=audio_signal, 
        sr=srate,
        hop_length=hop_length,
        start_bpm=60,
        std_bpm=20)[0]  # Extract scalar value
    
    midi = pianoroll_to_midi(tempo, pianoroll)
    
    print("New bpm apparently : ", tempo)

    return midi