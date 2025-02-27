import json
import traceback
from config import *

from app.processors.data_processor import DataProcessor
from app.processors.rinex_processor import RinexProcessor

import numpy as np

import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.use('Agg')

from shapely.geometry import Point, Polygon, MultiPolygon
from shapely.validation import explain_validity


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
            
def plot_polygon(boundary_clusters):
    for timestamp, entry in boundary_clusters.items():
        if not entry or entry.get('relation') == "left-right":
            continue
        
        cluster1 = np.array(entry["border1"])
        cluster2 = np.array(entry["border2"])
        
        
        if entry['relation'] == "top-bottom":
            polygon1 = Polygon(cluster1)
            polygon2 = Polygon(cluster2)
            
            if not polygon1.is_valid:
                explain = explain_validity(polygon1)
                if explain != "Valid Geometry":
                    logger.warning(f"Invalid polygon1 at {timestamp}:\n{explain}")
                    polygon1 = polygon1.buffer(0)
                
            if not polygon2.is_valid:
                explain = explain_validity(polygon2)
                if explain != "Valid Geometry":
                    logger.warning(f"Invalid polygon2 at {timestamp}:\n{explain}")
                    polygon2 = polygon2.buffer(0)
            
            intersection = polygon1.intersection(polygon2)
            fig, ax = plt.subplots()
            
            if isinstance(polygon1, Polygon):
                x1, y1 = polygon1.exterior.xy
                ax.plot(x1, y1, 'b--', label="Polygon 1")
            elif isinstance(polygon1, MultiPolygon):
                for i, poly in enumerate(polygon1.geoms):
                    x1, y1 = poly.exterior.xy
                    ax.plot(x1, y1, 'b--', label=f"Polygon 1 - Part {i+1}")

            if isinstance(polygon2, Polygon):
                x2, y2 = polygon2.exterior.xy
                ax.plot(x2, y2, 'r--', label="Polygon 2")
            elif isinstance(polygon2, MultiPolygon):
                for i, poly in enumerate(polygon2.geoms):
                    x2, y2 = poly.exterior.xy
                    ax.plot(x2, y2, 'r--', label=f"Polygon 2 - Part {i+1}")

            try:
                if not intersection.is_empty:
                    if isinstance(intersection, Polygon):  # Один полигон
                        x_int, y_int = intersection.exterior.xy
                        ax.fill(x_int, y_int, 'purple', alpha=0.5, label="Intersection")
                    elif isinstance(intersection, MultiPolygon):  # Несколько полигонов
                        for poly in intersection.geoms:
                            x_int, y_int = poly.exterior.xy
                            ax.fill(x_int, y_int, 'purple', alpha=0.5)
            except Exception as e:
                logger.error(f"Error while bilding polygon: {traceback.format_exc(e)}")
        
        # Если relation "left-right", строим два отдельных полигона
        elif entry['relation'] == "left-right":
            # Полигон для первого кластера: его точки + точки соединения
            cluster1_polygon = np.vstack([cluster1])
            cluster2_polygon = np.vstack([cluster2])
            
            ax.fill(cluster1_polygon[:, 0], cluster1_polygon[:, 1], 'b', alpha=0.3, label='Cluster 1 Polygon')
            ax.fill(cluster2_polygon[:, 0], cluster2_polygon[:, 1], 'r', alpha=0.3, label='Cluster 2 Polygon')

        ax.set_title(f"{timestamp} ({entry['relation']})")
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.legend()
        plt.show()


if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)
    
    # data_processor = DataProcessor(
    #     lon_condition=LON_CONDITION,
    #     lat_condition=LAT_CONDITION,
    #     segment_lon_step=SEGMENT_LON_STEP,
    #     segment_lat_step=SEGMENT_LAT_STEP,
    #     boundary_condition=BOUNDARY_CONDITION,
    #     save_to_file=False
    # )
    
    # file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    # boundary = data_processor.process(
    #     file_path=file_path,
    # )
    
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
    
    """
    """
    with open('boundary_clusters.json', "r") as file:
        boundary = json.load(file)    
        
    with open('roti_data.json', "r") as file:
        satellite_data = json.load(file)
    
    crossings = check_satellite_crossing(boundary, satellite_data)
       
    with open('crossings.json', "w") as file:
        json.dump(crossings, file, indent=4)
    
    # with open('crossings.json', "r") as file:
    #     crossings = json.load(file)
        
    with open('count_crossing.txt', "w") as file:  
        for key in crossings.keys():
            crossing_time_points = crossings[key]
            crossings_count = len(crossing_time_points)
            
            if 0 <= crossings_count <= 2:
                file.write(f"{key} crossings border {crossings_count}\n")