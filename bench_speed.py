#!/usr/bin/env python3
"""Mierzy tok/s generacji per model.

Odtwarza liczby typu "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s".

  python3 bench_speed.py qwen3-coder:30b gpt-oss:20b gemma3:27b
  python3 bench_speed.py --big qwen3-coder:30b devstral:24b   # duzy prompt (~12k tokenow)
"""
import json
import sys

from _common import generate, gen_tok_s, prompt_tok_s, total_seconds

SMALL_PROMPT = (
    "Napisz wypracowanie na okolo 250 slow o tym, dlaczego warto pic wode "
    "kazdego dnia. Pisz plynnie, bez punktow."
)

# Duzy prompt symuluje realny kontekst narzedziowy (system + definicje toolow + historia),
# jak w agentowym IDE. ~12 tys. tokenow zlepionych z powtorzonej instrukcji.
BIG_PREFIX = (
    "Ponizej znajduje sie obszerna dokumentacja narzedzi dostepnych dla agenta. "
    "Przeczytaj ja w calosci, a nastepnie odpowiedz na pytanie na koncu.\n\n"
)
BIG_BLOCK = (
    "TOOL: read_file(path) - czyta plik z dysku i zwraca jego tresc. "
    "TOOL: write_file(path, content) - zapisuje tresc do pliku. "
    "TOOL: run_bash(cmd) - uruchamia polecenie powloki i zwraca wynik. "
    "TOOL: search(query) - przeszukuje repozytorium po wzorcu. "
    "Kazde narzedzie zwraca JSON z polem result lub error.\n"
)


def build_big_prompt():
    # ~120 znakow * 500 powtorzen ~ 60k znakow ~ 12-15k tokenow
    return BIG_PREFIX + (BIG_BLOCK * 500) + "\nPYTANIE: streszcz w 3 zdaniach, co robi narzedzie run_bash."


def main():
    args = [a for a in sys.argv[1:]]
    big = "--big" in args
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Uzycie: python3 bench_speed.py [--big] MODEL [MODEL ...]")
        sys.exit(1)

    prompt = build_big_prompt() if big else SMALL_PROMPT
    num_predict = 64 if big else 300
    mode = "DUZY PROMPT (~12k tok)" if big else "maly prompt"
    print(f"== bench_speed [{mode}] ==\n")

    rows = []
    for m in models:
        print(f"  {m} ... ", end="", flush=True)
        try:
            r = generate(m, prompt, num_predict=num_predict)
        except Exception as e:
            print(f"BLAD: {e}")
            rows.append({"model": m, "error": str(e)})
            continue
        row = {
            "model": m,
            "gen_tok_s": gen_tok_s(r),
            "prompt_tok_s": prompt_tok_s(r),
            "total_s": total_seconds(r),
            "prompt_tokens": r.get("prompt_eval_count"),
            "gen_tokens": r.get("eval_count"),
        }
        rows.append(row)
        print(f"gen {row['gen_tok_s']} tok/s | prompt {row['prompt_tok_s']} tok/s | total {row['total_s']} s")

    print("\n== PODSUMOWANIE ==")
    print(f"{'model':<32} {'gen tok/s':>10} {'prompt tok/s':>13} {'total s':>9}")
    for r in rows:
        if "error" in r:
            print(f"{r['model']:<32} {'BLAD':>10}")
        else:
            print(f"{r['model']:<32} {str(r['gen_tok_s']):>10} {str(r['prompt_tok_s']):>13} {str(r['total_s']):>9}")

    with open("results_speed.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\nZapisano: results_speed.json")


if __name__ == "__main__":
    main()
