# two_harmonic_split.py
import numpy as np
import librosa
import soundfile as sf

def hz_to_bin(f, sr, n_fft):
    return f * (n_fft / sr)

def harmonic_summation(mag_col, sr, n_fft, f0_grid, max_partials=12, width_bins=1.5):
    """
    mag_col: magnitude spectrum of shape (F,)
    f0_grid: array of candidate f0 in Hz
    returns salience array same shape as f0_grid
    """
    F = mag_col.shape[0]
    sal = np.zeros_like(f0_grid, dtype=np.float32)
    freqs_per_bin = sr / n_fft
    for i, f0 in enumerate(f0_grid):
        if f0 <= 0:
            continue
        s = 0.0
        for k in range(1, max_partials + 1):
            fk = f0 * k
            b = hz_to_bin(fk, sr, n_fft)
            if b >= F - 1:
                break
            # integrate local neighborhood (triangle window)
            lo = int(max(0, np.floor(b - width_bins)))
            hi = int(min(F - 1, np.ceil(b + width_bins)))
            if hi <= lo:
                continue
            # simple triangular weights around center bin
            idx = np.arange(lo, hi + 1)
            w = 1.0 - (np.abs(idx - b) / (width_bins + 1e-6))
            w = np.clip(w, 0.0, 1.0)
            s += np.sum(w * mag_col[idx])
        sal[i] = s
    return sal

def build_comb_mask(freqs, T, f0_track, sr, max_partials=12, bw_rel=0.03, bw_min=20.0):
    """
    Build (F,T) mask as sum of Gaussians at partials of f0_track
    """
    F = len(freqs)
    mask = np.zeros((F, T), dtype=np.float32)
    for t in range(T):
        f0 = f0_track[t]
        if not np.isfinite(f0) or f0 <= 0:
            continue
        k = 1
        while k <= max_partials:
            fk = f0 * k
            if fk >= sr / 2:
                break
            bw = max(bw_min, bw_rel * fk)
            # Gaussian along frequency
            g = np.exp(-0.5 * ((freqs - fk) / (bw + 1e-12)) ** 2)
            mask[:, t] += g.astype(np.float32)
            k += 1
    # normalize per frame to [0,1]
    denom = mask.max(axis=0, keepdims=True) + 1e-8
    mask = mask / denom
    return mask

def smooth_track(track_hz, win=5):
    if win <= 1:
        return track_hz
    out = track_hz.copy()
    half = win // 2
    for t in range(len(track_hz)):
        lo = max(0, t - half)
        hi = min(len(track_hz), t + half + 1)
        # median is robust against occasional swaps
        out[t] = np.median(track_hz[lo:hi])
    return out

def separate_two_harmonic_sources(
    wav_path,
    out_a="source_A.wav",
    out_b="source_B.wav",
    n_fft=4096,
    hop=512,
    fmin=80.0,       # covers trumpet/piano lower bounds
    fmax=2000.0,     # upper bound for bright synth trumpet
    f0_step=2.0,     # Hz step for the f0 grid (trade accuracy/speed)
    max_partials=14,
    partial_width_bins=1.5,
    min_semitone_sep=1.0,  # ensure two distinct f0s per frame
    track_smooth=7,        # median smoothing frames
    comb_bw_rel=0.03,      # ~3% of freq
    comb_bw_min=20.0,
    blend_soft=0.25        # blend with raw magnitude for stability
):
    y, sr = librosa.load(wav_path, sr=None, mono=True)
    D = librosa.stft(y, n_fft=n_fft, hop_length=hop, window="hann")
    mag = np.abs(D)
    phase = np.angle(D)
    F, T = mag.shape
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    # f0 grid
    f0_grid = np.arange(fmin, fmax + f0_step, f0_step)
    # semitone conversion helper
    def hz_to_semitone(f): return 12.0 * np.log2(np.maximum(f, 1e-6) / 440.0)

    f0A = np.full(T, np.nan, dtype=np.float32)
    f0B = np.full(T, np.nan, dtype=np.float32)

    # 1) Frame-wise peak picking of top-2 f0s using harmonic summation
    for t in range(T):
        sal = harmonic_summation(
            mag[:, t].astype(np.float32), sr, n_fft, f0_grid,
            max_partials=max_partials, width_bins=partial_width_bins
        )
        if np.all(sal <= 0):
            continue
        # take best candidate
        i1 = int(np.argmax(sal))
        f1 = f0_grid[i1]
        # mask out +/- semitone neighborhood to find a distinct second peak
        st1 = hz_to_semitone(f1)
        st_grid = hz_to_semitone(f0_grid)
        mask_sep = np.abs(st_grid - st1) >= min_semitone_sep
        sal2 = sal.copy()
        sal2[~mask_sep] = -np.inf
        i2 = int(np.argmax(sal2))
        f2 = f0_grid[i2] if np.isfinite(sal2[i2]) and sal2[i2] > 0 else np.nan

        # ensure ordering is stable: let A be the LOWER f0 this frame
        fa, fb = (f1, f2) if (np.isnan(f2) or f1 <= f2) else (f2, f1)
        f0A[t] = fa
        f0B[t] = fb

    # 2) Temporal smoothing so IDs don’t swap constantly
    f0A = smooth_track(f0A, win=track_smooth)
    f0B = smooth_track(f0B, win=track_smooth)

    # If tracks cross often, softly re-assign so A is globally lower
    # (optional heuristic)
    if np.nanmedian(f0A) > np.nanmedian(f0B):
        f0A, f0B = f0B, f0A

    # 3) Build comb masks from the smoothed tracks
    maskA = build_comb_mask(freqs, T, f0A, sr,
                            max_partials=max_partials, bw_rel=comb_bw_rel, bw_min=comb_bw_min)
    maskB = build_comb_mask(freqs, T, f0B, sr,
                            max_partials=max_partials, bw_rel=comb_bw_rel, bw_min=comb_bw_min)

    # 4) Normalize and make them complementary where both exist
    eps = 1e-10
    S = maskA + maskB + eps
    maskA = maskA / S
    maskB = maskB / S

    # 5) Stability blend (optional): favor bins with strong magnitude
    # (prevents “phantom” activations during silence)
    mag_norm = (mag / (mag.max(axis=0, keepdims=True) + eps))
    maskA = (1 - blend_soft) * maskA + blend_soft * (maskA * mag_norm)
    maskB = (1 - blend_soft) * maskB + blend_soft * (maskB * mag_norm)

    # 6) Apply masks and reconstruct
    DA = (mag * maskA) * np.exp(1j * phase)
    DB = (mag * maskB) * np.exp(1j * phase)

    yA = librosa.istft(DA, hop_length=hop, window="hann")
    yB = librosa.istft(DB, hop_length=hop, window="hann")

    sf.write(out_a, yA, sr)
    sf.write(out_b, yB, sr)
    return out_a, out_b

if __name__ == "__main__":
    import sys
    if len(sys.argv) < 2:
        print("Usage: python two_harmonic_split.py <mix.wav> [piano.wav] [trumpet.wav]")
        sys.exit(1)
    in_wav = sys.argv[1]
    out_a = sys.argv[2] if len(sys.argv) >= 3 else "stem_A.wav"
    out_b = sys.argv[3] if len(sys.argv) >= 4 else "stem_B.wav"
    print(separate_two_harmonic_sources(in_wav, out_a, out_b))
