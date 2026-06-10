#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
# Copyright (c) 2026 Mykhailo Shumilov
"""
coherence_lib.py — ядро анализа фазовой когерентности пары RTL-SDR.
Финальный метод (валидирован на синтетике и на bench-кампании 2026-06-08).

Идея. Общий CW-тон приходит на оба канала; в кросс-произведении a·conj(b)
несущая common-mode сокращается, остаётся только межканальный рассинхрон клоков.
Для НЕЗАВИСИМЫХ клоков (baseline) между каналами есть значимый и медленно
гуляющий частотный сдвиг — «бит» (сотни Гц). Поэтому анализ идёт ПОБЛОЧНО:
в каждом блоке бит оценивается по пику FFT произведения и деротируется, затем
по окнам считается фаза и из неё (после линейного детренда внутри блока)
вынимается остаточный джиттер. Для общего клока (shared) бит ≈ 0 и метод
сводится к прямому усреднению.

ВАЖНО (две поправки к исходному скелету LESSONS §8.0):
  1. φ по окну = angle(mean(a·conj(b))) — БЕЗ домножения на exp(-j2π f_cw t):
     несущая в произведении уже сократилась, lo при f_cw≠0 занулит сигнал.
  2. Деротировать надо НЕ несущую, а межканальный БИТ (поблочно), иначе
     baseline даёт мусор. CRB порога для разности фаз = 1/√(ρN) (×√2 от одноканальной).

Лицензия: MIT.
"""

import os
import numpy as np


# ── загрузка IQ (rtl_sdr uint8 I/Q, offset 127.5) ───────────────────────────
def load_iq_chunk(filename, start_sample, n_samples):
    raw = np.memmap(filename, dtype=np.uint8, mode="r")
    a = raw[start_sample * 2:(start_sample + n_samples) * 2].astype(np.float32) - 127.5
    return a[0::2] + 1j * a[1::2]


def iq_num_samples(filename):
    return os.path.getsize(filename) // 2


# ── оценка бита и SNR ───────────────────────────────────────────────────────
def _peak_freq(prod, fs):
    """Частота доминирующего тона комплексного сигнала [Гц], суб-бин интерполяция."""
    P = np.fft.fftshift(np.fft.fft(prod))
    fr = np.fft.fftshift(np.fft.fftfreq(len(prod), 1.0 / fs))
    k = int(np.argmax(np.abs(P)))
    if 0 < k < len(P) - 1:
        y0, y1, y2 = abs(P[k - 1]), abs(P[k]), abs(P[k + 1])
        d = 0.5 * (y0 - y2) / (y0 - 2 * y1 + y2 + 1e-12)
    else:
        d = 0.0
    return float(fr[k] + d * (fr[1] - fr[0]))


def estimate_beat(file_a, file_b, fs, secs=2.0):
    """Средний межканальный бит [Гц] по первым `secs` секундам."""
    n = min(iq_num_samples(file_a), iq_num_samples(file_b), int(fs * secs))
    a = load_iq_chunk(file_a, 0, n); b = load_iq_chunk(file_b, 0, n)
    a -= a.mean(); b -= b.mean()
    return _peak_freq(a * np.conj(b), fs)


def estimate_snr_db(file_a, fs, search=1 << 20, bw=4_000.0):
    """Грубый спектральный SNR [дБ] по одному каналу (диагностика)."""
    a = load_iq_chunk(file_a, 0, min(iq_num_samples(file_a), search)); a -= a.mean()
    n = len(a)
    sp = np.fft.fftshift(np.fft.fft(a * np.hanning(n)))
    fr = np.fft.fftshift(np.fft.fftfreq(n, 1.0 / fs))
    psd = np.abs(sp) ** 2
    mg = np.abs(sp).copy(); mg[np.abs(fr) < 5_000.0] = 0.0
    fo = fr[int(np.argmax(mg))]
    sig = np.abs(fr - fo) < bw
    noise = (~sig) & (np.abs(fr) > 5_000.0)
    nd = np.median(psd[noise]) * sig.sum()
    if nd <= 0:
        return float("nan")
    return float(10 * np.log10(max(psd[sig].sum() - nd, 1e-12) / nd))


# ── основной анализ пары (поблочный трекинг бита) ───────────────────────────
def analyze_pair(file_a, file_b, fs, win_ms=100.0, block_ms=500.0):
    """Вернуть dict: jitter_deg, beat_hz (медиана), beat_wander_hz, n_blocks.

    Алгоритм на блок (block_ms): оценить локальный бит → деротировать →
    фаза по окнам (win_ms) с вычитанием DC → unwrap → линейный детренд →
    остатки. jitter = std пула остатков по всем блокам.
    """
    N = min(iq_num_samples(file_a), iq_num_samples(file_b))
    nwin = int(fs * win_ms / 1000.0)
    nblk = (int(fs * block_ms / 1000.0) // nwin) * nwin
    nblocks = N // nblk
    resid, beats = [], []
    for bi in range(nblocks):
        s0 = bi * nblk
        a = load_iq_chunk(file_a, s0, nblk); b = load_iq_chunk(file_b, s0, nblk)
        a -= a.mean(); b -= b.mean()
        prod = a * np.conj(b)
        fb = _peak_freq(prod, fs); beats.append(fb)
        t = np.arange(nblk) / fs
        pr = prod * np.exp(-2j * np.pi * fb * t)
        nw = nblk // nwin
        ph = np.degrees(np.unwrap(np.array(
            [np.angle(pr[w * nwin:(w + 1) * nwin].mean()) for w in range(nw)])))
        x = np.arange(nw)
        if nw >= 3:
            c = np.polyfit(x, ph, 1)
            resid.extend(ph - np.polyval(c, x))
    resid = np.asarray(resid); beats = np.asarray(beats)
    return {
        "jitter_deg": float(resid.std(ddof=1)) if resid.size > 1 else float("nan"),
        "beat_hz": float(np.median(beats)) if beats.size else float("nan"),
        "beat_wander_hz": float(beats.std(ddof=1)) if beats.size > 1 else 0.0,
        "n_blocks": int(nblocks),
    }


def is_contaminated(beat_hz, beat_wander_hz, beat_max_khz=10.0, wander_max_hz=2_000.0):
    """True, если запись засорена (FM перебил CW / дроп сэмплов)."""
    return abs(beat_hz) > beat_max_khz * 1000.0 or beat_wander_hz > wander_max_hz


# ── шумовой порог (jitter vs окно, сквозной метод) ──────────────────────────
def floor_sweep(file_a, file_b, fs, win_ms_list, block_ms=5000.0):
    """Вернуть (win_ms[], N_samples[], jitter_deg[]) для одной (чистой) записи.

    Деротация по среднему биту записи; на каждом окне — фаза по всей записи,
    затем поблочный (block_ms) линейный детренд, общий пул остатков → std.
    """
    beat = estimate_beat(file_a, file_b, fs)
    N = min(iq_num_samples(file_a), iq_num_samples(file_b))
    wins, Ns, J = [], [], []
    for win_ms in win_ms_list:
        nwin = int(fs * win_ms / 1000.0); nwt = N // nwin
        ph = np.empty(nwt)
        for w in range(nwt):
            s = w * nwin
            a = load_iq_chunk(file_a, s, nwin); b = load_iq_chunk(file_b, s, nwin)
            a -= a.mean(); b -= b.mean()
            t = (s + np.arange(nwin)) / fs
            ph[w] = np.angle((a * np.conj(b) * np.exp(-2j * np.pi * beat * t)).mean())
        deg = np.degrees(np.unwrap(ph))
        wpb = max(3, int(block_ms / win_ms)); resid = []
        for bi in range(0, nwt, wpb):
            seg = deg[bi:bi + wpb]
            if len(seg) >= 3:
                x = np.arange(len(seg)); c = np.polyfit(x, seg, 1)
                resid.extend(seg - np.polyval(c, x))
        wins.append(win_ms); Ns.append(nwin)
        J.append(float(np.std(resid, ddof=1)) if len(resid) > 1 else float("nan"))
    return np.array(wins), np.array(Ns), np.array(J)


# ── статистика ──────────────────────────────────────────────────────────────
def summarize(values):
    v = np.asarray([x for x in values if np.isfinite(x)], float)
    n = len(v)
    if n == 0:
        return {"mean": float("nan"), "std": float("nan"), "ci95": float("nan"), "n": 0}
    mean = float(v.mean()); std = float(v.std(ddof=1)) if n > 1 else 0.0
    ci = _t95(n - 1) * std / np.sqrt(n) if n > 1 else 0.0
    return {"mean": mean, "std": std, "ci95": float(ci), "n": n}


def _t95(df):
    table = {1: 12.706, 2: 4.303, 3: 3.182, 4: 2.776, 5: 2.571, 6: 2.447, 7: 2.365,
             8: 2.306, 9: 2.262, 10: 2.228, 11: 2.201, 12: 2.179, 15: 2.131,
             20: 2.086, 30: 2.042, 60: 2.000, 120: 1.980}
    if df <= 0:
        return float("nan")
    keys = sorted(table)
    if df in table:
        return table[df]
    if df > keys[-1]:
        return 1.96
    lo = max(k for k in keys if k <= df); hi = min(k for k in keys if k >= df)
    f = (df - lo) / (hi - lo)
    return table[lo] + f * (table[hi] - table[lo])


def theoretical_phase_floor_deg(snr_linear, n_samples, inter_channel=True):
    """CRB фазового шума [°]. inter_channel: σ=1/√(ρN); одноканальный: 1/√(2ρN)."""
    if snr_linear <= 0 or n_samples <= 0:
        return float("nan")
    k = 1.0 if inter_channel else 2.0
    return float(np.degrees(1.0 / np.sqrt(k * snr_linear * n_samples)))


def db_to_linear(db):
    return 10.0 ** (db / 10.0)
