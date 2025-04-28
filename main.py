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
        if borders[t1].size == 0 or borders[t2].size == 0:
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

    os.makedirs(FLYBYS_PATH, exist_ok=True)
    h5_path = os.path.join(FLYBYS_PATH, f"{date_str}.h5")

    with h5.File(h5_path, 'w') as h5file:
        for st in stations:
            satellites = flybys[st].keys()
            for sat in satellites:
                for fb_index, fb_key in enumerate(flybys[st][sat].keys()):
                    logger.info(f"Process {st}_{sat}_{fb_key}")

                    crossing_events = crossings.get(st, {}).get(sat, [])

                    if fb_index < len(crossing_events):
                        events = sorted(
                            crossing_events[fb_index],
                            key=lambda e: dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f")
                        )
                        event_times = [
                            dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
                            for e in events
                        ]
                        event_types = [e['event'] for e in events]

                        cleaned_times, cleaned_types = clean_events(event_times, event_types)

                        group_path = f"{st}/{sat}/flyby_{fb_index}"
                        flyby_group = h5file.create_group(group_path)

                        # Сохраняем атрибуты times и types
                        flyby_group.attrs['times'] = [t.isoformat() for t in cleaned_times]
                        flyby_group.attrs['types'] = cleaned_types

                        # Сохраняем roti и timestamps
                        flyby_data = flybys[st][sat][fb_key]
                        flyby_group.create_dataset('roti', data=flyby_data['roti'])
                        flyby_group.create_dataset('timestamps', data=flyby_data['timestamps'])

                    else:
                        logger.warning(f'Flyby index is lower than the crossing events {st}_{sat}_{fb_key}')
                        break

    logger.info(f"Flyby HDF5 saved to {h5_path}")

if __name__ == "__main__":
    np.set_printoptions(threshold=np.inf)

    map_processor = MapProcessor(
        lon_condition=LON_CONDITION,
        lat_condition=LAT_CONDITION,
        segment_lon_step=SEGMENT_LON_STEP,
        segment_lat_step=SEGMENT_LAT_STEP,
        boundary_condition=BOUNDARY_CONDITION
    )
    
    for rinex_file in os.listdir(FILES_PATH):
        if rinex_file.endswith('.h5') and os.path.isfile(os.path.join(FILES_PATH, rinex_file)):
            try:
                date_str = rinex_file.split('.')[0]
                h5_filename = f'{date_str}.h5'
                full_rinex_path = os.path.join(FILES_PATH, rinex_file)
                
                with RinexProcessor(full_rinex_path) as processor:
                    processor.process(h5_filename)
                    satellite_data = processor.data
                    flybys = processor.flybys
                
                full_map_path = os.path.join(MAP_PATH, h5_filename)
                if os.path.isfile(full_map_path):
                    logger.debug(f"For file {rinex_file} a meshing file was found: {full_map_path}")
                    
                    boundary_output_path = os.path.join(BOUNDARY_PATH, h5_filename)
                    full_flyby_path = os.path.join(FLYBYS_PATH, h5_filename)
                    
                    map_processor.process(
                        map_path=full_map_path,
                        output_path=boundary_output_path
                    )
                    
                    # Теперь достаем данные для графика
                    with h5.File(boundary_output_path, 'r') as boundary_file:
                        for time_point in boundary_file.keys():
                            time_grp = boundary_file[time_point]

                            # Загружаем нужные промежуточные результаты
                            filtered_points = {
                                'lon': time_grp['filtered_points']['lon'][()],
                                'lat': time_grp['filtered_points']['lat'][()],
                                'vals': time_grp['filtered_points']['vals'][()],
                            }
                            sliding_windows = {
                                'lon': time_grp['sliding_windows']['lon'][()],
                                'lat': time_grp['sliding_windows']['lat'][()],
                                'vals': time_grp['sliding_windows']['vals'][()],
                            }
                            boundary = {
                                'lon': time_grp['boundary']['lon'][()],
                                'lat': time_grp['boundary']['lat'][()],
                            }

                            if "boundary_clusters" in time_grp:
                                boundary_clusters = {'relation': time_grp['boundary_clusters'].attrs['relation']}
                                for cluster_key in time_grp['boundary_clusters']:
                                    cluster_grp = time_grp['boundary_clusters'][cluster_key]
                                    boundary_clusters[cluster_key] = np.column_stack((
                                        cluster_grp['lon'][()],
                                        cluster_grp['lat'][()]
                                    )).tolist()
                            else:
                                boundary_clusters = None
                                
                                
                            process_flyby(
                                boundary=boundary,
                                satellite_data=satellite_data,
                                flybys=flybys,
                                date_str=date_str
                            )

                            # Теперь можно вызвать plot
                            plot_combined_graphs(
                                map_points=filtered_points,
                                sliding_windows=sliding_windows,
                                flyby_file=full_flyby_path,
                                boundary_data=boundary,
                                boundary_condition=BOUNDARY_CONDITION,
                                time_point=time_point,
                                boundary_clusters=boundary_clusters,
                                roti_file=full_rinex_path,
                                stations=['picl'],
                                save_to_file=True
                            )

                    break
                else:
                    logger.warning(f"Meshing file not found: {full_map_path}")
                    
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