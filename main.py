import os

from config import *

from data_processor import DataProcessor

if __name__ == "__main__":
    data_processor = DataProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_lon_step=SEGMENT_LON_STEP,
        segment_lat_step=SEGMENT_LAT_STEP,
        boundary_condition=BOUNDARY_CONDITION,
        save_to_file=False
    )
    
    for root, dirs, files in os.walk(DIRECTORY_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            
            data_processor.run(file_path=file_path)