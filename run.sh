#!/usr/bin/env bash
# Runs the whole benchmark and saves results to results_*.json.
# Edit the model list below to match what you have pulled (ollama list).
# -e: stop on the first failure (do not publish partial results as a full run);
# -u: error on an undefined variable; pipefail: status from the whole pipe (grok/codex #5)
set -euo pipefail
cd "$(dirname "$0")"

# Base (public) models - change to your variants if you have e.g. qwen-fast.
SPEED_MODELS=("qwen3-coder:30b" "gpt-oss:20b")
THINK_MODEL="gpt-oss:20b"
REASON_MODELS=("qwen3-coder:30b" "gpt-oss:20b")

echo "############ 1/5 tok/s (small prompt) ############"
python3 bench_speed.py "${SPEED_MODELS[@]}"

echo "############ 2/5 tok/s (big prompt ~12k) ############"
python3 bench_speed.py --big "${SPEED_MODELS[@]}"

echo "############ 3/5 num_predict (length vs limit) ############"
python3 bench_numpredict.py "${THINK_MODEL}"

echo "############ 4/5 logic puzzles (reasoning quality) ############"
python3 bench_reasoning.py "${REASON_MODELS[@]}"

echo "############ 5/5 code quality (generation + bug finding) ############"
python3 bench_coding.py "${REASON_MODELS[@]}"

echo
echo "Done. Results: results_speed.json, results_numpredict.json, results_reasoning.json, results_coding.json"
