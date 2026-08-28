#!/usr/bin/env python3
"""Fresh, consistent ON/OFF thinking-split measurement for the blog article.

Measures, on ONE machine in ONE session (n=10), the visible-output cost of thinking:
  - north OFF vs north ON (visible tok/s: same visible text, how fast it actually arrives)
  - gpt-oss (thinking cannot be disabled): raw tok/s vs visible tok/s + %thinking

Uses a real, bounded code task (not the tiny speed prompt, which made gpt-oss spend its whole
budget on thinking -> 0 visible chars). raw = eval_count/eval_duration (includes thinking);
visible = raw * response_chars/(response_chars+thinking_chars); %thinking from the char split.
"""
import json
import statistics
import sys

from _common import generate, gen_tok_s, isolate

PROMPT = (
    "Implement merge_intervals(intervals): merge all overlapping intervals and return them "
    "sorted by start. Treat touching intervals like [1,2] and [2,3] as overlapping. Give the "
    "Python function, then state its time complexity in one line.")
NUM_PREDICT = 2200
RUNS = 10

# (model, think, label). gpt-oss ignores think=False (harmony, cannot disable) - it thinks anyway,
# which is exactly the point; its raw should land near the README batch (51.7 tok/s).
CONFIGS = [
    ("north-mini-code-1.0", False, "north OFF"),
    ("north-mini-code-1.0", True,  "north ON"),
    ("gpt-oss:20b",         False, "gpt-oss"),
]


def run(model, think, label):
    isolate(model)
    try:
        generate(model, "Hi", num_predict=8, think=think)  # warmup: load + compile kernels
    except Exception:
        pass
    raws, visibles, think_pcts, last = [], [], [], None
    for i in range(RUNS):
        last = generate(model, PROMPT, num_predict=NUM_PREDICT, think=think)
        r = gen_tok_s(last)
        tc = len(last.get("thinking") or "")
        rc = len(last.get("response") or "")
        if r:
            raws.append(r)
            visibles.append(r * rc / (rc + tc) if (rc + tc) else r)
        if (rc + tc):
            think_pcts.append(100.0 * tc / (rc + tc))
        print(f"    [{label}] run {i+1}/{RUNS}: raw {round(r,1) if r else None} tok/s | "
              f"resp {rc} / think {tc} chars", flush=True)
    return {
        "label": label, "model": model, "think": think, "n": len(raws),
        "raw_med": round(statistics.median(raws), 1) if raws else None,
        "visible_med": round(statistics.median(visibles), 1) if visibles else None,
        "think_pct_med": round(statistics.median(think_pcts)) if think_pcts else 0,
        "raw_runs": [round(x, 1) for x in raws],
    }


def main():
    results = []
    for cfg in CONFIGS:
        print(f"\n== {cfg[2]} (n={RUNS}, num_predict={NUM_PREDICT}) ==", flush=True)
        results.append(run(*cfg))
    print("\n== SUMMARY ==")
    for r in results:
        print(f"  {r['label']:<12} raw {r['raw_med']} | visible {r['visible_med']} tok/s | "
              f"thinking {r['think_pct_med']}%  (n={r['n']})")
    with open("think_split_results.json", "w") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("\nSaved: think_split_results.json")


if __name__ == "__main__":
    main()
