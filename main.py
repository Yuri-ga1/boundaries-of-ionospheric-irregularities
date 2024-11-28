import matplotlib
matplotlib.use('Agg')

import matplotlib.pyplot as plt
import numpy as np
import os
import h5py as h5

from config import *

def calculate_std_series(series, segment_length):
    """
    Calculate STD for successive segments in an array.
    
    :param series: List or array of numbers.
    :param segment_length: Length of one segment.
    :return: NumPy array with results [sko_b, sko_a].
    """
    n = len(series)
    results = []
    
    for start in range(0, n - segment_length + 1):
        # first segment
        segment1 = series[start:start + segment_length]
        sko_b = np.std(segment1, ddof=1)
        
        end_second = start + 2 * segment_length
        if end_second <= n:
            segment2 = series[start + segment_length:end_second]
            sko_a = np.std(segment2, ddof=1)
            results.append([sko_b, sko_a])
        else:
            return np.array(results)


file_path = os.path.join("files", "2016-10-25.h5")
stations = ['kugc', 'will', 'fsic', 'rabc', 'corc', 'ais5', 'pot6', 'sch2', 'invk', 'ac52', 'ab01', 'txdl']

        
def create_std_graphs_from_file():
    with h5.File(file_path, 'r') as file:
        
        for station in stations:
            station_loc = dict(file[station].attrs)
            is_near_pole = station_loc['lon'] <= LON_CONDITION and station_loc['lat'] >= LAT_CONDITION
            
            if not is_near_pole:
                continue
            
            station_dir = os.path.join('graphs', station)
            os.makedirs(station_dir, exist_ok=True)
            
            satellites = file[station].keys()
            for satellite in satellites:
                roti = file[station][satellite]['roti'][:]
            
                results = calculate_std_series(roti, 30)
                sko_a, sko_b = results[:, 1], results[:, 0]
                
                ratios = np.divide(sko_a, sko_b, where=sko_b != 0)

                points = [i for i in range(0, len(ratios))]
                
                plt.figure()
                plt.scatter(x=points, y=ratios)
                plt.xlabel('Points')
                plt.ylabel('Ratios')
                plt.title(f'{station} - {satellite}')
                plt.grid(True, linestyle='--', alpha=0.5)
                
                graph_path = os.path.join(station_dir, f'{satellite}.png')
                
                plt.savefig(graph_path)
                plt.close()


if __name__ == "__main__":
    create_std_graphs_from_file()