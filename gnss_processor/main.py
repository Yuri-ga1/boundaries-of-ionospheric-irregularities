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

def generate_5min_timestamps(flyby_datetimes):
    """
    Генерирует список строк времени с шагом 5 минут, 
    покрывающий диапазон flyby_datetimes и заканчивающийся на :00 или :05.

    :param flyby_datetimes: список меток времени
    :return: список строк времени в формате "%Y-%m-%d %H:%M:%S.%f"
    """
    start_time = min(flyby_datetimes)
    end_time = max(flyby_datetimes)

    # Округление начала до ближайшего >= ближайшего кратного 5 минут
    minute = (start_time.minute // 5) * 5
    start_time_rounded = start_time.replace(minute=minute, second=0, microsecond=0)
    if start_time > start_time_rounded:
        start_time_rounded += timedelta(minutes=5)

    # Шаг в 5 минут до конца
    five_min_steps = []
    current = start_time_rounded
    while current <= end_time:
        five_min_steps.append(current.strftime("%Y-%m-%d %H:%M:%S.%f"))
        current += timedelta(minutes=5)

    return five_min_steps

def check_satellite_crossing(borders, satellites, threshold=10800):
    """
    Identifies moments when satellites cross boundaries, marking "entered" or "exited" events.

    :param borders: dict, containing boundary data for each timestamp.
    :param satellites: dict, containing satellite data with 'lon' and 'lat' for each timestamp.
    :param threshold: int, the time threshold in seconds to group crossings.
    :return: dict, a dictionary with satellite IDs as keys and a list of crossing events with timestamps and event types.
    """
    crossings = {}

    if borders is None:
        return crossings
    
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
    h5_path = os.path.join(PROCESSED_FLYBYS_PATH, f"{date_str}.h5")
    
    crossings = check_satellite_crossing(boundary, satellite_data)
    stations = flybys.keys()

    with h5.File(h5_path, 'a') as h5file:
        for st in stations:
            satellites = flybys[st].keys()
            for sat in satellites:
                for fb_index, fb_key in enumerate(flybys[st][sat].keys()):
                    logger.debug(f"Process {st}_{sat}_{fb_key}")

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
                        flyby_group.create_dataset('lat', data=flyby_data['lat'])
                        flyby_group.create_dataset('lon', data=flyby_data['lon'])
                        logger.info(f'Successfully processed and added new flyby: {st}_{sat}_{fb_key}')

                    else:
                        # logger.warning(f'Flyby index is lower than the crossing events {st}_{sat}_{fb_key}')
                        break


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
            date_str = rinex_file.split('.')[0]
            h5_filename = f'{date_str}.h5'

            full_rinex_path = os.path.join(FILES_PATH, rinex_file)
            full_map_path = os.path.join(MAP_PATH, h5_filename)

            with RinexProcessor(full_rinex_path) as processor:
                processor.process(h5_filename)
                satellite_data = processor.map_data
                flybys = processor.flybys

            if os.path.isfile(full_map_path):
                logger.debug(f"For file {rinex_file} a meshing file was found: {full_map_path}")
                
                boundary_output_path = os.path.join(BOUNDARY_PATH, h5_filename)
                
                map_processor.process(
                    map_path=full_map_path,
                    output_path=boundary_output_path
                )
                
                with h5.File(boundary_output_path, 'r') as boundary_file:
                    time_points = boundary_file.keys()
                    
                    # Весь этот цикл выглядит как цирк который надо почистить и починить
                    # Будто тут много лишних действий
                    boundary_clusters = {}
                    for time_point in time_points:
                        logger.info(f'Processing {time_point} from {boundary_output_path}')
                        time_grp = boundary_file[time_point]

                        if "boundary_clusters" in time_grp:
                            boundary_clusters[time_point] = {
                                'relation': time_grp['boundary_clusters'].attrs['relation']
                            }   
                            for cluster_key in time_grp['boundary_clusters']:
                                cluster_grp = time_grp['boundary_clusters'][cluster_key]
                                boundary_clusters[time_point][cluster_key] = np.column_stack((
                                    cluster_grp['lon'][()],
                                    cluster_grp['lat'][()]
                                )).tolist()
                        else:
                            pass
                    
                    processed_flyby_path = os.path.join(PROCESSED_FLYBYS_PATH, h5_filename)
                    if os.path.exists(processed_flyby_path):
                        logger.info(f"Flyby file is exist: {processed_flyby_path}, skipping processing.")
                    else:
                        if not satellite_data and not flybys:
                            full_flyby_path = os.path.join(FLYBYS_PATH, h5_filename)
                            with RinexProcessor(full_rinex_path) as processor:
                                processor.restor_data(full_flyby_path)
                                satellite_data = processor.map_data
                                flybys = processor.flybys
                        
                        process_flyby(
                            boundary=boundary_clusters,
                            satellite_data=satellite_data,
                            flybys=flybys,
                            date_str=date_str
                        )

                    
                    video_converter = PngToVideoConverter(input_dir=FRAME_GRAPHS_PATH, output_dir=SAVE_VIDEO_PATH)
                    with h5.File(processed_flyby_path, 'r') as flyby_h5file:
                        stations = flyby_h5file.keys()

                        for station in stations:
                            satellites = flyby_h5file[station].keys()

                            for satellite in satellites:
                                sat_flybys = flyby_h5file[station][satellite].keys()

                                for sat_flyby in sat_flybys:
                                    flyby_group = flyby_h5file[station][satellite][sat_flyby]

                                    flyby_roti = flyby_group['roti'][:]
                                    flyby_ts = flyby_group['timestamps'][:]

                                    cleaned_times = flyby_group.attrs['times']
                                    cleaned_types = flyby_group.attrs['types']

                                    ts_time_points = [dt.fromtimestamp(float(t), datetime.UTC) for t in flyby_ts]
                                    time_points = generate_5min_timestamps(ts_time_points)
                                    for time_point in time_points:
                                        time_grp = boundary_file[time_point]
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

                                        plot_combined_graphs(
                                            map_points=filtered_points,
                                            sliding_windows=sliding_windows,
                                            flyby_roti=flyby_roti,
                                            flyby_times=ts_time_points,
                                            flyby_events_times=cleaned_times,
                                            flyby_events_types=cleaned_types,
                                            flyby_idx=sat_flyby,
                                            boundary_data=boundary,
                                            boundary_condition=BOUNDARY_CONDITION,
                                            time_point=time_point,
                                            boundary_clusters=boundary_clusters,
                                            roti_file=full_rinex_path,
                                            station=station,
                                            satellite=satellite,
                                            save_to_file=True
                                        )

                            video_converter.process_images_to_video()
                        
            else:
                logger.warning(f"Meshing file not found: {full_map_path}")
