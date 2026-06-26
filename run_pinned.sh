#!/usr/bin/env bash
# Run a benchmark via run_bench.py, optionally pinning the ollama systemd service to specific
# GPU(s) first and restoring the previous pin afterwards. Useful on multi-GPU hosts where a big
# model must land on a card with enough VRAM: CPU offload is not only slower but measurably
# DEGRADES quality (measured: qwen36 expert median 5.5 spilled to CPU vs 6 fully on GPU).
#
# Usage:
#   ./run_pinned.sh --task code --set --expert --runs 100 --models "qwen36-best gpt-oss-best"
#   ./run_pinned.sh --gpus 0,1 --restore-gpus 1 --task code --set --expert --runs 100 --models fleet
#   GPUS=GPU-aaa,GPU-bbb RESTORE_GPUS=GPU-bbb ./run_pinned.sh --task reasoning --runs 10 --models fleet
#
# Options (env equivalents in CAPS, flags win):
#   --gpus VALUE          CUDA_VISIBLE_DEVICES to pin the ollama service to (indices or UUIDs).
#                         Omit to leave the GPU config untouched.
#   --restore-gpus VALUE  CUDA_VISIBLE_DEVICES to restore after the run (e.g. your daytime default).
#   --task TASK           code | reasoning | speed                 (default: code)
#   --set FLAG            code task set: --default|--hard|--expert|--mutated  (default: --expert)
#   --runs N              repetitions, passed to run_bench --runs   (default: 3)
#   --models LIST         space-separated names, or 'fleet'/'all'  (default: fleet)
#   --out FILE            log file                                  (default: run_<task>.log)
#
# Requires: run_bench.py + models.json in the same dir. --gpus/--restore-gpus additionally need a
# systemd-managed ollama service and passwordless sudo (restarts the service to apply the pin).
set -euo pipefail

GPUS="${GPUS:-}"
RESTORE_GPUS="${RESTORE_GPUS:-}"
TASK="${TASK:-code}"
SET="${SET:-}"
RUNS="${RUNS:-3}"
MODELS="${MODELS:-fleet}"
OUT="${OUT:-}"

need_val() { [ -n "${2-}" ] || { echo "[!] $1 requires a value" >&2; exit 2; }; }
while [ $# -gt 0 ]; do
  case "$1" in
    --gpus)         need_val "$1" "${2-}"; GPUS="$2"; shift 2 ;;
    --restore-gpus) need_val "$1" "${2-}"; RESTORE_GPUS="$2"; shift 2 ;;
    --task)         need_val "$1" "${2-}"; TASK="$2"; shift 2 ;;
    --set)          need_val "$1" "${2-}"; SET="$2"; shift 2 ;;
    --runs)         need_val "$1" "${2-}"; RUNS="$2"; shift 2 ;;
    --models)       need_val "$1" "${2-}"; MODELS="$2"; shift 2 ;;
    --out)          need_val "$1" "${2-}"; OUT="$2"; shift 2 ;;
    -h|--help)      sed -n '2,/^set -/p' "$0" | sed '$d'; exit 0 ;;
    *) echo "[!] unknown option: $1" >&2; exit 2 ;;
  esac
done

case "$TASK" in code|reasoning|speed) ;; *) echo "[!] --task must be code|reasoning|speed" >&2; exit 2 ;; esac
case "$RUNS" in ''|*[!0-9]*) echo "[!] --runs must be a positive integer" >&2; exit 2 ;; esac
[ "$RUNS" -ge 1 ] || { echo "[!] --runs must be >= 1" >&2; exit 2; }
OUT="${OUT:-run_${TASK}.log}"

HERE="$(cd "$(dirname "$0")" && pwd)"
cd "$HERE"
[ -f run_bench.py ] || { echo "[!] run_bench.py not found in $HERE" >&2; exit 1; }

GPU_DROPIN=/etc/systemd/system/ollama.service.d/gpu.conf
pin_gpus() {  # $1 = CUDA_VISIBLE_DEVICES value
  echo "=== pin ollama to CUDA_VISIBLE_DEVICES=$1 ==="
  sudo mkdir -p "$(dirname "$GPU_DROPIN")"
  printf '[Service]\nEnvironment="CUDA_VISIBLE_DEVICES=%s"\n' "$1" | sudo tee "$GPU_DROPIN" >/dev/null
  sudo systemctl daemon-reload
  sudo systemctl restart ollama
  sleep 6
}

# restore the pin even if the run fails, so the host is not left on the wrong GPUs
restore() { [ -n "$RESTORE_GPUS" ] && pin_gpus "$RESTORE_GPUS" || true; }
[ -n "$GPUS" ] && trap restore EXIT

[ -n "$GPUS" ] && pin_gpus "$GPUS"

echo "=== $TASK | models: $MODELS | runs: $RUNS${SET:+ | set: $SET} -> $OUT ==="
set -f  # disable globbing so words in $MODELS/$SET are split into argv but not glob-expanded
# shellcheck disable=SC2086  # MODELS/SET are intentionally word-split into argv
if [ "$TASK" = "speed" ]; then
  python3 run_bench.py "$TASK" $MODELS 2>&1 | tee "$OUT"
else
  # awk (not grep) so an empty match does NOT exit non-zero and trip pipefail; a run_bench
  # failure still propagates (python's non-zero is the rightmost failing pipe element).
  python3 run_bench.py "$TASK" $MODELS $SET --runs "$RUNS" 2>&1 \
    | awk '/^-- |SCORE:|run [0-9]|Saved|mean/ { print; fflush() }' | tee "$OUT"
fi
set +f
echo "RUN_DONE" | tee -a "$OUT"
