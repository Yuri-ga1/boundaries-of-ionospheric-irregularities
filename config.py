LON_CONDITION = -60
LAT_CONDITION = 40

SEGMENT_LON_STEP = 0.2
SEGMENT_LAT_STEP = 1

BOUNDARY_CONDITION = 0.07

WINDOW_WIDTH=10
WINDOW_AREA = 50

import os
DIRECTORY_PATH =  os.path.join("files", "meshing")

from custom_logger import Logger

logger = Logger(
    filename="logs.log",
    console_logging=True
)