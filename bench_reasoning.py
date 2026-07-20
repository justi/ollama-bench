#!/usr/bin/env python3
"""Generate reasoning-puzzle answers and SAVE every answer to a file. Grading is a SEPARATE
step (grade_reasoning.py), so the expensive model generation is decoupled from the judge:
you can re-grade, audit, or swap the judge later without re-running any model.

  # canonical (num_predict supplied from models.json):
  python3 run_bench.py reasoning qwen36-best gpt-oss-best --runs 3
  # direct (--num-predict is REQUIRED - no silent default):
  python3 bench_reasoning.py --runs 3 --num-predict=10000 qwen36-best   # -> answers_reasoning_*.json

Each puzzle in the prompts file has a "q" and the canonical "correct" answer; both are saved
next to every model answer so the grading step is self-contained.
"""
import json
import os
import sys

from _common import generate, load_prompts, parse_options, parse_think

PUZZLES = [(p["q"], p["correct"]) for p in load_prompts()["reasoning"]]


def main():
    args = sys.argv[1:]
    runs = 1
    if "--runs" in args:
        idx = args.index("--runs")
        try:
            runs = int(args[idx + 1])
        except (IndexError, ValueError):
            print("--runs requires a number")
            sys.exit(1)
        if runs < 1:
            print("--runs must be >= 1")
            sys.exit(1)
        args = args[:idx] + args[idx + 2:]
    think = parse_think(args)  # default False (explicit OFF); --think=on for thinking
    try:
        options = parse_options(args)
    except ValueError as e:
        print(e, file=sys.stderr)
        sys.exit(1)
    np_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--num-predict=")), None)
    if np_arg is None:
        print("[!] --num-predict=N is REQUIRED (no silent default). Use run_bench.py so it comes "
              "from models.json (tasks.reasoning.num_predict).", file=sys.stderr)
        sys.exit(1)
    try:
        num_pred = int(np_arg)
    except ValueError:
        print("--num-predict requires a number")
        sys.exit(1)
    out_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--out=")), None)
    out_path = out_arg or "answers_reasoning.json"
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Usage: python3 bench_reasoning.py [--runs N] [--think=on|false|low|high] "
              "[--num-predict=N] [--option=key=value] [--out=FILE] MODEL [...]")
        print("Generates answers only. Grade them with: python3 grade_reasoning.py <FILE>")
        sys.exit(1)

    prompts_file = os.environ.get("BENCH_PROMPTS", "prompts_pl.json")
    out = {}
    for m in models:
        print(f"\n== {m} ==")
        model_runs = []
        for run_i in range(runs):
            answers = []
            for i, (q, correct) in enumerate(PUZZLES, 1):
                try:
                    r = generate(m, q, num_predict=num_pred, options=options, think=think)
                    ans = r.get("response") or ""
                    trunc = r.get("done_reason") == "length"
                    err = None
                except Exception as e:
                    ans, trunc, err = "", False, str(e)
                    print(f"    [!] run {run_i + 1} q{i} generate error: {e}")
                if trunc:
                    print(f"    [!] run {run_i + 1} q{i} TRUNCATED (num_predict={num_pred})")
                answers.append({"q": i, "question": q, "correct": correct,
                                "answer": ans, "trunc": trunc, "gen_error": err})
            model_runs.append(answers)
            print(f"  run {run_i + 1}: collected {len(answers)} answers")
        out[m] = {"prompts": prompts_file, "num_predict": num_pred, "think": think,
                  "options": options, "runs": model_runs}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved answers: {out_path}  (grade with: python3 grade_reasoning.py {out_path})")


if __name__ == "__main__":
    main()
