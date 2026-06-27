#!/usr/bin/env python3
"""Canonical benchmark dispatcher - reads models.json (the single source of truth) and runs each
model with ITS per-task think + num_predict, so invocations are never hand-assembled (no forgotten
--think flag, no guessed temperature, no drifting num_predict). It PRINTS the exact command per
model before running, so the invocation is auditable.

  python3 run_bench.py reasoning gemma-best qwen36-best --runs 10
  python3 run_bench.py reasoning all --runs 3
  BENCH_PROMPTS=prompts_en.json python3 run_bench.py reasoning gemma-best   # language passthrough
  python3 run_bench.py code gemma-best --expert
  python3 run_bench.py code fleet --expert --runs 10   # n=10, one committed command (reproducible)
  python3 run_bench.py code fleet --mutated
  python3 run_bench.py speed fleet

task = reasoning | code | speed. Models: explicit names, 'fleet' (8 main, no deepseek), or 'all'.
--runs N (default 3) applies to BOTH reasoning and code (code loops bench_coding N times per model,
model stays warm between passes). Code set flag (--default/--hard/--expert/--mutated) is passed
through; think/num_predict come from the manifest. Speed runs one isolated bench_speed call.
"""
import json
import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
MANIFEST = json.load(open(os.path.join(HERE, "models.json")))["models"]
FLEET = ["qwen36-best", "qwen-coder-best", "gpt-oss-best", "north-best",
         "phi4-best", "devstral-best", "unsloth-q4xl-best", "gemma-best"]


def resolve_models(tokens):
    out = []
    for t in tokens:
        if t == "all":
            out += list(MANIFEST.keys())
        elif t == "fleet":
            out += FLEET
        elif t in MANIFEST:
            out.append(t)
        else:
            print(f"[!] unknown model '{t}' (not in models.json)")
            sys.exit(1)
    seen, uniq = set(), []
    for m in out:
        if m not in seen:
            seen.add(m); uniq.append(m)
    return uniq


def run(cmd):
    print("  $ " + " ".join(cmd))
    return subprocess.call(cmd, cwd=HERE)


def main():
    args = sys.argv[1:]
    if len(args) < 2:
        print(__doc__)
        sys.exit(1)
    task = args[0]
    if task not in ("reasoning", "code", "speed"):
        print(f"[!] unknown task '{task}' (expected: reasoning | code | speed)")
        sys.exit(1)
    runs = "3"
    if "--runs" in args:
        i = args.index("--runs")
        if i + 1 >= len(args) or not args[i + 1].isdigit() or int(args[i + 1]) < 1:
            print("[!] --runs requires a positive integer")
            sys.exit(1)
        runs = args[i + 1]
        args = args[:i] + args[i + 2:]
    set_flags = [a for a in args[1:] if a.startswith("--")]      # e.g. --expert / --mutated
    model_tokens = [a for a in args[1:] if not a.startswith("--")]
    models = resolve_models(model_tokens)
    if not models:
        print("[!] no models resolved"); sys.exit(1)

    prompts = os.environ.get("BENCH_PROMPTS", "prompts_pl.json")
    print(f"== {task} | models: {', '.join(models)} | prompts: {prompts} ==\n")

    if task == "speed":
        # one isolated call; speed.think is 'false' for all = throughput convention
        miss = [m for m in models if MANIFEST[m]["tasks"]["speed"]["think"] != "false"]
        flag = ["--think=false"]
        print(f"(speed: think=false for all{'; NOTE leveled-thinking models present: ' + ','.join(miss) if miss else ''})")
        sys.exit(run([sys.executable, "bench_speed.py"] + flag + models))

    rc = 0
    for m in models:
        cfg = MANIFEST[m]["tasks"].get("reasoning" if task == "reasoning" else "code")
        if cfg is None:
            print(f"[!] no '{task}' config for {m}"); rc = 1; continue
        think = cfg["think"]
        np = str(cfg["num_predict"])
        print(f"-- {m}  (think={think}, num_predict={np}, runs={runs})")
        if task == "reasoning":
            # bench_reasoning has native --runs (saves all runs in one answers file)
            lang = prompts.replace("prompts_", "").replace(".json", "")
            out = f"answers_reasoning_{m}_{lang}.json"
            cmd = [sys.executable, "bench_reasoning.py", "--runs", runs,
                   f"--think={think}", f"--num-predict={np}", f"--out={out}", m]
            rc |= run(cmd) or 0
        else:  # code - bench_coding is single-pass, so loop it here (model stays warm between passes)
            base = [sys.executable, "bench_coding.py"] + set_flags + \
                   [f"--think={think}", f"--num-predict={np}", m]
            for r in range(int(runs)):
                if int(runs) > 1:
                    print(f"   [pass {r + 1}/{runs}]")
                rc |= run(base) or 0
        print()
    sys.exit(rc)


if __name__ == "__main__":
    main()
