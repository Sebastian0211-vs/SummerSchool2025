from __future__ import annotations
import argparse
import numpy as np
import soundfile as sf
import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from typing import Tuple, Dict, List

# ---------------------------
# Loading / utilities
# ---------------------------

def load_mono(path: str, sr: int) -> np.ndarray:
    y, file_sr = sf.read(path, always_2d=False)
    if y.ndim > 1:
        y = np.mean(y, axis=1)
    if sr is not None and file_sr != sr:
        y = librosa.resample(y, orig_sr=file_sr, target_sr=sr, res_type="kaiser_fast")
    return y.astype(np.float32)

def pad_or_trim(a: np.ndarray, length: int) -> np.ndarray:
    if len(a) < length:
        out = np.zeros(length, dtype=a.dtype)
        out[:len(a)] = a
        return out
    return a[:length]

def find_lag(ref: np.ndarray, est: np.ndarray, max_shift: int = 44100) -> int:
    """Find integer-sample lag aligning est to ref (ref ~ shift(est, lag))."""
    n = min(len(ref), len(est))
    ref = ref[:n]
    est = est[:n]
    # limit search window
    m = min(max_shift, n-1)
    # compute xcorr around 0 lag using FFT via librosa
    xcorr = librosa.core.cross_correlation(est, ref, mode="full")
    center = len(xcorr)//2
    window = xcorr[center-m:center+m+1]
    lag = np.argmax(window) - m
    return int(lag)

def shift_signal(x: np.ndarray, lag: int) -> np.ndarray:
    if lag == 0:
        return x
    if lag > 0:  # est delayed -> shift right (prepend zeros)
        return np.concatenate([np.zeros(lag, dtype=x.dtype), x])[:len(x)]
    else:        # est ahead -> shift left
        lag = -lag
        return np.concatenate([x[lag:], np.zeros(lag, dtype=x.dtype)])[:len(x)]

def gain_match(ref: np.ndarray, est: np.ndarray) -> np.ndarray:
    """Least-squares gain for est to match ref."""
    denom = np.dot(est, est) + 1e-12
    g = float(np.dot(est, ref) / denom)
    return g * est

# ---------------------------
# Metrics
# ---------------------------

def si_sdr(ref: np.ndarray, est: np.ndarray) -> float:
    """Scale-Invariant SDR in dB."""
    ref = ref.astype(np.float64)
    est = est.astype(np.float64)
    alpha = np.dot(est, ref) / (np.dot(ref, ref) + 1e-12)
    e_target = alpha * ref
    e_res = est - e_target
    ratio = (np.dot(e_target, e_target) + 1e-12) / (np.dot(e_res, e_res) + 1e-12)
    return 10.0 * np.log10(ratio)

def spectral_convergence(ref: np.ndarray, est: np.ndarray, sr: int, n_fft=2048, hop=512) -> float:
    """|||S_ref|-|S_est|||_F / ||S_ref||_F  (lower is better)."""
    S_ref = np.abs(librosa.stft(ref, n_fft=n_fft, hop_length=hop, window="hann"))
    S_est = np.abs(librosa.stft(est, n_fft=n_fft, hop_length=hop, window="hann"))
    num = np.linalg.norm(S_ref - S_est, ord="fro")
    den = np.linalg.norm(S_ref, ord="fro") + 1e-12
    return float(num / den)

def logmel_l2(ref: np.ndarray, est: np.ndarray, sr: int, n_mels=128, n_fft=2048, hop=512) -> float:
    M = librosa.filters.mel(sr=sr, n_fft=n_fft, n_mels=n_mels, fmin=20.0, fmax=sr/2)
    S_ref = np.abs(librosa.stft(ref, n_fft=n_fft, hop_length=hop))
    S_est = np.abs(librosa.stft(est, n_fft=n_fft, hop_length=hop))
    mel_ref = np.dot(M, S_ref)
    mel_est = np.dot(M, S_est)
    lref = np.log10(mel_ref + 1e-6)
    lest = np.log10(mel_est + 1e-6)
    return float(np.mean((lref - lest) ** 2))

def magspec_l1(ref: np.ndarray, est: np.ndarray, sr: int, n_fft=2048, hop=512) -> float:
    S_ref = np.abs(librosa.stft(ref, n_fft=n_fft, hop_length=hop))
    S_est = np.abs(librosa.stft(est, n_fft=n_fft, hop_length=hop))
    return float(np.mean(np.abs(S_ref - S_est)))

# ---------------------------
# Permutation-invariant evaluation
# ---------------------------

def align_and_score(ref: np.ndarray, est: np.ndarray, sr: int) -> Dict[str, float]:
    # time-align
    lag = find_lag(ref, est, max_shift=int(0.5 * sr))  # search up to 0.5s
    est_a = shift_signal(est, lag)
    # trim to common length
    L = min(len(ref), len(est_a))
    ref = ref[:L]
    est_a = est_a[:L]
    # SI gain-match
    est_g = gain_match(ref, est_a)

    return {
        "lag_samples": float(lag),
        "SI-SDR(dB)": si_sdr(ref, est_g),
        "SpecConv": spectral_convergence(ref, est_g, sr),
        "LogMelL2": logmel_l2(ref, est_g, sr),
        "MagSpecL1": magspec_l1(ref, est_g, sr),
    }

def mean_sisdr(scores_a: Dict[str, float], scores_b: Dict[str, float]) -> float:
    return 0.5 * (scores_a["SI-SDR(dB)"] + scores_b["SI-SDR(dB)"])

def pretty_table(rows: List[Dict[str, float]], names: List[str]) -> str:
    headers = ["Stem", "SI-SDR(dB)", "SpecConv", "LogMelL2", "MagSpecL1", "Lag(samples)"]
    lines = [" | ".join(headers), "-" * 72]
    for name, sc in zip(names, rows):
        lines.append(
            f"{name:>6} | {sc['SI-SDR(dB)']:>10.2f} | {sc['SpecConv']:>8.4f} | {sc['LogMelL2']:>9.5f} | {sc['MagSpecL1']:>10.5f} | {int(sc['lag_samples']):>11d}"
        )
    return "\n".join(lines)

# ---------------------------
# Optional plots
# ---------------------------

def save_spec_compare(path: str, ref: np.ndarray, est: np.ndarray, sr: int, title: str):
    n_fft, hop = 2048, 512
    S_ref = librosa.amplitude_to_db(np.abs(librosa.stft(ref, n_fft=n_fft, hop_length=hop)) + 1e-9, ref=np.max)
    S_est = librosa.amplitude_to_db(np.abs(librosa.stft(est, n_fft=n_fft, hop_length=hop)) + 1e-9, ref=np.max)
    fig = plt.figure(figsize=(10, 6))
    ax1 = plt.subplot(2, 1, 1)
    librosa.display.specshow(S_ref, sr=sr, hop_length=hop, x_axis="time", y_axis="hz", ax=ax1)
    ax1.set_title(f"Reference — {title}")
    ax2 = plt.subplot(2, 1, 2)
    librosa.display.specshow(S_est, sr=sr, hop_length=hop, x_axis="time", y_axis="hz", ax=ax2)
    ax2.set_title(f"Estimate (aligned/gain-matched) — {title}")
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close(fig)

# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Evaluate separation quality against reference stems.")
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--ref-piano", required=True)
    ap.add_argument("--ref-trumpet", required=True)
    ap.add_argument("--est-piano", required=True)
    ap.add_argument("--est-trumpet", required=True)
    ap.add_argument("--plots-dir", default=None, help="If set, saves spectrogram comparisons.")
    args = ap.parse_args()

    # Load
    rp = load_mono(args.ref_piano, args.sr)
    rt = load_mono(args.ref_trumpet, args.sr)
    ep = load_mono(args.est_piano, args.sr)
    et = load_mono(args.est_trumpet, args.sr)

    # Length-normalize all to the reference mix span
    L = max(len(rp), len(rt), len(ep), len(et))
    rp, rt, ep, et = (pad_or_trim(x, L) for x in (rp, rt, ep, et))

    # Two assignments (PI evaluation)
    # A: est_piano -> ref_piano, est_trumpet -> ref_trumpet
    a_p = align_and_score(rp, ep, args.sr)
    a_t = align_and_score(rt, et, args.sr)
    mean_a = mean_sisdr(a_p, a_t)

    # B: est_piano -> ref_trumpet, est_trumpet -> ref_piano (swapped)
    b_p = align_and_score(rp, et, args.sr)
    b_t = align_and_score(rt, ep, args.sr)
    mean_b = mean_sisdr(b_p, b_t)

    if mean_b > mean_a:
        chosen = [b_p, b_t]
        names = ["Piano*", "Trpt*"]  # * indicates swapped match
        assignment = "Swapped (best)"
        # For plots, we align to the chosen pairing
        piano_ref, piano_est = rp, et
        trpt_ref, trpt_est  = rt, ep
    else:
        chosen = [a_p, a_t]
        names = ["Piano", "Trpt"]
        assignment = "Direct"
        piano_ref, piano_est = rp, ep
        trpt_ref, trpt_est  = rt, et

    # Print results
    print("\nPermutation-invariant assignment:", assignment)
    print(pretty_table(chosen, names))
    print(f"\nMean SI-SDR (dB): {0.5*(chosen[0]['SI-SDR(dB)']+chosen[1]['SI-SDR(dB)']):.2f}")
    print("(Lower is better) SpecConv / LogMelL2 / MagSpecL1")

    # Optional plots
    if args.plots_dir:
        import os
        os.makedirs(args.plots_dir, exist_ok=True)
        # Realign + gain-match for plotting
        def align_and_gain(ref, est):
            lag = find_lag(ref, est, max_shift=int(0.5*args.sr))
            est = shift_signal(est, lag)
            L = min(len(ref), len(est))
            ref = ref[:L]; est = est[:L]
            return ref, gain_match(ref, est)

        pr, pe = align_and_gain(piano_ref, piano_est)
        tr, te = align_and_gain(trpt_ref, trpt_est)
        save_spec_compare(os.path.join(args.plots_dir, "piano_spec.png"), pr, pe, args.sr, "Piano")
        save_spec_compare(os.path.join(args.plots_dir, "trumpet_spec.png"), tr, te, args.sr, "Trumpet")
        print(f"\nSaved plots to: {args.plots_dir}")

if __name__ == "__main__":
    main()
# Example usage:
# python src/audio/evaluate_separation.py --ref-piano ressources/temp/piano_ref.wav --ref-trumpet ressources/temp/trumpet_ref.wav --est-piano ressources/temp/piano.wav --est-trumpet ressources/temp/trumpet.wav --plots-dir ressources/temp/plots