#!/usr/bin/env python3
"""
si5351_cw_100M.py — Si5351A №2 как тест-CW генератор 100.000 МГц (на Pi, I²C).

Это ОТДЕЛЬНАЯ от клок-инжекции плата (#2). Даёт чистый CW для A/B-замеров
когерентности. Si5351 #1 (28.8 МГц клок) — не трогаем.

БЕЗ ДЕЛИТЕЛЯ: включаем СРАЗУ ДВА выхода — CLK0 и CLK1, оба 100 МГц от ОДНОГО
PLL_A. Это фазово-связанные копии одного тона (общий PLL → его фазовый шум
common-mode и сокращается в a·conj(b)). CLK0 → стик #3, CLK1 → стик #4, двумя
кабелями напрямую. Сплиттер не нужен.

Расчёт: опорный кварц breakout = 25 МГц.
  PLL_A = 25 × 32 = 800 МГц  (в допустимом окне 600–900 МГц)
  CLK0,CLK1 = 800 / 8 = 100.000 МГц  (целочисленные делители → джиттер минимален)

Drive = 2 мА (минимум): CW не должен перегружать вход RTL-SDR. Уровень добиваем
аттенюатором и/или gain приёмника (см. инструкцию, контрольная запись покажет).

Запуск:
  sudo python3 si5351_cw_100M.py      # включить CW и оставить (Ctrl-C для выхода)

Зависимости (как в Этапе A):
  sudo apt install python3-pip python3-smbus
  pip3 install adafruit-circuitpython-si5351 adafruit-blinka --break-system-packages
"""

import time

import board
import busio
import adafruit_si5351

i2c = busio.I2C(board.SCL, board.SDA)
si = adafruit_si5351.SI5351(i2c)        # адрес 0x60 по умолчанию

# PLL_A = 25 МГц × 32 = 800 МГц
si.pll_a.configure_integer(32)
# CLK0 и CLK1 = PLL_A / 8 = 100.000 МГц (две когерентные копии одного тона)
si.clock_0.configure_integer(si.pll_a, 8)
si.clock_1.configure_integer(si.pll_a, 8)
# adafruit_si5351 не даёт менять drive strength → по умолчанию 8 мА.
# Выход сильный: уровень на входе RTL-SDR гасим низким gain приёмника и/или
# аттенюатором (check_tone.py + railed-% подскажут). 8 мА безопасны для входа
# (доли–единицы мВт), максимум — цифровой клиппинг, не порча железа.
si.outputs_enabled = True

print(f"CW включён: CLK0 и CLK1 = {si.clock_0.frequency/1e6:.6f} МГц "
      f"(общий PLL_A {si.pll_a.frequency/1e6:.1f} МГц / 8), drive 8 мА по умолч.)")
print("CLK0 → стик #3 (dev0), CLK1 → стик #4 (dev1). Без делителя.")
print("Ctrl-C для выхода (выходы останутся включёнными до сброса питания).")

try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("\nВыход. CLK0 продолжает генерировать, пока подано питание.")
