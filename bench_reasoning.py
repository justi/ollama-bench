#!/usr/bin/env python3
"""6 logic puzzles with key-based auto-grading. Reproduces scores like "gpt-oss 2/6, qwen 6/6".

  python3 bench_reasoning.py qwen3-coder:30b gpt-oss:20b

Auto-grading is approximate (it looks for the key in the answer). For ambiguous
answers, check results_reasoning.json and grade manually - this is the same problem
that the article solved with manual quality grading.
"""
import json
import re
import sys

from _common import generate, load_prompts

# (question, keys-OR, anti-REJECT, all-groups-AND) - read from prompts.json
PUZZLES = [(p["q"], p.get("keys", []), p.get("anti"), p.get("all")) for p in load_prompts()["reasoning"]]


def grade(answer, keys, anti=None, all_groups=None):
    # Normalize: strip markdown (**bold**, #, `) and collapse whitespace, so the key
    # matches answers like "**4**\nDziewczyn: **3**". re.DOTALL so '.' spans newlines.
    a = answer.lower()
    # LaTeX: \frac{2}{3} -> 2/3, strip \boxed \text \[ ] and curly braces (r1 writes math
    # in LaTeX, key "2/3" did not match "\frac{2}{3}" - false-negative, manual r1 audit).
    a = re.sub(r"\\frac\s*\{(\d+)\}\s*\{(\d+)\}", r"\1/\2", a)
    a = re.sub(r"\\[a-z]+", " ", a)  # \boxed \text \frac etc.
    a = re.sub(r"[{}\\\[\]]", " ", a)
    # Diacritics -> ASCII, so key "chlop" matches "chlopcow" written with Polish characters
    # (ch-l-o-p with stroked 'l'). Manual r1 audit: "4 chlopce" with 'l-stroke' did not match key "4 chlop".
    a = a.translate(str.maketrans("ąćęłńóśźż", "acelnoszz"))
    a = re.sub(r"[*#`]", " ", a)
    a = re.sub(r"\s+", " ", a)
    # anti: if the answer contains a contradictory/wrong pattern, reject it (Monty Hall "equal probab").
    if anti:
        for k in anti:
            if re.search(k.lower(), a, re.DOTALL):
                return False
    # all: EACH group must have >=1 hit (AND between groups). Z1 requires 4 boys AND 3 girls,
    # otherwise "4 chlopcow, 100 dziewczynek" would pass (grok/codex round2 #4).
    if all_groups:
        for group in all_groups:
            if not any(re.search(k.lower(), a, re.DOTALL) for k in group):
                return False
        return True
    for k in keys:
        if re.search(k.lower(), a, re.DOTALL):
            return True
    return False


def main():
    args = sys.argv[1:]
    # --runs N: N full runs, report MEAN + range. Smooths out temp 0.7 noise (+-1)
    # and reveals variance (stable vs chaotic model). Defaults to 1.
    runs = 1
    if "--runs" in args:
        idx = args.index("--runs")
        try:
            runs = int(args[idx + 1])
        except (IndexError, ValueError):
            print("--runs requires a number")
            sys.exit(1)
        args = args[:idx] + args[idx + 2:]
    no_think = "--no-think" in args  # disables thinking on thinking-models
    # --think=VALUE: explicit level (false->disable; low/high->string for gpt-oss, which cannot
    # be disabled - harmony); otherwise --no-think -> False, no flag -> None (default mode).
    think_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--think=")), None)
    if think_arg is not None:
        think = False if think_arg == "false" else (None if think_arg in ("none", "default") else think_arg)
    else:
        think = False if no_think else None
    # --num-predict=N: token budget. Defaults to 3000, but with thinking ON the reasoning eats
    # the budget and the ANSWER can get truncated (as in bench_coding) - for thinking-on be generous.
    np_arg = next((a.split("=", 1)[1] for a in args if a.startswith("--num-predict=")), None)
    num_pred = int(np_arg) if np_arg else 3000
    models = [a for a in args if not a.startswith("--")]
    if not models:
        print("Usage: python3 bench_reasoning.py [--runs N] [--no-think|--think=low] [--num-predict=N] MODEL [...]")
        sys.exit(1)
    maxs = len(PUZZLES)

    all_results = {}
    for m in models:
        print(f"\n== {m} ==")
        run_scores, last_details = [], []
        for run_i in range(runs):
            score, details = 0, []
            for i, (q, keys, anti, all_g) in enumerate(PUZZLES, 1):
                try:
                    r = generate(m, q, num_predict=num_pred, think=think)
                    ans = r.get("response") or ""
                    trunc = r.get("done_reason") == "length"  # answer truncated by the budget
                except Exception as e:
                    details.append({"q": i, "error": str(e)})
                    continue
                ok = grade(ans, keys, anti, all_g)
                score += 1 if ok else 0
                if trunc:
                    print(f"    [!] q{i} TRUNCATED (num_predict={num_pred}) - possible false negative")
                details.append({"q": i, "ok": ok, "trunc": trunc, "answer": ans})
            run_scores.append(score)
            last_details = details
            print(f"  run {run_i + 1}: {score}/{maxs}")
        mean = sum(run_scores) / len(run_scores)
        if runs > 1:
            print(f"  MEAN: {mean:.1f}/{maxs}  (range {min(run_scores)}-{max(run_scores)}, runs {run_scores})")
        all_results[m] = {"mean": round(mean, 2), "runs": run_scores, "max": maxs, "details": last_details}

    print("\n== SUMMARY ==")
    for m, r in all_results.items():
        if len(r["runs"]) > 1:
            print(f"  {m:<30} mean {r['mean']}/{r['max']}  range {min(r['runs'])}-{max(r['runs'])}  {r['runs']}")
        else:
            print(f"  {m:<30} {r['runs'][0]}/{r['max']}")

    with open("results_reasoning.json", "w") as f:
        json.dump(all_results, f, ensure_ascii=False, indent=2)
    print("\nSaved: results_reasoning.json")


if __name__ == "__main__":
    main()
