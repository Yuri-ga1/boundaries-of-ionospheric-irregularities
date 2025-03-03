import matplotlib.pyplot as plt
import h5py as h5
import numpy as np
import os

from copy import deepcopy
from sklearn.cluster import DBSCAN
from collections import Counter

from scipy.interpolate import griddata

from config import *
from debug_code.plot_graphs import *

# TODO убедиться в точности последовательности точек

class DataProcessor:
    def __init__(
        self,
        lon_condition: float,
        lat_condition: float,
        segment_lon_step: float,
        segment_lat_step: float,
        boundary_condition: float,
        save_to_file : bool = False
    ):
        """
        Initializes the DataProcessor object.

        :param lon_condition: float, longitude condition for pole proximity.
        :param lat_condition: float, latitude condition for pole proximity.
        :param segment_lon_step: float, sliding window step in longitude.
        :param segment_lat_step: float, sliding window step in latitude.
        :param save_to_file : bool, whether to save graphs to file or show them.
        """
        self.lon_condition = lon_condition
        self.lat_condition = lat_condition
        self.segment_lon_step = segment_lon_step
        self.segment_lat_step = segment_lat_step
        self.boundary_condition = boundary_condition
        self.save_to_file  = save_to_file 
        
        self.file_name = None
        self.boundary_points = {}
        self.sliding_window_maps = {}
            
    def __filter_points(self, points_group):
        lon = points_group['lon'][()]
        lat = points_group['lat'][()]
        vals = points_group['vals'][()]
        
        mask = (lon >= -120) & (lon <= self.lon_condition) & (lat >= self.lat_condition)
        
        filtered_points = {
            'lon': lon[mask],
            'lat': lat[mask],
            'vals': vals[mask]
        }
        
        return filtered_points
    
    def __apply_sliding_window(self, filtered_points, window_size=(5, 10)):
        """
        Applies a sliding window approach to segment the data.

        :param filtered_points: dict, containing 'lon', 'lat', and 'vals'.
        :param window_size: tuple, defining (lat, lon) window size.
        :return: List of windowed data segments.
        """
        lon = filtered_points['lon']
        lat = filtered_points['lat']
        vals = filtered_points['vals']
        
        min_lon, max_lon = np.min(lon), np.max(lon)
        min_lat, max_lat = np.min(lat), np.max(lat)
        
        windows = []
        current_lat = min_lat
        
        while current_lat + window_size[0] <= max_lat:
            current_lon = min_lon
            while current_lon + window_size[1] <= max_lon:
                mask = (lon >= current_lon) & (lon < current_lon + window_size[1]) & \
                       (lat >= current_lat) & (lat < current_lat + window_size[0])
                
                if np.any(mask):
                    windows.append({
                        'lon': current_lon,
                        'lat': current_lat,
                        'vals': np.median(vals[mask])
                    })
                
                current_lon += self.segment_lon_step
            
            current_lat += self.segment_lat_step
            
        return windows
    
    def __get_boundary_data(self, sliding_windows):
        lon = np.array([entry['lon'] for entry in sliding_windows])
        lat = np.array([entry['lat'] for entry in sliding_windows])
        vals = np.array([entry['vals'] for entry in sliding_windows])

        grid_points = 100
        xi = np.linspace(lon.min(), lon.max(), grid_points)
        yi = np.linspace(lat.min(), lat.max(), grid_points)
        zi = griddata(
            (lon, lat), 
            vals, 
            (xi[None, :], yi[:, None]), 
            method='linear', 
            fill_value=np.nan
        )
        
        boundary_data = {'lat': [], 'lon': []}
            
        if np.all(np.isnan(zi)):
            return boundary_data
        
        plt.figure()
        cs = plt.contour(xi, yi, zi, levels=[self.boundary_condition])
        plt.close()

        if len(cs.allsegs) > 0:
            contour_segments = cs.allsegs[0]
            for segment in contour_segments:
                if len(segment) > 0:
                    boundary_data['lon'].extend(segment[:, 0].tolist())
                    boundary_data['lat'].extend(segment[:, 1].tolist())
        
        return boundary_data
    
    
    def __delete_circle(self, data):
        first_col_abs = np.abs(data[:, 0])
        
        increasing = first_col_abs[1] > first_col_abs[0]
        
        if increasing:
            max_index = np.argmax(first_col_abs)
            mask = (np.arange(len(data)) <= max_index) | np.any(data == 0, axis=1)
        else:
            min_index = np.argmin(first_col_abs)
            mask = (np.arange(len(data)) <= min_index) | np.any(data == 90, axis=1)
        
        return data[mask]

    def __create_boundary_clusters(self, lat_list, lon_list, min_cluster_size=MIN_CLUSTER_SIZE):
        dbscan = DBSCAN(eps=0.7, min_samples=3)
        filtered_boundary_data = {}
            
        if lat_list and lon_list:
            column_coords = np.column_stack((lon_list, lat_list))
            labels = dbscan.fit_predict(column_coords)
            
            label_counts = Counter(labels)
            del label_counts[-1]  # Убираем шум (-1)
            
            if len(label_counts) >= 2:
                top_clusters = [label for label, _ in label_counts.most_common(2)]
            else:
                top_clusters = list(label_counts.keys())
            
            valid_clusters = [label for label in top_clusters if label_counts[label] >= min_cluster_size]
            
            if len(valid_clusters) == 2:
                cluster1 = column_coords[labels == valid_clusters[0]]
                cluster2 = column_coords[labels == valid_clusters[1]]
                
                cluster1_center = np.mean(cluster1, axis=0)
                cluster2_center = np.mean(cluster2, axis=0)
                
                if abs(cluster1_center[0] - cluster2_center[0]) > abs(cluster1_center[1] - cluster2_center[1]):
                    relation = "left-right"
                else:
                    relation = "top-bottom"
                
                if relation == "top-bottom":
                    if cluster1_center[1] > cluster2_center[1]:
                        top_cluster = cluster1
                        bottom_cluster = cluster2
                    else:
                        top_cluster = cluster2
                        bottom_cluster = cluster1
                    
                    left_edge_top_cluster = deepcopy(min(top_cluster, key=lambda p: (p[0])))
                    right_edge_top_cluster = deepcopy(max(top_cluster, key=lambda p: (p[0])))
                    left_edge_bottom_cluster= deepcopy(min(bottom_cluster, key=lambda p: (p[0])))
                    right_edge_bottom_cluster = deepcopy(max(bottom_cluster, key=lambda p: (p[0])))
                    
                    if abs(left_edge_bottom_cluster[0]) > abs(left_edge_top_cluster[0]):
                        left_edge_top_cluster[0] = left_edge_bottom_cluster[0]
                        top_cluster = np.insert(top_cluster, len(top_cluster), left_edge_top_cluster, axis=0)
                        
                    if abs(right_edge_top_cluster[0]) > abs(right_edge_bottom_cluster[0]):
                        right_edge_top_cluster[0] = right_edge_bottom_cluster[0]
                        top_cluster = np.insert(top_cluster, 0, right_edge_top_cluster, axis=0)
                    
                    left_edge_top_cluster[1], right_edge_top_cluster[1] = 0, 0
                    left_edge_bottom_cluster[1], right_edge_bottom_cluster[1] = 90, 90
                    
                    top_cluster = np.insert(top_cluster, len(top_cluster), left_edge_top_cluster, axis=0)
                    top_cluster = np.insert(top_cluster, len(top_cluster), right_edge_top_cluster, axis=0)
                    bottom_cluster = np.insert(bottom_cluster, 0, left_edge_bottom_cluster, axis=0)
                    bottom_cluster = np.insert(bottom_cluster, len(bottom_cluster), right_edge_bottom_cluster, axis=0)
                    
                    cluster1 = self.__delete_circle(top_cluster).tolist()
                    cluster2 = self.__delete_circle(bottom_cluster).tolist()
                    
                    if len(cluster1) < 100 or len(cluster2) < 100:
                        return None
                    
                    return {
                        "relation": relation,
                        "border1": cluster1,
                        "border2": cluster2,
                    }

                else:
                    if cluster1_center[0] < cluster2_center[0]:
                        left_cluster = cluster1
                        right_cluster = cluster2
                    else:
                        left_cluster = cluster2
                        right_cluster = cluster1
                        
                    # bottom_left = min(left_cluster, key=lambda p: (p[0], -p[1]))
                    # top_left = max(left_cluster, key=lambda p: (p[0], -p[1]))
                    # bottom_right = min(right_cluster, key=lambda p: (-p[0], p[1]))
                    # top_right = max(right_cluster, key=lambda p: (p[0], p[1]))
                
                    return {
                        "relation": relation,
                        "border1": cluster1.tolist(),
                        "border2": cluster2.tolist(),
                    }
        
        return filtered_boundary_data

    def process(self, file_path: str, roti_data = None, time_points = None):
        """
        Main function to process the file.
        
        :param file_path: str, path to the HDF5 file with points.
        """ 
        self.file_name = os.path.basename(file_path)
        result = {}
        with h5.File(file_path, 'r') as file:
            
            data = file["data"]
            if time_points is None:
                time_points = data.keys()
                
            for time_point in time_points:
                logger.info(f"Processing {time_point} in {self.file_name}.")
                points_group = data[time_point]
                
                filtered_points = self.__filter_points(points_group)
                
                window_heigth = WINDOW_AREA / WINDOW_WIDTH
                
                sliding_windows = self.__apply_sliding_window(
                    filtered_points=filtered_points,
                    window_size=(window_heigth, WINDOW_WIDTH),
                )
                
                boundary_data = self.__get_boundary_data(sliding_windows)
                
                self.sliding_window_maps[time_point] = sliding_windows
                self.boundary_points[time_point] = boundary_data
                
                # plot_combined_results(
                #     sliding_windows=sliding_windows,
                #     time_point=time_point,
                #     boundary_data=boundary_data,
                #     roti_data=roti_data,
                #     roti_data={time_point: filtered_points},
                #     save_to_file=self.save_to_file,
                #     filename=self.file_name,
                #     boundary_condition=BOUNDARY_CONDITION
                # )
                
                result[time_point] = self.__create_boundary_clusters(
                    lat_list=boundary_data['lat'],
                    lon_list=boundary_data['lon']
                )
                
                plot_combined_graphs(
                    map_points=filtered_points,
                    sliding_windows=sliding_windows,
                    boundary_data=boundary_data,
                    boundary_condition=BOUNDARY_CONDITION,
                    time_point=time_point,
                    boundary_clusters=result,
                    save_to_file=self.save_to_file
                )
                    
        return result
