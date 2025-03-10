LON_CONDITION = -60
LAT_CONDITION = 40

SEGMENT_LON_STEP = 0.2
SEGMENT_LAT_STEP = 0.7

BOUNDARY_CONDITION = 0.07

WINDOW_WIDTH=10
WINDOW_AREA = 50

RE_KM = 6356
HM = 300

MIN_CLUSTER_SIZE = 100

import os
DIRECTORY_PATH =  os.path.join("files", "meshing")

FRAME_GRAPHS_PATH = os.path.join('graphs', 'combined')
SAVE_VIDEO_PATH = os.path.join('graphs', 'video')

from custom_logger import Logger

logger = Logger(
    filename="logs.log",
    console_logging=False
)