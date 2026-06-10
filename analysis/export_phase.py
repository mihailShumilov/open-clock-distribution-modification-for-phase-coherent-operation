#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""export_phase.py — выгрузить оконную межканальную фазу φ_AB(t) одной записи
(бит снят, ~300 точек) в маленький CSV для построения временных рядов/ADEV.

  python3 export_phase.py --rec ../raw_iq/shared_run04 [--win-ms 100]
"""
import argparse, os
import numpy as np
import coherence_lib as cl
p = argparse.ArgumentParser()
p.add_argument("--rec", required=True); p.add_argument("--sps", type=float, default=2.4e6)
p.add_argument("--win-ms", type=float, default=100.0); p.add_argument("--out", default=".")
g = p.parse_args()
fa, fb = g.rec + "_ch0.iq", g.rec + "_ch1.iq"; fs = g.sps
beat = cl.estimate_beat(fa, fb, fs)
N = min(cl.iq_num_samples(fa), cl.iq_num_samples(fb)); nwin = int(fs * g.win_ms / 1000); nw = N // nwin
ph = np.empty(nw)
for w in range(nw):
    s = w * nwin
    a = cl.load_iq_chunk(fa, s, nwin); b = cl.load_iq_chunk(fb, s, nwin)
    a -= a.mean(); b -= b.mean()
    t = (s + np.arange(nwin)) / fs
    ph[w] = np.angle((a * np.conj(b) * np.exp(-2j * np.pi * beat * t)).mean())
deg = np.degrees(np.unwrap(ph)); deg -= deg.mean()
out = os.path.join(g.out, os.path.basename(g.rec) + "_phase.csv")
np.savetxt(out, np.column_stack([np.arange(nw) * g.win_ms / 1000, deg]),
           delimiter=",", header="time_s,phase_deg", comments="")
print(f"→ {out}  ({nw} точек, бит снят {beat:+.1f} Гц, std={deg.std():.3f}°)")
