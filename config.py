LON_CONDITION = -0.349066
LAT_CONDITION = 45

SEGMENT_MOVE_STEP = 0.1

import os
DIRECTORY_PATH =  os.path.join("files", "meshing")

from custom_logger import Logger

logger = Logger(
    filename="logs.log",
    console_logging=True
)