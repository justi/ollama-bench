#!/usr/bin/env bash
# Odpala caly benchmark i zapisuje wyniki do results_*.json.
# Edytuj liste modeli ponizej pod to, co masz pobrane (ollama list).
set -u
cd "$(dirname "$0")"

# Modele bazowe (publiczne) - zmien na swoje warianty, jesli masz np. qwen-fast.
SPEED_MODELS=("qwen3-coder:30b" "gpt-oss:20b")
THINK_MODEL="gpt-oss:20b"
REASON_MODELS=("qwen3-coder:30b" "gpt-oss:20b")

echo "############ 1/4 tok/s (maly prompt) ############"
python3 bench_speed.py "${SPEED_MODELS[@]}"

echo "############ 2/4 tok/s (duzy prompt ~12k) ############"
python3 bench_speed.py --big "${SPEED_MODELS[@]}"

echo "############ 3/4 num_predict (dlugosc vs limit) ############"
python3 bench_numpredict.py "${THINK_MODEL}"

echo "############ 4/5 zagadki logiczne (jakosc reasoning) ############"
python3 bench_reasoning.py "${REASON_MODELS[@]}"

echo "############ 5/5 jakosc kodowa (generacja + bug finding) ############"
python3 bench_coding.py "${REASON_MODELS[@]}"

echo
echo "Gotowe. Wyniki: results_speed.json, results_numpredict.json, results_reasoning.json, results_coding.json"
