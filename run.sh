#!/usr/bin/env bash
# Full benchmark suite - CONFIG-DRIVEN via run_bench.py (models.json is the single source of truth).
# Every per-model knob (sampling, num_ctx, think, num_predict, bug_num_predict) comes from
# models.json / the generated Modelfiles; this script only picks WHICH models and HOW MANY runs.
# No silent defaults: the bench_* scripts hard-error on a missing budget, so a run is never ambiguous.
#
# Prereq: build the variants first - for each KEY below:
#   ollama create <key> -f configs/<key>.best.Modelfile   (base tag must be pulled)
# Edit MODELS to match what you have built (ollama list). Comment out anything not pulled.
# -e: stop on first failure (no partial results as a full run); -u: undefined var = error; pipefail.
set -euo pipefail
cd "$(dirname "$0")"

# Manifest KEYS from models.json (NOT base tags like qwen3-coder:30b).
MODELS=(
  qwen36-best qwen-coder-best gpt-oss-best north-best
  phi4-best devstral-best unsloth-q4xl-best gemma-best
  # laguna-best gemma12b-best      # new candidates (2026-07): uncomment AFTER ollama pull + ollama create
  # deepseek-r1-best               # available but excluded by default: ~4 tok/s makes n=100 impractical
)
RUNS_CODE="${RUNS_CODE:-10}"        # sane default; the published canonical run is RUNS_CODE=100 (long: 100 x models x expert set)
RUNS_REASON="${RUNS_REASON:-3}"     # reasoning n=3 (answers saved per model; grade with grade_reasoning.py)

echo "############ 1/4 speed - small prompt (think=false, isolated, median of 3) ############"
python3 run_bench.py speed "${MODELS[@]}"
mv results_speed.json results_speed_small.json      # both speed runs write results_speed.json; keep each

echo "############ 2/4 speed - big prompt (~12k tokens) ############"
# --big is NOT exposed via run_bench; bench_speed has no per-model config (sampling from the Modelfile,
# generation budget is a fixed methodology constant equal for all models), so this direct call stays config-clean.
python3 bench_speed.py --big "${MODELS[@]}"
mv results_speed.json results_speed_big.json

echo "############ 3/4 reasoning - logic puzzles (per-model thinking from models.json) ############"
# Generates answers only -> answers_reasoning_<model>_<lang>.json. Grade separately with grade_reasoning.py.
python3 run_bench.py reasoning "${MODELS[@]}" --runs "$RUNS_REASON"

echo "############ 4/4 code quality - expert set (generation + bug finding) ############"
# run_bench calls bench_coding once per model, so results_coding.json is overwritten per model -
# tee the full transcript to a log so every model's score is captured (parse with _parse100.py).
python3 run_bench.py code "${MODELS[@]}" --expert --runs "$RUNS_CODE" 2>&1 | tee results_code_run.log

echo
echo "Done. Results:"
echo "  speed     -> results_speed_small.json, results_speed_big.json"
echo "  reasoning -> answers_reasoning_<model>_pl.json  (grade: python3 grade_reasoning.py <file>)"
echo "  code      -> results_code_run.log  (per-model scores; results_coding.json = last model only)"
