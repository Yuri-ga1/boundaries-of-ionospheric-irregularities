from datetime import timedelta, datetime as dt
import datetime
import numpy as np
import h5py
import os

from mag_converter import *

from custom_logger import Logger
from mag_converter import bilinear_interpolate

logger = Logger(
    filename="fill_logs.log",
    console_logging=False
)

def get_metadata_from_h5(file_path, station, satellite, fb):
    """Извлекает данные из группы HDF5 файла."""
    try:
        with h5py.File(file_path, 'r') as h5file:
            if station in h5file:
                station_h5file = h5file[station]
                if satellite in station_h5file:
                    satellite_h5file = station_h5file[satellite]
                    if fb in satellite_h5file:
                        group = satellite_h5file[fb]

                        roti = group.get('roti', None)
                        timestamps = group.get('timestamps', None)
                        lon = group.get('lon', None)
                        lat = group.get('lat', None)

                        event_times = group.attrs['times']
                        event_types = group.attrs['types']

                        roti = roti[:] if roti is not None else None
                        timestamps = timestamps[:] if timestamps is not None else None
                        lon = lon[:] if lon is not None else None
                        lat = lat[:] if lat is not None else None

                        if timestamps is not None:
                            mask = (timestamps % 60 == 0)

                            timestamps = timestamps[mask]
                            roti = roti[mask] if roti is not None else None
                            lon = lon[mask] if lon is not None else None
                            lat = lat[mask] if lat is not None else None
                        return roti, timestamps, lon, lat, event_times, event_types
    except Exception as e:
        logger.error(f"Ошибка при чтении HDF5 файла: {station}_{satellite}_{fb}")
        return [], [], None, None, None, None, None
    
def ydhm_to_timestamps(years, doys, hours, minutes):
    """
    Векторное преобразование: year, day_of_year, hour, minute -> unix timestamp (float)
    """
    base_dates = np.array([f'{y}-01-01' for y in years], dtype='datetime64[D]')

    dates = base_dates + (doys - 1).astype('timedelta64[D]') + \
            hours.astype('timedelta64[h]') + minutes.astype('timedelta64[m]')

    timestamps = dates.astype('datetime64[s]').astype(np.int64)

    return timestamps.astype(float)

def extract_symh_by_date(file_path, date_str, target_col_index=41):
    def get_doy(date_str):
        """Преобразует дату в формат ГГГГ-ММ-ДД в номер дня года"""
        date = dt.strptime(date_str, "%Y-%m-%d")
        return date.year, date.timetuple().tm_yday
    
    year, doy = get_doy(date_str)

    data = np.loadtxt(file_path)

    mask = (data[:, 0] == year) & (data[:, 1] == doy)
    filtered = data[mask]

    y = filtered[:, 0].astype(int)
    d = filtered[:, 1].astype(int)
    h = filtered[:, 2].astype(int)
    m = filtered[:, 3].astype(int)

    timestamps = ydhm_to_timestamps(y, d, h, m)
    values = filtered[:, target_col_index]

    return np.column_stack((timestamps, values))

def get_symh_for_timestamps(timestamp_with_symh, timestamps):
    symh_timestamps = timestamp_with_symh[:, 0]
    symh_values = timestamp_with_symh[:, 1]

    mask = np.isin(symh_timestamps, timestamps)

    filtered_symh_values = symh_values[mask]

    return filtered_symh_values

def calc_symh(date, timestamps):
    timestamp_with_symh = extract_symh_by_date('omni_min2019.asc', date)
    return get_symh_for_timestamps(timestamp_with_symh, timestamps)

def calc_roti_amplitude_spectrum_gradient(roti):
    window_size = 10
    amplitude = np.array([
        np.ptp(roti[max(0, i - window_size // 2): min(len(roti), i + window_size // 2)])
        for i in range(len(roti))
    ])

    spectrum = np.fft.fft(roti)
    gradient = np.gradient(roti)
    
    return amplitude, spectrum, gradient

def calc_sin_and_cos_time(timestamps, lon):
    """
    timestamps: np.ndarray — массив UNIX-времени (UTC)
    lon: np.ndarray — массив долгот, в градусах
    Возвращает: sin_time, cos_time — np.ndarray
    """
    local_times = []

    for ts, lo in zip(timestamps, lon):
        # Переводим в datetime UTC
        utc_time = dt.fromtimestamp(ts, datetime.UTC)

        # Смещение в часах от UTC (локальное солнечное время)
        offset_hours = lo / 15.0

        # Добавляем смещение
        local_time = utc_time + timedelta(hours=offset_hours)

        # Получаем локальное время в десятичном формате часов
        local_hour = local_time.hour + local_time.minute / 60 + local_time.second / 3600
        local_times.append(local_hour)

    local_times = np.array(local_times)
    angles = 2 * np.pi * (local_times / 24.0)

    sin_time = np.sin(angles)
    cos_time = np.cos(angles)

    return sin_time, cos_time

def calc_mlat_mlon(lat, lon):
    grid = read_geomagnetic_grid('lat_lon_geo_mag_v2010.csv')
    vec_interpolate = np.vectorize(
            lambda la, lo: bilinear_interpolate(la, lo, grid),
            otypes=[float, float]
        )
    return vec_interpolate(lat, lon)