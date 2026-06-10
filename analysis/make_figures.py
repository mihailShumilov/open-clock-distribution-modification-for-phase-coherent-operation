#!/usr/bin/env python3
"""
make_figures.py — публикационные фигуры Статьи 1 (HardwareX).

Читает сохранённые фазовые массивы results/phases/*.npy (из batch_analyze.py) и
results/*_metrics.csv, строит:

  fig1_phase_timeseries.png — φ_AB(t) одной baseline и одной shared записи
                              (наглядно: ~13.6° разброс против полки).
  fig2_jitter_by_condition.png — джиттер по всем прогонам, baseline vs shared
                                 (strip + mean±σ); ось log.

Запуск:
  python3 make_figures.py --out ../results [--win-ms 100]

Лицензия: MIT.
"""

import argparse
import csv
import glob
import os

import numpy as np


def _mpl():
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    return plt


def load_phase(out, cond, run=None):
    """Загрузить фазовый .npy (град). Если run=None — первый по порядку."""
    pat = os.path.join(out, "phases", f"{cond}_run*.npy")
    files = sorted(glob.glob(pat))
    if not files:
        return None, None
    if run is not None:
        want = os.path.join(out, "phases", f"{cond}_run{run}.npy")
        files = [want] if want in files else files
    f = files[0]
    return np.degrees(np.load(f)), os.path.basename(f).replace(".npy", "")


def fig_timeseries(out, win_ms):
    plt = _mpl()
    fig, ax = plt.subplots(figsize=(6.5, 4.2))
    dt = win_ms / 1000.0
    plotted = False
    for cond, color in (("baseline", "#d62728"), ("shared", "#1f77b4")):
        ph, tag = load_phase(out, cond)
        if ph is None:
            continue
        ph = ph - np.mean(ph)  # убрать константный offset для наглядности
        t = np.arange(len(ph)) * dt
        ax.plot(t, ph, color=color, lw=1.0,
                label=f"{cond} (σ={ph.std(ddof=1):.2f}°)")
        plotted = True
    if not plotted:
        print("(нет фазовых массивов — fig1 пропущена)")
        return
    ax.set_xlabel("Время, с")
    ax.set_ylabel("Межканальная фаза φ_AB, ° (offset убран)")
    ax.set_title("Фазовая когерентность пары RTL-SDR: до/после общего клока")
    ax.grid(True, alpha=0.3)
    ax.legend()
    fig.tight_layout()
    p = os.path.join(out, "fig1_phase_timeseries.png")
    fig.savefig(p, dpi=200)
    print(f"→ {p}")


def fig_jitter_by_condition(out):
    plt = _mpl()
    data = {}
    for fp in sorted(glob.glob(os.path.join(out, "*_metrics.csv"))):
        if fp.endswith("measurement_log.csv"):
            continue
        cond = os.path.basename(fp).replace("_metrics.csv", "")
        with open(fp) as f:
            vals = [float(r["jitter_deg_std"]) for r in csv.DictReader(f)
                    if r.get("jitter_deg_std")]
        if vals:
            data[cond] = vals
    if not data:
        print("(нет *_metrics.csv — fig2 пропущена)")
        return
    order = sorted(data, key=lambda c: (0 if c == "baseline" else
                                        1 if c == "shared" else 2, c))
    fig, ax = plt.subplots(figsize=(5.5, 4.2))
    for i, cond in enumerate(order):
        vals = np.array(data[cond])
        x = np.full(len(vals), i) + np.random.uniform(-0.07, 0.07, len(vals))
        ax.scatter(x, vals, s=28, alpha=0.7, zorder=3,
                   color="#d62728" if cond == "baseline" else "#1f77b4")
        m, sd = vals.mean(), vals.std(ddof=1) if len(vals) > 1 else 0
        ax.errorbar(i, m, yerr=sd, fmt="_", color="k", capsize=6,
                    markersize=22, lw=1.5, zorder=4)
        ax.annotate(f"{m:.2f}±{sd:.2f}°", (i, m), textcoords="offset points",
                    xytext=(14, 0), va="center", fontsize=9)
    ax.set_yscale("log")
    ax.set_xticks(range(len(order)))
    ax.set_xticklabels([f"{c}\n(n={len(data[c])})" for c in order])
    ax.set_ylabel("Residual jitter, ° (log)")
    ax.set_title("Остаточный джиттер по прогонам")
    ax.grid(True, axis="y", which="both", alpha=0.3)
    fig.tight_layout()
    p = os.path.join(out, "fig2_jitter_by_condition.png")
    fig.savefig(p, dpi=200)
    print(f"→ {p}")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../results")
    ap.add_argument("--win-ms", type=float, default=100.0)
    args = ap.parse_args()
    try:
        import matplotlib  # noqa
    except ImportError:
        raise SystemExit("matplotlib не установлен: pip install matplotlib")
    fig_timeseries(args.out, args.win_ms)
    fig_jitter_by_condition(args.out)


if __name__ == "__main__":
    main()
