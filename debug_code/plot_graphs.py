import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec
import numpy as np
import traceback
import os

from shapely.geometry import Polygon, MultiPolygon
from shapely.validation import explain_validity

from config import logger

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
        
def plot_combined_results(
    sliding_windows,
    boundary_data,
    time_point,
    roti_data,
    boundary_condition,
    filename,
    save_to_file
):
    """
    Plots two graphs: on the left, a scatter plot of sliding windows with boundaries, and on the right, a ROTI map for each timestamp.
    
    :param sliding_windows: A list of processed data segments from the sliding window.
    :param boundary_data_dict: A dictionary with time_point keys and values containing boundary data ('lon', 'lat').
    :param roti_data: A dictionary with ROTI data, where the key is a timestamp, and the value is a list of points {'lat', 'lon', 'roti'}.
    """
    if save_to_file:
        import matplotlib
        matplotlib.use('Agg')
    
    logger.debug("ploting results")
    lon = np.array([entry['lon'] for entry in sliding_windows])
    lat = np.array([entry['lat'] for entry in sliding_windows])
    vals = np.array([entry['vals'] for entry in sliding_windows])

    safe_time_point = time_point.replace(":", "_")
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    cmap = plt.get_cmap("coolwarm")
    norm = plt.Normalize(0, 0.1)
    scatter = axes[0].scatter(lon, lat, c=vals, cmap=cmap, norm=norm, edgecolors=None)
    axes[0].set_xlabel("Longitude")
    axes[0].set_ylabel("Latitude")
    axes[0].set_title(f"{safe_time_point}")
    fig.colorbar(scatter, ax=axes[0], label='ROTI')

    roti_points = roti_data[time_point]
    lons = roti_points['lon'][()]
    lats = roti_points['lat'][()]
    rotis = roti_points['vals'][()]
        
    axes[1].scatter(lons, lats, c=rotis, cmap=cmap, norm=norm, marker='o', edgecolors='black')
    axes[1].set_xlabel('Longitude')
    axes[1].set_ylabel('Latitude')
    axes[1].set_title(f'ROTI Map at {time_point}')
    axes[1].grid(True)
    fig.colorbar(scatter, ax=axes[1], label='ROTI')
    
    if boundary_data['lon'] and boundary_data['lat']:
        axes[0].scatter(boundary_data['lon'], boundary_data['lat'], color='black', label=f'{boundary_condition} boundary')
        axes[1].scatter(boundary_data['lon'], boundary_data['lat'], color='black', label=f'{boundary_condition} boundary')
    axes[0].legend()
    axes[1].legend()

    if save_to_file:
        file_name_base = os.path.splitext(filename)[0]
        graphs_dir = os.path.join('graphs', file_name_base)
        os.makedirs(graphs_dir, exist_ok=True)
        graph_path = os.path.join(graphs_dir, f'{safe_time_point}.png')
        plt.savefig(graph_path)
        plt.close()
    else:
        plt.show()
            
def plot_roti(
    map_points,
    time_point,
    roti_data,
    save_to_file
):
    """
    Plots two graphs: on the left, a scatter plot of sliding windows with boundaries, and on the right, a ROTI map for each timestamp.
    
    :param sliding_windows: A list of processed data segments from the sliding window.
    :param boundary_data_dict: A dictionary with time_point keys and values containing boundary data ('lon', 'lat').
    :param roti_data: A dictionary with ROTI data, where the key is a timestamp, and the value is a list of points {'lat', 'lon', 'roti'}.
    """
    if save_to_file:
        import matplotlib
        matplotlib.use('Agg')
    
    logger.debug("ploting results")
    map_lons = map_points['lon'][()]
    map_lats = map_points['lat'][()]
    map_vals = map_points['vals'][()]
    
    fig, axes = plt.subplots(1, 2, figsize=(16, 6))

    cmap = plt.get_cmap("coolwarm")
    norm = plt.Normalize(0, 0.1)
    scatter1 = axes[0].scatter(map_lons, map_lats, c=map_vals, cmap=cmap, norm=norm, marker='o', edgecolors='black')
    axes[0].set_xlabel('Longitude')
    axes[0].set_ylabel('Latitude')
    axes[0].set_title(f'Map points at {time_point}')
    axes[0].grid(True)
    fig.colorbar(scatter1, ax=axes[0], label='ROTI')

    roti_points = roti_data[time_point]
    lats = [point['lat'] for point in roti_points]
    lons = [point['lon'] for point in roti_points]
    rotis = [point['roti'] for point in roti_points]
        
    norm = plt.Normalize(0, 0.35)
    scatter2 = axes[1].scatter(lons, lats, c=rotis, cmap=cmap, norm=norm, marker='o', edgecolors='black')
    axes[1].set_xlabel('Longitude')
    axes[1].set_ylabel('Latitude')
    axes[1].set_title(f'ROTI at {time_point}')
    axes[1].grid(True)
    fig.colorbar(scatter2, ax=axes[1], label='ROTI')

    if save_to_file:
        graphs_dir = os.path.join('graphs', 'map_vs_roti')
        os.makedirs(graphs_dir, exist_ok=True)
        safe_time_point = time_point.replace(":", "_")
        graph_path = os.path.join(graphs_dir, f'{safe_time_point}.png')
        plt.savefig(graph_path)
        plt.close()
    else:
        plt.show()
        
def plot_combined_graphs(
    map_points, sliding_windows, boundary_data, boundary_condition,
    time_point, boundary_clusters, save_to_file=False
):
    if save_to_file:
        import matplotlib
        matplotlib.use('Agg')
    
    fig = plt.figure(figsize=(12, 8))
    # fig = plt.figure(figsize=(12, 8), layout="constrained")
    gs = GridSpec(2, 2, height_ratios=[1, 1], figure=fig)
    map_graph = fig.add_subplot(gs[0, 0])
    sl_win_graph = fig.add_subplot(gs[0, 1])
    polygon_graph = fig.add_subplot(gs[1, :])
    
    cmap = plt.get_cmap("coolwarm")
    norm = plt.Normalize(0, 0.1)
    
    # 1. Карта
    map_lons = map_points['lon'][()]
    map_lats = map_points['lat'][()]
    map_vals = map_points['vals'][()]
    map_graph_scatter = map_graph.scatter(map_lons, map_lats, c=map_vals, cmap=cmap, norm=norm, marker='o', edgecolors='black')
    map_graph.set_title("Карта")
    map_graph.set_xlabel("Longitude")
    map_graph.set_ylabel("Latitude")
    map_graph.grid(True)
    fig.colorbar(map_graph_scatter, ax=map_graph, label='ROTI')
    
    # 2. Sliding Window + граница
    lon = np.array([entry['lon'] for entry in sliding_windows])
    lat = np.array([entry['lat'] for entry in sliding_windows])
    vals = np.array([entry['vals'] for entry in sliding_windows])
    sl_win_graph.scatter(lon, lat, c=vals, cmap=cmap, norm=norm)
    if boundary_data['lon'] and boundary_data['lat']:
        sl_win_graph.scatter(boundary_data['lon'], boundary_data['lat'], color='black', label=f'{boundary_condition} boundary')
    sl_win_graph.set_title("Sliding Window + Boundary")
    sl_win_graph.set_xlabel("Longitude")
    sl_win_graph.set_ylabel("Latitude")
    sl_win_graph.legend()
    sl_win_graph.grid(True)
    
    # 3. Полигон
    if time_point in boundary_clusters:
        entry = boundary_clusters[time_point]
        if entry and entry.get('relation') == "top-bottom":
            cluster1 = np.array(entry["border1"])
            cluster2 = np.array(entry["border2"])
            polygon1 = Polygon(cluster1).buffer(0)
            polygon2 = Polygon(cluster2).buffer(0)
            intersection = polygon1.intersection(polygon2)
            
            if isinstance(polygon1, Polygon):
                x1, y1 = polygon1.exterior.xy
                polygon_graph.plot(x1, y1, 'b--', label="Polygon 1")
            elif isinstance(polygon1, MultiPolygon):
                for i, poly in enumerate(polygon1.geoms):
                    x1, y1 = poly.exterior.xy
                    polygon_graph.plot(x1, y1, 'b--', label=f"Polygon 1 - Part {i+1}")

            if isinstance(polygon2, Polygon):
                x2, y2 = polygon2.exterior.xy
                polygon_graph.plot(x2, y2, 'r--', label="Polygon 2")
            elif isinstance(polygon2, MultiPolygon):
                for i, poly in enumerate(polygon2.geoms):
                    x2, y2 = poly.exterior.xy
                    polygon_graph.plot(x2, y2, 'r--', label=f"Polygon 2 - Part {i+1}")
            
            if not intersection.is_empty:
                if isinstance(intersection, Polygon):
                    x_int, y_int = intersection.exterior.xy
                    polygon_graph.fill(x_int, y_int, 'purple', alpha=0.5, label="Intersection")
    else:
        polygon_graph.text(
            0.5, 0.5, "No Data for Polygon", 
            fontsize=12, color='red', alpha=0.7, 
            ha='center', va='center', rotation=45, 
            transform=polygon_graph.transAxes
        )
    
    polygon_graph.set_title("Polygon")
    polygon_graph.set_xlabel("Longitude")
    polygon_graph.set_ylabel("Latitude")
    polygon_graph.legend()
    polygon_graph.grid(True)
    
    fig.tight_layout()
    if save_to_file:
        graphs_dir = os.path.join('graphs', 'combined')
        os.makedirs(graphs_dir, exist_ok=True)
        safe_time_point = time_point.replace(":", "_")
        graph_path = os.path.join(graphs_dir, f'{safe_time_point}.png')
        plt.savefig(graph_path)
        plt.close()
    else:
        plt.show()
