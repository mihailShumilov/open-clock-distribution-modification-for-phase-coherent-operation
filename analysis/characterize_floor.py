#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
characterize_floor.py — шумовой порог замера на одной (чистой) записи:
jitter vs окно интегрирования (должен падать ∝1/√N → полка = floor).

  python3 characterize_floor.py --rec ../raw_iq/shared_run04 [--wins 2,5,10,20,50,100,200]

Печатает таблицу + наклон log-log; при наличии matplotlib сохраняет PNG. MIT.
"""
import argparse, os
import numpy as np
import coherence_lib as cl

p = argparse.ArgumentParser()
p.add_argument("--rec", required=True, help="префикс без _ch0.iq")
p.add_argument("--sps", type=float, default=2.4e6)
p.add_argument("--wins", default="2,5,10,20,50,100,200")
p.add_argument("--out", default="../results")
a = p.parse_args()

fa, fb = a.rec + "_ch0.iq", a.rec + "_ch1.iq"
wins = [float(x) for x in a.wins.split(",")]
W, N, J = cl.floor_sweep(fa, fb, a.sps, wins)
print(f"{'win_ms':>7}{'N':>9}{'jitter°':>11}")
for w, n, j in zip(W, N, J):
    print(f"{w:7.0f}{n:9d}{j:11.4f}")
ok = J > 1e-6
slope = np.polyfit(np.log10(N[ok]), np.log10(J[ok]), 1)[0]
print(f"\nнаклон log-log = {slope:.3f} (CRB ждёт -0.5)")
print(f"шумовой пол ≈ {J[ok].min():.4f}° при {W[ok][int(np.argmin(J[ok]))]:.0f}мс")

try:
    import matplotlib; matplotlib.use("Agg"); import matplotlib.pyplot as plt
    os.makedirs(a.out, exist_ok=True)
    tag = os.path.basename(a.rec)
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.loglog(W[ok], J[ok], "o-", color="#1f77b4", label=f"измерено (наклон {slope:.2f})")
    ref = J[ok][0] * np.sqrt(N[ok][0] / N[ok])
    ax.loglog(W[ok], ref, "--", color="#888", label="∝ 1/√N (наклон −0.5)")
    ax.set_xlabel("окно интегрирования, мс"); ax.set_ylabel("остаточный джиттер, °")
    ax.set_title(f"Шумовой порог ({tag})"); ax.grid(True, which="both", alpha=0.3); ax.legend()
    fig.tight_layout(); fig.savefig(f"{a.out}/floor_{tag}.png", dpi=200)
    print(f"→ {a.out}/floor_{tag}.png")
except ImportError:
    pass
