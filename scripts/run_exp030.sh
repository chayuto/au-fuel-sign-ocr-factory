#!/bin/bash
# EXP-030 driver: train 3 seeds on the clean (zero-leakage) split, eval on canonical_test_v2.
# Wall time ~2.5 hrs.

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p logs/exp030 runs/finder
DRIVER_LOG="logs/exp030/driver.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DRIVER_LOG"; }

failed_runs=()

run_train() {
    local name="$1"; local seed="$2"
    log "START train: $name (seed=$seed)"
    if PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
            data=data/finder/dataset.yaml model=yolo26n.pt \
            epochs=50 imgsz=640 batch=4 device=mps amp=False \
            freeze=0 mosaic=0.5 seed="$seed" \
            project=runs/finder name="$name" \
            > "logs/exp030/${name}.log" 2>&1; then
        log "DONE train: $name"
    else
        log "FAIL train: $name"
        failed_runs+=("train:$name")
    fi
}

run_eval() {
    local name="$1"; local weights="$2"
    log "START eval: $name"
    if PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect val \
            data=data/finder_canonical_test_v2/dataset.yaml \
            model="$weights" \
            device=mps amp=False end2end=False \
            project=runs/finder name="$name" \
            > "logs/exp030/${name}.log" 2>&1; then
        log "DONE eval: $name"
    else
        log "FAIL eval: $name"
        failed_runs+=("eval:$name")
    fi
}

log "==== EXP-030 driver start (clean split, no canonical_test_v2 leakage) ===="
log "Dataset: 460 train / 89 val / 31 test_local | eval: canonical_test_v2 (50)"

for seed in 42 43 44; do
    run_train "exp030_clean_s${seed}" "$seed"
done

log "Eval all on canonical_test_v2"
for seed in 42 43 44; do
    weights="runs/detect/runs/finder/exp030_clean_s${seed}/weights/best.pt"
    if [ -f "$weights" ]; then
        run_eval "exp030_eval_s${seed}" "$weights"
    else
        log "  Missing $weights; skipping eval"
    fi
done

log "==== EXP-030 driver complete ===="
if [ ${#failed_runs[@]} -gt 0 ]; then
    log "FAILED runs: ${failed_runs[*]}"
else
    log "All runs OK"
fi
