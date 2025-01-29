import os

from config import *

from data_processor import DataProcessor

if __name__ == "__main__":
    data_processor = DataProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_move_step=SEGMENT_MOVE_STEP,
        save_to_file=True
    )
    
    for root, dirs, files in os.walk(DIRECTORY_PATH):
        for file in files:
            file_path = os.path.join(root, file)
            
            data_processor.run(file_path=file_path)