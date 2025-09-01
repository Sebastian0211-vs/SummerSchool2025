import numpy as np
import librosa
import soundfile as sf
from scipy.ndimage import median_filter

def stft(y, n_fft=2048, hop=512, win="hann"):
    return librosa.stft(y, n_fft=n_fft, hop_length=hop, window=win)

def istft(S, hop=512, win="hann", length=None):
    return librosa.istft(S, hop_length=hop, window=win, length=length)

def power_db(x, eps=1e-10):
    return 10.0 * np.log10(np.maximum(eps, x))

def wiener_mask(S_target_mag, S_resid_mag, p=2.0, eps=1e-12):
    """Soft mask de type Wiener: M = T^p / (T^p + R^p)"""
    Tp = np.power(np.maximum(S_target_mag, 0.0), p)
    Rp = np.power(np.maximum(S_resid_mag, 0.0), p)
    return Tp / np.maximum(Tp + Rp, eps)

def spectral_gate(S_target_mag, S_mix_mag, gate_rel_db=-12.0, axis=1):
    """
    Gate adaptatif: coupe les TF-bins où la cible est trop faible par rapport
    au plancher local (percentile) du mix.
    gate_rel_db: seuil relatif en dB sous le percentile local.
    """
    # bruit/plancher local: percentile par fréquence (ou par temps)
    if axis == 1:
        # profil par fréquence (percentile sur le temps)
        noise_floor = np.percentile(S_mix_mag, 20, axis=axis, keepdims=True)
    else:
        # profil par temps (percentile sur les fréquences)
        noise_floor = np.percentile(S_mix_mag, 20, axis=axis, keepdims=True)

    # masque binaire doux basé sur dB
    target_db = power_db(S_target_mag)
    floor_db  = power_db(noise_floor)
    mask = (target_db >= (floor_db + gate_rel_db)).astype(float)

    # lisser un peu (réduit les “trous” musicaux)
    mask = median_filter(mask, size=(5, 3))
    return mask

def cleanup_instrument(
    mix_path: str,
    highlighted_path: str,
    out_path: str,
    sr=None,
    n_fft=4096,
    hop=512,
    wiener_p=2.0,
    gate_rel_db=-12.0,
    freq_bias=None,
    strength=1.0,
):
    """
    Nettoie la piste 'highlighted' en supprimant l'instrument parasite.

    - mix_path: mp3/wav du mix original
    - highlighted_path: mp3/wav de la piste mise en évidence (celle à garder)
    - out_path: chemin de sortie wav
    - wiener_p: agressivité du soft-mask (2.0 = standard, 3–4 = plus agressif)
    - gate_rel_db: seuil du gate adaptatif (p.ex. -12 dB, -18 dB plus agressif)
    - freq_bias: tuple (f1, f2) pour booster la cible dans [f1, f2] Hz
                 (utile si trompette ~ 400–4000 Hz, ou piano bas < 800 Hz)
    - strength: 0.0–1.5 pour renforcer/atténuer la sélectivité globale
    """

    # 1) Chargement (mono)
    y_mix, sr = librosa.load(mix_path, sr=sr, mono=True)
    y_high, _ = librosa.load(highlighted_path, sr=sr, mono=True)

    # 2) STFT
    S_mix = stft(y_mix, n_fft=n_fft, hop=hop)
    S_high = stft(y_high, n_fft=n_fft, hop=hop)

    # Magnitudes
    M_mix = np.abs(S_mix)
    M_high = np.abs(S_high)

    # 3) Estimation du résiduel “autre instrument”
    #    On borne à >= 0 pour éviter les négatifs.
    M_resid_est = np.maximum(M_mix - M_high, 0.0)

    # 4) (Optionnel) Biais fréquentiel pour privilégier la zone utile de l’instrument
    if freq_bias is not None:
        f1, f2 = freq_bias
        freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)
        band = ((freqs >= f1) & (freqs <= f2)).astype(float)
        band = band[:, None]  # broadcast sur le temps
        # on renforce la cible dans la bande, atténue hors bande
        bias_gain_in = 1.25
        bias_gain_out = 0.85
        M_high = M_high * (band * bias_gain_in + (1.0 - band) * bias_gain_out)

    # 5) Soft-mask Wiener
    M_mask_wiener = wiener_mask(M_high, M_resid_est, p=wiener_p)
    # renforcer ou adoucir
    M_mask_wiener = np.clip(np.power(M_mask_wiener, 1.0/np.maximum(1e-6, strength)), 0.0, 1.0)

    # 6) Gate spectral adaptatif (supplémentaire)
    M_gate = spectral_gate(M_high, M_mix, gate_rel_db=gate_rel_db, axis=1)

    # 7) Masque final lissé
    #    On multiplie soft-mask et gate, puis on lisse un peu dans le temps/fréquence.
    M_mask = M_mask_wiener * M_gate
    M_mask = median_filter(M_mask, size=(3, 3))
    M_mask = np.clip(M_mask, 0.0, 1.0)

    # 8) Application du masque (on garde la phase du mix pour cohérence)
    S_clean = M_mask * S_mix

    # 9) iSTFT
    y_clean = istft(S_clean, hop=hop, length=len(y_mix))

    # 10) Normalisation douce
    peak = np.max(np.abs(y_clean)) + 1e-12
    y_clean = 0.98 * y_clean / peak

    # 11) Écriture
    sf.write(out_path, y_clean, sr)
    return out_path

# ---------- Exemples d’utilisation ----------
if __name__ == "__main__":
    # Cas 2: Nettoyer un piano mis en évidence (accentuer < 800 Hz)
    cleanup_instrument(
        mix_path="PinkPanther_Both.mp3",
        highlighted_path="piano.wav",
        out_path="piano_clean.wav",
        n_fft=4096,
        hop=512,
        wiener_p=2.0,
        gate_rel_db=-12.0,
        freq_bias=(50, 200),
        strength=1.0,
    )
