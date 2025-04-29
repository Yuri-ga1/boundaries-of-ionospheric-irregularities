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
            
    def __divide_by_flyby(self, station_name, satellite_name, roti, ts):
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
                'roti': flyby_roti,
                'timestamps': flyby_ts,
            }
            
    def __process_satellite(self, station_name, satellite_name):
        roti = self.file[station_name][satellite_name]['roti'][:]
        azs = self.file[station_name][satellite_name]['azimuth'][:]
        els = self.file[station_name][satellite_name]['elevation'][:]
        ts = self.file[station_name][satellite_name]['timestamp'][:]
        
        self.__divide_by_flyby(station_name, satellite_name, roti, ts)
        
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
    
    def __create_map(self, output_path):
        with h5.File(output_path, 'w') as f:
            processed_data_group = f.create_group('processed_data')
            data_group = f.create_group('data')
            flybys_group = f.create_group('flybys')

            for ts, st_sat in self.data.items():
                lats = []
                lons = []
                vals = []
                
                for st_sat_data in st_sat.values():
                    lats.append(st_sat_data['lat'])
                    lons.append(st_sat_data['lon'])
                    vals.append(st_sat_data['vals'])

                # Склеиваем все данные
                lats = np.array(lats)
                lons = np.array(lons)
                vals = np.array(vals)

                if lats.ndim > 1:
                    lats = lats.flatten()
                if lons.ndim > 1:
                    lons = lons.flatten()
                if vals.ndim > 1:
                    vals = vals.flatten()

                # Создаем группу для текущего времени
                ts_group = data_group.create_group(ts)
                ts_group.create_dataset('lat', data=lats)
                ts_group.create_dataset('lon', data=lons)
                ts_group.create_dataset('vals', data=vals)


                pd_ts_group = processed_data_group.create_group(ts)
                # Для каждой станции создаем соответствующие наборы данных
                for station_name, entry in st_sat.items():
                    station_group = pd_ts_group.create_group(station_name)
                    station_group.create_dataset('lat', data=entry['lat'])
                    station_group.create_dataset('lon', data=entry['lon'])
                    station_group.create_dataset('vals', data=entry['vals'])

            for station_name, satellites in self.flybys.items():
                station_group = flybys_group.create_group(station_name)
                for satellite_name, flyby_data in satellites.items():
                    satellite_group = station_group.create_group(satellite_name)
                    for flyby_name, flyby_info in flyby_data.items():
                        flyby_group = satellite_group.create_group(flyby_name)
                        flyby_group.create_dataset('roti', data=flyby_info['roti'])
                        flyby_group.create_dataset('timestamps', data=flyby_info['timestamps'])
    
    def __restor_data(self, map_path):
        processed_data = {}
        flybys_data = {}

        with h5.File(map_path, 'r') as f:
            # Восстановление данных карты
            processed_data_group = f['processed_data']
            for ts in processed_data_group:
                ts_group = processed_data_group[ts]
                entries = {}
                for station_name in ts_group:
                    station_group = ts_group[station_name]
                    lat = station_group['lat'][()]
                    lon = station_group['lon'][()]
                    vals = station_group['vals'][()]
                    entries[station_name] = {
                        'lat': lat,
                        'lon': lon,
                        'vals': vals
                    }
                processed_data[ts] = entries

            # Восстановление данных о пролётах
            if 'flybys' in f:
                flybys_group = f['flybys']
                for station_name in flybys_group:
                    station_group = flybys_group[station_name]
                    flybys_data[station_name] = {}
                    for satellite_name in station_group:
                        satellite_group = station_group[satellite_name]
                        flybys_data[station_name][satellite_name] = {}
                        for flyby_name in satellite_group:
                            flyby_group = satellite_group[flyby_name]
                            flybys_data[station_name][satellite_name][flyby_name] = {
                                'roti': flyby_group['roti'][()],
                                'timestamps': flyby_group['timestamps'][()]
                            }

        self.data = self.sort_dict(processed_data)
        self.flybys = self.sort_dict(flybys_data)


    def process(self, map_name):
        map_path = os.path.join(MAP_PATH, map_name)
        
        if os.path.exists(map_path):
            logger.info(f"Map file is exist: {map_path} restoring data")
            self.__restor_data(map_path)
            return
        
        processed_data  = {}
        for station in self.file:
            self.__save_station_coords(station)
        
        for station_name in self.stations_coords:
            logger.info(f"Processing {station_name}")
            for satellite_name in self.file[station_name]:
                result = self.__process_satellite(station_name, satellite_name)
                
                if result is None:
                    continue
                
                st_sat = f"{station_name}_{satellite_name}"
                for i in range(len(result['timestamp'])):
                    ts = dt.fromtimestamp(float(result['timestamp'][i]), datetime.UTC).strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    entry = {
                        'vals': result['vals'][i]/3,
                        'lat': result['lat'][i],
                        'lon': result['lon'][i]
                    }
                    
                    if ts not in processed_data:
                        processed_data[ts] = {}
                        
                    processed_data[ts][st_sat] = entry
                    
        self.data = self.sort_dict(processed_data)
        map_path = os.path.join(MAP_PATH, map_name)
        self.__create_map(map_path)