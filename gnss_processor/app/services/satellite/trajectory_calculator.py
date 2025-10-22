import numpy as np
from datetime import datetime as dt
from datetime import timedelta
import datetime
from typing import List, Tuple

from config import *
from gnss_processor.app.utils.az_el_to_lot_lon import az_el_to_lat_lon


class SatelliteTrajectory:
    """
    Класс для расчета и обработки траекторий спутников.
    
    Преобразует азимут и угол возвышения в географические координаты,
    применяет фильтрацию и добавляет искусственные точки для непрерывности траектории.
    """
    
    def __init__(self, station_latitude: float, station_longitude: float) -> None:
        """
        Инициализация калькулятора траектории.
        
        Args:
            station_latitude: Широта станции в радианах
            station_longitude: Долгота станции в радианах
        """
        self.station_latitude = station_latitude
        self.station_longitude = station_longitude
        self.trajectory_latitudes: np.ndarray = np.array([])
        self.trajectory_longitudes: np.ndarray = np.array([])
        self.timestamps: np.ndarray = np.array([])
        
    def filter_coordinate_points(self) -> None:
        """
        Фильтрация точек траектории по координатным условиям.
        
        Отбрасывает точки, выходящие за заданные границы долготы и широты.
        """
        valid_points_mask = (
            (self.trajectory_longitudes >= -120) & 
            (self.trajectory_longitudes <= LON_CONDITION) & 
            (self.trajectory_latitudes >= LAT_CONDITION)
        )
        
        self.trajectory_longitudes = self.trajectory_longitudes[valid_points_mask]
        self.trajectory_latitudes = self.trajectory_latitudes[valid_points_mask]
        self.timestamps = self.timestamps[valid_points_mask]
    
    def _find_large_time_gaps(self) -> np.ndarray:
        """
        Поиск больших временных промежутков в данных.
        
        Returns:
            np.ndarray: Индексы, после которых находятся большие промежутки
        """
        datetime_points = np.array([dt.fromtimestamp(ts, datetime.UTC) for ts in self.timestamps])
        time_differences = np.diff(datetime_points)
        
        large_gap_indices = np.where(
            time_differences > timedelta(minutes=ARTIFICIAL_POINTS_INTERVAL_MINUTES)
        )[0] + 1
        
        return large_gap_indices
    
    def _calculate_midpoint_timestamps(self, gap_indices: np.ndarray) -> List[float]:
        """
        Вычисление временных меток для искусственных точек в середине промежутков.
        
        Args:
            gap_indices: Индексы больших промежутков
            
        Returns:
            List[float]: Список временных меток для вставки
        """
        datetime_points = np.array([dt.fromtimestamp(ts, datetime.UTC) for ts in self.timestamps])
        timestamps_to_insert = []
        
        for index in gap_indices:
            midpoint_time = datetime_points[index - 1] + (datetime_points[index] - datetime_points[index - 1]) / 2
            
            # Добавляем три точки вокруг середины
            timestamps_to_insert.extend([
                (midpoint_time - timedelta(seconds=ARTIFICIAL_POINTS_OFFSET_SECONDS)).timestamp(),
                midpoint_time.timestamp(),
                (midpoint_time + timedelta(seconds=ARTIFICIAL_POINTS_OFFSET_SECONDS)).timestamp()
            ])
        
        return timestamps_to_insert
    
    def insert_artificial_points(self, interval_minutes: int = ARTIFICIAL_POINTS_INTERVAL_MINUTES) -> None:
        """
        Вставка искусственных точек в большие временные промежутки.
        
        Args:
            interval_minutes: Минимальный промежуток для вставки точек (в минутах)
        """
        large_gap_indices = self._find_large_time_gaps()
        
        if len(large_gap_indices) == 0:
            return
        
        artificial_timestamps = self._calculate_midpoint_timestamps(large_gap_indices)
        
        # Количество искусственных точек для каждой вставки
        points_per_gap = 3
        artificial_coordinates = [np.nan] * (points_per_gap * len(large_gap_indices))
        
        # Вставка искусственных точек
        insertion_indices = large_gap_indices.repeat(points_per_gap)
        
        self.timestamps = np.insert(self.timestamps, insertion_indices, artificial_timestamps)
        self.trajectory_latitudes = np.insert(
            self.trajectory_latitudes, insertion_indices, artificial_coordinates
        )
        self.trajectory_longitudes = np.insert(
            self.trajectory_longitudes, insertion_indices, artificial_coordinates
        )
    
    def calculate_satellite_coordinates(
        self, 
        azimuths: np.ndarray, 
        elevations: np.ndarray
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Вычисление географических координат спутника.
        
        Args:
            azimuths: Массив азимутов в радианах
            elevations: Массив углов возвышения в радианах
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Широты и долготы в градусах
        """
        latitudes = []
        longitudes = []
        
        for azimuth, elevation in zip(azimuths, elevations):
            lat, lon = az_el_to_lat_lon(
                s_lat=self.station_latitude,
                s_lon=self.station_longitude,
                az=azimuth,
                el=elevation
            )
            latitudes.append(lat)
            longitudes.append(lon)
            
        return np.degrees(latitudes), np.degrees(longitudes)
    
    def process_trajectory(
        self, 
        azimuths: np.ndarray, 
        elevations: np.ndarray, 
        timestamps: np.ndarray
    ) -> None:
        """
        Основной метод обработки траектории спутника.
        
        Args:
            azimuths: Массив азимутов в радианах
            elevations: Массив углов возвышения в радианах
            timestamps: Массив временных меток
            
        Raises:
            AssertionError: Если размеры массивов не совпадают после обработки
        """
        self.timestamps = np.array(timestamps, dtype=float)
        
        # Расчет координат спутника
        self.trajectory_latitudes, self.trajectory_longitudes = self.calculate_satellite_coordinates(
            azimuths, elevations
        )
        
        # Фильтрация точек по координатам
        self.filter_coordinate_points()
        
        # Вставка искусственных точек для непрерывности
        self.insert_artificial_points()
        
        # Проверка целостности данных
        self._validate_data_integrity()
    
    def _validate_data_integrity(self) -> None:
        """
        Проверка целостности данных траектории.
        
        Raises:
            AssertionError: Если размеры массивов координат и времени не совпадают
        """
        assert len(self.trajectory_latitudes) == len(self.trajectory_longitudes) == len(self.timestamps), \
            "Размеры массивов координат и времени должны совпадать"
    
    def get_trajectory_data(self) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
        """
        Получение данных траектории.
        
        Returns:
            Tuple[np.ndarray, np.ndarray, np.ndarray]: 
            Широты, долготы и временные метки траектории
        """
        return self.trajectory_latitudes, self.trajectory_longitudes, self.timestamps
    
    def get_trajectory_length(self) -> int:
        """
        Получение количества точек в траектории.
        
        Returns:
            int: Количество точек траектории
        """
        return len(self.timestamps)