import json
from AudioSplitter_v1 import AudioSplit, Params

# Load params from JSON
with open("ressources/temp/tune_runs/best_params.json", "r") as f:
    d = json.load(f)

params = Params(**{k: v for k, v in d.items() if not k.startswith("_")})
n_fft = d.get("_n_fft", 2048)
hop = d.get("_hop", n_fft // 4)
expand_piano = d.get("_expand_piano", True)

AudioSplit(
    "ressources/MP3/Final/Gamme.mp3",
    "ressources/temp/piano_best.wav",
    "ressources/temp/trpt_best.wav",
    sr=44100, n_fft=n_fft, hop_length=hop,
    params=params, expand_piano=expand_piano, enable_plots=False
)
