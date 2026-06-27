#!/usr/bin/env python3
"""Measures generation tok/s per model.

Reproduces numbers like "qwen ~52 tok/s, gemma ~6 tok/s, devstral ~12 tok/s".

  python3 bench_speed.py qwen3-coder:30b gpt-oss:20b gemma3:27b
  python3 bench_speed.py --big qwen3-coder:30b devstral:24b   # big prompt (~12k tokens)
"""
import json
import statistics
import sys

from _common import (generate, gen_tok_s, prompt_tok_s, total_seconds, load_prompts,
                     isolate, list_loaded, parse_think)

P = load_prompts()
SMALL_PROMPT = P["speed_small"]


def build_big_prompt():
    # prefix + block*repeat + suffix -> ~12-15k tokens (agent tooling context)
    b = P["speed_big"]
    return b["prefix"] + (b["block"] * b["repeat"]) + b["suffix"]


RUNS = 3  # number of measurements per model AFTER warmup; we report the median


def _strip_latest(n):
    return n[:-7] if n.endswith(":latest") else n


def measure_model(model, prompt, num_predict, runs=RUNS, think=None):
    # Isolation: unload ALL other models, so only the measured one is in memory.
    # More than one model = contention for VRAM/RAM = understated, unreliable tok/s.
    iso_confirmed = isolate(model)  # True only once /api/ps confirms emptiness
    # Warmup: one short run to load the model and compile the Metal kernels.
    # Without it the first measurement tends to be understated (cold start). We discard the warmup result.
    # gen tok/s is computed from eval_duration, which does NOT include load_duration (disk load excluded from tok/s).
    try:
        generate(model, "Hi", num_predict=8, think=think)
    except Exception:
        pass
    # Verification: after warmup, memory should hold EXACTLY the measured model.
    # :latest normalization: /api/ps returns e.g. 'deepseek-fast:latest'.
    loaded = list_loaded()
    norm = None if loaded is None else [_strip_latest(x) for x in loaded]
    isolation_ok = bool(iso_confirmed) and norm == [_strip_latest(model)]
    rates, last, think_chars, resp_chars = [], None, 0, 0
    for _ in range(runs):
        last = generate(model, prompt, num_predict=num_predict, think=think)
        gr = gen_tok_s(last)
        if gr:
            rates.append(gr)
        # For 'thinking' models (gpt-oss) the content goes into the thinking field, and eval_count
        # counts THINKING tokens. gen_tok_s is then the throughput of the thinking channel, not the output.
        think_chars = len(last.get("thinking") or "")
        resp_chars = len(last.get("response") or "")
    med = round(statistics.median(rates), 1) if rates else None
    # spread = max-min of raw runs (consistency): small = stable, large = variable
    spread = round(max(rates) - min(rates), 1) if len(rates) >= 2 else None
    # response_tok_s_est: for thinking models eval_count counts thinking tokens, so the raw
    # tok/s overstates the throughput of the VISIBLE output. We estimate the output proportionally to
    # the share of response characters in the whole generated text.
    resp_est = med
    if med and think_chars > 0 and (resp_chars + think_chars) > 0:
        resp_est = round(med * resp_chars / (resp_chars + think_chars), 1)
    return {
        "model": model,
        "eval_tok_s": med,               # raw generation throughput (with thinking tokens)
        "response_tok_s_est": resp_est,  # estimated VISIBLE output (for thinking < eval_tok_s)
        "gen_tok_s": med,                # backward-compatible alias (= eval_tok_s)
        "gen_tok_s_spread": spread,      # max-min of runs = consistency measure
        "gen_tok_s_runs": rates,
        "prompt_tok_s": prompt_tok_s(last) if last else None,
        "total_s": total_seconds(last) if last else None,
        "gen_tokens": last.get("eval_count") if last else None,
        "isolated": isolation_ok,
        "loaded_during": loaded,
        "is_thinking": think_chars > 0,
        "response_chars": resp_chars,
        "thinking_chars": think_chars,
    }


def main():
    args = sys.argv[1:]
    big = "--big" in args
    # Default False (throughput convention): None = model default = thinking-ON for some models,
    # whose thinking tokens then inflate eval_tok_s. Pass --think=none for the model default.
    think = parse_think(args)
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Usage: python3 bench_speed.py [--big] MODEL [MODEL ...]")
        sys.exit(1)

    prompt = build_big_prompt() if big else SMALL_PROMPT
    # --big: 256 (not 64) generation tokens - at 64, gen tok/s is prone to noise/EOS
    # after a big prompt. Prompt-eval is measured separately via prompt_tok_s anyway.
    num_predict = 256 if big else 300
    mode = "BIG PROMPT (~12k tok)" if big else "small prompt"
    print(f"== bench_speed [{mode}] : warmup + median of {RUNS} runs ==\n")

    rows = []
    for m in models:
        print(f"  {m} ... ", end="", flush=True)
        try:
            row = measure_model(m, prompt, num_predict, think=think)
        except Exception as e:
            print(f"ERROR: {e}")
            rows.append({"model": m, "error": str(e)})
            continue
        rows.append(row)
        warn = "" if row.get("isolated") else f"  [!] ISOLATION VIOLATED (in memory: {row.get('loaded_during')})"
        # NOTE: separate name (think_note), NOT 'think' - overwriting the loop parameter broke
        # subsequent models ("think":"" -> HTTP 400 on all after the first).
        think_note = ""
        if row.get("is_thinking"):
            think_note = (f"  [!] THINKING: tok/s includes thinking tokens, not just output "
                          f"(response {row['response_chars']} chars / thinking {row['thinking_chars']} chars)")
        print(f"gen {row['gen_tok_s']} tok/s (median of {row['gen_tok_s_runs']}) | "
              f"prompt {row['prompt_tok_s']} tok/s | total {row['total_s']} s{warn}{think_note}")

    print("\n== SUMMARY (median of 3, isolation) ==")
    print(f"{'model':<30}{'output tok/s':>13}{'eval tok/s':>12}  note")
    for r in rows:
        if "error" in r:
            print(f"{r['model']:<30}{'ERROR':>13}")
            continue
        # no isolation = unreliable number; thinking = eval > output
        if not r.get("isolated"):
            note = "[!] NO ISOLATION - number uncertain"
        elif r.get("is_thinking"):
            note = "thinking: eval_tok_s includes thinking, output lower"
        else:
            note = ""
        out = r.get("response_tok_s_est")
        ev = r.get("eval_tok_s")
        print(f"{r['model']:<30}{str(out):>13}{str(ev):>12}  {note}")

    with open("results_speed.json", "w") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)
    print("\nSaved: results_speed.json")


if __name__ == "__main__":
    main()
