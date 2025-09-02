from __future__ import annotations
import os
import numpy as np
import librosa
import soundfile as sf

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt


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

def _adaptive_cutoffs(mag: np.ndarray, sr: int, freqs: np.ndarray, expand_piano: bool = True):
    # Mesures globales (simple, robuste)
    sc  = librosa.feature.spectral_centroid(S=mag, sr=sr)
    r80 = librosa.feature.spectral_rolloff(S=mag, sr=sr, roll_percent=0.80)
    r95 = librosa.feature.spectral_rolloff(S=mag, sr=sr, roll_percent=0.95)

    sc  = float(np.nan_to_num(sc,  nan=0.0).mean())
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

    # Trompette plus haut pour éviter la main droite du piano

    tr_hp1 = clamp(0.9 * sc, 600.0, 1400.0)  # was forced >= 2000
    tr_hp2 = clamp(1.25 * sc, tr_hp1 + 150.0, 2200.0)
    tr_lp2 = clamp(0.90 * r95, 2600.0, min(6500.0, fmax))
    tr_lp1 = clamp(0.65 * r95, tr_hp2 + 120.0, tr_lp2 - 80.0)

    return piano_f1, piano_f2, tr_hp1 , tr_hp2 , tr_lp1, tr_lp2


def _hpss_soft_indices(mag: np.ndarray):
    """
    HPSS en 'indice' souple : on évite la moyenne de trop de configs.
    Deux kernels typiques pour réduire le biais.
    """
    H1, P1 = librosa.decompose.hpss(mag, kernel_size=(31, 5), margin=(2.0, 1.0))
    H2, P2 = librosa.decompose.hpss(mag, kernel_size=(17, 7), margin=(1.5, 1.0))
    H = 0.5 * (H1 + H2)
    P = 0.5 * (P1 + P2)
    return H.astype(np.float32), P.astype(np.float32)


# =========================
# F0 trompette (HP) & peigne
# =========================

def _preprocess_for_f0(audio: np.ndarray, sr: int, low: float = 180.0, high: float = 2000.0):
    """Band-pass to keep trumpet fundamentals & lower harmonics, suppress lows/high hiss."""
    try:
        from scipy.signal import butter, filtfilt
        ny = sr / 2.0
        lo = max(10.0, low) / ny
        hi = min(high, ny * 0.98) / ny
        b, a = butter(4, [lo, hi], btype='bandpass')
        y = filtfilt(b, a, audio)
    except Exception:
        # Fallback: light preemphasis if SciPy is missing
        y = librosa.effects.preemphasis(audio, coef=0.97)
    return y.astype(np.float32)


def estimate_f0_trumpet(audio: np.ndarray, sr: int, hop_length: int,
                        fmin: float = 220.0, fmax: float = 1100.0):
    # Keep fundamentals (band-pass), then estimate F0
    y = _preprocess_for_f0(audio, sr, low=180.0, high=2000.0)
    f0, vflag, vprob = librosa.pyin(
        y, fmin=fmin, fmax=fmax, frame_length=4096, hop_length=hop_length, center=True
    )
    f0 = np.asarray(f0)

    # Interpolate NaNs to stabilize the comb
    idx = np.isfinite(f0)
    if np.sum(idx) >= 2:
        f0_interp = np.interp(np.arange(len(f0)), np.flatnonzero(idx), f0[idx])
    else:
        # fallback to a sane constant if tracking totally fails
        f0_interp = np.full_like(f0, 440.0)
    # Median smooth to kill tiny jitters
    try:
        from scipy.ndimage import median_filter
        f0_s = median_filter(f0_interp, size=5)
    except Exception:
        f0_s = f0_interp

    # Return F0 and voiced probability (used to gate comb strength)
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
        # décroissance 1/sqrt(k) : évite de sur-pondérer les aigus
        weight = 1.0 / np.sqrt(k)
        ck = 1200.0 * np.log2(np.maximum(k * f0, 1e-12) / f0)
        mask += weight * np.exp(-0.5 * ((c - ck) / std) ** 2)

    if mask.max() > 0:
        mask = mask / (mask.max() + 1e-9)
    return mask.astype(np.float32)


# =========================
# Agressivité (adoucie)
# =========================

def map_aggressiveness(aggressiveness: float):
    a = np.clip(float(aggressiveness), 0.0, 1.0)
    # Seuils plus doux qu'avant (on évite les "trous")
    ratio_thresh = 1.5 + 3.0 * a   # borne haute ~4.5
    min_db = -50.0 + 15.0 * a      # entre -50 et -35 dB
    comb_bw_cents = 120.0 - 80.0 * a  # 140 -> 80 cents
    return ratio_thresh, min_db, comb_bw_cents


# =========================
# Debug plotting helpers
# =========================

def _ensure_dir(d: str):
    if d and not os.path.exists(d):
        os.makedirs(d, exist_ok=True)


def _time_freq_extent(n_frames: int, sr: int, hop_length: int, freqs: np.ndarray):
    t_max = (n_frames * hop_length) / float(sr)
    return [0.0, t_max, float(freqs[0]), float(freqs[-1])]


def _time_axis(n_frames: int, sr: int, hop_length: int):
    return np.arange(n_frames) * (hop_length / float(sr))


def save_spectrogram_png(path: str, mag: np.ndarray, sr: int, hop_length: int,
                         freqs: np.ndarray, title: str = ""):
    mag_db = librosa.amplitude_to_db(np.maximum(mag, 1e-12), ref=np.max)
    extent = _time_freq_extent(mag.shape[1], sr, hop_length, freqs)
    plt.figure(figsize=(10, 4))
    plt.imshow(mag_db, origin='lower', aspect='auto', extent=extent)
    plt.xlabel('Temps (s)')
    plt.ylabel('Fréquence (Hz)')
    if title:
        plt.title(title)
    plt.colorbar(label='Amplitude (dB, ref max)')
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def save_mask_png(path: str, mask: np.ndarray, sr: int, hop_length: int,
                  freqs: np.ndarray, title: str = ""):
    extent = _time_freq_extent(mask.shape[1], sr, hop_length, freqs)
    plt.figure(figsize=(10, 4))
    plt.imshow(mask, origin='lower', aspect='auto', extent=extent)
    plt.xlabel('Temps (s)')
    plt.ylabel('Fréquence (Hz)')
    if title:
        plt.title(title)
    plt.colorbar(label='Poids (0..1)')
    plt.tight_layout()
    plt.savefig(path, dpi=140)
    plt.close()


def save_overlay_with_f0(path: str, mag: np.ndarray, mask: np.ndarray, f0: np.ndarray,
                         sr: int, hop_length: int, freqs: np.ndarray, title: str = ""):
    mag_db = librosa.amplitude_to_db(np.maximum(mag, 1e-12), ref=np.max)
    extent = _time_freq_extent(mag.shape[1], sr, hop_length, freqs)
    t = _time_axis(mag.shape[1], sr, hop_length)
    plt.figure(figsize=(10, 4))
    plt.imshow(mag_db, origin='lower', aspect='auto', extent=extent)
    plt.imshow(mask, origin='lower', aspect='auto', extent=extent, alpha=0.25)
    valid = np.isfinite(f0)
    for k in [1, 2, 3, 4, 5, 6]:
        f = np.copy(f0)
        f[~valid] = np.nan
        plt.plot(t, f * k, linewidth=0.8)
    plt.xlabel('Temps (s)')
    plt.ylabel('Fréquence (Hz)')
    if title:
        plt.title(title)
    plt.tight_layout()
    plt.savefig(path, dpi=160)
    plt.close()


# =========================
# Main splitter (Wiener + consistency)
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
    # Taper: peu d'effet sous ~tr_hp1-200 Hz, fort au-dessus.
    edge = max(0.0, tr_hp1 - 200.0)
    ramp = np.clip((freqs - edge) / max(1.0, (freqs[-1] - edge)), 0.0, 1.0)
    return (0.35 + 0.65 * ramp)[..., None] * anti  # (F,1)


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
    # Taper: peu d'effet sous ~tr_hp1-200 Hz, fort au-dessus.
    edge = max(0.0, tr_hp1 - 200.0)
    ramp = np.clip((freqs - edge) / max(1.0, (freqs[-1] - edge)), 0.0, 1.0)
    return (0.35 + 0.65 * ramp)[..., None] * anti  # (F,1)


def AudioSplit(input_file: str, output_piano: str, output_trumpet: str,
               sr: int = 44100, n_fft: int = 2048, hop_length: int = 512,
               aggressiveness: float = 0.6, debug_dir: str | None = None,
               expand_piano: bool = True):

    # 1) Load & STFT
    audio, sr = librosa.load(input_file, mono=True, sr=None)
    S = stft(audio, sr, n_fft, hop_length)
    mag = np.abs(S).astype(np.float32)
    phase = np.angle(S)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    if debug_dir:
        _ensure_dir(debug_dir)
        save_spectrogram_png(os.path.join(debug_dir, "mix_spectrogram.png"),
                             mag, sr, hop_length, freqs,
                             title="Mix — Spectrogramme (dB)")

    # 2) Cutoffs / masques fréquentiels
    piano_f1, piano_f2, tr_hp1, tr_hp2, tr_lp1, tr_lp2 = _adaptive_cutoffs(mag, sr, freqs, expand_piano=expand_piano)

    # 3) Indices HPSS souples
    H, P = _hpss_soft_indices(mag)
    sigma = np.maximum(1e-6, np.median(mag) * 0.5)
    piano_bias   = 1.0 / (1.0 + np.exp(-(P - H) / (sigma + 1e-12)))
    trumpet_bias = 1.0 - piano_bias

    # 4) F0 trompette (HP) + peigne
    f0, vprob = estimate_f0_trumpet(audio, sr, hop_length, fmin=220.0, fmax=1100.0)
    ratio_thresh, min_db, comb_bw_cents = map_aggressiveness(aggressiveness)
    comb = np.stack([comb_mask_for_frame(freqs, f, num_harmonics=18, bw_cents=comb_bw_cents)
                     for f in f0], axis=1).astype(np.float32)  # (F,T)
    v_gate = (0.3 + 0.7 * np.clip(vprob, 0.0, 1.0))[None, :] if vprob is not None else 1.0

    # 5) Scores mous de base (sans gate sur trompette)
    piano_lp = lowpass_mask(freqs, piano_f1, piano_f2)[:, None]  # (F,1)
    trump_bp = bandpass_mask(freqs, tr_hp1, tr_hp2, tr_lp1, tr_lp2)[:, None]

    score_p = piano_lp * piano_bias
    score_t = trump_bp * trumpet_bias * (0.10 + 1.10 * comb) * v_gate

    # 6) NOUVEAU: Anti-peigne PIANO (réduit fortement les harmoniques de trompette)
    anti = piano_anti_harmonics(comb, freqs, tr_hp1, alpha=0.92, min_floor=0.08)  # (F,1)
    score_p *= anti

    # 7) Masques de Wiener + lissage
    eps = 1e-12
    gamma = 3.0
    score_p = np.maximum(score_p, eps)
    score_t = np.maximum(score_t, eps)
    m_p = (score_p**gamma) / (score_p**gamma + score_t**gamma + eps)
    m_t = 1.0 - m_p

    try:
        from scipy.ndimage import median_filter
        m_p = median_filter(m_p, size=(11, 3))
        m_t = median_filter(m_t, size=(11, 3))
    except Exception:
        pass

    # 8) Reconstruction + mixture consistency (1 passe)
    Sp = (mag * m_p) * np.exp(1j * phase)
    St = (mag * m_t) * np.exp(1j * phase)
    resid = S - (Sp + St)
    Sp += 0.5 * resid
    St += 0.5 * resid

    # 9) Sidechain spectral doux: retire un peu de trompette du piano (pré-ISTFT)
    #   -> sans créer de trous (clip>=0) et on re-projette ensuite.
    lam = 0.26  # 0.15–0.30 typiquement
    Sp_mag = np.abs(Sp)
    St_mag = np.abs(St)
    Sp_mag = np.maximum(0.0, Sp_mag - lam * St_mag)         # soustraction douce
    Sp = Sp_mag * np.exp(1j * np.angle(Sp))

    # Re-projection mixture-consistent (courte)
    resid2 = S - (Sp + St)
    Sp += 0.5 * resid2
    St += 0.5 * resid2

    # 10) ISTFT (passe 1)
    y_p1 = istft(Sp, sr, n_fft, hop_length, target_length=len(audio))
    y_t1 = istft(St, sr, n_fft, hop_length, target_length=len(audio))

    # 11) PASSE 2 (raffinement) — on ré-estime F0 sur la trompette extraite
    f0_ref, vprob_ref = estimate_f0_trumpet(y_t1, sr, hop_length, fmin=220.0, fmax=1100.0)
    comb_ref = np.stack([comb_mask_for_frame(freqs, f, num_harmonics=20, bw_cents=comb_bw_cents)
                         for f in f0_ref], axis=1).astype(np.float32)
    v_gate2 = (0.3 + 0.7 * np.clip(vprob_ref, 0.0, 1.0))[None, :] if vprob_ref is not None else 1.0

    score_p2 = piano_lp * piano_bias
    score_t2 = trump_bp * trumpet_bias * (0.10 + 1.10 * comb_ref) * v_gate2
    anti2 = piano_anti_harmonics(comb_ref, freqs, tr_hp1, alpha=0.95, min_floor=0.06)
    score_p2 *= anti2

    score_p2 = np.maximum(score_p2, eps)
    score_t2 = np.maximum(score_t2, eps)
    m_p2 = (score_p2**2) / (score_p2**2 + score_t2**2 + eps)
    m_t2 = 1.0 - m_p2

    try:
        from scipy.ndimage import median_filter
        m_p2 = median_filter(m_p2, size=(11, 3))
        m_t2 = median_filter(m_t2, size=(11, 3))
    except Exception:
        pass

    Sp2 = (mag * m_p2) * np.exp(1j * phase)
    St2 = (mag * m_t2) * np.exp(1j * phase)

    # Sidechain doux encore (plus léger)
    lam2 = 0.18
    Sp2_mag = np.maximum(0.0, np.abs(Sp2) - lam2 * np.abs(St2))
    Sp2 = Sp2_mag * np.exp(1j * np.angle(Sp2))

    # Re-projection finale
    resid3 = S - (Sp2 + St2)
    Sp2 += 0.5 * resid3
    St2 += 0.5 * resid3

    # 12) ISTFT final
    y_piano = istft(Sp2, sr, n_fft, hop_length, target_length=len(audio))
    y_trumpet = istft(St2, sr, n_fft, hop_length, target_length=len(audio))

    # 13) Export
    sf.write(output_piano, normalize(y_piano), sr)
    sf.write(output_trumpet, normalize(y_trumpet), sr)

    print(f"[Separation] aggr={aggressiveness:.2f} min_db={min_db:.1f}dB comb_bw={comb_bw_cents:.0f}c")
    print(f"[Cutoffs] Piano {piano_f1:.1f}-{piano_f2:.1f} Hz  |  Trp {tr_hp1:.1f}-{tr_hp2:.1f} / {tr_lp1:.1f}-{tr_lp2:.1f} Hz")
    print("Fichiers sauvegardés :", output_piano, output_trumpet)

