#!/usr/bin/env python3
"""
aggregate_table.py — собрать итоговую таблицу Статьи 1 (mean±σ, 95% CI).

Читает results/<condition>_metrics.csv (из batch_analyze.py), считает по каждому
состоянию среднее, σ и 95% доверительный интервал для drift и jitter, выводит:
  results/article_table.md   — таблица в формате статьи (markdown)
  results/article_table.csv   — то же машиночитаемо
  + печатает в консоль улучшение (baseline/shared) с распространением погрешности.

Запуск:
  python3 aggregate_table.py --out ../results

Лицензия: MIT.
"""

import argparse
import csv
import glob
import os

import coherence_lib as cl


def read_metrics(path):
    with open(path) as f:
        return list(csv.DictReader(f))


def col(rows, name):
    out = []
    for r in rows:
        try:
            out.append(float(r[name]))
        except (ValueError, KeyError):
            pass
    return out


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../results")
    args = ap.parse_args()

    files = sorted(glob.glob(os.path.join(args.out, "*_metrics.csv")))
    files = [f for f in files if not f.endswith("measurement_log.csv")]
    if not files:
        raise SystemExit(f"Нет *_metrics.csv в {args.out}. Сначала batch_analyze.py.")

    summary = {}
    order = []
    for fp in files:
        cond = os.path.basename(fp).replace("_metrics.csv", "")
        rows = read_metrics(fp)
        drift = cl.summarize(col(rows, "drift_deg_per_s"))
        jitter = cl.summarize(col(rows, "jitter_deg_std"))
        snr = cl.summarize(col(rows, "snr_db"))
        summary[cond] = {"drift": drift, "jitter": jitter, "snr": snr,
                         "n": jitter["n"]}
        order.append(cond)

    # упорядочить: baseline первым, shared вторым
    order.sort(key=lambda c: (0 if c == "baseline" else 1 if c == "shared" else 2, c))

    # ── markdown ──
    lines = []
    lines.append("# Статья 1 — итоговая таблица когерентности\n")
    lines.append("| Состояние | n | Drift, °/с (mean ± σ) | "
                 "Residual jitter, ° (mean ± σ) | 95% CI jitter | SNR, дБ |")
    lines.append("|---|---|---|---|---|---|")
    for cond in order:
        s = summary[cond]
        d, j, sn = s["drift"], s["jitter"], s["snr"]
        lines.append(
            f"| {cond} | {j['n']} | "
            f"{d['mean']:+.4f} ± {d['std']:.4f} | "
            f"{j['mean']:.3f} ± {j['std']:.3f} | "
            f"±{j['ci95']:.3f} | "
            f"{sn['mean']:.1f} ± {sn['std']:.1f} |"
        )
    lines.append("")

    # ── улучшение ──
    if "baseline" in summary and "shared" in summary:
        jb = summary["baseline"]["jitter"]
        js = summary["shared"]["jitter"]
        if js["mean"] > 0:
            factor = jb["mean"] / js["mean"]
            # относительная погрешность фактора ≈ корень суммы квадратов отн. погрешностей
            rb = (jb["std"] / jb["mean"]) if jb["mean"] else 0
            rs = (js["std"] / js["mean"]) if js["mean"] else 0
            rel = (rb ** 2 + rs ** 2) ** 0.5
            lines.append(f"**Улучшение джиттера:** ×{factor:.0f} "
                         f"(±{factor*rel:.0f}, 1σ), "
                         f"baseline {jb['mean']:.2f}° → shared {js['mean']:.3f}°.")
            lines.append("")
            lines.append("> Если shared-джиттер лежит на шумовом полу замера "
                         "(см. floor_*.png), корректная формулировка — "
                         "«≤ floor°», а фактор — нижняя оценка.")

    md = "\n".join(lines) + "\n"
    md_p = os.path.join(args.out, "article_table.md")
    with open(md_p, "w") as f:
        f.write(md)
    print(md)
    print(f"→ {md_p}")

    # ── csv ──
    csv_p = os.path.join(args.out, "article_table.csv")
    with open(csv_p, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["condition", "n",
                    "drift_mean", "drift_std", "drift_ci95",
                    "jitter_mean", "jitter_std", "jitter_ci95",
                    "snr_mean", "snr_std"])
        for cond in order:
            s = summary[cond]
            d, j, sn = s["drift"], s["jitter"], s["snr"]
            w.writerow([cond, j["n"],
                        f"{d['mean']:.5f}", f"{d['std']:.5f}", f"{d['ci95']:.5f}",
                        f"{j['mean']:.4f}", f"{j['std']:.4f}", f"{j['ci95']:.4f}",
                        f"{sn['mean']:.2f}", f"{sn['std']:.2f}"])
    print(f"→ {csv_p}")


if __name__ == "__main__":
    main()
