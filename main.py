import json
import traceback
from config import *

from app.processors.map_processor import MapProcessor
from app.processors.rinex_processor import RinexProcessor
from app.png_to_video_converter import PngToVideoConverter

from debug_code.plot_graphs import *

import numpy as np

import matplotlib.pyplot as plt
import matplotlib
matplotlib.use('Agg')

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
                
                st, sat = sat.split('_')

                if st not in crossings:
                    crossings[st] = {}
                if sat not in crossings[st]:
                    crossings[st][sat] = []

                if not crossings[st][sat] or (dt.strptime(t2, "%Y-%m-%d %H:%M:%S.%f") - dt.strptime(crossings[st][sat][-1][-1]['time'], "%Y-%m-%d %H:%M:%S.%f")).total_seconds() > threshold:
                    crossings[st][sat].append([])

                crossings[st][sat][-1].append({"time": t2, "event": event_type})

    return crossings

def process_flyby(boundary, satellite_data, flybys, date_str):
    crossings = check_satellite_crossing(boundary, satellite_data)
    stations = flybys.keys()
    all_metadata = {}

    for st in stations:
        satellites = flybys[st].keys()
        for sat in satellites:
            flyby_keys = list(flybys[st][sat].keys())
            for fb_index, fb_key in enumerate(flyby_keys):
                logger.info(f"Process {st}_{sat}_{fb_key}")

                crossing_events = crossings.get(st, {}).get(sat, [])

                if fb_index < len(crossing_events):
                    events = sorted(crossing_events[fb_index], key=lambda e: dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f"))
                    event_times = [dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC) for e in events]
                    event_types = [e['event'] for e in events]

                    cleaned_times, cleaned_types = clean_events(event_times, event_types)

                    metadata = {
                        'final_times': [t.isoformat() for t in cleaned_times],
                        'final_types': cleaned_types
                    }

                    relative_path = os.path.join(date_str, st, f"{sat}_flyby_{fb_index}.png")
                    all_metadata[relative_path] = metadata
                else:
                    logger.warning(f'Break {st}_{sat}_{fb_key}')
                    break

    metadata_save_dir = os.path.join(FLYBYS_GRAPHS_PATH, date_str)
    os.makedirs(metadata_save_dir, exist_ok=True)
    metadata_path = os.path.join(metadata_save_dir, 'metadata.json')

    with open(metadata_path, 'w') as f:
        json.dump(all_metadata, f, indent=4, ensure_ascii=False)

    logger.info(f"Metadata saved to {metadata_path}")

if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)

    map_processor = MapProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_lon_step=SEGMENT_LON_STEP,
        segment_lat_step=SEGMENT_LAT_STEP,
        boundary_condition=BOUNDARY_CONDITION,
        save_to_file=True
    )
    
    for rinex_file in os.listdir(FILES_PATH):
        if rinex_file.endswith('.h5') and os.path.isfile(os.path.join(FILES_PATH, rinex_file)):
            try:
                full_rinex_path = os.path.join(FILES_PATH, rinex_file)
                date_str = rinex_file.split('.')[0]
                date_obj = dt.strptime(date_str, '%Y-%m-%d')
                
                year = date_obj.year
                doy = date_obj.timetuple().tm_yday
                map_name = f'roti_{year}_{doy}.h5'
                
                with RinexProcessor(full_rinex_path) as processor:
                    processor.process(map_name)
                    satellite_data = processor.data
                    flybys = processor.flybys
                
                meshing_path = os.path.join(MESHING_PATH, map_name)
                if os.path.isfile(meshing_path):
                    # full_rinex_path = os.path.join(FILES_PATH, rinex_file)
                    logger.debug(f"For file {rinex_file} a meshing file was found: {meshing_path}")
                    
                    boundary = map_processor.process(
                        map_path=meshing_path,
                        roti_file=full_rinex_path,
                        # stations=['sask', 'picl', 'dubo', 'gilc']
                        stations=['picl']
                    )
                    # process_flyby(
                    #     full_meshing_path=full_meshing_path,
                    #     full_rinex_path=full_rinex_path,
                    #     date_str=date_str
                    # )

                    break
                else:
                    logger.warning(f"Meshing file not found: {meshing_path}")
                    
            except ValueError:
                logger.error(f"Incorrect file name format: {rinex_file}")

    
        
    #     with open('roti_data.json', "w") as file:
    #         json.dump(processor.data, file, indent=4)
            
    #     with open('stations.txt', "w") as file:
    #         file.write(f"{processor.stations_coords.keys()}")
            
    #     file_path = os.path.join("files", "meshing", 'roti_2019_134_-90_90_N_-180_180_E_ec78.h5')
    #     boundary = map_processor.process(
    #         file_path=file_path,
    #         stations=processor.stations_coords.keys()
    #     )
    
    # for root, dirs, files in os.walk(DIRECTORY_PATH):
    #     for file in files:
    #         file_path = os.path.join(root, file)
            
    #         boundary = map_processor.process(file_path=file_path)
    
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
    # with open('boundary_clusters.json', "r") as file:
    #     boundary = json.load(file)

    # with open('roti_data.json', "r") as file:
    #     satellite_data = json.load(file)

    # crossings = check_satellite_crossing(boundary, satellite_data)

    # with open('crossings.json', "w") as file:
    #     json.dump(crossings, file, indent=4)

    # sorted_entries = []
    # with open('count_crossing.txt', "w") as file:
    #     for key, time_groups in crossings.items():
    #         for group in time_groups:
    #             crossings_count = len(group)
    #             if 0 <= crossings_count < 2:
    #                 events = ", ".join(f"{entry['time']} ({entry['event']})" for entry in group)
    #                 sorted_entries.append(f"{key} crossings border {crossings_count}: {events}\n")

    #     for entry in sorted(sorted_entries):
    #         file.write(entry)
    """"""
    # converter = PngToVideoConverter(input_dir=FRAME_GRAPHS_PATH, output_dir=SAVE_VIDEO_PATH)
    # converter.process_images_to_video()
    
    """
    Inside/out polygon by satellite flyby
    """
    # with open('flybys.json', "r") as file:
    #     flybys = json.load(file)
    
    # with open('crossings.json', "r") as file:
    #     crossings = json.load(file)

    # stations = flybys.keys()
    # for st in stations:
    #     satellites = flybys[st].keys()
    #     for sat in satellites:
    #         flyby_keys = list(flybys[st][sat].keys())
    #         for fb_index, fb_key in enumerate(flyby_keys):
    #             logger.info(f"Process {st}_{sat}_{fb_key}")
    #             roti = flybys[st][sat][fb_key]['roti']
    #             ts = flybys[st][sat][fb_key]['timestamps']
    #             crossing_events = crossings.get(st, {}).get(sat, [])
                
    #             fig, ax = plt.subplots(figsize=(10, 5))

    #             if fb_index < len(crossing_events):
                    
    #                 plot_flyby(roti=roti, ts=ts, station=st, satellite=sat,
    #                         crossing_events=crossing_events[fb_index], ax=ax)
    #             else:
    #                 logger.warning(f'Break {st}_{sat}_{fb_key}')
    #                 plt.close()
    #                 break

    #             save_dir = os.path.join("graphs", "flybys", st)
    #             os.makedirs(save_dir, exist_ok=True)

    #             save_path = os.path.join(save_dir, f"{sat}_flyby_{fb_index}.png")
    #             fig.savefig(save_path, bbox_inches="tight")
    #             plt.close(fig)