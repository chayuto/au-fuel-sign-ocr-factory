#!/bin/bash
# EXP-029 driver: 3-seed A/B comparing pre-QA labels vs post-QA labels
# Wall time ~4 hrs. Logs to logs/exp029/

set -u
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

mkdir -p logs/exp029 runs/finder
DRIVER_LOG="logs/exp029/driver.log"

log() { echo "[$(date '+%Y-%m-%d %H:%M:%S')] $*" | tee -a "$DRIVER_LOG"; }

failed_runs=()

run_train() {
    local name="$1"; local seed="$2"; local data_yaml="$3"
    log "START train: $name (seed=$seed, data=$data_yaml)"
    if PYTORCH_ENABLE_MPS_FALLBACK=1 .venv/bin/yolo detect train \
            data="$data_yaml" model=yolo26n.pt \
            epochs=50 imgsz=640 batch=4 device=mps amp=False \
            freeze=0 mosaic=0.5 seed="$seed" \
            project=runs/finder name="$name" \
            > "logs/exp029/${name}.log" 2>&1; then
        log "DONE train: $name"
    else
        log "FAIL train: $name (continuing)"
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
            > "logs/exp029/${name}.log" 2>&1; then
        log "DONE eval: $name"
    else
        log "FAIL eval: $name (continuing)"
        failed_runs+=("eval:$name")
    fi
}

log "==== EXP-029 driver start ===="
log "Phase 1: baseline replicates (data/finder = April 13 state)"

run_train exp029_baseline_s43 43 data/finder/dataset.yaml
run_train exp029_baseline_s44 44 data/finder/dataset.yaml

log "Phase 2: backup baseline data, rebuild with today's QA labels"
if [ ! -d data/finder_baseline ]; then
    mv data/finder data/finder_baseline
    log "  Moved data/finder → data/finder_baseline"
else
    log "  data/finder_baseline already exists; skipping move"
fi

if [ ! -d data/finder ] || [ -z "$(ls -A data/finder 2>/dev/null)" ]; then
    .venv/bin/python scripts/build_finder_dataset.py \
        --classes 0 --seed 42 \
        --freeze-split data/finder_baseline/image_manifest.json \
        > logs/exp029/dataset_rebuild.log 2>&1
    log "  Rebuilt data/finder from current annotations"
else
    log "  data/finder already populated; skipping rebuild"
fi

log "Phase 3: treatment runs"
run_train exp029_treatment_s42 42 data/finder/dataset.yaml
run_train exp029_treatment_s43 43 data/finder/dataset.yaml
run_train exp029_treatment_s44 44 data/finder/dataset.yaml

log "Phase 4: eval all on canonical_test_v2"
# Re-eval EXP-024a (baseline seed=42 already trained Apr 13)
EXP024A_BEST="runs/detect/runs/finder/exp024a_freeze0/weights/best.pt"
if [ -f "$EXP024A_BEST" ]; then
    run_eval exp029_eval_baseline_s42_recheck "$EXP024A_BEST"
else
    log "  EXP-024a best.pt not found at $EXP024A_BEST; skipping recheck"
fi

for run in baseline_s43 baseline_s44 treatment_s42 treatment_s43 treatment_s44; do
    weights="runs/detect/runs/finder/exp029_${run}/weights/best.pt"
    if [ -f "$weights" ]; then
        run_eval "exp029_eval_${run}" "$weights"
    else
        log "  Missing $weights; skipping eval for $run"
    fi
done

log "==== EXP-029 driver complete ===="
if [ ${#failed_runs[@]} -gt 0 ]; then
    log "FAILED runs: ${failed_runs[*]}"
else
    log "All runs OK"
fi
