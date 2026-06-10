#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
batch_analyze.py — прогон beat-tracked анализа по всем записям состояния,
с авто-исключением засорённых (FM/USB-дроп) записей, и сводной статистикой.

  python3 batch_analyze.py --raw ../raw_iq --condition baseline
  python3 batch_analyze.py --raw ../raw_iq --condition shared

Соглашение имён: <condition>_run<NN>_{ch0,ch1}.iq (+ .json опц.).
Метод — см. coherence_lib.analyze_pair (поблочный трекинг бита). Лицензия: MIT.
"""
import argparse, glob, json, os
import numpy as np
import coherence_lib as cl

p = argparse.ArgumentParser()
p.add_argument("--raw", default="../raw_iq")
p.add_argument("--condition", required=True)
p.add_argument("--sps", type=float, default=2.4e6)
p.add_argument("--win-ms", type=float, default=100.0)
p.add_argument("--block-ms", type=float, default=500.0)
a = p.parse_args()

jsons = sorted(glob.glob(f"{a.raw}/{a.condition}_run*.json")) or \
        sorted(glob.glob(f"{a.raw}/{a.condition}_run*_ch0.iq"))
records = []
for j in jsons:
    base = j[:-5] if j.endswith(".json") else j[:-8]
    fa, fb = base + "_ch0.iq", base + "_ch1.iq"
    if os.path.exists(fa) and os.path.exists(fb):
        records.append((os.path.basename(base), fa, fb))

good, bad = [], []
for name, fa, fb in records:
    m = cl.analyze_pair(fa, fb, a.sps, a.win_ms, a.block_ms)
    snr = cl.estimate_snr_db(fa, a.sps)
    run = name.split("_run")[-1]
    if cl.is_contaminated(m["beat_hz"], m["beat_wander_hz"]):
        bad.append((run, m, snr))
        print(f"  run{run}: EXCLUDED (contaminated) jitter={m['jitter_deg']:.3f}° "
              f"beat={m['beat_hz']/1e3:.0f}кГц wander={m['beat_wander_hz']:.0f}Гц")
    else:
        good.append((run, m, snr))
        print(f"  run{run}: jitter={m['jitter_deg']:.3f}°  beat={m['beat_hz']:+.1f}±"
              f"{m['beat_wander_hz']:.1f}Гц  SNR={snr:.1f}дБ")

if good:
    J = [g[1]["jitter_deg"] for g in good]
    st = cl.summarize(J)
    out = f"{a.raw}/{a.condition}_metrics.csv"
    with open(out, "w") as f:
        f.write("run,jitter_deg,beat_hz,beat_wander_hz,snr_db\n")
        for run, m, snr in good:
            f.write(f"{run},{m['jitter_deg']:.4f},{m['beat_hz']:.2f},"
                    f"{m['beat_wander_hz']:.2f},{snr:.2f}\n")
    print(f"\n{a.condition}: clean n={st['n']} (excluded {len(bad)})")
    print(f"  jitter = {st['mean']:.3f} ± {st['std']:.3f}° (σ), 95% CI ±{st['ci95']:.3f}°")
    print(f"→ {out}")
else:
    print("Нет чистых записей.")
