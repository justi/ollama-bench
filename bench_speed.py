#!/usr/bin/env python3
"""Mierzy tok/s generacji per model.

Odtwarza liczby typu "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s".

  python3 bench_speed.py qwen3-coder:30b gpt-oss:20b gemma3:27b
  python3 bench_speed.py --big qwen3-coder:30b devstral:24b   # duzy prompt (~12k tokenow)
"""
import json
import statistics
import sys

from _common import generate, gen_tok_s, prompt_tok_s, total_seconds, load_prompts, isolate, list_loaded

P = load_prompts()
SMALL_PROMPT = P["speed_small"]


def build_big_prompt():
    # prefix + block*repeat + suffix -> ~12-15k tokenow (kontekst narzedziowy agenta)
    b = P["speed_big"]
    return b["prefix"] + (b["block"] * b["repeat"]) + b["suffix"]


RUNS = 3  # liczba pomiarow per model PO warmupie; raportujemy mediane


def measure_model(model, prompt, num_predict, runs=RUNS):
    # Izolacja: wyladuj WSZYSTKIE inne modele, by w pamieci byl tylko mierzony.
    # Wiecej niz jeden model = konkurencja o VRAM/RAM = zanizone, niewiarygodne tok/s.
    isolate(model)
    # Warmup: jeden krotki przebieg, by zaladowac model i skompilowac kernele Metal.
    # Bez tego pierwszy pomiar bywa zanizony (cold start). Wynik warmupu odrzucamy.
    # Uwaga: gen tok/s i tak liczymy z eval_duration, ktore NIE zawiera load_duration -
    # czyli czas wczytania modelu z dysku nigdy nie wchodzi do tok/s.
    try:
        generate(model, "Czesc", num_predict=8)
    except Exception:
        pass
    # Weryfikacja izolacji: po zaladowaniu w pamieci powinien byc tylko mierzony model.
    loaded = list_loaded()
    isolation_ok = loaded == [model] or loaded == []
    rates, last = [], None
    for _ in range(runs):
        last = generate(model, prompt, num_predict=num_predict)
        gr = gen_tok_s(last)
        if gr:
            rates.append(gr)
    return {
        "model": model,
        "gen_tok_s": round(statistics.median(rates), 1) if rates else None,
        "gen_tok_s_runs": rates,
        "prompt_tok_s": prompt_tok_s(last) if last else None,
        "total_s": total_seconds(last) if last else None,
        "gen_tokens": last.get("eval_count") if last else None,
        "isolated": isolation_ok,
        "loaded_during": loaded,
    }


def main():
    args = sys.argv[1:]
    big = "--big" in args
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Uzycie: python3 bench_speed.py [--big] MODEL [MODEL ...]")
        sys.exit(1)

    prompt = build_big_prompt() if big else SMALL_PROMPT
    num_predict = 64 if big else 300
    mode = "DUZY PROMPT (~12k tok)" if big else "maly prompt"
    print(f"== bench_speed [{mode}] : warmup + mediana z {RUNS} przebiegow ==\n")

    rows = []
    for m in models:
        print(f"  {m} ... ", end="", flush=True)
        try:
            row = measure_model(m, prompt, num_predict)
        except Exception as e:
            print(f"BLAD: {e}")
            rows.append({"model": m, "error": str(e)})
            continue
        rows.append(row)
        warn = "" if row.get("isolated") else f"  [!] IZOLACJA NARUSZONA (w pamieci: {row.get('loaded_during')})"
        print(f"gen {row['gen_tok_s']} tok/s (mediana z {row['gen_tok_s_runs']}) | "
              f"prompt {row['prompt_tok_s']} tok/s | total {row['total_s']} s{warn}")

    print("\n== PODSUMOWANIE (mediana gen tok/s) ==")
    print(f"{'model':<32} {'gen tok/s':>10} {'przebiegi':>24}")
    for r in rows:
        if "error" in r:
            print(f"{r['model']:<32} {'BLAD':>10}")
        else:
            print(f"{r['model']:<32} {str(r['gen_tok_s']):>10} {str(r['gen_tok_s_runs']):>24}")

    with open("results_speed.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_speed.json")


if __name__ == "__main__":
    main()
