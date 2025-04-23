from matplotlib.gridspec import GridSpec
from matplotlib.patches import Patch
import matplotlib.ticker as ticker
import matplotlib.dates as mdates
import matplotlib.pyplot as plt

from datetime import datetime as dt
from datetime import timedelta
import datetime

import numpy as np
import h5py as h5
import os

from shapely.geometry import Polygon, MultiPolygon

from debug_code.calc_sat_trajectory import Trajectory
from config import FRAME_GRAPHS_PATH, LAT_CONDITION, LON_CONDITION

def remove_traj_lines(trajectory_elements):
    if trajectory_elements:
        for line, scatter in trajectory_elements:
            line.remove()
            scatter.remove()
        trajectory_elements.clear()

def plot_clusters(cluster_dict, time_point):
    fig, ax = plt.subplots()
    
    for label, cluster in cluster_dict.items():
        cluster = np.array(cluster)
        ax.scatter(cluster[:, 0], cluster[:, 1], label=label)
        
    ax.set_xlim(-120, -70)
    ax.set_ylim(40, 90)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.set_title(f"Clusters at {time_point}")
    ax.legend()
    plt.show()

def compute_polygons(boundary_clusters, time_point):
    """
    Computes polygons and their intersection based on boundary clusters.
    
    :param boundary_clusters: dict, boundary cluster data.
    :param time_point: str, timestamp for the data.
    :return: tuple (polygons, intersection, single_cluster_polygon)
    """
    entry = boundary_clusters.get(time_point)
    if not entry:
        return None, None, None
    
    if entry.get('relation') == "single-cluster":
        polygon = Polygon(np.array(entry["border1"])).buffer(0)
        return [(polygon, 'r', "Polygon")], None, polygon
    
    if entry.get('relation') == "left-right":
        return None, None, None
    
    clusters = [np.array(entry[f"border{i+1}"]) for i in range(len(entry) - 1)]
    
    if entry['relation'] == "top-bottom":
        polygon1 = Polygon(clusters[0]).buffer(0)
        polygon2 = Polygon(clusters[1]).buffer(0)
        intersection = polygon1.intersection(polygon2)
        
        return [(polygon1, 'b', "Polygon 1"), (polygon2, 'r', "Polygon 2")], intersection, None
    
    return None, None, None

def plot_polygon(boundary_clusters, time_point, ax=None):
    """
    Plots boundary polygons based on the provided clusters.
    
    :param boundary_clusters: dict, boundary cluster data.
    :param time_point: str, timestamp for the data.
    :param ax: matplotlib axis, optional.
    :return: fig, ax objects.
    """
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
        ax.set_title(f"Polygon at {time_point}")
    else:
        fig = ax.figure
        created_fig = False
        ax.set_title(f"Polygon")
    
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    
    polygons, intersection, single_cluster_polygon = compute_polygons(boundary_clusters, time_point)
    
    if polygons is None:
        ax.text(0.5, 0.5, "No Data for Polygon", fontsize=12, color='red', alpha=0.7, ha='center', va='center', 
                rotation=45, transform=ax.transAxes)
        if created_fig:
            plt.show()
        return fig, ax
    
    for poly, color, label in polygons:
        if isinstance(poly, Polygon):
            x, y = poly.exterior.xy
            ax.plot(x, y, f'{color}--', label=label)
        elif isinstance(poly, MultiPolygon):
            for part in poly.geoms:
                x, y = part.exterior.xy
                ax.plot(x, y, f'{color}--', label=label)
    
    if single_cluster_polygon:
        x, y = single_cluster_polygon.exterior.xy
        ax.fill(x, y, 'purple', alpha=0.5, label="Polygon area")
    
    if intersection and not intersection.is_empty:
        for poly in ([intersection] if isinstance(intersection, Polygon) else intersection.geoms):
            x, y = poly.exterior.xy
            ax.fill(x, y, 'purple', alpha=0.5, label="Intersection")
    
    if created_fig:
        plt.show()
    else:
        return fig, ax


def plot_roti_map(roti_points, time_point, ax=None, cmap='coolwarm'):
    """
    Plots a ROTI map based on provided points.

    :param roti_points: dict, contains 'lon', 'lat', and 'vals'.
    :param time_point: str, timestamp for the data.
    :param ax: matplotlib axis, optional.
    :param cmap: str, colormap for visualization.
    :return: fig, ax objects.
    """
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
    else:
        fig = ax.figure
    
    cmap = plt.get_cmap(cmap)
    norm = plt.Normalize(0, 0.1)
    
    lons = roti_points['lon'][()]
    lats = roti_points['lat'][()]
    rotis = roti_points['vals'][()]
    
    scatter = ax.scatter(lons, lats, c=rotis, cmap=cmap, norm=norm, 
                        marker='o', edgecolors='grey')
    
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True)
    fig.colorbar(scatter, ax=ax, label='ROTI')
    
    if created_fig:
        ax.set_title(f'ROTI Map at {time_point}')
        plt.show()
    else:
        ax.set_title(f'ROTI Map')
        return fig, ax


def plot_sliding_window(
        sliding_windows,
        boundary_data,
        boundary_condition,
        ax=None,
        time_point = None,
        cmap='coolwarm'
    ):
    """
    Plots a sliding window visualization with boundary data.

    :param sliding_windows: list, contains sliding window data.
    :param boundary_data: dict, boundary points.
    :param boundary_condition: str, condition type.
    :param time_point: str, timestamp for the data.
    :param ax: matplotlib axis, optional.
    :param cmap: str, colormap.
    :return: fig, ax objects.
    """
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
    else:
        fig = ax.figure
    
    cmap = plt.get_cmap(cmap)
    norm = plt.Normalize(0, 0.1)
    
    lon = np.array([entry['lon'] for entry in sliding_windows])
    lat = np.array([entry['lat'] for entry in sliding_windows])
    vals = np.array([entry['vals'] for entry in sliding_windows])
    
    scatter_sliding = ax.scatter(lon, lat, c=vals, cmap=cmap, norm=norm)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    fig.colorbar(scatter_sliding, ax=ax, label='ROTI')    
    
    if boundary_data['lon'] and boundary_data['lat']:
        ax.scatter(
            boundary_data['lon'],
            boundary_data['lat'], 
            color='grey',
            label=f'{boundary_condition} boundary'
        )
        ax.legend()

    if created_fig:
        ax.set_title(f"Sliding Window at {time_point}")
        plt.show()
    else:
        ax.set_title(f"Sliding Window")
        return fig, ax


def plot_roti_dynamics(station_data, satellite, time_point=None, ax=None):
    """
    Plots ROTI dynamics for a station-satellite pair.

    :param station_data: dict, contains ROTI data.
    :param satellite: str, satellite identifier.
    :param time_range: tuple, optional, time range filter.
    :param ax: matplotlib axis, optional.
    :return: fig, ax objects.
    """
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
    else:
        fig = ax.figure

    roti = station_data[satellite]['roti'][:]
    ts = station_data[satellite]['timestamp'][:]
    times = [dt.fromtimestamp(float(t), datetime.UTC) for t in ts]

    ax.scatter(times, roti)

    day_start = dt.combine(times[0].date(), dt.min.time())
    day_end = dt.combine(times[0].date(), dt.max.time())
    ax.set_xlim(day_start, day_end)

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(axis='x', rotation=45)

    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))

    y_max = max(roti)
    y_lim = ((y_max // 0.5) + 1) * 0.5
    ax.set_ylim(0, y_lim)

    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.grid(True, which='major', linewidth=1, linestyle='-', alpha=0.7)
    ax.grid(True, which='minor', linestyle='--', alpha=0.4)

    ax.set_xlabel("Time")
    ax.set_ylabel("ROTI")

    try:
        time_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
    except ValueError:
        time_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)
        
    ax.axvspan(time_dt, time_dt + timedelta(minutes=5), color='red', alpha=0.3, label="Time Point")

    if created_fig:
        ax.set_title(f"ROTI Dynamics for {satellite}")
        plt.show()
    else:
        ax.set_title(f"ROTI Dynamics")
        return fig, ax
    
def add_sat_traj(station_lat, station_lon, sat_azs, sat_els, sat_times, time_point, ax_list=None):
    trajectory = Trajectory(
        lat_site=station_lat,
        lon_site=station_lon,
    )

    trajectory.procces(
        azs=sat_azs,
        els=sat_els,
        times=sat_times
    )

    trajectory_elements = []
    if trajectory.traj_lat.size > 0 and trajectory.traj_lon.size > 0:
        color = 'black'
        for ax in ax_list:
            handles, labels = ax.get_legend_handles_labels()
            
            seen = set()
            filtered = [(h, l) for h, l in zip(handles, labels) if l not in seen and not seen.add(l)]
            handles, labels = list(zip(*filtered)) if filtered else ([], [])
            handles, labels = list(handles), list(labels)
            
            # find the satellite position at that time and plots the point. 
            try:
                time_point_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
            except ValueError:
                time_point_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)

            time_point_ts = time_point_dt.timestamp()
            closest_idx = np.argmin(np.abs(np.array(trajectory.times) - time_point_ts))
            try:
                scatter = ax.scatter(
                    trajectory.traj_lon[closest_idx], trajectory.traj_lat[closest_idx],
                    color='green', marker='o', s=40, edgecolor=color
                )
            except Exception:
                scatter = ax.scatter(trajectory.traj_lon[0], trajectory.traj_lat[0], color='green', marker='o', s=40, edgecolor=color, alpha=0)
            # plot sattelite trajectory
            line, = ax.plot(trajectory.traj_lon, trajectory.traj_lat, color=color, linewidth=2)
            trajectory_elements.append((line, scatter))
            
            # create legend
            
            handles.append(scatter)
            labels.append("Time Point")
            handles.append(line)
            labels.append("Trajectory")
            
            ax.legend(handles, labels, loc='upper right', bbox_to_anchor=(1, 1))

    return trajectory_elements

def clean_events(event_times, event_types):
    dedup_times = []
    dedup_types = []
    for idx, (t, e) in enumerate(zip(event_times, event_types)):
        if idx == 0 or e != event_types[idx - 1]:
            dedup_times.append(t)
            dedup_types.append(e)
            
    i = 0
    cleaned_times = []
    cleaned_types = []

    while i < len(dedup_times):
        current_time = dedup_times[i]
        current_type = dedup_types[i]

        j = i + 1
        future = []
        while j < len(dedup_times) and dedup_times[j] <= current_time + timedelta(minutes=15):
            future.append((dedup_times[j], dedup_types[j]))
            j += 1

        if len(future) == 1:
            cleaned_times.append(future[0][0])
            cleaned_types.append(current_type)
            i = j
        elif len(future) >= 2:
            k = j-1
            look_time = dedup_times[k]

            while k < len(dedup_times):
                m = k + 1
                count = 0

                while m < len(dedup_times) and dedup_times[m] <= look_time + timedelta(minutes=15):
                    count += 1
                    m += 1

                if count >= 2:
                    look_time = dedup_times[m - 1]
                    k = m
                    i = m
                    if m >= len(dedup_times):
                        cleaned_times.append(dedup_times[m - 1])
                        cleaned_types.append(dedup_types[m - 1])
                else:
                    cleaned_times.append(dedup_times[m - 1])
                    cleaned_types.append(dedup_types[m - 1])
                    i = m
                    break
            
        else:
            cleaned_times.append(current_time)
            cleaned_types.append(current_type)
            i += 1
        
    final_times = []
    final_types = []
    for idx, (t, e) in enumerate(zip(cleaned_times, cleaned_types)):
        if idx == len(cleaned_times) - 1 or e != cleaned_types[idx + 1]:
            final_times.append(t)
            final_types.append(e)

    return final_times, final_types

def plot_flyby(roti, ts, station, satellite, crossing_events=None, ax=None):
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
    else:
        fig = ax.figure

    times = [dt.fromtimestamp(float(t), datetime.UTC) for t in ts]
    ax.scatter(times, roti)

    ax.set_xlim(min(times), max(times))

    ax.xaxis.set_major_locator(mdates.HourLocator(interval=1))
    ax.xaxis.set_major_formatter(mdates.DateFormatter('%H:%M'))
    ax.tick_params(axis='x', rotation=45)

    ax.yaxis.set_major_formatter(ticker.FormatStrFormatter('%.3f'))

    y_max = max(roti)
    y_lim = ((y_max // 0.5) + 1) * 0.5
    ax.set_ylim(0, y_lim)

    ax.yaxis.set_major_locator(ticker.MultipleLocator(0.5))
    ax.yaxis.set_minor_locator(ticker.MultipleLocator(0.1))
    ax.grid(True, which='major', linewidth=1, linestyle='-', alpha=0.7)
    ax.grid(True, which='minor', linestyle='--', alpha=0.4)

    ax.set_xlabel("Time")
    ax.set_ylabel("ROTI")

    if crossing_events:
        events = sorted(crossing_events, key=lambda e: dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f"))
        event_times = [dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC) for e in events]
        event_types = [e['event'] for e in events]

        cleaned_times, cleaned_types = clean_events(event_times, event_types)

        last_time = times[0]
        for i in range(len(cleaned_times)):
            current_time = cleaned_times[i]
            current_event = cleaned_types[i]

            color = {
                "entered": "green",
                "exited": "red",
                "noise": "yellow"
            }.get(current_event, "gray")

            ax.axvspan(last_time, current_time, color=color, alpha=0.3)
            last_time = current_time

        final_color = {
            "entered": "red",
            "exited": "green",
            "noise": "yellow"
        }.get(cleaned_types[-1], "gray")

        ax.axvspan(last_time, times[-1], color=final_color, alpha=0.3)

        legend_elements = [
            Patch(facecolor='red', alpha=0.3, label='Inside'),
            # Patch(facecolor='yellow', alpha=0.3, label='Шум'),
            Patch(facecolor='green', alpha=0.3, label='Outside')
        ]
        ax.legend(handles=legend_elements, loc='upper right')

    ax.set_title(f"Flyby for {station}_{satellite}")
    if created_fig:
        plt.show()
    else:
        return fig, ax

def plot_combined_graphs(
    map_points, sliding_windows, boundary_data, boundary_condition,
    time_point, boundary_clusters, roti_file, stations = None, save_to_file=False
):
    """
    Generates a composite visualization combining multiple plots.

    :param map_points: dict, ROTI map data containing coordinates and values.
    :param sliding_windows: list, data segments for sliding window visualization.
    :param boundary_data: dict, boundary points used for visualization.
    :param boundary_condition: str, condition defining boundary characteristics.
    :param time_point: str, timestamp for data reference.
    :param boundary_clusters: dict, polygonal boundary clusters for visualization.
    :param roti_file: str, path to the HDF5 file containing ROTI dynamics.
    :param save_to_file: bool, whether to save the generated plot to a file.
    :return: matplotlib.figure.Figure, the generated figure.
    """
    fig = plt.figure(figsize=(16, 12))
    gs = GridSpec(2, 2, figure=fig)
    
    # Create axes for all graphs
    map_ax = fig.add_subplot(gs[0, 0])
    sl_win_ax = fig.add_subplot(gs[0, 1])
    poly_ax = fig.add_subplot(gs[1, 0])
    dynamic_ax = fig.add_subplot(gs[1, 1])
    
    common_xlim = (-120, LON_CONDITION)
    common_ylim = (LAT_CONDITION, 90)
    
    # Create axes for all graphs
    for ax in [map_ax, sl_win_ax, poly_ax, dynamic_ax]:
        ax.set_xlim(common_xlim)
        ax.set_ylim(common_ylim)
    
    # 1. ROTI map
    plot_roti_map(
        roti_points=map_points,
        time_point=time_point,
        ax=map_ax
    )
    
    # 2. Sliding window with borders
    plot_sliding_window(
        sliding_windows=sliding_windows,
        boundary_data=boundary_data,
        boundary_condition=boundary_condition,
        time_point=time_point,
        ax=sl_win_ax
    )
    
    # 3. polygons
    plot_polygon(
        boundary_clusters=boundary_clusters,
        time_point=time_point,
        ax=poly_ax
    )
    
    # 4. ROTI dynamics
    with h5.File(roti_file, 'r') as h5file:
        if stations is None:
            stations = h5file.keys()

        for station in stations:
            for satellite in h5file[station]:
                dynamic_ax.clear()

                plot_roti_dynamics(h5file[station], satellite, time_point=time_point, ax=dynamic_ax)
                trajectory_elements = add_sat_traj(
                    station_lat=h5file[station].attrs['lat'],
                    station_lon=h5file[station].attrs['lon'],
                    sat_azs=h5file[station][satellite]['azimuth'][:],
                    sat_els=h5file[station][satellite]['elevation'][:],
                    sat_times=h5file[station][satellite]['timestamp'][:],
                    time_point=time_point,
                    ax_list=[map_ax, sl_win_ax, poly_ax]
                )

                fig.suptitle(f'Graphs for {station}_{satellite} at {time_point}')
                fig.tight_layout()
                
                map_box = map_ax.get_position()
                poly_box = poly_ax.get_position()
                dynamic_box = dynamic_ax.get_position()
                
                poly_ax.set_position([poly_box.x0, poly_box.y0, map_box.width, poly_box.height])
                dynamic_ax.set_position([dynamic_box.x0, dynamic_box.y0, map_box.width, dynamic_box.height])

                if save_to_file:
                    output_dir = os.path.join(FRAME_GRAPHS_PATH, station, satellite)
                    os.makedirs(output_dir, exist_ok=True)
                    filename = f"{time_point.replace(':', '_')}.png"
                    plt.savefig(os.path.join(output_dir, filename))
                    remove_traj_lines(trajectory_elements)
                else:
                    fig.canvas.draw()
                    plt.pause(60)
                    remove_traj_lines(trajectory_elements)
                    

    if not save_to_file:
        plt.show()
    else:
        plt.close(fig)
