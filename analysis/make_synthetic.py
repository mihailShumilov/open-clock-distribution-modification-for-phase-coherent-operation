#!/usr/bin/env python3
"""
make_synthetic.py — синтетические IQ-пары с ИЗВЕСТНЫМИ drift/jitter/SNR.

Нужен для (а) самопроверки пайплайна без железа, (б) валидации, что
batch_analyze/characterize_floor восстанавливают заложенные параметры.

Модель: общий CW s(t)=exp(j2π·f_off·t) приходит на оба канала (фаза источника
сокращается). Канал A получает добавочную межканальную фазу
   φ_A(t) = drift·t + offset + jitter_step(t),
канал B — нулевую. jitter_step — кусочно-постоянная (на окне win_ms) случайная
добавка со std = --jitter градусов (имитирует рассинхрон клоков). Плюс
комплексный белый шум на оба канала под заданный per-sample SNR.

Пишет uint8 I/Q (формат rtl_sdr) + .json. Имена как в кампании.

Пример:
  python3 make_synthetic.py --out ../raw_iq --tag shared_run01 \
      --drift 0.02 --jitter 0.08 --snr-db 40 --len 5
  python3 make_synthetic.py --out ../raw_iq --tag baseline_run01 \
      --drift 0.02 --jitter 13.6 --snr-db 40 --len 5

Лицензия: MIT.
"""

import argparse
import json
import os

import numpy as np


def write_iq_uint8(path, z, amplitude=40.0):
    """Записать complex массив как uint8 I/Q (offset 127.5), с клиппингом."""
    i = np.clip(np.round(z.real * amplitude + 127.5), 0, 255).astype(np.uint8)
    q = np.clip(np.round(z.imag * amplitude + 127.5), 0, 255).astype(np.uint8)
    inter = np.empty(2 * len(z), dtype=np.uint8)
    inter[0::2] = i
    inter[1::2] = q
    inter.tofile(path)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out", default="../raw_iq")
    ap.add_argument("--tag", required=True, help="напр. shared_run01")
    ap.add_argument("--drift", type=float, default=0.02, help="°/с (истинный)")
    ap.add_argument("--jitter", type=float, default=0.08, help="° per-window (истинный)")
    ap.add_argument("--offset", type=float, default=5.9, help="° константный")
    ap.add_argument("--snr-db", type=float, default=40.0, help="per-sample SNR, дБ")
    ap.add_argument("--freq-offset", type=float, default=200e3, help="CW от центра, Гц")
    ap.add_argument("--sps", type=float, default=2.4e6)
    ap.add_argument("--len", type=float, default=5.0, help="секунд")
    ap.add_argument("--win-ms", type=float, default=100.0, help="шаг jitter_step")
    ap.add_argument("--seed", type=int, default=None)
    args = ap.parse_args()

    rng = np.random.default_rng(args.seed)
    fs = args.sps
    n = int(fs * args.len)
    t = np.arange(n) / fs

    # межканальная фаза A относительно B
    win_n = int(fs * args.win_ms / 1000.0)
    n_win = n // win_n + 1
    steps = np.radians(args.jitter) * rng.standard_normal(n_win)
    jitter_per_sample = np.repeat(steps, win_n)[:n]
    phi_a = (np.radians(args.drift) * t
             + np.radians(args.offset)
             + jitter_per_sample)

    carrier = np.exp(2j * np.pi * args.freq_offset * t)
    a = carrier * np.exp(1j * phi_a)
    b = carrier.copy()

    # шум под per-sample SNR: signal power = 1 → noise var = 10^(-snr/10)
    nvar = 10.0 ** (-args.snr_db / 10.0)
    sigma = np.sqrt(nvar / 2.0)
    a = a + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))
    b = b + sigma * (rng.standard_normal(n) + 1j * rng.standard_normal(n))

    os.makedirs(args.out, exist_ok=True)
    write_iq_uint8(os.path.join(args.out, args.tag + "_ch0.iq"), a)
    write_iq_uint8(os.path.join(args.out, args.tag + "_ch1.iq"), b)

    cond = args.tag.split("_run")[0]
    meta = {
        "timestamp": "SYNTHETIC",
        "condition": cond,
        "run": args.tag.split("_run")[-1] if "_run" in args.tag else "00",
        "freq_MHz": 100.0,
        "tx_source": "synthetic CW",
        "stick_A_SN": "SYN-A",
        "stick_B_SN": "SYN-B",
        "gain": 29.7,
        "sps": int(fs),
        "len_s": args.len,
        "board_temp_C": None,
        "synthetic_truth": {
            "drift_deg_per_s": args.drift,
            "jitter_deg": args.jitter,
            "offset_deg": args.offset,
            "snr_db_per_sample": args.snr_db,
            "freq_offset_hz": args.freq_offset,
        },
        "notes": "synthetic",
    }
    with open(os.path.join(args.out, args.tag + ".json"), "w") as f:
        json.dump(meta, f, ensure_ascii=False, indent=2)
    print(f"написано {args.tag}: drift={args.drift}°/с jitter={args.jitter}° "
          f"SNR={args.snr_db}дБ len={args.len}с")


if __name__ == "__main__":
    main()
