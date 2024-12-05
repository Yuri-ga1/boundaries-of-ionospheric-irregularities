   # import matplotlib
# matplotlib.use('Agg')

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
        segment1_filtered = segment1[segment1 != 0]
        
        if len(segment1_filtered) * 2 <= segment_length:
            sko_b = None
        else:
            sko_b = np.std(segment1_filtered, ddof=1)
        
        end_second = start + 2 * segment_length
        if end_second <= n:
            segment2 = series[start + segment_length:end_second]
            segment2_filtered = segment2[segment2 != 0] 
            
            if len(segment2_filtered)  * 2 <= segment_length:
                sko_a = None
            else:
                sko_a = np.std(segment2_filtered, ddof=1)
                
            results.append([sko_b, sko_a])
        else:
            return np.array(results)


file_path = os.path.join("files", "2016-10-25.h5")
# stations = ['kugc', 'will', 'fsic', 'rabc', 'corc', 'ais5', 'pot6', 'sch2', 'invk', 'ac52', 'ab01', 'txdl']
stations = ['kugc']

        
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

                results = calculate_std_series(roti, SEGMENT_LENGTH)
                sko_a, sko_b = results[:, 1], results[:, 0]
                
                if np.any(sko_a == None) or np.any(sko_b == None):
                    print("Here is None in sko series")
                
                # Calculate the ratios
                extremum_max = np.zeros_like(roti)
                extremum_min = np.zeros_like(roti)
                ratios_max = np.divide(sko_a, sko_b, where=sko_b != 0)
                ratios_min = np.divide(sko_b, sko_a, where=sko_a != 0)
                extremum_max[SEGMENT_LENGTH:-SEGMENT_LENGTH+1] = ratios_max
                extremum_min[SEGMENT_LENGTH:-SEGMENT_LENGTH+1] = ratios_min
                
                # Find maximum and minimum indices
                max_index = np.argmax(ratios_max)
                min_index = np.argmax(ratios_min)

                # Define segments for max
                max_before_start = max(0, SEGMENT_LENGTH - 1 + max_index - SEGMENT_LENGTH)
                max_before_end = max(0, SEGMENT_LENGTH - 1 + max_index)
                max_after_start = max(0, max_before_end + 1)
                max_after_end = min(len(extremum_max), max_after_start + SEGMENT_LENGTH)

                # Define segments for min
                min_before_start = max(0, SEGMENT_LENGTH - 1 + min_index - SEGMENT_LENGTH)
                min_before_end = max(0, SEGMENT_LENGTH - 1 + min_index)
                min_after_start = max(0, min_before_end + 1)
                min_after_end = min(len(extremum_min), min_after_start + SEGMENT_LENGTH)
                
                points = np.arange(len(roti))
                
                # Create subplots
                fig, axes = plt.subplots(3, 1, figsize=(10, 15), sharex=True)
                
                # Plot 1: extremum_max
                axes[0].scatter(points, extremum_max)
                axes[0].axvspan(max_before_start, max_before_end, color='yellow', alpha=0.3, label='Before max segment')
                axes[0].axvspan(max_after_start, max_after_end, color='green', alpha=0.3, label='After max segment')
                axes[0].set_ylabel('extremum_max')
                axes[0].set_title(f'{station} - {satellite} - extremum_max')
                axes[0].grid(True, linestyle='--', alpha=0.5)
                axes[0].legend()

                # Plot 2: extremum_min
                axes[1].scatter(points, extremum_min)
                axes[1].axvspan(min_before_start, min_before_end, color='yellow', alpha=0.3, label='Before min segment')
                axes[1].axvspan(min_after_start, min_after_end, color='green', alpha=0.3, label='After min segment')
                axes[1].set_ylabel('extremum_min')
                axes[1].set_title(f'{station} - {satellite} - extremum_min')
                axes[1].grid(True, linestyle='--', alpha=0.5)
                axes[1].legend()

                # Plot 3: roti
                axes[2].scatter(points, roti, label="roti")
                axes[2].set_xlabel('Points')
                axes[2].set_ylabel('roti')
                axes[2].set_title(f'{station} - {satellite} - ROTI')
                axes[2].grid(True, linestyle='--', alpha=0.5)
                axes[2].legend()

                # Adjust layout
                plt.xticks(rotation=45)
                fig.tight_layout()

                # Show the plot
                plt.show()


if __name__ == "__main__":
    create_std_graphs_from_file()