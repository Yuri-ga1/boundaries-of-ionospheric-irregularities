import matplotlib.pyplot as plt
from matplotlib.dates import DateFormatter
from matplotlib.axes import Axes
import h5py as h5
from datetime import datetime, timezone
import numpy as np
import os
from typing import Optional

from config import logger

class DataProcessor:
    def __init__(
        self,
        lon_condition: float,
        lat_condition: float,
        elevation_cutoff: float,
        data_case_threshold: float,
        timestamps_threshold: float,
        segment_length: int,
        save_to_file : bool = False
    ):
        """
        Initializes the DataProcessor object.

        :param lon_condition: float, longitude condition for pole proximity.
        :param lat_condition: float, latitude condition for pole proximity.
        :param elevation_cutoff: float, minimum elevation angle.
        :param data_case_threshold: float, threshold for data quality.
        :param timestamps_threshold: float, threshold for splitting timestamps.
        :param segment_length: int, length of segments for standard deviation calculation.
        :param save_to_file : bool, whether to save graphs to file or show them.
        """
        self.lon_condition = lon_condition
        self.lat_condition = lat_condition
        self.elevation_cutoff = elevation_cutoff
        self.data_case_threshold = data_case_threshold
        self.timestamps_threshold = timestamps_threshold
        self.segment_length = segment_length
        self.save_to_file  = save_to_file 
        
        
        if self.save_to_file:
            import matplotlib
            matplotlib.use('Agg')
        
        self.calm_roti = None
        self.calm_timestamps = None
        
        self.restless_roti = None
        self.elevation = None
        self.timestamps = None
        
        self.file_name = None
        
    def __split_by_timestamp_threshold(self, data: np.ndarray, timestamps: np.ndarray, threshold: int):
        """
        Splits data and timestamps into segments where time gaps exceed the threshold.

        :param data: numpy.ndarray, data array to split.
        :param timestamps: numpy.ndarray, timestamp array corresponding to the data.
        :param threshold: int, time gap threshold in seconds.
        :return: tuple (list of numpy.ndarray, list of numpy.ndarray), split data and timestamps.
        """
        # Calculate differences between consecutive timestamps
        differences = np.diff(timestamps)

        # Find indices where the time gap exceeds the threshold
        break_indices = np.where(differences > threshold)[0] + 1

        # Split data and timestamps at the identified indices
        split_data = np.split(data, break_indices)
        splited_timestamps = np.split(timestamps, break_indices)

        return np.array(split_data, dtype=object), np.array(splited_timestamps, dtype=object)

    def __is_good_data(self, data: np.ndarray, threshold: float = 0.1):
        """
        Checks if the data is "good" by comparing the medians of its two halves.

        :param data: List or numpy.ndarray, numerical data.
        :param threshold: float, relative difference threshold for medians.
        :return: bool, True if "good", False if "bad".
        """
        n = len(data)
        
        if n < 2:
            raise ValueError("Not enough data to split into two parts")
        
        # Split the data into two halves
        mid = n // 2
        part1 = data[:mid]
        part2 = data[mid:]
        
        part1_meaning = np.median(part1)
        part2_meaning = np.median(part2)
        
        # Calculate the relative difference between the two parts
        relative_difference = abs(part1_meaning - part2_meaning) / max([part1_meaning, part2_meaning])
        
        # Classify the data based on the threshold
        if relative_difference <= threshold:
            return False
        else:
            return True


    def __calculate_std_series(self, series: np.ndarray, segment_length: int):
        """
        Calculate the standard deviation (STD) for successive segments in an array.

        :param series: List or array of numbers.
        :param segment_length: int, length of each segment.
        :return: numpy.ndarray
            - Array of results with standard deviations [sko_b, sko_a] for each segment pair.
        """
        n = len(series)
        
        if n <= segment_length*2:
            return None
        
        results = []
        for start in range(0, n - segment_length + 1):
            # first segment
            segment1 = series[start:start + segment_length]
            segment1_filtered = segment1[segment1 != 0]
            
            if len(segment1_filtered) * 2 <= segment_length:
                sko_b = None
            else:
                sko_b = np.median(segment1_filtered)
                # sko_b = np.std(segment1_filtered, ddof=1)
            
            end_second = start + 2 * segment_length
            if end_second <= n:
                segment2 = series[start + segment_length:end_second]
                segment2_filtered = segment2[segment2 != 0] 
                
                if len(segment2_filtered)  * 2 <= segment_length:
                    sko_a = None
                else:
                    sko_a = np.median(segment2_filtered)
                    # sko_a = np.std(segment2_filtered, ddof=1)
                    
                results.append([sko_b, sko_a])
            else:
                return np.array(results)
        
    def __process_station(self, restless: h5.File, calm: Optional[h5.File], station: str):
        """
        Processes data for a specific station.

        :param restless: h5py.File, the file containing restless station data.
        :param calm: Optional[h5py.File], the file containing calm station data, or None if not provided.
        :param station: str, name of the station.
        """
        station_loc = dict(restless[station].attrs)
        is_near_pole = station_loc['lon'] <= self.lon_condition and station_loc['lat'] >= self.lat_condition
        if not is_near_pole:
            return
        
        satellites = restless[station].keys()
        for satellite in satellites:
            self.__process_satellite(restless, calm, station, satellite)


    def __process_satellite(self, restless: h5.File, calm: Optional[h5.File], station: str, satellite: str):
        """
        Processes data for a specific satellite of a station.

        :param restless: h5py.File, the file containing restless satellite data.
        :param calm: Optional[h5py.File], the file containing calm satellite data, or None if not provided.
        :param station: str, name of the station.
        :param satellite: str, name of the satellite.
        """
        logger.info(f"Processing {station} - {satellite}")
        if calm is not None:
            try:
                self.calm_roti = calm[station][satellite]['roti'][:]
                self.calm_timestamps = calm[station][satellite]['timestamp'][:]
            except Exception as e:
                logger.error(f"There is no station or satelite on calm day. {station}-{satellite}")
        
        self.restless_roti = restless[station][satellite]['roti'][:]
        self.timestamps = restless[station][satellite]['timestamp'][:]
        self.elevation = np.degrees(restless[station][satellite]['elevation'][:])

        valid_indices = self.elevation >= self.elevation_cutoff
        valid_roti = self.restless_roti[valid_indices]
        valid_timestamps = self.timestamps[valid_indices]
        
        splited_roti, splited_timestamps = self.__split_by_timestamp_threshold(valid_roti, valid_timestamps, self.timestamps_threshold)

        try:
            delete_idx = []
            for i, roti in enumerate(splited_roti):
                if not self.__is_good_data(data=roti, threshold=self.data_case_threshold):
                    logger.info(f"Data is bad in {station}-{satellite} {i} period")
                    delete_idx.append(i)
                    continue
            splited_roti = np.delete(splited_roti, delete_idx)
            splited_timestamps = np.delete(splited_timestamps, delete_idx)
        except ValueError as e:
            logger.error(f"{e}. {station}-{satellite}")
        
        self.__create_graphs_for_satellite(
            station, satellite, splited_roti, splited_timestamps
        )


    def __create_graphs_for_satellite(self, station: str, satellite: str, splited_roti: np.ndarray, splited_timestamps: np.ndarray):
        """
        Creates graphs for satellite data after processing.

        :param station: str, name of the station.
        :param satellite: str, name of the satellite.
        :param splited_roti: list of numpy.ndarray, split ROTI data.
        :param splited_timestamps: list of numpy.ndarray, split timestamps.
        """
        all_extremum_max, all_extremum_min = [], []
        all_max_index, all_min_index = [], []
        
        if len(splited_roti) <= 0:
            logger.warning(f"There is no good data period in {station}-{satellite}")
            return

        for roti_part, timestamp_part in zip(splited_roti, splited_timestamps):
            results = self.__calculate_std_series(roti_part, self.segment_length)
            
            if results is None:
                logger.warning(f"Data segment < than segment_length*2 in {station}-{satellite}")
                splited_timestamps = [x for x in splited_timestamps if not np.array_equal(x, timestamp_part)]
                continue
            
            sko_a, sko_b = results[:, 1], results[:, 0]

            if None in sko_a or None in sko_b:
                logger.warning(f"None values in sko series for {station}-{satellite}")
                continue
            
            extremum_max, extremum_min, max_index, min_index = self.__process_extremum(sko_a, sko_b, roti_part)
            all_extremum_max.extend(extremum_max)
            all_extremum_min.extend(extremum_min)
            all_max_index.append(max_index)
            all_min_index.append(min_index)
            
        if len(all_extremum_max) <= 0:
            logger.warning(f"It is impossible to find extremums in {station}-{satellite}")
            return
        
        self.__plot_graphs(
            station=station,
            satellite=satellite,
            extremum_max=all_extremum_max,
            extremum_min=all_extremum_min,
            max_indices=all_max_index,
            min_indices=all_min_index,
            splited_timestamps=splited_timestamps
        )


    def __process_extremum(self, sko_a: np.ndarray, sko_b: np.ndarray, roti_part: np.ndarray):
        """
        Finds extremum values and their indices.

        :param sko_a: numpy.ndarray, standard deviation for the second segment.
        :param sko_b: numpy.ndarray, standard deviation for the first segment.
        :param roti_part: numpy.ndarray, ROTI values for the segment.
        :return: tuple (numpy.ndarray, numpy.ndarray, int, int), extremum arrays and indices.
        """
        extremum_max = np.zeros_like(roti_part)
        extremum_min = np.zeros_like(roti_part)
        ratios_max = np.divide(sko_a, sko_b, where=sko_b != 0)
        ratios_min = np.divide(sko_b, sko_a, where=sko_a != 0)
        extremum_max[self.segment_length:-self.segment_length+1] = ratios_max
        extremum_min[self.segment_length:-self.segment_length+1] = ratios_min
        
        max_index = np.argmax(extremum_max)
        min_index = np.argmax(extremum_min)
        return extremum_max, extremum_min, max_index, min_index

    def __plot_graphs(
        self,
        station: str,
        satellite: str,
        extremum_max: np.ndarray,
        extremum_min: np.ndarray,
        splited_timestamps: np.ndarray,
        max_indices: list,
        min_indices: list,
    ):
        """
        Plots graphs for extremums and ROTI data.

        :param station: str, name of the station.
        :param satellite: str, name of the satellite.
        :param extremum_max: numpy.ndarray, extremum max values.
        :param extremum_min: numpy.ndarray, extremum min values.
        :param max_indices: list, indices of maximum values.
        :param max_indices: list, indices of minimum values.
        :param splited_timestamps: list of numpy.ndarray, split timestamps.
        """    
        valid_indices = self.elevation >= self.elevation_cutoff
        invalid_indices = ~valid_indices

        valid_roti = self.restless_roti[valid_indices]
        valid_timestamps = self.timestamps[valid_indices]
        invalid_roti = self.restless_roti[invalid_indices]
        invalid_timestamps = self.timestamps[invalid_indices]
        
        splited_timestamps_one_dem = np.concatenate(splited_timestamps).astype(int)
        
        valid_times = [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in valid_timestamps]
        invalid_times = [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in invalid_timestamps]
        splited_times = [datetime.fromtimestamp(ts, tz=timezone.utc) for ts in splited_timestamps_one_dem]
        
        fig, axes = plt.subplots(3, 1, figsize=(10, 15), sharex=True)

        # Plot 1: extremum_max
        axes[0].scatter(splited_times, extremum_max)
        self.__highlight_extremums(axes[0], max_indices, splited_timestamps, "yellow", "green")
        axes[0].set_ylabel('sko_a/sko_b')
        axes[0].set_title(f'{station} - {satellite} - extremum_max')
        axes[0].grid(True, linestyle='--', alpha=0.5)

        # Plot 2: extremum_min
        axes[1].scatter(splited_times, extremum_min)
        self.__highlight_extremums(axes[1], min_indices, splited_timestamps, "yellow", "green")
        axes[1].set_ylabel('sko_b/sko_a')
        axes[1].set_title(f'{station} - {satellite} - extremum_min')
        axes[1].grid(True, linestyle='--', alpha=0.5)

        # Plot 3: ROTI
        axes[2].scatter(valid_times, valid_roti, label="Valid roti for restless day", color="blue")
        axes[2].scatter(invalid_times, invalid_roti, label="Invalid roti for restless day", color="red")
        
        if self.calm_roti is not None:
            dt = valid_times[0].date()
            calm_times = [datetime.fromtimestamp(ts, tz=timezone.utc).replace(year=dt.year, month=dt.month, day=dt.day) for ts in self.calm_timestamps]
            axes[2].scatter(calm_times, self.calm_roti, label="Roti for calm day", color="green")
            
        axes[2].set_xlabel('Time')
        axes[2].set_ylabel('ROTI')
        axes[2].set_title(f'{station} - {satellite} - ROTI')
        axes[2].grid(True, linestyle='--', alpha=0.5)
        axes[2].legend()

        time_formatter = DateFormatter('%H:%M')
        plt.gca().xaxis.set_major_formatter(time_formatter)
        plt.xticks(rotation=45)
        fig.tight_layout()
        
        
        if self.save_to_file:
            station_dir = os.path.join('graphs', self.file_name, station)
            os.makedirs(station_dir, exist_ok=True)
            graph_path = os.path.join(station_dir, f'{station}_{satellite}.png')
            plt.savefig(graph_path)
            plt.close()
        else:
            plt.show()
        

    def __highlight_extremums(
        self,
        axis: Axes,
        indices: list,
        splited_timestamps: np.ndarray,
        color_before: str,
        color_after: str
    ):
        """
        Highlights extremums on the plot.

        :param axis: matplotlib.axes.Axes, plot axis to highlight.
        :param indices: list, indices of extremum points.
        :param splited_timestamps: list of numpy.ndarray, split timestamps.
        :param color_before: str, color for the range before extremum.
        :param color_after: str, color for the range after extremum.
        """
        for max_idx, timestamps_part in zip(indices, splited_timestamps):
            max_before_start = max(0, timestamps_part[max_idx] - (self.segment_length * 30))
            max_before_end = timestamps_part[max_idx]
            max_after_start = timestamps_part[max_idx]
            max_after_end = min(timestamps_part[-1], timestamps_part[max_idx] + (self.segment_length * 30))

            max_before_start_time = datetime.fromtimestamp(max_before_start, tz=timezone.utc)
            max_before_end_time = datetime.fromtimestamp(max_before_end, tz=timezone.utc)
            max_after_start_time = datetime.fromtimestamp(max_after_start, tz=timezone.utc)
            max_after_end_time = datetime.fromtimestamp(max_after_end, tz=timezone.utc)

            axis.axvspan(max_before_start_time, max_before_end_time, color=color_before, alpha=0.3)
            axis.axvspan(max_after_start_time, max_after_end_time, color=color_after, alpha=0.3)


    def run(self, restless_day: str, calm_day: str = None, stations: list = None):
        """
        Main function to process the file and create graphs.

        Reads station data and processes satellites for each station.
        
        :param restless_day: str, path to the HDF5 file with restless data.
        :param calm_day: str, path to the HDF5 file calm restless data.
        :param stations: list, stations to process.
        """ 
        with h5.File(restless_day, 'r') as restless:
            self.file_name = restless.filename
            
            if stations is None:
                stations = restless.keys()
                    
            if calm_day is not None:
                calm = h5.File(calm_day, 'r')
            else:
                calm = None
            
            try:
                for station in stations:
                    self.__process_station(restless, calm, station)
            finally:
                if calm is not None:
                    calm.close()
                