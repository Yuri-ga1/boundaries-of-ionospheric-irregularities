#!/usr/bin/env bash

# Укажи имя своей Conda-среды
CONDA_ENV_NAME="bii_nw"

CONDA_SH="$HOME/miniconda3/etc/profile.d/conda.sh"

if [ ! -f "$CONDA_SH" ]; then
    echo "conda.sh not found. Please check the CONDA_SH path."
    exit 1
fi

source "$CONDA_SH"
conda activate "$CONDA_ENV_NAME"

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/../nn_training/main.py"

python "$TARGET_SCRIPT"
