#!/usr/bin/env python3
"""
make_presentation_graphs.py
Generate clear, presentation-ready graphs that show the efficiency of your piano/trumpet split.

Usage examples
--------------
# Minimal (no references) — makes spectrograms + waveforms
python make_presentation_graphs.py \
  --mix "ressources/MP3/Final/Gamme.mp3" \
  --est-piano "ressources/temp/piano_best.wav" \
  --est-trumpet "ressources/temp/trpt_best.wav" \
  --out-dir "ressources/temp/figs"

# With references — also computes SI-SDR and error metrics + bar charts
python make_presentation_graphs.py \
  --mix "ressources/MP3/Final/Gamme.mp3" \
  --est-piano "ressources/temp/piano_best.wav" \
  --est-trumpet "ressources/temp/trpt_best.wav" \
  --ref-piano "ressources/MP3/Final/Gamme_Piano.wav" \
  --ref-trumpet "ressources/MP3/Final/Gamme_Trumpet.wav" \
  --out-dir "ressources/temp/figs"
"""
import argparse
from pathlib import Path
import numpy as np
import soundfile as sf
import librosa
import librosa.display
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt

# ---------------------------
# Utilities
# ---------------------------

def load_mono(path: str, sr: int | None = None):
    y, file_sr = librosa.load(path, mono=True, sr=sr)
    return y.astype(np.float32), (file_sr if sr is None else sr)

def pad_to_min(*arrs):
    L = min(len(a) for a in arrs if a is not None)
    out = []
    for a in arrs:
        if a is None:
            out.append(None)
        else:
            out.append(a[:L])
    return out

def stft_mag_db(y, sr, n_fft=2048, hop=512):
    S = librosa.stft(y, n_fft=n_fft, hop_length=hop, window="hann")
    M = np.abs(S) + 1e-9
    return librosa.amplitude_to_db(M, ref=np.max)

def save_spec(path, Mdb, sr, hop, title):
    plt.figure(figsize=(10, 4))
    librosa.display.specshow(Mdb, sr=sr, hop_length=hop, x_axis="time", y_axis="hz")
    plt.title(title)
    plt.xlabel("Time (s)"); plt.ylabel("Frequency (Hz)")
    plt.colorbar(format="%.0f dB")
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def save_waveform(path, y, sr, title):
    t = np.arange(len(y)) / sr
    plt.figure(figsize=(10, 2.8))
    plt.plot(t, y, linewidth=0.8)
    plt.xlabel("Time (s)"); plt.ylabel("Amplitude")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

# ---------------------------
# Metrics
# ---------------------------

def si_sdr(ref, est):
    ref64 = ref.astype(np.float64)
    est64 = est.astype(np.float64)
    alpha = np.dot(est64, ref64) / (np.dot(ref64, ref64) + 1e-12)
    e_target = alpha * ref64
    e_res = est64 - e_target
    ratio = (np.dot(e_target, e_target) + 1e-12) / (np.dot(e_res, e_res) + 1e-12)
    return 10.0 * np.log10(ratio)

def save_metric_bars(path, piano_sisdr, trpt_sisdr, mean_sisdr, title="Separation Quality (SI-SDR)"):
    labels = ["Piano", "Trumpet", "Mean"]
    vals = [piano_sisdr, trpt_sisdr, mean_sisdr]
    plt.figure(figsize=(7.5, 4.5))
    x = np.arange(len(labels))
    plt.bar(x, vals)
    plt.xticks(x, labels)
    plt.ylabel("SI-SDR (dB)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

def save_scatter(path, piano_sisdr, trpt_sisdr, title="Per-stem SI-SDR"):
    plt.figure(figsize=(5.5, 5.0))
    plt.scatter([piano_sisdr], [trpt_sisdr], s=60)
    plt.axhline(0, linestyle="--", linewidth=0.8)
    plt.axvline(0, linestyle="--", linewidth=0.8)
    plt.xlabel("Piano SI-SDR (dB)")
    plt.ylabel("Trumpet SI-SDR (dB)")
    plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()

# ---------------------------
# Main
# ---------------------------

def main():
    ap = argparse.ArgumentParser(description="Generate graphs for a piano/trumpet separation demo.")
    ap.add_argument("--mix", required=True)
    ap.add_argument("--est-piano", required=True)
    ap.add_argument("--est-trumpet", required=True)
    ap.add_argument("--ref-piano", default=None)
    ap.add_argument("--ref-trumpet", default=None)
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--out-dir", required=True)
    ap.add_argument("--n-fft", type=int, default=2048)
    ap.add_argument("--hop", type=int, default=512)
    args = ap.parse_args()

    outdir = Path(args.out_dir)
    outdir.mkdir(parents=True, exist_ok=True)

    # Load audio
    mix, _ = load_mono(args.mix, sr=args.sr)
    ep, _ = load_mono(args.est_piano, sr=args.sr)
    et, _ = load_mono(args.est_trumpet, sr=args.sr)
    mix, ep, et = pad_to_min(mix, ep, et)

    # Spectrograms
    save_spec(outdir/"01_mix_spec.png", stft_mag_db(mix, args.sr, args.n_fft, args.hop), args.sr, args.hop, "Mix — Spectrogram")
    save_spec(outdir/"02_piano_spec.png", stft_mag_db(ep, args.sr, args.n_fft, args.hop), args.sr, args.hop, "Estimated Piano — Spectrogram")
    save_spec(outdir/"03_trumpet_spec.png", stft_mag_db(et, args.sr, args.n_fft, args.hop), args.sr, args.hop, "Estimated Trumpet — Spectrogram")

    # Waveforms
    save_waveform(outdir/"11_mix_wave.png", mix, args.sr, "Mix — Waveform")
    save_waveform(outdir/"12_piano_wave.png", ep, args.sr, "Estimated Piano — Waveform")
    save_waveform(outdir/"13_trumpet_wave.png", et, args.sr, "Estimated Trumpet — Waveform")

    # If references provided
    if args.ref_piano and args.ref_trumpet:
        rp, _ = load_mono(args.ref_piano, sr=args.sr)
        rt, _ = load_mono(args.ref_trumpet, sr=args.sr)
        rp, rt, ep, et = pad_to_min(rp, rt, ep, et)

        sisdr_p = si_sdr(rp, ep)
        sisdr_t = si_sdr(rt, et)
        sisdr_m = 0.5*(sisdr_p + sisdr_t)

        save_metric_bars(outdir/"21_si_sdr_bars.png", sisdr_p, sisdr_t, sisdr_m)
        save_scatter(outdir/"22_scatter.png", sisdr_p, sisdr_t)

        with open(outdir/"00_metrics.txt", "w", encoding="utf-8") as f:
            f.write(f"Piano SI-SDR: {sisdr_p:.2f} dB\nTrumpet SI-SDR: {sisdr_t:.2f} dB\nMean SI-SDR: {sisdr_m:.2f} dB\n")

    print(f"Figures saved to {outdir.resolve()}")

if __name__ == "__main__":
    main()
