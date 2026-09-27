#!/bin/bash -l
# Tapis launches one coordinator; Femora launches the task-level MPI jobs.
set -eo pipefail

APP_DIR=$(cd -- "$(dirname -- "${BASH_SOURCE[0]}")" && pwd)
OUTPUT_DIR=${_tapisExecSystemOutputDir:-"$PWD/output"}
mkdir -p "$OUTPUT_DIR"
finish() {
    status=$?
    trap - EXIT
    printf '%s\n' "$status" > "$OUTPUT_DIR/tapisjob.exitcode"
    exit "$status"
}
trap finish EXIT

if [[ -z ${SLURM_JOB_ID:-${SLURM_JOBID:-}} ]]; then
    echo 'Femora requires a Slurm compute allocation, not a FORK/login-node job.' >&2
    exit 1
fi
if ! type module >/dev/null 2>&1; then
    echo 'The TACC module command is unavailable. Check the system batch environment.' >&2
    exit 1
fi

# These module settings are packaged by the app owner, not passed as shell code.
source "$APP_DIR/site.sh"
module load "$FEMORA_PYTHON_MODULE"
module use "$FEMORA_MODULE_PATH"
module load "$FEMORA_MODULE" "$FEMORA_OPENSEES_MODULE"
export FEMORA_OPENSEES
FEMORA_OPENSEES=$(command -v OpenSeesMP)
export OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 OPENBLAS_NUM_THREADS=1
export PYTHONNOUSERSITE=1

python "$APP_DIR/run_workflow.py" \
    --bundle "${_tapisExecSystemInputDir:-$PWD}/workflow.zip" \
    --workspace "${_tapisExecSystemExecDir:-$PWD}/work" \
    --output "$OUTPUT_DIR"
