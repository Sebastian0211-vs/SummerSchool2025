# tune_params.py — readable console output + robust runner
import json
import os
import random
import subprocess
import sys
import time
from pathlib import Path

PY = sys.executable

# ── Pretty console helpers ────────────────────────────────────────────────────
USE_COLOR = sys.stdout.isatty() and os.environ.get("NO_COLOR", "") == ""

def _c(text, code):
    if not USE_COLOR:
        return text
    return f"\033[{code}m{text}\033[0m"

def c_ok(x):   return _c(x, "92")   # green
def c_bad(x):  return _c(x, "91")   # red
def c_war(x):  return _c(x, "93")   # yellow
def c_dim(x):  return _c(x, "2")    # faint
def c_bld(x):  return _c(x, "1")    # bold
def c_cy(x):   return _c(x, "36")   # cyan
def c_mg(x):   return _c(x, "35")   # magenta
def c_blu(x):  return _c(x, "34")   # blue


def bar(p, width=24):
    p = max(0.0, min(1.0, p))
    k = int(round(p * width))
    return "[" + "#" * k + "-" * (width - k) + "]"

# ── Paths / Files ────────────────────────────────────────────────────────────
MODULE_FILE = "src/audio/AudioSplitter_v1.py"   # not used directly (we resolve below)
EVAL = "src/audio/evaluate_separation.py"

# Your data
MIX  = "ressources/MP3/Final/Gamme.mp3"        # mix for tuning
RP   = "ressources/MP3/Final/Gamme_Piano.mp3"  # reference piano
RT   = "ressources/MP3/Final/Gamme_Trumpet.mp3"  # reference trpt

OUTDIR = Path("ressources/temp/tune_runs")
OUTDIR.mkdir(parents=True, exist_ok=True)

N_TRIALS = 40
PATIENCE = 10
SEED     = 1337
random.seed(SEED)

# Prefer the param-tuned splitter (no top-level matplotlib)
CANDIDATES = [
    "src/audio/audio_splitter_param_tuned.py",
    "audio_splitter_param_tuned.py",
    "src/audio/AudioSplitter_v1.py",
]
for cand in CANDIDATES:
    _p = Path(cand)
    if _p.exists():
        SPLITTER_FILE = str(_p.resolve())
        break
else:
    raise FileNotFoundError(f"Couldn't find splitter at any of: {CANDIDATES}")

# ── Search space ─────────────────────────────────────────────────────────────
def sample_params():
    return {
        "f0_fmin": random.uniform(260, 360),
        "f0_fmax": random.uniform(850, 1050),
        "f0_frame_len": random.choice([4096, 8192]),
        "comb_harmonics": random.choice([14, 16, 18, 20]),
        "comb_bw_cents": random.uniform(35.0, 70.0),
        "vprob_lo": random.uniform(0.35, 0.5),
        "vprob_hi": random.uniform(0.55, 0.7),
        "comb_hit_mid": random.uniform(0.18, 0.28),
        "comb_hit_lo": random.uniform(0.08, 0.16),
        "tr_hp1_mul": random.uniform(0.85, 1.05),
        "tr_hp1_min": random.uniform(1000.0, 1400.0),
        "tr_hp2_gap": random.uniform(220.0, 320.0),
        "tr_hp2_mul": random.uniform(1.30, 1.50),
        "tr_lp2_mul": random.uniform(0.80, 0.95),
        "tr_lp2_min": random.uniform(4200.0, 5200.0),
        "tr_lp1_gap": random.uniform(180.0, 280.0),
        "tr_lp1_mul": random.uniform(0.55, 0.70),
        "anti_alpha1": random.uniform(0.94, 0.99),
        "anti_min1": random.uniform(0.04, 0.08),
        "anti_alpha2": random.uniform(0.95, 0.995),
        "anti_min2": random.uniform(0.04, 0.08),
        "wiener_gamma1": random.uniform(3.5, 4.8),
        "wiener_gamma2": random.uniform(1.8, 2.8),
        "score_t_comb_gain1": random.uniform(1.30, 1.70),
        "score_t_comb_gain2": random.uniform(1.30, 1.75),
        "score_t_base": random.uniform(0.04, 0.09),
        "lam1": random.uniform(0.25, 0.40),
        "lam2": random.uniform(0.18, 0.35),
        "sc_floor1": random.uniform(0.010, 0.030),
        "sc_floor2": random.uniform(0.010, 0.025),
        "tr_hi_k": random.uniform(900.0, 1500.0),
        "pi_lo_gain": random.uniform(0.3, 0.7),
        "tr_hi_gain": random.uniform(0.4, 0.8),
        "aggressiveness": random.uniform(0.6, 0.9),
        # non-model sweep keys
        "_n_fft": random.choice([2048, 4096]),
        "_hop": None,
        "_expand_piano": random.choice([True, False]),
    }

# ── Split/eval/oracle ────────────────────────────────────────────────────────
def run_split(tag, params):
    n_fft = params.pop("_n_fft")
    hop = params["_hop"] or n_fft // 4
    expand_piano = False

    op = OUTDIR / f"piano_{tag}.wav"
    ot = OUTDIR / f"trpt_{tag}.wav"

    runner = OUTDIR / f"run_{tag}.py"
    code = f"""
import importlib.util, sys, os, json
SPLITTER_FILE = r\"\"\"{SPLITTER_FILE}\"\"\"
spec = importlib.util.spec_from_file_location("splitmod", SPLITTER_FILE)
mod  = importlib.util.module_from_spec(spec)
sys.modules[spec.name] = mod   # ensure @dataclass doesn't crash
spec.loader.exec_module(mod)

os.environ.setdefault("MPLBACKEND", "Agg")
p = mod.Params(**{json.dumps({k:v for k,v in params.items() if not k.startswith("_")})})

p.score_t_comb_gain1 = 0.0
p.score_t_comb_gain2 = 0.0

mod.AudioSplit(
    r"{MIX}", r"{op}", r"{ot}",
    sr=22050,                   # faster for tuning
    n_fft={n_fft}, hop_length={hop},
    params=p, debug_dir=None, expand_piano={str(expand_piano)},
    enable_plots=False
)
"""
    runner.write_text(code, encoding="utf-8")
    env = os.environ.copy()
    env["MPLBACKEND"] = "Agg"
    env["NO_COLOR"] = env.get("NO_COLOR", "1")
    subprocess.check_call([PY, str(runner)], env=env)
    return op, ot

def parse_eval(text):
    vals = {"piano": None, "trpt": None, "mean": None}
    for l in text.splitlines():
        s = l.strip()
        if s.startswith("Piano"):
            vals["piano"] = float(s.split("|")[1])
        elif s.startswith("Trpt"):
            vals["trpt"] = float(s.split("|")[1])
        elif s.startswith("Mean SI-SDR"):
            vals["mean"] = float(s.split(":")[1].replace("dB", ""))
    return vals

def eval_pair(op, ot):
    cmd = [PY, EVAL, "--ref-piano", RP, "--ref-trumpet", RT,
           "--est-piano", str(op), "--est-trumpet", str(ot)]
    res = subprocess.run(cmd, capture_output=True, text=True, check=True)
    return parse_eval(res.stdout), res.stdout

def objective(vals):
    # higher is better
    piano = vals["piano"] if vals["piano"] is not None else -999.0
    trpt  = vals["trpt"]  if vals["trpt"]  is not None else -999.0
    mean  = vals["mean"]  if vals["mean"]  is not None else -999.0
    penalty = 0.0 if piano >= 2.0 else (2.0 - piano)
    return 1.8*trpt + 1.0*mean - 0.8*penalty

# ── Main loop with readable output ───────────────────────────────────────────
def print_header():
    print(c_bld(f"\nParameter Tuning on {c_cy(MIX)}  →  splitter: {c_cy(Path(SPLITTER_FILE).name)}"))
    print(c_dim(f"Trials={N_TRIALS}, Patience={PATIENCE}, Seed={SEED}"))
    print(c_bld("─" * 78))
    print(c_bld(f"{'Trial':>5}  {'Prog':<26}  {'Score':>8}  {'ΔBest':>7}  "
                f"{'Piano dB':>8}  {'Trpt dB':>8}  {'Mean dB':>8}  {'t(s)':>5}"))
    print(c_dim("Note: higher Score & SI-SDR are better; progress bar ~ trials completed."))


def print_trial(i, start_time, score, best_score, vals):
    elapsed = time.time() - start_time
    p = (i) / max(1, N_TRIALS)
    delta = (score - best_score) if best_score is not None else 0.0
    dcol = c_ok(f"{delta:+.2f}") if delta > 1e-9 else c_bad(f"{delta:+.2f}") if delta < -1e-9 else c_dim(f"{delta:+.2f}")
    scol = c_ok(f"{score:8.2f}") if (best_score is None or score >= best_score) else f"{score:8.2f}"
    pc = vals['piano']; tc = vals['trpt']; mc = vals['mean']
    pc_str = f"{pc:8.2f}" if pc is not None else c_dim(f"{'n/a':>8}")
    tc_str = f"{tc:8.2f}" if tc is not None else c_dim(f"{'n/a':>8}")
    mc_str = f"{mc:8.2f}" if mc is not None else c_dim(f"{'n/a':>8}")
    print(f"{i:5d}  {c_bld(bar(p))}  {scol}  {dcol}  {pc_str}  {tc_str}  {mc_str}  {elapsed:5.1f}")

def print_top5(history):
    print(c_blu("\nTop-5 so far:"))
    print(c_bld
(f"{'Rank':>4}  {'Score':>8}  {'Piano dB':>8}  {'Trpt dB':>8}  {'Mean dB':>8}  {'Tag':>8}"))
    for r, (sc, tag, vals) in enumerate(history[:5], start=1):
        print(f"{r:4d}  {sc:8.2f}  {vals['piano']:8.2f}  {vals['trpt']:8.2f}  {vals['mean']:8.2f}  {tag:>8}")

def main():
    best = None  # (score, params, vals, tag)
    history_sorted = []  # [(score, tag, vals), ...]
    no_improve = 0
    start_all = time.time()

    print_header()

    for i in range(1, N_TRIALS + 1):
        params = sample_params()
        params["_hop"] = params["_n_fft"] // 4
        tag = f"t{i:03d}"

        t0 = time.time()
        try:
            op, ot = run_split(tag, params.copy())
            vals, out = eval_pair(op, ot)
            score = objective(vals)

            # Update best & artifacts
            improved = (best is None) or (score > best[0])
            if improved:
                best = (score, params, vals, tag)
                no_improve = 0
                (OUTDIR / "best_params.json").write_text(json.dumps(best[1], indent=2), encoding="utf-8")
                (OUTDIR / "best_eval.txt").write_text(out, encoding="utf-8")
            else:
                no_improve += 1

            # Keep sorted top list
            history_sorted.append((score, tag, vals))
            history_sorted.sort(key=lambda x: x[0], reverse=True)

            # Console line
            print_trial(i, t0, score, best[0] if best else None, vals)

            # Every 5 trials, show snapshot
            if i % 5 == 0:
                print_top5(history_sorted)

            # Early stop condition
            if no_improve >= PATIENCE:
                print(c_war(f"\nEarly stop at trial {i} (no improvement in {PATIENCE} trials)."))
                break

        except subprocess.CalledProcessError as e:
            print(c_bad(f"{tag} ERROR (subprocess): {e}"))
            no_improve += 1
        except Exception as e:
            print(c_bad(f"{tag} ERROR: {e}"))
            no_improve += 1

    if best:
        print(c_bld("\n=== BEST RESULT ==="))
        print(f"Tag: {c_mg(best[3])}")
        print(f"Score: {c_ok(f'{best[0]:.2f}')}")
        print(f"Piano SI-SDR: {best[2]['piano']:.2f} dB,  Trpt SI-SDR: {best[2]['trpt']:.2f} dB,  Mean: {best[2]['mean']:.2f} dB")
        print(f"Saved: {c_cy
(str(OUTDIR / 'best_params.json'))}  &  {c_cy
(str(OUTDIR / 'best_eval.txt'))}")
    print(c_dim
(f"Total time: {time.time() - start_all:.1f}s"))

if __name__ == "__main__":
    main()
