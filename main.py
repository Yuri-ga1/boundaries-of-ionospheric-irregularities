import json
from config import *

from app.processors.data_processor import DataProcessor
from app.processors.rinex_processor import RinexProcessor


if __name__ == "__main__":
    data_processor = DataProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_lon_step=SEGMENT_LON_STEP,
        segment_lat_step=SEGMENT_LAT_STEP,
        boundary_condition=BOUNDARY_CONDITION,
        save_to_file=False
    )
    
    with RinexProcessor("files/2019-05-14.h5") as processor:
        processor.process()
        
        with open('roti_data_radians.json', "w") as file:
            json.dump(processor.data, file, indent=4)
            
        file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
        boundary = data_processor.process(
            file_path=file_path,
            roti_data=processor.data,
            time_points=['2019-05-14 02:10:00.000000']
        )
    
    # for root, dirs, files in os.walk(DIRECTORY_PATH):
    #     for file in files:
    #         file_path = os.path.join(root, file)
            
    #         boundary = data_processor.process(file_path=file_path)
    
    
    # with open('roti_data_radians.json', "r") as file:
    #     data = json.load(file)
    
    # file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    # boundary = data_processor.process(
    #     file_path=file_path,
    #     roti_data=data,
    #     time_points=['2019-05-14 02:10:00.000000']
    # )
    
    