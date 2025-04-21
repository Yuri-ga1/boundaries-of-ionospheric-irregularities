import numpy as np
import os
import h5py as h5
from config import *
from datetime import datetime as dt
import datetime
from collections import OrderedDict

from app.az_el_to_lot_lon import az_el_to_lat_lon

class RinexProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.file = None
        self.lon_condition = LON_CONDITION
        self.lat_condition = LAT_CONDITION
        
        self.stations_coords = {}
        self.data = {}
        self.flybys = {}
    
    def __enter__(self):
        self.file = h5.File(self.file_path, 'r')
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        if self.file:
            self.file.close()
    
    def __save_station_coords(self, station_name):
        station = self.file[station_name]
        lat, lon = station.attrs['lat'], station.attrs['lon']
        if lat >= 0 and -2.53073 <= lon <= -0.523599:
            self.stations_coords[station_name] = {'lat': lat, 'lon': lon}
            
    def __process_flyby(self, station_name, satellite_name, roti, ts):
        time_diffs = np.diff(ts)
        pass_indices = np.where(time_diffs >= 1800)[0] + 1
        pass_splits = np.split(np.arange(len(ts)), pass_indices)

        if station_name not in self.flybys:
            self.flybys[station_name] = {}
        if satellite_name not in self.flybys[station_name]:
            self.flybys[station_name][satellite_name] = {}

        for pass_num, indices in enumerate(pass_splits):
            flyby_roti = roti[indices]
            flyby_ts = ts[indices]

            self.flybys[station_name][satellite_name][f'flyby{pass_num}'] = {
                'roti': flyby_roti.tolist(),
                'timestamps': flyby_ts.tolist(),
            }
            
    def __process_satellite(self, station_name, satellite_name):
        logger.info(f"Processing {station_name}_-_{satellite_name}")
        
        roti = self.file[station_name][satellite_name]['roti'][:]
        azs = self.file[station_name][satellite_name]['azimuth'][:]
        els = self.file[station_name][satellite_name]['elevation'][:]
        ts = self.file[station_name][satellite_name]['timestamp'][:]
        
        self.__process_flyby(station_name, satellite_name, roti, ts)
        
        el_mask = (els >= np.radians(10))
        roti = roti[el_mask]
        azs = azs[el_mask]
        els = els[el_mask]
        ts = ts[el_mask]
        
        st_coords = self.stations_coords[station_name]
        
        all_lat, all_lon = [], []
        for az, el in zip(azs, els):
            lat, lon = az_el_to_lat_lon(
                s_lat=st_coords['lat'],
                s_lon=st_coords['lon'],
                az=az,
                el=el
            )
            all_lat.append(lat)
            all_lon.append(lon)
        
        all_lat = np.degrees(all_lat)
        all_lon = np.degrees(all_lon)
        mask = (all_lon >= -120) & (all_lon <= self.lon_condition) & (all_lat >= self.lat_condition) & (ts % 300 == 0)
        
        return {
            'vals': roti[mask],
            'lat': all_lat[mask],
            'lon': all_lon[mask],
            'timestamp': ts[mask]
        }

    def sort_dict(self, d):
        """
        Recursively sorts a nested dictionary by its keys.
        
        Parameters:
            d (dict): The dictionary to be sorted. Can contain nested dictionaries.
        
        Returns:
            OrderedDict: A new dictionary with all levels sorted by keys.
        """
        if isinstance(d, dict):
            return OrderedDict(
                sorted((key, self.sort_dict(value)) for key, value in d.items())
            )
        return d
        
    def process(self):
        processed_data  = {}
        for station in self.file:
            self.__save_station_coords(station)
        
        for station_name in self.stations_coords:
            for satellite_name in self.file[station_name]:
                result = self.__process_satellite(station_name, satellite_name)
                
                if result is None:
                    continue
                
                st_sat = f"{station_name}_{satellite_name}"
                for i in range(len(result['timestamp'])):
                    ts = dt.fromtimestamp(float(result['timestamp'][i]), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    entry = {
                        'vals': result['vals'][i],
                        'lat': result['lat'][i],
                        'lon': result['lon'][i]
                    }
                    
                    if ts not in processed_data:
                        processed_data[ts] = {}
                        
                    processed_data[ts][st_sat] = entry
                    
        self.data = self.sort_dict(processed_data)