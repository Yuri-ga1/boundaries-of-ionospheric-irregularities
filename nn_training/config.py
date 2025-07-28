import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
FILES_PATH = os.path.join(SCRIPT_DIR, '..', 'files')
MODEL_PATH = os.path.join(FILES_PATH, 'neural_networks', 'model_v2-1.keras')
DATASET = os.path.join(FILES_PATH, 'datasets', 'dataset_v2-1.h5')

ONE_WEIGTH = 16
ZERO_WEIGTH= 1

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from custom_logger import Logger

logger = Logger(
    filename="neural_network_training.log",
    console_logging=False
)