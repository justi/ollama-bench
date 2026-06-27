#!/usr/bin/env python3
"""Energy consumption (kWh) per 1M generated tokens.

Key relationship: at constant power draw, energy is INVERSELY proportional
to tok/s - a slow model uses many times more electricity for the same output.

kWh instead of currency on purpose: electricity price differs between countries/tariffs
and changes over time, while kWh is a pure physical fact. Cost = kWh * your_price_per_kWh -
multiply it yourself, or pass BENCH_PRICE_KWH to have the script add a currency column.

  python3 bench_cost.py "qwen3-coder:30b=54.8" "deepseek-coder:33b=10.4"
  BENCH_PRICE_KWH=1.1 python3 bench_cost.py ...   # also show cost in PLN

Parameters (env):
  BENCH_POWER_W   - power draw under load in watts (default 45, M1 Max estimate)
  BENCH_PRICE_KWH - energy price in PLN/kWh (optional; without it we compute only kWh)

NOTE: the 45 W power figure is an ESTIMATE for the M1 Max during inference (GPU-bound).
  For an accurate measurement: sudo powermetrics --samplers gpu_power -i 1000 during
  generation. Differences between models stem mainly from tok/s anyway, not from power
  (power is similar), so the ranking is robust against this estimate.
"""
import os
import sys

POWER_W = float(os.environ.get("BENCH_POWER_W", 45))
SHOW_PRICE = "BENCH_PRICE_KWH" in os.environ
PRICE = float(os.environ.get("BENCH_PRICE_KWH", 1.1))


def cost_per_1m(tok_s):
    seconds = 1_000_000 / tok_s
    kwh = POWER_W * seconds / 3_600_000  # W*s -> kWh
    return seconds / 3600.0, kwh, kwh * PRICE  # hours, kWh, PLN


def main():
    pairs = sys.argv[1:]
    if not pairs:
        print("Usage: python3 bench_cost.py MODEL=TOKS [MODEL=TOKS ...]")
        sys.exit(1)
    extra = f", price {PRICE} PLN/kWh" if SHOW_PRICE else ""
    print(f"== estimated energy / 1M OUTPUT tokens - generation only (power {POWER_W} W{extra}) ==")
    print("   does not include: prompt processing, model load, power differences between models\n")
    head = f"{'model':<30}{'tok/s':>8}{'h/1M':>9}{'kWh/1M':>10}"
    if SHOW_PRICE:
        head += f"{'PLN/1M':>9}"
    print(head)
    for p in pairs:
        name, _, val = p.rpartition("=")
        ts = float(val)
        h, kwh, zl = cost_per_1m(ts)
        line = f"{name:<30}{ts:>8}{h:>9.1f}{kwh:>10.3f}"
        if SHOW_PRICE:
            line += f"{zl:>9.2f}"
        print(line)


if __name__ == "__main__":
    main()
