#!/usr/bin/env python3
"""
jitter_vs_snr.py — зависимость остаточного джиттера от SNR (shared-clock).

Берёт набор shared-записей, снятых при разных уровнях сигнала (аттенюатор /
ослабленная связь), измеряет джиттер и SNR каждой и строит jitter vs SNR.
Контекстует floor и подтверждает заявление про выигрыш в effective SNR.

Соглашение: записи лежат как обычно (raw_iq/<cond>_run<NN>_{ch0,ch1}.iq + .json).
По умолчанию берёт все 'shared*'. Можно указать любой префикс через --prefix.

Вывод:
  results/jitter_vs_snr.csv
  results/jitter_vs_snr.png

Запуск:
  python3 jitter_vs_snr.py --raw ../raw_iq --out ../results --win-ms 100 --prefix shared

Лицензия: MIT.
"""

import argparse
import csv
import glob
import json
import os

import numpy as np

import coherence_lib as cl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--raw", default="../raw_iq")
    ap.add_argument("--out", default="../results")
    ap.add_argument("--win-ms", type=float, default=100.0)
    ap.add_argument("--prefix", default="shared",
                    help="префикс записей для анализа (shared / snr / …)")
    args = ap.parse_args()

    jsons = sorted(glob.glob(os.path.join(args.raw, f"{args.prefix}*run*.json")))
    if not jsons:
        raise SystemExit(f"Нет записей {args.prefix}*run*.json в {args.raw}")

    rows = []
    for jp in jsons:
        base = jp[:-5]
        fa, fb = base + "_ch0.iq", base + "_ch1.iq"
        if not (os.path.exists(fa) and os.path.exists(fb)):
            continue
        with open(jp) as f:
            meta = json.load(f)
        fs = float(meta.get("sps", 2_400_000))
        m, _ = cl.analyze_record(fa, fb, fs, win_ms=args.win_ms)
        rows.append({
            "record": os.path.basename(base),
            "snr_db": round(m["snr_db"], 2),
            "jitter_meas_deg": round(m["jitter_deg_std"], 4),
        })
        print(f"  {os.path.basename(base):20s}  SNR={m['snr_db']:6.1f} дБ  "
              f"jitter={m['jitter_deg_std']:.4f}°")

    if not rows:
        raise SystemExit("Не нашёл ни одной полной записи (ch0+ch1).")

    # опорная CRB-линия как функция SNR: σ ∝ 10^(-SNR/20). Калибруем 1 параметр C.
    import numpy as np
    logC = np.mean([np.log10(r["jitter_meas_deg"]) + r["snr_db"] / 20.0
                    for r in rows if r["jitter_meas_deg"] > 0])
    for r in rows:
        r["jitter_crb_ref_deg"] = round(float(10 ** (logC - r["snr_db"] / 20.0)), 4)

    rows.sort(key=lambda r: r["snr_db"])
    os.makedirs(args.out, exist_ok=True)
    csv_p = os.path.join(args.out, "jitter_vs_snr.csv")
    with open(csv_p, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        w.writeheader()
        w.writerows(rows)
    print(f"→ {csv_p}")

    _plot(rows, args.win_ms, args.out)


def _plot(rows, win_ms, out):
    try:
        import matplotlib
        matplotlib.use("Agg")
        import matplotlib.pyplot as plt
    except ImportError:
        print("(matplotlib не установлен — график пропущен)")
        return
    snr = [r["snr_db"] for r in rows]
    jm = [r["jitter_meas_deg"] for r in rows]
    jt = [r["jitter_crb_ref_deg"] for r in rows]
    fig, ax = plt.subplots(figsize=(6, 4.2))
    ax.semilogy(snr, jm, "o-", label="Измерено", color="#1f77b4")
    ax.semilogy(snr, jt, "--", label="CRB-тренд ∝ 10^(−SNR/20)", color="#d62728")
    ax.set_xlabel("SNR, дБ")
    ax.set_ylabel("Остаточный джиттер фазы, °")
    ax.set_title(f"Джиттер vs SNR (shared clock, окно {win_ms:.0f} мс)")
    ax.grid(True, which="both", alpha=0.3)
    ax.legend()
    fig.tight_layout()
    png = os.path.join(out, "jitter_vs_snr.png")
    fig.savefig(png, dpi=200)
    print(f"→ {png}")


if __name__ == "__main__":
    main()
