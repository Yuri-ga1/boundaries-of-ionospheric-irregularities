import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.axes import Axes
import h5py as h5
from datetime import datetime, timezone
import numpy as np
import os
from typing import Optional
import traceback

from config import logger

class DataProcessor:
    def __init__(
        self,
        lon_condition: float,
        lat_condition: float,
        segment_move_step: float,
        save_to_file : bool = False
    ):
        """
        Initializes the DataProcessor object.

        :param lon_condition: float, longitude condition for pole proximity.
        :param lat_condition: float, latitude condition for pole proximity.
        :param segment_move_step: float, length of segments for standard deviation calculation.
        :param save_to_file : bool, whether to save graphs to file or show them.
        """
        self.lon_condition = lon_condition
        self.lat_condition = lat_condition
        self.segment_move_step = segment_move_step
        self.save_to_file  = save_to_file 
        
        self.file_name = None
        
        if self.save_to_file:
            import matplotlib
            matplotlib.use('Agg')
            
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
    
    def __apply_sliding_window(self, filtered_points, window_size=(5, 10), step=0.2):
        """
        Applies a sliding window approach to segment the data.

        :param filtered_points: dict, containing 'lon', 'lat', and 'vals'.
        :param window_size: tuple, defining (lat, lon) window size.
        :param step: float, step size in degrees.
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
                
                current_lon += step
            
            current_lat += 1.0
            
        return windows


    def run(self, file_path: str):
        """
        Main function to process the file.
        
        :param file_path: str, path to the HDF5 file with points.
        """ 
        with h5.File(file_path, 'r') as file:
            self.file_name = file.filename
            data = file["data"]
            points_group = data['2016-10-25 02:15:00.000000']
            
            filtered_points = self.__filter_points(points_group)
            
            logger.debug(f"Filtered data count = {len(filtered_points['vals'])} in file: {self.file_name}")
            
            sliding_windows = self.__apply_sliding_window(filtered_points)
            
            logger.info(f"Processed {len(sliding_windows)} sliding windows in file: {self.file_name}")
            self.plot_results(sliding_windows)
    
    
    def plot_results(self, sliding_windows):
        """
        Plots a scatter plot of the processed data.
        
        :param sliding_windows: List of processed data segments.
        """
        lon = [entry['lon'] for entry in sliding_windows]
        lat = [entry['lat'] for entry in sliding_windows]
        vals = [entry['vals'] for entry in sliding_windows]
        
        cmap = plt.get_cmap("coolwarm")
        norm = plt.Normalize(0, 0.1)
        
        plt.figure(figsize=(10, 6))
        scatter = plt.scatter(lon, lat, c=vals, cmap=cmap, norm=norm, edgecolors='k')
        plt.colorbar(scatter, label='Values')
        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.title("Scatter Plot of Processed Data")
        
        if self.save_to_file:
            plt.savefig("scatter_plot.png")
        else:
            plt.show()
                