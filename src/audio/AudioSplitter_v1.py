from __future__ import annotations
import os
from dataclasses import dataclass
from typing import Optional

import numpy as np
import librosa
import soundfile as sf

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


# =========================
# Parameter dataclass
# =========================

@dataclass
class Params:
    # F0 tracking
    f0_fmin: float = 300.0
    f0_fmax: float = 950.0
    f0_frame_len: int = 8192

    pyin_resolution: float = 0.1
    pyin_max_tr_rate: float = 25.0

    # Comb & gates
    comb_harmonics: int = 18
    comb_bw_cents: float = 50.0
    vprob_lo: float = 0.4
    vprob_hi: float = 0.6
    comb_hit_mid: float = 0.22
    comb_hit_lo: float = 0.12

    # Trumpet band (adaptive offsets)
    tr_hp1_mul: float = 0.95   # * spectral centroid
    tr_hp1_min: float = 1200.0
    tr_hp2_gap: float = 280.0
    tr_hp2_mul: float = 1.40
    tr_lp2_mul: float = 0.88   # * rolloff95
    tr_lp2_min: float = 4600.0
    tr_lp1_gap: float = 220.0
    tr_lp1_mul: float = 0.60

    # Piano anti-peigne
    anti_alpha1: float = 0.97
    anti_min1: float = 0.05
    anti_alpha2: float = 0.98
    anti_min2: float = 0.05

    # Mask shaping (Wiener exponents & comb gains)
    wiener_gamma1: float = 4.2
    wiener_gamma2: float = 2.2
    score_t_comb_gain1: float = 1.55
    score_t_comb_gain2: float = 1.60
    score_t_base: float = 0.06

    # Sidechain
    lam1: float = 0.36
    lam2: float = 0.26
    sc_floor1: float = 0.02
    sc_floor2: float = 0.015

    # Bias frequency weighting
    tr_hi_k: float = 1200.0   # slope scale for high-boost
    pi_lo_gain: float = 0.5
    tr_hi_gain: float = 0.6

    # Global feel
    aggressiveness: float = 0.8


# =========================
# STFT / ISTFT & utilities
# =========================

def stft(signal: np.ndarray, sample_rate: int, n_fft: int = 2048, hop_length: int = 512):
    return librosa.stft(signal, n_fft=n_fft, hop_length=hop_length, window="hann")


def istft(spectrogram, sample_rate: int, n_fft: int, hop_length: int, target_length: int):
    return librosa.istft(spectrogram, hop_length=hop_length, win_length=n_fft, window="hann", length=target_length)


def normalize(signal: np.ndarray):
    max_val = np.max(np.abs(signal)) + 1e-12
    return (0.98 * signal / max_val).astype(np.float32)


def _ensure_dir(d: str):
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _time_freq_extent(n_frames: int, sr: int, hop_length: int, freqs: np.ndarray):
    t_max = (n_frames * hop_length) / float(sr)
    return [0.0, t_max, float(freqs[0]), float(freqs[-1])]


def _time_axis(n_frames: int, sr: int, hop_length: int):
    return np.arange(n_frames) * (hop_length / float(sr))


def save_spectrogram_png(path: str, mag, sr, hop_length, freqs, title: str = ""):
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import librosa
    mag_db = librosa.amplitude_to_db(np.maximum(mag, 1e-12), ref=np.max)
    extent = _time_freq_extent(mag.shape[1], sr, hop_length, freqs)
    plt.figure(figsize=(10, 4))
    plt.imshow(mag_db, origin='lower', aspect='auto', extent=extent)
    plt.xlabel('Temps (s)'); plt.ylabel('Fréquence (Hz)')
    if title: plt.title(title)
    plt.colorbar(label='Amplitude (dB, ref max)')
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()



# =========================
# Frequency masks
# =========================

def lowpass_mask(freqs: np.ndarray, cutoff_start: float, cutoff_end: float):
    mask = np.ones_like(freqs)
    mask[freqs >= cutoff_end] = 0.0
    band = (freqs >= cutoff_start) & (freqs < cutoff_end)
    mask[band] = 0.5 * (1 + np.cos(np.pi * (freqs[band] - cutoff_start) / (cutoff_end - cutoff_start)))
    return mask.astype(np.float32)


def bandpass_mask(freqs: np.ndarray, low_cutoff_start: float, low_cutoff_end: float,
                  high_cutoff_start: float, high_cutoff_end: float):
    hp = np.zeros_like(freqs)
    hp[freqs >= low_cutoff_end] = 1.0
    band_low = (freqs > low_cutoff_start) & (freqs < low_cutoff_end)
    hp[band_low] = 0.5 * (1 - np.cos(np.pi * (freqs[band_low] - low_cutoff_start) / (low_cutoff_end - low_cutoff_start)))
    lp = lowpass_mask(freqs, high_cutoff_start, high_cutoff_end)
    return (hp * lp).astype(np.float32)


# =========================
# Adaptive cutoffs & HPSS
# =========================

def _adaptive_cutoffs(mag: np.ndarray, sr: int, freqs: np.ndarray, expand_piano: bool, *, p: Params):
    sc = librosa.feature.spectral_centroid(S=mag, sr=sr)
    r80 = librosa.feature.spectral_rolloff(S=mag, sr=sr, roll_percent=0.80)
    r95 = librosa.feature.spectral_rolloff(S=mag, sr=sr, roll_percent=0.95)

    sc = float(np.nan_to_num(sc, nan=0.0).mean())
    r80 = float(np.nan_to_num(r80, nan=0.0).mean())
    r95 = float(np.nan_to_num(r95, nan=0.0).mean())

    fmax = float(freqs[-1])

    def clamp(x, lo, hi):
        return float(max(lo, min(hi, x)))

    # Piano élargi vers médiums
    piano_f1 = clamp(0.45 * sc, 120.0, 800.0)
    piano_f2 = clamp(0.65 * r80 * 1.8, 800.0, 2500.0)
    if expand_piano:
        piano_f2 = min(piano_f2 * 2.0, 3000.0)
    if piano_f2 <= piano_f1 + 150:
        piano_f2 = piano_f1 + 150.0

    # Trompette (paramétré)
    tr_hp1 = clamp(max(p.tr_hp1_min, p.tr_hp1_mul * sc), 900.0, 1900.0)
    tr_hp2 = clamp(max(tr_hp1 + p.tr_hp2_gap, p.tr_hp2_mul * sc), tr_hp1 + p.tr_hp2_gap, 2600.0)
    tr_lp2 = clamp(max(p.tr_lp2_min, p.tr_lp2_mul * r95), p.tr_lp2_min, min(7000.0, fmax))
    tr_lp1 = clamp(max(tr_hp2 + p.tr_lp1_gap, p.tr_lp1_mul * r95), tr_hp2 + p.tr_lp1_gap, tr_lp2 - 150.0)

    return 0, piano_f1, tr_hp1, tr_hp2, tr_lp1, tr_lp2


def _hpss_soft_indices(mag: np.ndarray):
    """HPSS moyenne douce pour réduire le biais."""
    H1, P1 = librosa.decompose.hpss(mag, kernel_size=(31, 5), margin=(2.0, 1.0))
    H2, P2 = librosa.decompose.hpss(mag, kernel_size=(17, 7), margin=(1.5, 1.0))
    H = 0.5 * (H1 + H2)
    P = 0.5 * (P1 + P2)
    return H.astype(np.float32), P.astype(np.float32)


# =========================
# F0 trompette (HP) & peigne
# =========================

def _preprocess_for_f0(audio: np.ndarray, sr: int, low: float = 220.0, high: float = 2400.0):
    """Band-pass to keep trumpet fundamentals & lower harmonics, suppress lows/high hiss."""
    try:
        from scipy.signal import butter, filtfilt
        ny = sr / 2.0
        lo = max(10.0, low) / ny
        hi = min(high, ny * 0.98) / ny
        b, a = butter(4, [lo, hi], btype='bandpass')
        y = filtfilt(b, a, audio)
    except Exception:
        # Fallback: pre-emphasis if SciPy is missing
        y = librosa.effects.preemphasis(audio, coef=0.97)
    return y.astype(np.float32)


def estimate_f0_trumpet(audio: np.ndarray, sr: int, hop_length: int, *, p: Params):
    y = _preprocess_for_f0(audio, sr, low=220.0, high=2400.0)

    # Try a few progressively safer pyin configs if librosa complains
    attempts = []
    attempts.append((p.f0_fmin, p.f0_fmax, p.f0_frame_len, p.pyin_resolution, p.pyin_max_tr_rate))
    attempts.append((p.f0_fmin, p.f0_fmax, max(4096, p.f0_frame_len), max(0.08, p.pyin_resolution*0.8), max(18.0, p.pyin_max_tr_rate*0.8)))
    attempts.append((max(240.0, p.f0_fmin*0.9), min(1200.0, p.f0_fmax*1.1),
                     max(4096, p.f0_frame_len), 0.05, 15.0))
    attempts.append((220.0, 1100.0, 4096, 0.04, 12.0))

    f0 = vprob = None
    last_err = None
    for fmin, fmax, flen, resol, tr in attempts:
        try:
            f0, vflag, vprob = librosa.pyin(
                y,
                fmin=fmin, fmax=fmax, sr=sr,
                frame_length=flen, hop_length=hop_length, center=True,
                resolution=resol,           # increases n_pitch_bins when smaller
                max_transition_rate=tr      # narrows allowed pitch jumps
            )
            break
        except _LibrosaParamErr as e:
            last_err = e
            continue
    if f0 is None:
        # final ultra-safe attempt
        f0, vflag, vprob = librosa.pyin(
            y, fmin=220.0, fmax=880.0, sr=sr,
            frame_length=4096, hop_length=hop_length, center=True,
            resolution=0.04, max_transition_rate=10.0
        )

    f0 = np.asarray(f0)
    idx = np.isfinite(f0)
    if np.sum(idx) >= 2:
        f0_interp = np.interp(np.arange(len(f0)), np.flatnonzero(idx), f0[idx])
    else:
        f0_interp = np.full_like(f0, 440.0)

    try:
        from scipy.ndimage import median_filter
        f0_s = median_filter(f0_interp, size=5)
    except Exception:
        f0_s = f0_interp

    return f0_s.astype(np.float32), (vprob.astype(np.float32) if vprob is not None else None)


def comb_mask_for_frame(freqs: np.ndarray, f0: float,
                        num_harmonics: int = 16, bw_cents: float = 110.0):
    if not np.isfinite(f0) or f0 <= 0:
        return np.zeros_like(freqs, dtype=np.float32)

    def cents(x):
        return 1200.0 * np.log2(np.maximum(x, 1e-12) / f0)

    c = cents(freqs)
    mask = np.zeros_like(freqs, dtype=np.float32)
    std = max(bw_cents / 2.355, 1e-3)  # FWHM ≈ bw_cents

    for k in range(1, num_harmonics + 1):
        weight = 1.0 / np.sqrt(k)
        ck = 1200.0 * np.log2(np.maximum(k * f0, 1e-12) / f0)
        mask += weight * np.exp(-0.5 * ((c - ck) / std) ** 2)

    if mask.max() > 0:
        mask = mask / (mask.max() + 1e-9)
    return mask.astype(np.float32)


# =========================
# Anti-peigne Piano
# =========================

def piano_anti_harmonics(comb: np.ndarray, freqs: np.ndarray,
                         tr_hp1: float, alpha: float = 0.85,
                         min_floor: float = 0.12) -> np.ndarray:
    """
    Fabrique un anti-peigne pour le PIANO à partir du peigne trompette.
    - On n'éteint pas totalement (min_floor), pour éviter les trous.
    - On n'applique fort que dans la bande médium/haut (>= tr_hp1-200 Hz).
    """
    anti = 1.0 - alpha * np.clip(comb, 0.0, 1.0)          # [0..1]
    anti = np.maximum(anti, min_floor)
    edge = max(0.0, tr_hp1 - 200.0)
    ramp = np.clip((freqs - edge) / max(1.0, (freqs[-1] - edge)), 0.0, 1.0)
    return (0.35 + 0.65 * ramp)[..., None] * anti  # (F,1)


# =========================
# Main splitter (Wiener + consistency)
# =========================

def AudioSplit(input_file: str, output_piano: str, output_trumpet: str,
               sr: int = 44100, n_fft: int = 2048, hop_length: int = 512,
               params: Optional[Params] = None,
               debug_dir: str | None = None,
               expand_piano: bool = True,
               enable_plots: bool = False):

    p = params or Params()

    # 1) Load & STFT
    audio, sr = librosa.load(input_file, mono=True, sr=None)
    S = stft(audio, sr, n_fft, hop_length)
    mag = np.abs(S).astype(np.float32)
    phase = np.angle(S)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    if debug_dir and enable_plots:
        _ensure_dir(debug_dir)
        save_spectrogram_png(os.path.join(debug_dir, "mix_spectrogram.png"),
                             mag, sr, hop_length, freqs,
                             title="Mix — Spectrogramme (dB)")

    # 2) Cutoffs / masques fréquentiels
    piano_f1, piano_f2, tr_hp1, tr_hp2, tr_lp1, tr_lp2 = _adaptive_cutoffs(mag, sr, freqs, expand_piano=expand_piano, p=p)

    # 3) Indices HPSS souples
    H, P = _hpss_soft_indices(mag)
    sigma = float(max(1e-6, np.median(mag) * 0.5))

    x = (P - H) / (sigma + 1e-12)
    piano_bias = 0.5 * (1.0 + np.tanh(0.5 * x))  # 0..1
    trumpet_bias = 1.0 - piano_bias

    # frequency weighting (trumpet trusted more in highs)
    w_tr_hi = np.clip((freqs - 1200.0) / p.tr_hi_k, 0.0, 1.0)[:, None]
    w_pi_lo = (1.0 - w_tr_hi)
    trumpet_bias = np.clip(trumpet_bias * (0.8 + p.tr_hi_gain * w_tr_hi), 0.0, 1.0)
    piano_bias   = np.clip(piano_bias   * (0.9 + p.pi_lo_gain * w_pi_lo),  0.0, 1.0)

    # 4) F0 trompette (HP) + peigne
    f0, vprob = estimate_f0_trumpet(audio, sr, hop_length, p=p)
    comb = np.stack([comb_mask_for_frame(freqs, f, num_harmonics=p.comb_harmonics, bw_cents=p.comb_bw_cents)
                     for f in f0], axis=1).astype(np.float32)  # (F,T)

    # voiced gate
    if vprob is not None:
        vp = np.clip(vprob, 0.0, 1.0)[None, :]
        v_gate = np.where(vp > p.vprob_hi, 1.0, np.where(vp > p.vprob_lo, 0.5, 0.05))
    else:
        v_gate = 1.0

    # harmonicity gate inside trumpet band
    tr_band = (freqs[:, None] >= tr_hp1) & (freqs[:, None] <= tr_lp2)
    comb_in_band = np.where(tr_band, comb, 0.0)
    band_area = np.maximum(1e-6, tr_band.sum(axis=0, keepdims=True))  # (1,T)
    comb_hit = comb_in_band.sum(axis=0, keepdims=True) / band_area    # (1,T)
    gate_harm = np.where(comb_hit > p.comb_hit_mid, 1.0,
                  np.where(comb_hit > p.comb_hit_lo, 0.5, 0.05))
    v_gate = v_gate * gate_harm

    # 5) Scores de base
    piano_lp = lowpass_mask(freqs, piano_f1, piano_f2)[:, None]  # (F,1)
    trump_bp = bandpass_mask(freqs, tr_hp1, tr_hp2, tr_lp1, tr_lp2)[:, None]

    score_p = piano_lp * piano_bias
    score_t = trump_bp * trumpet_bias * (p.score_t_base + p.score_t_comb_gain1 * comb) * v_gate

    # 6) Anti-peigne PIANO (réduit fortement les harmoniques de trompette)
    anti = piano_anti_harmonics(comb, freqs, tr_hp1,
                                alpha=params.anti_alpha1 if hasattr(params, 'anti_alpha1') else 0.98,
                                min_floor=params.anti_min1 if hasattr(params, 'anti_min1') else 0.04)
    score_p *= anti

    # 7) Masques de Wiener + lissage (pass 1)
    eps = 1e-12
    score_p = np.maximum(score_p, eps)
    score_t = np.maximum(score_t, eps)
    gamma = p.wiener_gamma1
    m_p = (score_p**gamma) / (score_p**gamma + score_t**gamma + eps)
    m_t = 1.0 - m_p

    try:
        from scipy.ndimage import median_filter
        m_p = median_filter(m_p, size=(11, 3))
        m_t = median_filter(m_t, size=(11, 3))
    except Exception:
        pass

    # 8) Reconstruction + mixture consistency (1 passe) + sidechain
    Sp = (mag * m_p) * np.exp(1j * phase)
    St = (mag * m_t) * np.exp(1j * phase)

    resid = S - (Sp + St)
    Sp += 0.5 * resid
    St += 0.5 * resid

    # Sidechain doux
    lam = p.lam1
    Sp_mag = np.abs(Sp)
    St_mag = np.abs(St)
    Sp_mag = np.maximum(0.0, Sp_mag - lam * St_mag)         # soustraction douce
    Sp_mag = np.maximum(Sp_mag, p.sc_floor1 * np.abs(S))     # petit plancher
    Sp = Sp_mag * np.exp(1j * np.angle(Sp))

    # Re-projection mixture-consistent (courte)
    resid2 = S - (Sp + St)
    Sp += 0.5 * resid2
    St += 0.5 * resid2

    # 9) ISTFT (passe 1)
    y_p1 = istft(Sp, sr, n_fft, hop_length, target_length=len(audio))
    y_t1 = istft(St, sr, n_fft, hop_length, target_length=len(audio))

    # 10) PASSE 2 (raffinement) — ré-estime F0 sur la trompette extraite
    f0_ref, vprob_ref = estimate_f0_trumpet(y_t1, sr, hop_length, p=p)
    comb_ref = np.stack([comb_mask_for_frame(freqs, f, num_harmonics=p.comb_harmonics, bw_cents=p.comb_bw_cents)
                         for f in f0_ref], axis=1).astype(np.float32)

    if vprob_ref is not None:
        vp2 = np.clip(vprob_ref, 0.0, 1.0)[None, :]
        v_gate2 = np.where(vp2 > p.vprob_hi, 1.0, np.where(vp2 > p.vprob_lo, 0.5, 0.05))
    else:
        v_gate2 = 1.0

    tr_band2 = tr_band  # same band limits
    comb_in_band2 = np.where(tr_band2, comb_ref, 0.0)
    band_area2 = band_area
    comb_hit2 = comb_in_band2.sum(axis=0, keepdims=True) / band_area2
    gate_harm2 = np.where(comb_hit2 > p.comb_hit_mid, 1.0,
                   np.where(comb_hit2 > p.comb_hit_lo, 0.5, 0.05))
    v_gate2 *= gate_harm2

    score_p2 = piano_lp * piano_bias
    score_t2 = trump_bp * trumpet_bias * (p.score_t_base + p.score_t_comb_gain2 * comb_ref) * v_gate2
    anti2 = piano_anti_harmonics(comb_ref, freqs, tr_hp1,
                                 alpha=params.anti_alpha2 if hasattr(params, 'anti_alpha2') else 0.99,
                                 min_floor=params.anti_min2 if hasattr(params, 'anti_min2') else 0.04)
    score_p2 *= anti2

    score_p2 = np.maximum(score_p2, eps)
    score_t2 = np.maximum(score_t2, eps)
    m_p2 = (score_p2**p.wiener_gamma2) / (score_p2**p.wiener_gamma2 + score_t2**p.wiener_gamma2 + eps)
    m_t2 = 1.0 - m_p2

    try:
        from scipy.ndimage import median_filter
        m_p2 = median_filter(m_p2, size=(11, 3))
        m_t2 = median_filter(m_t2, size=(11, 3))
    except Exception:
        pass

    Sp2 = (mag * m_p2) * np.exp(1j * phase)
    St2 = (mag * m_t2) * np.exp(1j * phase)

    beta = 0.28  # siphon strength (0.2–0.35 is usually safe)
    thr = 0.35  # only siphon where comb_ref is strong
    route = (comb_ref > thr).astype(np.float32) * (comb_ref)  # (F,T)

    Sp2_mag = np.abs(Sp2)
    St2_mag = np.abs(St2)
    delta = beta * route * Sp2_mag

    # conserve mixture energy: subtract from piano, add to trumpet
    Sp2_mag = np.maximum(0.0, Sp2_mag - delta)
    St2_mag = St2_mag + delta

    Sp2 = Sp2_mag * np.exp(1j * np.angle(Sp2))
    St2 = St2_mag * np.exp(1j * np.angle(St2))

    # Sidechain doux encore (plus léger)
    lam2 = p.lam2
    Sp2_mag = np.maximum(0.0, np.abs(Sp2) - lam2 * np.abs(St2))
    Sp2_mag = np.maximum(Sp2_mag, p.sc_floor2 * np.abs(S))
    Sp2 = Sp2_mag * np.exp(1j * np.angle(Sp2))

    # Re-projection finale
    resid3 = S - (Sp2 + St2)
    Sp2 += 0.5 * resid3
    St2 += 0.5 * resid3

    # 11) ISTFT final
    y_piano = istft(Sp2, sr, n_fft, hop_length, target_length=len(audio))
    y_trumpet = istft(St2, sr, n_fft, hop_length, target_length=len(audio))

    # 12) Export
    sf.write(output_piano, normalize(y_piano), sr)
    sf.write(output_trumpet, normalize(y_trumpet), sr)




# =========================
# CLI helper
# =========================
if __name__ == "__main__":
    import argparse, json
    ap = argparse.ArgumentParser(description="Trumpet/Piano audio splitter (param-tunable)")
    ap.add_argument("input", help="Path to input audio (mix)")
    ap.add_argument("--out-piano", default="piano.wav")
    ap.add_argument("--out-trumpet", default="trumpet.wav")
    ap.add_argument("--sr", type=int, default=44100)
    ap.add_argument("--n-fft", type=int, default=2048)
    ap.add_argument("--hop", type=int, default=512)
    ap.add_argument("--params-json", type=str, default=None, help="JSON file with Params fields")
    ap.add_argument("--expand-piano", action="store_true")
    ap.add_argument("--debug-dir", type=str, default=None)
    args = ap.parse_args()

    p = Params()
    if args.params_json and os.path.exists(args.params_json):
        with open(args.params_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        for k, v in data.items():
            if hasattr(p, k):
                setattr(p, k, v)

    AudioSplit(
        args.input,
        args.out_piano,
        args.out_trumpet,
        sr=args.sr,
        n_fft=args.n_fft,
        hop_length=args.hop,
        params=p,
        debug_dir=args.debug_dir,
        expand_piano=args.expand_piano,
    )
