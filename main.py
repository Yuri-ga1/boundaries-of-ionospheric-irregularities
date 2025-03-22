import json
import traceback
from config import *

from app.processors.data_processor import DataProcessor
from app.processors.rinex_processor import RinexProcessor
from app.png_to_video_converter import PngToVideoConverter

from debug_code.plot_graphs import *

import numpy as np

import matplotlib.pyplot as plt
# import matplotlib
# matplotlib.use('Agg')

from shapely.geometry import Point

def check_satellite_crossing(borders, satellites, threshold=10800):
    """
    Identifies moments when satellites cross boundaries, marking "entered" or "exited" events.

    :param borders: dict, containing boundary data for each timestamp.
    :param satellites: dict, containing satellite data with 'lon' and 'lat' for each timestamp.
    :param threshold: int, the time threshold in seconds to group crossings.
    :return: dict, a dictionary with satellite IDs as keys and a list of crossing events with timestamps and event types.
    """
    crossings = {}
    time_keys = sorted(borders.keys())

    for i in range(len(time_keys) - 1):
        t1, t2 = time_keys[i], time_keys[i + 1]
        if not borders[t1] or not borders[t2]:
            continue

        _, intersection1, single_cluster1 = compute_polygons(borders, t1)
        _, intersection2, single_cluster2 = compute_polygons(borders, t2)

        boundary1 = intersection1 if intersection1 else single_cluster1
        boundary2 = intersection2 if intersection2 else single_cluster2

        if not boundary1 or not boundary2:
            continue

        for sat, data in satellites.get(t1, {}).items():
            pos1, pos2 = Point(data['lon'], data['lat']), None
            if sat in satellites.get(t2, {}):
                pos2 = Point(satellites[t2][sat]['lon'], satellites[t2][sat]['lat'])

            if pos2:
                was_inside = boundary1.contains(pos1)
                is_inside = boundary2.contains(pos2)

                if was_inside and not is_inside:
                    event_type = "exited"
                elif not was_inside and is_inside:
                    event_type = "entered"
                else:
                    continue

                if sat not in crossings:
                    crossings[sat] = []

                if not crossings[sat] or (dt.strptime(t2, "%Y-%m-%d %H:%M:%S.%f") - dt.strptime(crossings[sat][-1][-1]['time'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds() > threshold:
                    crossings[sat].append([])

                crossings[sat][-1].append({"time": t2, "event": event_type})

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
    
    # with open("stations.txt", "r", encoding="utf-8") as file:
    #     content = file.read()
    #     stations = content.replace("dict_keys([", "").replace("])", "").replace("'", "").split(", ")
    
    # file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    # boundary = data_processor.process(
    #     file_path=file_path,
    #     roti_file="files/2019-05-14.h5",
    #     stations=['picl', 'dubo', 'gilc']
    #     # stations=['sask', 'picl', 'dubo', 'gilc']
    #     # stations=['chur', 'rabc', 'repc', 'kugc', 'will']
    # )
    
    # with open('boundary_clusters.json', "w") as file:
    #     json.dump(boundary, file, indent=4)
    
    # with RinexProcessor("files/2019-05-14.h5") as processor:
    #     processor.process()
        
    #     with open('roti_data.json', "w") as file:
    #         json.dump(processor.data, file, indent=4)
            
    #     with open('stations.txt', "w") as file:
    #         file.write(f"{processor.stations_coords.keys()}")
            
    #     file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    #     boundary = data_processor.process(
    #         file_path=file_path,
    #         stations=processor.stations_coords.keys()
    #     )
    
    # for root, dirs, files in os.walk(DIRECTORY_PATH):
    #     for file in files:
    #         file_path = os.path.join(root, file)
            
    #         boundary = data_processor.process(file_path=file_path)
    
    """
    Plot polygon from json file
    """
    # with open('boundary_clusters.json', "r") as file:
    #     boundary = json.load(file)
        
    # for time_point in boundary.keys():
    #     plot_polygon(
    #         boundary_clusters=boundary,
    #         time_point=time_point
    #     )
    """"""
    
    
    """
    Calculate satellite crossing count
    """
    with open('boundary_clusters.json', "r") as file:
        boundary = json.load(file)

    with open('roti_data.json', "r") as file:
        satellite_data = json.load(file)

    crossings = check_satellite_crossing(boundary, satellite_data)

    with open('crossings.json', "w") as file:
        json.dump(crossings, file, indent=4)

    sorted_entries = []
    with open('count_crossing.txt', "w") as file:
        for key, time_groups in crossings.items():
            for group in time_groups:
                crossings_count = len(group)
                if 0 <= crossings_count < 2:
                    events = ", ".join(f"{entry['time']} ({entry['event']})" for entry in group)
                    sorted_entries.append(f"{key} crossings border {crossings_count}: {events}\n")

        for entry in sorted(sorted_entries):
            file.write(entry)
    """"""
    converter = PngToVideoConverter(input_dir=FRAME_GRAPHS_PATH, output_dir=SAVE_VIDEO_PATH)
    converter.process_images_to_video()