# autotune_split.py
import json, os, subprocess, sys, itertools, tempfile, shutil
from pathlib import Path

from AudioSplitter_v1 import AudioSplit
PY = sys.executable

# paths you may tweak:
EVAL = "src/audio/evaluate_separation.py"
MIX  = "ressources/MP3/Final/Gamme.mp3"         # your mix for tuning (or the same clip you used)
RP   = "ressources/MP3/Final/Gamme_Piano.mp3"   # reference stems ("gamme")
RT   = "ressources/MP3/Final/Gamme_Trumpet.mp3"

OUTDIR = Path("ressources/temp/autotune_out")
OUTDIR.mkdir(parents=True, exist_ok=True)

# modest search space (kept small to run quickly)
AGGRS  = [0.55, 0.7, 0.85]
NFFT   = [2048, 4096]
HOPS   = [x//4 for x in NFFT]  # keep hop=n_fft/4
EXPAND = [True, False]

def run_split(n_fft, hop, aggr, expand, tag):
    op = OUTDIR / f"piano_{tag}.wav"
    ot = OUTDIR / f"trpt_{tag}.wav"
    # call your splitter via a tiny wrapper module (so we can pass args)
    code = f"""
from AudioSplitter_v1 import AudioSplit
AudioSplit("{MIX}", r"{op}", r"{ot}",
           n_fft={n_fft}, hop_length={hop},
           aggressiveness={aggr}, expand_piano={expand}, debug_dir=None)
"""
    tmp = OUTDIR / f"run_{tag}.py"
    tmp.write_text(code)
    subprocess.check_call([PY, str(tmp)])
    return op, ot

def parse_eval(text):
    # grabs two SI-SDR lines and the final mean
    lines = [l.strip() for l in text.splitlines()]
    vals = {"piano": None, "trpt": None, "mean": None}
    for l in lines:
        if l.startswith("Piano"):
            vals["piano"] = float(l.split("|")[1])
        if l.startswith("Trpt"):
            vals["trpt"] = float(l.split("|")[1])
        if l.startswith("Mean SI-SDR"):
            vals["mean"] = float(l.split(":")[1].strip().replace("dB",""))
    return vals

def eval_pair(op, ot):
    cmd = [PY, EVAL,
           "--ref-piano", RP,
           "--ref-trumpet", RT,
           "--est-piano", str(op),
           "--est-trumpet", str(ot)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return parse_eval(res.stdout), res.stdout

def score(vals):
    # prioritize trumpet recovery while not tanking the piano
    piano  = vals["piano"]
    trpt   = vals["trpt"]
    mean   = vals["mean"]
    # weighted objective: trumpet heavy, small penalty if piano < 2 dB
    penalty = 0.0 if piano is None or piano >= 2.0 else (2.0 - piano)
    return 1.8*trpt + 1.0*mean - 0.8*penalty

def main():
    best = None
    tried = []
    for n_fft, hop, aggr, expand in itertools.product(NFFT, HOPS, AGGRS, EXPAND):
        tag = f"n{n_fft}_h{hop}_a{aggr:.2f}_e{int(expand)}"
        op, ot = run_split(n_fft, hop, aggr, expand, tag)
        vals, raw = eval_pair(op, ot)
        sc = score(vals)
        tried.append((sc, tag, vals))
        print(f"[{tag}] -> {vals} objective={sc:.2f}")
        sys.stdout.flush()
    tried.sort(reverse=True, key=lambda x: x[0])
    print("\n=== Top 5 ===")
    for sc, tag, vals in tried[:5]:
        print(f"{tag}: score={sc:.2f}  vals={vals}")

if __name__ == "__main__":
    main()
