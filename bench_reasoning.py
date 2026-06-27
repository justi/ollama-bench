#!/usr/bin/env python3
"""Generate reasoning-puzzle answers and SAVE every answer to a file. Grading is a SEPARATE
step (grade_reasoning.py), so the expensive model generation is decoupled from the judge:
you can re-grade, audit, or swap the judge later without re-running any model.

  python3 bench_reasoning.py --runs 3 qwen36-best gpt-oss-best   # -> answers_reasoning.json
  BENCH_PROMPTS=prompts_en.json python3 bench_reasoning.py --runs 3 qwen36-best

Each puzzle in the prompts file has a "q" and the canonical "correct" answer; both are saved
next to every model answer so the grading step is self-contained.
"""
import json
import os
import sys

from _common import generate, load_prompts, parse_think

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
    np_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--num-predict=")), None)
    try:
        num_pred = int(np_arg) if np_arg else 3000
    except ValueError:
        print("--num-predict requires a number")
        sys.exit(1)
    out_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--out=")), None)
    out_path = out_arg or "answers_reasoning.json"
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Usage: python3 bench_reasoning.py [--runs N] [--think=on|false|low|high] "
              "[--num-predict=N] [--out=FILE] MODEL [...]")
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
                    r = generate(m, q, num_predict=num_pred, think=think)
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
        out[m] = {"prompts": prompts_file, "num_predict": num_pred, "think": think, "runs": model_runs}

    with open(out_path, "w", encoding="utf-8") as f:
        json.dump(out, f, ensure_ascii=False, indent=2)
    print(f"\nSaved answers: {out_path}  (grade with: python3 grade_reasoning.py {out_path})")


if __name__ == "__main__":
    main()
