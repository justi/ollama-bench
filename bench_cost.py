#!/usr/bin/env python3
"""Zuzycie energii (kWh) na 1M wygenerowanych tokenow.

Kluczowa zaleznosc: przy stalym poborze mocy energia jest ODWROTNIE proporcjonalna
do tok/s - wolny model zuzywa wielokrotnie wiecej pradu na ten sam output.

kWh zamiast zl celowo: cena pradu rozni sie miedzy krajami/taryfami i zmienia w czasie,
a kWh to czysty fakt fizyczny. Koszt = kWh * Twoja_cena_kWh - pomnoz sam, albo podaj
BENCH_PRICE_KWH, by skrypt dodal kolumne ze zlotowkami.

  python3 bench_cost.py "qwen3-coder:30b=54.8" "deepseek-coder:33b=10.4"
  BENCH_PRICE_KWH=1.1 python3 bench_cost.py ...   # dodatkowo koszt w zl

Parametry (env):
  BENCH_POWER_W   - pobor mocy pod obciazeniem w watach (domyslnie 45, szacunek M1 Max)
  BENCH_PRICE_KWH - cena energii w zl/kWh (opcjonalnie; bez niej liczymy tylko kWh)

UWAGA: moc 45 W to SZACUNEK dla M1 Max podczas inference (GPU-bound). Dokladny pomiar:
  sudo powermetrics --samplers gpu_power -i 1000 podczas generacji. Roznice miedzy modelami
  i tak wynikaja glownie z tok/s, nie z mocy (moc jest podobna), wiec ranking jest odporny
  na ten szacunek.
"""
import os
import sys

POWER_W = float(os.environ.get("BENCH_POWER_W", 45))
SHOW_PRICE = "BENCH_PRICE_KWH" in os.environ
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
    extra = f", cena {PRICE} zl/kWh" if SHOW_PRICE else ""
    print(f"== zuzycie energii / 1M tokenow (moc {POWER_W} W{extra}) ==\n")
    head = f"{'model':<30}{'tok/s':>8}{'h/1M':>9}{'kWh/1M':>10}"
    if SHOW_PRICE:
        head += f"{'zl/1M':>9}"
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
