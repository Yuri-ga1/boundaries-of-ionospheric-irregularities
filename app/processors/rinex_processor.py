import numpy as np
import os
import h5py as h5
from config import *
from datetime import datetime as dt
import datetime
from collections import OrderedDict

class RinexProcessor:
    def __init__(self, file_path):
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.file = None
        self.stations_coords = {}
        self.data = {}
        self.lon_condition = LON_CONDITION
        self.lat_condition = LAT_CONDITION
    
    def __enter__(self):
        self.file = h5.File(self.file_path, 'r')
        return self
        
    def __exit__(self, exc_type, exc_value, traceback):
        if self.file:
            self.file.close()
    
    def __save_station_coords(self, station_name):
        station = self.file[station_name]
        lat, lon = station.attrs['lat'], station.attrs['lon']
        # if lat >= 0 and -2.53073 <= lon <= -0.523599:
        self.stations_coords[station_name] = {'lat': lat, 'lon': lon}
            
    def __process_satellite(self, station_name, satellite_name):
        logger.info(f"Processing {station_name}_-_{satellite_name}")
        
        roti = self.file[station_name][satellite_name]['roti'][:]
        azs = self.file[station_name][satellite_name]['azimuth'][:]
        els = self.file[station_name][satellite_name]['elevation'][:]
        ts = self.file[station_name][satellite_name]['timestamp'][:]
        
        el_mask = (els >= np.radians(10))
        roti = roti[el_mask]
        azs = azs[el_mask]
        els = els[el_mask]
        ts = ts[el_mask]
        
        datetimes = [dt.fromtimestamp(float(t), datetime.UTC) for t in ts]
        try:
            i = datetimes.index(dt(2019, 5, 14, 2, 10, tzinfo=datetime.UTC))
        except Exception as e:
            return None
        
        
        
        roti = [roti[i]]
        azs = [azs[i]]
        els = [els[i]]
        ts = [ts[i]]
        
        st_coords = self.stations_coords[station_name]
        
        all_lat, all_lon = [], []
        for az, el in zip(azs, els):
            lat, lon = self.__az_el_to_lat_lon(
                s_lat=st_coords['lat'],
                s_lon=st_coords['lon'],
                az=az,
                el=el
            )
            all_lat.append(lat)
            all_lon.append(lon)
        
        # all_lat = np.degrees(all_lat)
        # all_lon = np.degrees(all_lon)
        #mask = (all_lon >= -120) & (all_lon <= self.lon_condition) & (all_lat >= self.lat_condition) & (ts % 300 == 0)
        return {
            'roti': roti,
            'lat': all_lat,
            'lon': all_lon,
            'timestamp': ts
        }
        # return {
        #     'roti': roti[mask],
        #     'lat': all_lat[mask],
        #     'lon': all_lon[mask],
        #     'timestamp': ts[mask]
        # }
    
    @staticmethod 
    def __az_el_to_lat_lon(s_lat, s_lon, az, el,  hm=HM, R=RE_KM):
        """
        Calculates subionospheric point and deltas from site
        Parameters:
            s_lat, slon - site latitude and longitude in radians
            hm - ionposheric maximum height (km)
            az, el - azimuth and elevation of the site-sattelite line of sight in
                radians
            R - Earth radius (km)
        """
        #TODO use meters
        psi = np.pi / 2 - el - np.arcsin(np.cos(el) * R / (R + hm))
        lat = bi = np.arcsin(np.sin(s_lat) * np.cos(psi) + np.cos(s_lat) * np.sin(psi) * np.cos(az))
        lon = s_lon + np.arcsin(np.sin(psi) * np.sin(az) / np.cos(bi))

        lon = lon - 2 * np.pi if lon > np.pi else lon
        lon = lon + 2 * np.pi if lon < -np.pi else lon
        return lat, lon

        
    def process(self):
        processed_data  = {}
        for station in self.file:
            self.__save_station_coords(station)
        
        for station_name in self.stations_coords:
            for satellite_name in self.file[station_name]:
                result = self.__process_satellite(station_name, satellite_name)
                
                if result is None:
                    continue
                
                for i in range(len(result['timestamp'])):
                    ts = dt.fromtimestamp(float(result['timestamp'][i]), datetime.UTC)
                    ts = str(ts)
                    entry = {
                        'station': station_name,
                        'satellite': satellite_name,
                        'roti': result['roti'][i],
                        'lat': result['lat'][i],
                        'lon': result['lon'][i]
                    }
                    if ts not in processed_data:
                        processed_data[ts] = []
                    processed_data[ts].append(entry)
                    
        self.data = OrderedDict(sorted(processed_data.items()))