#!/usr/bin/env python3
"""
record_campaign.py — запись серии парных IQ для A/B когерентности (на Pi).

Пишет n парных записей одного состояния (baseline | shared) на два стика
одновременно через два процесса rtl_sdr. На каждую запись кладёт .json с
метаданными (частота, gain, sps, длина, серийники, температура платы, время).

ВАЖНО — единые условия baseline vs shared:
  частота, gain, sps, длина записи, источник CW, SNR — ОДИНАКОВЫЕ.
  Меняется ровно одно: общий клок (shared) против двух своих TCXO (baseline).

Запуск (пример):
  # baseline на стоковых стиках (dev 0/1, серийники для журнала):
  python3 record_campaign.py --condition baseline --runs 12 \
      --dev-a 0 --dev-b 1 --sn-a 3003 --sn-b 3004 \
      --freq 99.8e6 --gain 29.7 --sps 2.4e6 --len 30 \
      --tx "Si5351 #2 CW 100.0 MHz" --out ../raw_iq

  # shared на модифицированных стиках на общем CLK0:
  python3 record_campaign.py --condition shared --runs 12 \
      --dev-a 0 --dev-b 1 --sn-a 1 --sn-b 2 \
      --freq 99.8e6 --gain 29.7 --sps 2.4e6 --len 30 \
      --tx "Si5351 #2 CW 100.0 MHz" --out ../raw_iq

Замечания:
  * gain: задавать ВАЛИДНОЕ значение R820T2 (…28.0 29.7 32.8…). 0 = AGC! (LESSONS §«gain»)
  * CW не ставить ровно в центр приёмника — сместить ~200 кГц от --freq,
    чтобы несущая не попала в DC-спайк. Анализ сам найдёт пик.
  * между записями скрипт по флагу --replug-every просит реплаг/прогрев,
    чтобы поймать run-to-run разброс.

Лицензия: MIT.
"""

import argparse
import datetime as dt
import json
import os
import shutil
import subprocess
import sys
import time


def board_temp_c():
    """Температура платы Pi через vcgencmd; None если недоступно."""
    exe = shutil.which("vcgencmd")
    if not exe:
        return None
    try:
        out = subprocess.check_output([exe, "measure_temp"], text=True).strip()
        # формат: temp=47.2'C
        return float(out.split("=")[1].split("'")[0])
    except Exception:
        return None


def record_pair(dev_a, dev_b, freq, gain, sps, n_samples, path_a, path_b):
    """Запустить два rtl_sdr параллельно, дождаться завершения обоих."""
    base = ["rtl_sdr", "-f", str(int(freq)), "-s", str(int(sps)),
            "-g", str(gain), "-n", str(int(n_samples))]
    cmd_a = base + ["-d", str(dev_a), path_a]
    cmd_b = base + ["-d", str(dev_b), path_b]
    # запускаем максимально близко по времени
    pa = subprocess.Popen(cmd_a, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    pb = subprocess.Popen(cmd_b, stdout=subprocess.DEVNULL, stderr=subprocess.PIPE)
    ea = pa.communicate()[1]
    eb = pb.communicate()[1]
    if pa.returncode != 0:
        sys.stderr.write(f"rtl_sdr dev {dev_a} код {pa.returncode}:\n{ea.decode(errors='ignore')}\n")
    if pb.returncode != 0:
        sys.stderr.write(f"rtl_sdr dev {dev_b} код {pb.returncode}:\n{eb.decode(errors='ignore')}\n")
    return pa.returncode == 0 and pb.returncode == 0


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", required=True, choices=["baseline", "shared"])
    ap.add_argument("--runs", type=int, default=12)
    ap.add_argument("--dev-a", type=int, default=0)
    ap.add_argument("--dev-b", type=int, default=1)
    ap.add_argument("--sn-a", default="", help="серийник/метка стика A (журнал)")
    ap.add_argument("--sn-b", default="", help="серийник/метка стика B (журнал)")
    ap.add_argument("--freq", type=float, default=99.8e6, help="центр приёмника, Гц")
    ap.add_argument("--gain", type=float, default=29.7, help="валидный gain R820T2")
    ap.add_argument("--sps", type=float, default=2.4e6)
    ap.add_argument("--len", type=float, default=30.0, help="длина записи, с")
    ap.add_argument("--tx", default="", help="описание тест-источника CW")
    ap.add_argument("--out", default="../raw_iq")
    ap.add_argument("--start-run", type=int, default=1,
                    help="с какого номера прогона начинать (для дозаписи)")
    ap.add_argument("--replug-every", type=int, default=4,
                    help="каждые N записей — пауза на реплаг/прогрев (0 = выкл)")
    args = ap.parse_args()

    if args.gain == 0:
        print("ВНИМАНИЕ: gain=0 у R820T2 = AGC! Задай валидный ручной gain "
              "(напр. 29.7). См. LESSONS.")
        sys.exit(1)
    if not shutil.which("rtl_sdr"):
        print("rtl_sdr не найден в PATH. Установи rtl-sdr (apt install rtl-sdr).")
        sys.exit(1)

    os.makedirs(args.out, exist_ok=True)
    n_samples = int(args.sps * args.len)
    bytes_per = n_samples * 2
    print(f"Состояние: {args.condition} | прогонов: {args.runs} | "
          f"{args.len}с @ {args.sps/1e6:.2f} Msps | "
          f"~{bytes_per/1e6:.0f} МБ/канал/запись")
    print(f"Центр {args.freq/1e6:.3f} МГц, gain {args.gain}, "
          f"dev {args.dev_a}/{args.dev_b}, СН {args.sn_a}/{args.sn_b}")
    print("CW-источник должен быть смещён ~200 кГц от центра (не в DC).\n")

    last = args.start_run + args.runs - 1
    for run in range(args.start_run, last + 1):
        tag = f"{args.condition}_run{run:02d}"
        path_a = os.path.join(args.out, tag + "_ch0.iq")
        path_b = os.path.join(args.out, tag + "_ch1.iq")

        if (args.replug_every and run > args.start_run
                and (run - args.start_run) % args.replug_every == 0):
            input(f"\n[run {run}] Реплаг/прогрев. Переткни стики, "
                  f"дай 10–20 с прогреться, затем Enter…")

        print(f"[run {run}/{last}] запись {tag} …", flush=True)
        t0 = time.time()
        ok = record_pair(args.dev_a, args.dev_b, args.freq, args.gain,
                         args.sps, n_samples, path_a, path_b)
        dur = time.time() - t0

        meta = {
            "timestamp": dt.datetime.now().isoformat(timespec="seconds"),
            "condition": args.condition,
            "run": f"{run:02d}",
            "freq_MHz": round(args.freq / 1e6, 4),
            "tx_source": args.tx,
            "stick_A_SN": args.sn_a,
            "stick_B_SN": args.sn_b,
            "gain": args.gain,
            "sps": int(args.sps),
            "len_s": args.len,
            "board_temp_C": board_temp_c(),
            "dev_a": args.dev_a,
            "dev_b": args.dev_b,
            "capture_wall_s": round(dur, 1),
            "ok": ok,
            "notes": "",
        }
        with open(os.path.join(args.out, tag + ".json"), "w") as f:
            json.dump(meta, f, ensure_ascii=False, indent=2)

        status = "OK" if ok else "ОШИБКА (см. stderr)"
        print(f"    {status}  ({dur:.1f} с, temp={meta['board_temp_C']}°C)")

    print(f"\nГотово: {args.condition}, прогоны {args.start_run}..{last}. "
          f"Дальше: python3 ../analysis/batch_analyze.py "
          f"--condition {args.condition}")


if __name__ == "__main__":
    main()
