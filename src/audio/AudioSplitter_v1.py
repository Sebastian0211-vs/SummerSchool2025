"""
Module de Séparation Audio
==========================

Ce module permet de séparer un enregistrement audio contenant
**un piano** et **une trompette** en deux fichiers distincts.

Il s’agit d’une version simple, pensée pour des cas où l’on sait
qu’il n’y a que deux instruments. Le principe repose sur deux idées :

1. **Le piano** joue surtout dans les basses et moyennes fréquences.
2. **La trompette** joue plus haut, avec des harmoniques bien marquées.

Plutôt que d’utiliser de l’intelligence artificielle, on applique
des filtres et des transformations mathématiques simples pour séparer
les sons.

---

Étapes principales :
    1. Charger le fichier audio (MP3/WAV).
    2. Transformer le son en un spectre temps/fréquence (STFT).
    3. Construire des filtres :
        - **Passe-bas** → garde les graves (piano).
        - **Passe-bande** → garde une zone médium-aigu (trompette).
    4. Utiliser un algorithme (HPSS) qui repère ce qui est **plutôt
       harmonique** (trompette) et **plutôt percussif/soutenu** (piano).
    5. Mélanger filtres + HPSS pour obtenir deux « masques ».
    6. Appliquer les masques, puis revenir dans le domaine du temps
       (ISTFT) pour recréer des fichiers audio.
    7. Normaliser le volume et sauvegarder deux fichiers distincts.

---

Fonctions :
    - **stft()** : calcule la transformation temps/fréquence.
    - **istft()** : revient au signal audio.
    - **lowpass_mask()** : fabrique un filtre passe-bas.
    - **bandpass_mask()** : fabrique un filtre passe-bande.
    - **normalize()** : ajuste le volume pour éviter la saturation.
    - **AudioSplit()** : la fonction principale qui sépare piano/trompette.

---

Exemple :
    >>> from audio.AudioSplitter_v1 import AudioSplit
    >>> AudioSplit("chanson.mp3", "piano.wav", "trompette.wav")

Cela crée deux fichiers :
    - `piano.wav` → contenant uniquement le piano
    - `trompette.wav` → contenant uniquement la trompette

---

Limites :
    - Les réglages de fréquence sont **fixes** et adaptés à un exemple précis.
    - Si l’enregistrement contient d’autres instruments, le résultat sera
      beaucoup moins bon.
    - Pour améliorer, il faudrait calculer automatiquement les bonnes zones
      de fréquence selon chaque morceau.
"""

import numpy as np
import librosa
import soundfile as sf


def stft(signal: np.ndarray, sample_rate: int, n_fft: int = 4096, hop_length: int = 1024):
    """Transforme le signal audio en spectrogramme (STFT).

    Args:
        signal: Vecteur audio mono.
        sample_rate: Fréquence d’échantillonnage.
        n_fft: Taille de la fenêtre de FFT (défaut : 4096).
        hop_length: Décalage entre deux fenêtres (défaut : 1024).

    Returns:
        Matrice complexe représentant le spectrogramme.
    """
    return librosa.stft(signal, n_fft=n_fft, hop_length=hop_length, window="hann")


def istft(spectrogram, sample_rate: int, n_fft: int, hop_length: int, target_length: int):
    """Reconstruction d’un signal audio depuis son spectrogramme.

    Args:
        spectrogram: Matrice complexe issue du STFT.
        sample_rate: Fréquence d’échantillonnage.
        n_fft: Taille de la fenêtre de FFT.
        hop_length: Décalage entre deux fenêtres.
        target_length: Longueur du signal de sortie.

    Returns:
        Signal audio reconstruit (vecteur).
    """
    return librosa.istft(spectrogram, hop_length=hop_length, win_length=n_fft, window="hann", length=target_length)


def lowpass_mask(freqs: np.ndarray, cutoff_start: float, cutoff_end: float):
    """Crée un filtre passe-bas avec transition douce.

    Garde les fréquences basses (piano) et atténue progressivement
    entre `cutoff_start` et `cutoff_end`.
    """
    mask = np.ones_like(freqs)
    mask[freqs >= cutoff_end] = 0.0
    band = (freqs >= cutoff_start) & (freqs < cutoff_end)
    mask[band] = 0.5 * (1 + np.cos(np.pi * (freqs[band] - cutoff_start) / (cutoff_end - cutoff_start)))
    return mask


def bandpass_mask(freqs: np.ndarray, low_cutoff_start: float, low_cutoff_end: float, high_cutoff_start: float, high_cutoff_end: float):
    """Crée un filtre passe-bande avec transitions douces.

    Garde une zone de fréquences précises (trompette),
    en atténuant ce qui est trop bas ou trop haut.
    """
    hp = np.zeros_like(freqs)
    hp[freqs >= low_cutoff_end] = 1.0
    band_low = (freqs > low_cutoff_start) & (freqs < low_cutoff_end)
    hp[band_low] = 0.5 * (1 - np.cos(np.pi * (freqs[band_low] - low_cutoff_start) / (low_cutoff_end - low_cutoff_start)))

    lp = np.ones_like(freqs)
    lp[freqs >= high_cutoff_end] = 0.0
    band_high = (freqs >= high_cutoff_start) & (freqs < high_cutoff_end)
    lp[band_high] = 0.5 * (1 + np.cos(np.pi * (freqs[band_high] - high_cutoff_start) / (high_cutoff_end - high_cutoff_start)))

    return hp * lp


def normalize(signal: np.ndarray):
    """Normalise le volume du signal audio.

    Évite la saturation en ramenant l’amplitude max à ~0.98.
    """
    max_val = np.max(np.abs(signal)) + 1e-12
    return (0.98 * signal / max_val).astype(np.float32)


def AudioSplit(input_file: str, output_piano: str, output_trumpet: str, sr: int = 44100, n_fft: int = 4096, hop_length: int = 1024):
    """Fonction principale : sépare piano et trompette.

    Args:
        input_file: Chemin du fichier audio d’entrée (MP3/WAV).
        output_piano: Nom du fichier de sortie pour le piano.
        output_trumpet: Nom du fichier de sortie pour la trompette.
        sr: Fréquence d’échantillonnage cible (défaut : 44100).
        n_fft: Taille fenêtre FFT.
        hop_length: Décalage entre fenêtres.

    Retour:
        Aucun. Écrit deux fichiers sur le disque.
    """
    audio, sr = librosa.load(input_file, mono=True, sr=None)
    S = stft(audio, sr, n_fft, hop_length)
    mag = np.abs(S)
    phase = np.angle(S)
    freqs = librosa.fft_frequencies(sr=sr, n_fft=n_fft)

    piano_f1, piano_f2 = 560.0, 900.0
    tr_hp1, tr_hp2 = 900.0, 1050.0
    tr_lp1, tr_lp2 = 3000.0, 3500.0

    piano_mask = lowpass_mask(freqs, piano_f1, piano_f2)
    trumpet_mask = bandpass_mask(freqs, tr_hp1, tr_hp2, tr_lp1, tr_lp2)

    H, P = librosa.decompose.hpss(mag)
    piano_bias = (P + 1e-9) / (H + P + 1e-9)
    trumpet_bias = (H + 1e-9) / (H + P + 1e-9)

    piano_mask = (piano_mask[:, None]) * piano_bias
    trumpet_mask = (trumpet_mask[:, None]) * trumpet_bias

    eps = 1e-8
    total_mask = piano_mask + trumpet_mask + eps
    piano_mag = mag * (piano_mask / total_mask)
    trumpet_mag = mag * (trumpet_mask / total_mask)

    Sp = piano_mag * np.exp(1j * phase)
    St = trumpet_mag * np.exp(1j * phase)

    y_piano = istft(Sp, sr, n_fft, hop_length, target_length=len(audio))
    y_trumpet = istft(St, sr, n_fft, hop_length, target_length=len(audio))

    sf.write(output_piano, normalize(y_piano), sr)
    sf.write(output_trumpet, normalize(y_trumpet), sr)

    print("Fichiers sauvegardés :", output_piano, output_trumpet)