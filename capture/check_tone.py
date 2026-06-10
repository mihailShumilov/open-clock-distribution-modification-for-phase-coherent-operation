#!/usr/bin/env python3
"""
check_tone.py — быстрая проверка одного выхода Si5351 на одном стике.

Снимает короткую IQ-запись с ОДНОГО устройства и печатает: найден ли CW-пик,
на каком смещении от центра, спектральный SNR и railed-% (клиппинг). Нужен для
sanity ДО сборки двойной цепи и серии замеров.

Запуск (CLK0 → стик на dev 0):
  python3 check_tone.py --dev 0 --freq 99.8e6 --gain 7.7
  python3 check_tone.py --dev 1 --freq 99.8e6 --gain 7.7   # потом CLK1 → второй стик

Норма: пик на ~+200 кГц (если CW=100.0, центр=99.8), SNR десятки дБ, railed < 0.5%.

Лицензия: MIT.
"""

import argparse
import os
import subprocess
import sys
import tempfile

import numpy as np

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "analysis"))
import coherence_lib as cl


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--dev", type=int, default=0)
    ap.add_argument("--freq", type=float, default=99.8e6)
    ap.add_argument("--gain", type=float, default=7.7)
    ap.add_argument("--sps", type=float, default=2.4e6)
    ap.add_argument("--secs", type=float, default=0.5)
    args = ap.parse_args()

    n = int(args.sps * args.secs)
    tmp = tempfile.mktemp(suffix=".iq")
    cmd = ["rtl_sdr", "-d", str(args.dev), "-f", str(int(args.freq)),
           "-s", str(int(args.sps)), "-g", str(args.gain), "-n", str(n), tmp]
    print(f"Запись {args.secs}с с dev {args.dev} @ {args.freq/1e6:.3f} МГц, gain {args.gain}…")
    r = subprocess.run(cmd, stderr=subprocess.PIPE)
    if r.returncode != 0 or not os.path.exists(tmp):
        print("rtl_sdr ошибка:\n", r.stderr.decode(errors="ignore"))
        sys.exit(1)

    raw = np.fromfile(tmp, dtype=np.uint8)
    railed = 100.0 * np.mean((raw == 0) | (raw == 255))
    f_off = cl.find_cw_offset(tmp, args.sps)
    snr = cl.estimate_snr_db(tmp, args.sps, f_off)
    os.remove(tmp)

    print(f"\n  CW-пик:   {f_off/1e3:+.1f} кГц от центра  "
          f"({(args.freq+f_off)/1e6:.4f} МГц абсолютно)")
    print(f"  SNR:      {snr:.1f} дБ (спектральный)")
    print(f"  railed-%: {railed:.3f}  (клиппинг; норма < 0.5)")
    verdict = []
    if abs(f_off) < 20_000:
        verdict.append("⚠ пик у DC — сдвинь CW дальше от центра или проверь, что тон есть")
    if snr < 15:
        verdict.append("⚠ слабый сигнал — подними gain или проверь кабель/разъём CLK")
    if railed > 0.5:
        verdict.append("⚠ клиппинг — снизь gain или добавь аттенюатор")
    if not verdict:
        verdict.append("✓ тон есть, уровень нормальный — этот выход годится")
    print("  " + "\n  ".join(verdict))


if __name__ == "__main__":
    main()
