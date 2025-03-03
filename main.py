import json
import traceback
from config import *

from app.processors.data_processor import DataProcessor
from app.processors.rinex_processor import RinexProcessor

from debug_code.plot_graphs import *

import numpy as np

import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.use('Agg')

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.validation import explain_validity

# TODO 4 панельки 

def get_valid_polygon(coords, timestamp, label):
    """Создает валидный полигон, исправляя ошибки, если необходимо."""
    poly = Polygon(coords)
    if not poly.is_valid:
        explain = explain_validity(poly)
        if explain != "Valid Geometry":
            logger.warning(f"Invalid {label} at {timestamp}: {explain}")
            poly = poly.buffer(0)
    return poly

def get_intersection(poly1, poly2):
    """Возвращает пересечение двух полигонов."""
    intersection = poly1.intersection(poly2)
    return intersection if not intersection.is_empty else None

def check_satellite_crossing(borders, satellites):
    """Определяет моменты пересечения границ спутниками."""
    crossings = {}
    time_keys = sorted(borders.keys())
    
    for i in range(len(time_keys) - 1):
        t1, t2 = time_keys[i], time_keys[i + 1]
        if not borders[t1] or not borders[t2]:
            continue
        
        poly1 = get_valid_polygon(borders[t1]['border1'], t1, "border1")
        poly2 = get_valid_polygon(borders[t1]['border2'], t1, "border2")
        intersection1 = get_intersection(poly1, poly2)
        
        poly3 = get_valid_polygon(borders[t2]['border1'], t2, "border1")
        poly4 = get_valid_polygon(borders[t2]['border2'], t2, "border2")
        intersection2 = get_intersection(poly3, poly4)
        
        if not intersection1 or not intersection2:
            continue
        
        for sat, data in satellites.get(t1, {}).items():
            pos1, pos2 = Point(data['lon'], data['lat']), None
            if sat in satellites.get(t2, {}):
                pos2 = Point(satellites[t2][sat]['lon'], satellites[t2][sat]['lat'])
            
            if pos2 and ((intersection1.contains(pos1) and not intersection2.contains(pos2)) or
                         (not intersection1.contains(pos1) and intersection2.contains(pos2))):
                crossings.setdefault(sat, []).append(t2)
    
    return crossings

if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    
    data_processor = DataProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_lon_step=SEGMENT_LON_STEP,
        segment_lat_step=SEGMENT_LAT_STEP,
        boundary_condition=BOUNDARY_CONDITION,
        save_to_file=True
    )
    
    file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    boundary = data_processor.process(
        file_path=file_path,
    )
    
    # with open('boundary_clusters.json', "w") as file:
    #     json.dump(boundary, file, indent=4)
    
    # with RinexProcessor("files/2019-05-14.h5") as processor:
    #     processor.process()
        
    #     with open('roti_data.json', "w") as file:
    #         json.dump(processor.data, file, indent=4)
            
    #     file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    #     boundary = data_processor.process(
    #         file_path=file_path,
    #         roti_data=processor.data
    #     )
    
    # for root, dirs, files in os.walk(DIRECTORY_PATH):
    #     for file in files:
    #         file_path = os.path.join(root, file)
            
    #         boundary = data_processor.process(file_path=file_path)
    
    # with open('boundary_clusters.json', "r") as file:
    #     boundary = json.load(file)
    
        
    # with open('roti_data.json', "r") as file:
    #     satellite_data = json.load(file)
    
    # crossings = check_satellite_crossing(boundary, satellite_data)
       
    # with open('crossings.json', "w") as file:
    #     json.dump(crossings, file, indent=4)
    
    # # with open('crossings.json', "r") as file:
    # #     crossings = json.load(file)
        
    # with open('count_crossing.txt', "w") as file:  
    #     for key in crossings.keys():
    #         crossing_time_points = crossings[key]
    #         crossings_count = len(crossing_time_points)
            
    #         if 0 <= crossings_count <= 2:
    #             file.write(f"{key} crossings border {crossings_count}\n")