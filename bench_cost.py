#!/usr/bin/env python3
"""Koszt energii na 1M wygenerowanych tokenow.

Kluczowa zaleznosc: przy stalym poborze mocy koszt energii jest ODWROTNIE proporcjonalny
do tok/s - wolny model zuzywa wielokrotnie wiecej pradu na ten sam output.

  python3 bench_cost.py "qwen3-coder:30b=54.8" "deepseek-coder:33b=10.4"

Parametry (env, z domyslnymi dla Apple M1 Max + taryfa PL G11 ~2026):
  BENCH_POWER_W   - pobor mocy pod obciazeniem w watach (domyslnie 45)
  BENCH_PRICE_KWH - cena energii w zl/kWh (domyslnie 1.1)

UWAGA: moc 45 W to SZACUNEK dla M1 Max podczas inference (GPU-bound). Dokladny pomiar:
  sudo powermetrics --samplers gpu_power -i 1000 podczas generacji. Roznice miedzy modelami
  i tak wynikaja glownie z tok/s, nie z mocy (moc jest podobna), wiec ranking kosztu jest
  odporny na ten szacunek.
"""
import os
import sys

POWER_W = float(os.environ.get("BENCH_POWER_W", 45))
PRICE = float(os.environ.get("BENCH_PRICE_KWH", 1.1))


def cost_per_1m(tok_s):
    seconds = 1_000_000 / tok_s
    kwh = POWER_W * seconds / 3_600_000  # W*s -> kWh
    return seconds / 3600.0, kwh, kwh * PRICE  # godziny, kWh, zl


def main():
    pairs = sys.argv[1:]
    if not pairs:
        print("Uzycie: python3 bench_cost.py MODEL=TOKS [MODEL=TOKS ...]")
        sys.exit(1)
    print(f"== koszt energii / 1M tokenow (moc {POWER_W} W, cena {PRICE} zl/kWh) ==\n")
    print(f"{'model':<30}{'tok/s':>8}{'h/1M':>9}{'kWh/1M':>9}{'zl/1M':>9}")
    for p in pairs:
        name, _, val = p.rpartition("=")
        ts = float(val)
        h, kwh, zl = cost_per_1m(ts)
        print(f"{name:<30}{ts:>8}{h:>9.1f}{kwh:>9.3f}{zl:>9.2f}")


if __name__ == "__main__":
    main()
