import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
import numpy as np

import os
import h5py as h5
from datetime import datetime as dt
import datetime
from shapely.geometry import Polygon, MultiPolygon

from debug_code.calc_sat_trajectory import Trajectory

def remove_traj_lines(trajectory_elements):
    if trajectory_elements:
        for line, scatter in trajectory_elements:
            line.remove()
            scatter.remove()
        trajectory_elements.clear()

def plot_polygon(boundary_clusters, time_point, ax=None):
    """
    Plots boundary polygons based on the provided clusters.

    :param boundary_clusters: dict, boundary cluster data.
    :param time_point: str, timestamp for the data.
    :param ax: matplotlib axis, optional.
    :return: fig, ax objects.
    """
    created_fig = False
    if ax is None:
        fig, ax = plt.subplots()
        created_fig = True
    else:
        fig = ax.figure
    
    entry = boundary_clusters.get(time_point)
    if not entry or entry.get('relation') == "left-right":
        ax.text(
            0.5, 0.5, "No Data for Polygon", 
            fontsize=12, color='red', alpha=0.7, 
            ha='center', va='center', rotation=45, 
            transform=ax.transAxes
        )
        if ax is None:
            plt.close()
            return
        else:
            return fig, ax
    
    cluster1 = np.array(entry["border1"])
    cluster2 = np.array(entry["border2"])
    
    if entry['relation'] == "top-bottom":
        polygon1 = Polygon(cluster1).buffer(0)
        polygon2 = Polygon(cluster2).buffer(0)
        intersection = polygon1.intersection(polygon2)

        # Drawing polygons
        for poly, color, label in [(polygon1, 'b', "Polygon 1"), 
                                 (polygon2, 'r', "Polygon 2")]:
            if isinstance(poly, Polygon):
                x, y = poly.exterior.xy
                ax.plot(x, y, f'{color}--', label=label)
            elif isinstance(poly, MultiPolygon):
                for i, part in enumerate(poly.geoms):
                    x, y = part.exterior.xy
                    ax.plot(x, y, f'{color}--', label=f"{label} - Part {i+1}")

        # Drawing the intersection
        if not intersection.is_empty:
            if isinstance(intersection, (Polygon, MultiPolygon)):
                for poly in ([intersection] if isinstance(intersection, Polygon) 
                           else intersection.geoms):
                    x, y = poly.exterior.xy
                    ax.fill(x, y, 'purple', alpha=0.5, label="Intersection")

    ax.set_title(f"Polygon at {time_point}")
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    ax.legend()
    
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
                        marker='o', edgecolors='black')
    ax.set_title(f'ROTI Map at {time_point}')
    ax.set_xlabel('Longitude')
    ax.set_ylabel('Latitude')
    ax.grid(True)
    fig.colorbar(scatter, ax=ax, label='ROTI')
    
    if created_fig:
        plt.show()
    else:
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
    
    ax.scatter(lon, lat, c=vals, cmap=cmap, norm=norm)
    ax.set_xlabel("Longitude")
    ax.set_ylabel("Latitude")
    if time_point:
        ax.set_title(f"Sliding Window at {time_point}")
    else:
        ax.set_title(f"Sliding Window")
    
    if boundary_data['lon'] and boundary_data['lat']:
        ax.scatter(
            boundary_data['lon'],
            boundary_data['lat'], 
            color='black',
            label=f'{boundary_condition} boundary'
        )
        ax.legend()

    if created_fig:
        plt.show()
    else:
        return fig, ax


def plot_roti_dynamics(station_data, satellite, time_range=None, ax=None):
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

    ax.set_title(f"ROTI Dynamics for {satellite}")
    ax.set_xlabel("Time")
    ax.set_ylabel("ROTI")
    ax.grid(True)

    if created_fig:
        plt.show()
    else:
        return fig, ax
    
def add_sat_traj(station_lat, station_lon, sat_azs, sat_els, sat_times, ax_list=None):
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
        color='green'
        for ax in ax_list:
            line, = ax.plot(trajectory.traj_lon, trajectory.traj_lat, color=color, label="Trajectory", linewidth=2)
            scatter = ax.scatter(trajectory.traj_lon[-1], trajectory.traj_lat[-1], color=color, marker='s', s=20, label="End")

            ax.legend()
            trajectory_elements.append((line, scatter))

    return trajectory_elements


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

                plot_roti_dynamics(h5file[station], satellite, ax=dynamic_ax)
                trajectory_elements = add_sat_traj(
                    station_lat=h5file[station].attrs['lat'],
                    station_lon=h5file[station].attrs['lon'],
                    sat_azs=h5file[station][satellite]['azimuth'][:],
                    sat_els=h5file[station][satellite]['elevation'][:],
                    sat_times=h5file[station][satellite]['timestamp'][:],
                    ax_list=[sl_win_ax, poly_ax]
                )

                fig.suptitle(f'Graphs for {station}_{satellite} at {time_point}')
                fig.tight_layout()

                if save_to_file:
                    output_dir = os.path.join('graphs', 'combined', station, satellite)
                    os.makedirs(output_dir, exist_ok=True)
                    filename = f"{time_point.replace(':', '_')}.png"
                    plt.savefig(os.path.join(output_dir, filename))
                    remove_traj_lines(trajectory_elements)
                else:
                    fig.canvas.draw()
                    plt.pause(20)
                    remove_traj_lines(trajectory_elements)
                    

    if not save_to_file:
        plt.show()
    else:
        plt.close(fig)
