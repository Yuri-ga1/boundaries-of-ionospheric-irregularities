import os

from config import *

from data_processor import DataProcessor

file_path = os.path.join("files", "2016-10-25.h5")
# stations = ['kugc', 'will', 'fsic', 'rabc', 'corc', 'ais5', 'pot6', 'sch2', 'invk', 'ac52', 'ab01', 'txdl']
stations = ['kugc']


if __name__ == "__main__":
    data_processor = DataProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        elevation_cutoff=ELEVATION_CUTOFF,
        data_case_threshold=DATA_CASE_THRESHOLD,
        timestamps_threshold=TIMESTAMPS_THRESHOLD,
        segment_length=SEGMENT_LENGTH,
        save_to_file=True
    )
    
    data_processor.run(
        file_path=file_path,
        stations=stations
    )