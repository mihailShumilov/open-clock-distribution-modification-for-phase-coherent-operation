#!/usr/bin/env python3
# SPDX-License-Identifier: MIT
"""
si5351_clk_28M8.py — Si5351A #1 как ОБЩИЙ опорный клок 28.8 МГц (CLK0) для стиков.
Запуск на хосте (Raspberry Pi), I²C, адрес 0x60.

  sudo python3 si5351_clk_28M8.py

PLL_A = 25 МГц × 24 = 600 МГц; делитель CLK0 = 20 + 5/6 → 600/20.8333 = 28.800 МГц.
Drive по умолчанию 8 мА — подходит для инжекции. После настройки генерация
продолжается на питании, I²C можно снять. Лицензия: MIT.

Зависимости: pip3 install adafruit-circuitpython-si5351 adafruit-blinka --break-system-packages
"""
import time
import board, busio
import adafruit_si5351

i2c = busio.I2C(board.SCL, board.SDA)
si = adafruit_si5351.SI5351(i2c)
si.pll_a.configure_integer(24)                       # 600 МГц
si.clock_0.configure_fractional(si.pll_a, 20, 5, 6)  # 28.800 МГц
si.outputs_enabled = True

print(f"CLK0 = {si.clock_0.frequency/1e6:.4f} МГц (общий клок для стиков)")
print("Ctrl-C для выхода; генерация продолжится на питании.")
try:
    while True:
        time.sleep(5)
except KeyboardInterrupt:
    print("выход")
