import numpy as np
from datetime import timedelta
import datetime
from datetime import datetime as dt
from gnss_processor.app.utils.az_el_to_lot_lon import az_el_to_lat_lon
from config import *

class Trajectory:
    def __init__(self, lat_site: float, lon_site: float) -> None:
        self.lat_site = lat_site
        self.lon_site = lon_site
        self.traj_lat = []
        self.traj_lon = []
        self.times = []
        
    def filter_points(self):
        mask = (self.traj_lon >= -120) & (self.traj_lon <= LON_CONDITION) & (self.traj_lat >= LAT_CONDITION)
        
        self.traj_lon = self.traj_lon[mask]
        self.traj_lat = self.traj_lat[mask]
        self.times = self.times[mask]

    def adding_artificial_value(self, minutes: int = 10) -> None:
        interval = timedelta(minutes=minutes)
        times_dt = np.array([dt.fromtimestamp(t, datetime.UTC) for t in self.times])
        diffs = np.diff(times_dt)
        indices_to_insert = np.where(diffs > interval)[0] + 1
        
        values_to_insert_time = []
        for i in indices_to_insert:
            midpoint = times_dt[i - 1] + (times_dt[i] - times_dt[i - 1]) / 2
            values_to_insert_time.extend([
                (midpoint - timedelta(seconds=30)).timestamp(),
                midpoint.timestamp(),
                (midpoint + timedelta(seconds=30)).timestamp()
            ])
        
        values_to_insert_coords = [None] * (3 * len(indices_to_insert))
        
        self.times = np.insert(self.times, indices_to_insert.repeat(3), values_to_insert_time)
        self.traj_lat = np.insert(self.traj_lat, indices_to_insert.repeat(3), values_to_insert_coords)
        self.traj_lon = np.insert(self.traj_lon, indices_to_insert.repeat(3), values_to_insert_coords)

    def procces(self, azs, els, times) -> None:
        self.times = np.array(times, dtype=float)
        self.traj_lat = []
        self.traj_lon = []
        
        for az, el in zip(azs, els):
            lat, lon = az_el_to_lat_lon(
                s_lat=self.lat_site,
                s_lon=self.lon_site,
                az=az,
                el=el
            )
            self.traj_lat.append(lat)
            self.traj_lon.append(lon)
            
        self.traj_lat = np.degrees(self.traj_lat)
        self.traj_lon = np.degrees(self.traj_lon)
        self.filter_points()
        self.traj_lat = np.array(self.traj_lat, dtype=object)
        self.traj_lon = np.array(self.traj_lon, dtype=object)
        self.adding_artificial_value()
        
        assert len(self.traj_lat) == len(self.traj_lon) == len(self.times)
