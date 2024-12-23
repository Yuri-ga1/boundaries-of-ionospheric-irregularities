LON_CONDITION = -0.349066
LAT_CONDITION = 0.680678

DIRECTORY_PATH = 'files'

#number of points in the segment by which we calculate std
SEGMENT_LENGTH = 91

# Assessment of the difference between the first and second half of the data, to determine bad and good data (from 0 to 1)
DATA_CASE_THRESHOLD = 0.4
# Threshold for how long there was no data (in seconds)
TIMESTAMPS_THRESHOLD = 120
# Elevation cutoff in degrees
ELEVATION_CUTOFF = 15

from custom_logger import Logger

logger = Logger(
    filename="logs.log",
    console_logging=True
)