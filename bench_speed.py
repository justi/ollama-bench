#!/usr/bin/env python3
"""Mierzy tok/s generacji per model.

Odtwarza liczby typu "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s".

  python3 bench_speed.py qwen3-coder:30b gpt-oss:20b gemma3:27b
  python3 bench_speed.py --big qwen3-coder:30b devstral:24b   # duzy prompt (~12k tokenow)
"""
import json
import sys

from _common import generate, gen_tok_s, prompt_tok_s, total_seconds, load_prompts

P = load_prompts()
SMALL_PROMPT = P["speed_small"]


def build_big_prompt():
    # prefix + block*repeat + suffix -> ~12-15k tokenow (kontekst narzedziowy agenta)
    b = P["speed_big"]
    return b["prefix"] + (b["block"] * b["repeat"]) + b["suffix"]


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
