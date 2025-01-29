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
        
        
        if self.save_to_file:
            import matplotlib
            matplotlib.use('Agg')
            
    def __filter_data(self, points_group):
        lon = points_group['lon'][()]
        lat = points_group['lat'][()]
        vals = points_group['vals'][()]
        
        mask = (lon <= 120) & (lon >= 60) & (lat >= self.lat_condition)
        
        return vals[mask]


    def run(self, file_path: str):
        """
        Main function to process the file.
        
        :param file_path: str, path to the HDF5 file with points.
        """ 
        with h5.File(file_path, 'r') as file:
            data = file["data"]
            points_group = data['2010-04-05 02:15:00.000000']
            
            print(f"points_group data count: {len(points_group)}")
            filtered_points = self.__filter_data(points_group)
            
            print(f"Filtered data count: {len(filtered_points)}")
            
                