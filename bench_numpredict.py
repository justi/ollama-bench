#!/usr/bin/env python3
"""Shows the effect of num_predict on response length and time - for a model with a thinking mode.

Reproduces the numbers: "default limit ~293 words -> num_predict 3000 ~747 words, ~45 s -> ~85 s".

  python3 bench_numpredict.py gpt-oss:20b
  python3 bench_numpredict.py gpt-oss:20b 1500 3000   # custom thresholds
"""
import json
import sys

from _common import generate, total_seconds, word_count, load_prompts

# A task requiring a longer response - a thinking model first "thinks",
# so with a low limit it cuts off the actual answer (thinking overflow).
TASK = load_prompts()["numpredict_task"]


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 bench_numpredict.py MODEL [low high]")
        sys.exit(1)
    model = sys.argv[1]
    low = int(sys.argv[2]) if len(sys.argv) > 2 else 1500
    high = int(sys.argv[3]) if len(sys.argv) > 3 else 3000
    if low >= high:
        print(f"ERROR: lower threshold ({low}) must be smaller than the upper one ({high}). "
              f"Provide: MODEL low high")
        sys.exit(1)

    print(f"== bench_numpredict [{model}] : num_predict {low} vs {high} ==\n")
    rows = []
    for np in (low, high):
        print(f"  num_predict={np} ... ", end="", flush=True)
        try:
            r = generate(model, TASK, num_predict=np)
        except Exception as e:
            print(f"ERROR: {e}")
            rows.append({"num_predict": np, "error": str(e)})
            continue
        wc = word_count(r)
        ts = total_seconds(r)
        rows.append({"num_predict": np, "words": wc, "total_s": ts, "gen_tokens": r.get("eval_count")})
        print(f"{wc} words | {ts} s | {r.get('eval_count')} tokens")

    print("\n== SUMMARY ==")
    print(f"{'num_predict':>12} {'words':>8} {'time s':>8}")
    for r in rows:
        if "error" in r:
            print(f"{r['num_predict']:>12} {'ERROR':>8}")
        else:
            print(f"{r['num_predict']:>12} {r['words']:>8} {str(r['total_s']):>8}")
    if len(rows) == 2 and all("error" not in r for r in rows):
        dw = rows[1]["words"] - rows[0]["words"]
        print(f"\nLength increase after raising the limit: +{dw} words "
              f"({rows[0]['words']} -> {rows[1]['words']}).")

    with open("results_numpredict.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("Saved: results_numpredict.json")


if __name__ == "__main__":
    main()
