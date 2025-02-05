import matplotlib.pyplot as plt
import h5py as h5
import numpy as np
import os

from scipy.interpolate import griddata

from config import *

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
        self.boundary_coords = None
        
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


    def process(self, file_path: str):
        """
        Main function to process the file.
        
        :param file_path: str, path to the HDF5 file with points.
        """ 
        self.file_name = os.path.basename(file_path)
        
        with h5.File(file_path, 'r') as file:
            data = file["data"]
            for time_point in data.keys():
                logger.debug(f"Processing {time_point} in {self.file_name}.")
                points_group = data[time_point]
                
                filtered_points = self.__filter_points(points_group)
                
                window_heigth = WINDOW_AREA / WINDOW_WIDTH
                
                sliding_windows = self.__apply_sliding_window(
                    filtered_points=filtered_points,
                    window_size=(window_heigth, WINDOW_WIDTH),
                )
                
                self.plot_results(sliding_windows, time_point)
    
    
    def plot_results(self, sliding_windows, time_point):
        """
        Plots a scatter plot with a contour line at boundary_condition value.
        
        :param sliding_windows: List of processed data segments.
        """
        lon = np.array([entry['lon'] for entry in sliding_windows])
        lat = np.array([entry['lat'] for entry in sliding_windows])
        vals = np.array([entry['vals'] for entry in sliding_windows])

        safe_time_point = time_point.replace(":", "_")

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

        plt.figure(figsize=(10, 6))
        cmap = plt.get_cmap("coolwarm")
        norm = plt.Normalize(0, 0.1)
        scatter = plt.scatter(lon, lat, c=vals, cmap=cmap, norm=norm, edgecolors=None)
        plt.colorbar(scatter, label='Values')

        boundary_data = {'lat': [], 'lon': []}

        if not np.all(np.isnan(zi)):
            cs = plt.contour(
                xi, yi, zi, 
                levels=[self.boundary_condition], 
                colors='black', 
                linewidths=2
            )
            
            if cs is not None:
                for coll in cs.collections:
                    coll.remove()
                
                contour_segments = cs.allsegs[0]
                for segment in contour_segments:
                    if len(segment) > 0:
                        boundary_data['lon'].extend(segment[:, 0].tolist())
                        boundary_data['lat'].extend(segment[:, 1].tolist())
            
            if boundary_data['lon'] and boundary_data['lat']:
                self.boundary_coords = boundary_data
                
                plt.scatter(
                    boundary_data['lon'], 
                    boundary_data['lat'], 
                    color='black',
                    label=f'boundary'
                )
                plt.legend()

        plt.xlabel("Longitude")
        plt.ylabel("Latitude")
        plt.title(f"{safe_time_point} with {self.boundary_condition} Boundary")

        if self.save_to_file:
            file_name_base = os.path.splitext(self.file_name)[0]
            
            graphs_dir = os.path.join('graphs', file_name_base)
            os.makedirs(graphs_dir, exist_ok=True)
            
            graph_path = os.path.join(graphs_dir, f'{safe_time_point}.png')
            
            plt.savefig(graph_path)
            plt.close()
        else:
            plt.show()
                