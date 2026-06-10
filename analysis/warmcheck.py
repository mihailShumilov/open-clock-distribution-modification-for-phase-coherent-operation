#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""warmcheck.py — быстрый bench-чек: записать короткую пару (оба dev) и
сразу посчитать бит/джиттер. Удобно для прогрева и проверки общего клока.

  python3 warmcheck.py [--secs 8 --gain 32.8 --freq 99.8e6]
"""
import argparse, os, subprocess, datetime, tempfile
import coherence_lib as cl
p = argparse.ArgumentParser()
p.add_argument("--secs", type=float, default=8.0); p.add_argument("--gain", type=float, default=32.8)
p.add_argument("--freq", type=float, default=99.8e6); p.add_argument("--sps", type=float, default=2.4e6)
g = p.parse_args()
d = tempfile.mkdtemp(); fa, fb = d + "/a.iq", d + "/b.iq"; n = int(g.sps * g.secs)
base = ["rtl_sdr", "-f", str(int(g.freq)), "-s", str(int(g.sps)), "-g", str(g.gain), "-n", str(n)]
A = subprocess.Popen(base + ["-d", "0", fa], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
B = subprocess.Popen(base + ["-d", "1", fb], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
A.wait(); B.wait()
m = cl.analyze_pair(fa, fb, g.sps)
print(f"{datetime.datetime.now():%H:%M:%S}  бит={m['beat_hz']:+.1f}Гц  "
      f"разброс±{m['beat_wander_hz']:.1f}Гц  jitter={m['jitter_deg']:.3f}°")
os.remove(fa); os.remove(fb); os.rmdir(d)
