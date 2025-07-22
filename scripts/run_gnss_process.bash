#!/usr/bin/env bash

# Укажи имя своей Conda-среды
CONDA_ENV_NAME="boundaries-of-ionospheric-irregularities"

# Укажи путь к conda.sh
CONDA_SH="$HOME/miniconda3/etc/profile.d/conda.sh"

# Проверка наличия conda
if [ ! -f "$CONDA_SH" ]; then
    echo "conda.sh not found. Please check the CONDA_SH path."
    exit 1
fi

# Подгружаем conda
source "$CONDA_SH"
conda activate "$CONDA_ENV_NAME"

# Определим путь к скрипту
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
TARGET_SCRIPT="$SCRIPT_DIR/../gnss_processor/main.py"

# Запуск
python "$TARGET_SCRIPT"
