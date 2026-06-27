#!/usr/bin/env bash
# Runs the whole benchmark and saves results to results_*.json.
# Edit the model list below to match what you have pulled (ollama list).
# -e: stop on the first failure (do not publish partial results as a full run);
# -u: error on an undefined variable; pipefail: status from the whole pipe.
set -euo pipefail
cd "$(dirname "$0")"

# Base (public) models - change to your variants if you have e.g. qwen-fast.
SPEED_MODELS=("qwen3-coder:30b" "gpt-oss:20b")
THINK_MODEL="gpt-oss:20b"
REASON_MODELS=("qwen3-coder:30b" "gpt-oss:20b")

echo "############ 1/5 tok/s (small prompt) ############"
python3 bench_speed.py "${SPEED_MODELS[@]}"
mv results_speed.json results_speed_small.json   # both runs write results_speed.json; keep each

echo "############ 2/5 tok/s (big prompt ~12k) ############"
python3 bench_speed.py --big "${SPEED_MODELS[@]}"
mv results_speed.json results_speed_big.json

echo "############ 3/5 num_predict (length vs limit) ############"
python3 bench_numpredict.py "${THINK_MODEL}"

echo "############ 4/5 logic puzzles (reasoning quality) ############"
# Generates answers only (no-thinking baseline by default). Grade them, and for per-model
# thinking use the canonical dispatcher: python3 run_bench.py reasoning fleet --runs 3
python3 bench_reasoning.py "${REASON_MODELS[@]}"

echo "############ 5/5 code quality (generation + bug finding) ############"
python3 bench_coding.py "${REASON_MODELS[@]}"

echo
echo "Done. Results: results_speed_small.json, results_speed_big.json, results_numpredict.json,"
echo "      answers_reasoning.json (grade with grade_reasoning.py), results_coding.json"
