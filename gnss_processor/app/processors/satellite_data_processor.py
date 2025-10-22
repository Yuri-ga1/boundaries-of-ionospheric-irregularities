import numpy as np
from typing import Dict, Tuple, Any
from gnss_processor.app.utils.az_el_to_lot_lon import az_el_to_lat_lon
from config import MIN_ELEVATION_DEGREES, MAP_TIME_STEP_SECONDS, LON_CONDITION, LAT_CONDITION


class SatelliteDataProcessor:
    """Класс для обработки данных отдельного спутника."""
    
    def __init__(self, station_coords: Dict[str, float]):
        """
        Инициализация процессора данных спутника.
        
        Args:
            station_coords: Координаты станции {'lat': float, 'lon': float}
        """
        self.station_coords = station_coords
    
    def calculate_satellite_coordinates(self, azimuths: np.ndarray, elevations: np.ndarray) -> Tuple[np.ndarray, np.ndarray]:
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
        
        for az, el in zip(azimuths, elevations):
            lat, lon = az_el_to_lat_lon(
                s_lat=self.station_coords['lat'],
                s_lon=self.station_coords['lon'],
                az=az,
                el=el
            )
            latitudes.append(lat)
            longitudes.append(lon)
        
        return np.degrees(latitudes), np.degrees(longitudes)
    
    def apply_data_filters(self, roti: np.ndarray, elevations: np.ndarray, 
                          timestamps: np.ndarray, latitudes: np.ndarray, 
                          longitudes: np.ndarray) -> Dict[str, np.ndarray]:
        """
        Применение фильтров к данным спутника.
        
        Args:
            roti: Массив значений ROTI
            elevations: Массив углов возвышения
            timestamps: Массив временных меток
            latitudes: Массив широт
            longitudes: Массив долгот
            
        Returns:
            Dict[str, np.ndarray]: Отфильтрованные данные
        """
        # Фильтр по углу возвышения
        elevation_mask = (elevations >= np.radians(MIN_ELEVATION_DEGREES))
        
        filtered_roti = roti[elevation_mask]
        filtered_timestamps = timestamps[elevation_mask]
        filtered_latitudes = latitudes[elevation_mask]
        filtered_longitudes = longitudes[elevation_mask]
        
        # Фильтр по координатам и временному шагу
        coordinate_mask = (
            (filtered_longitudes >= -120) & 
            (filtered_longitudes <= LON_CONDITION) & 
            (filtered_latitudes >= LAT_CONDITION) & 
            (filtered_timestamps % MAP_TIME_STEP_SECONDS == 0)
        )
        
        return {
            'roti': filtered_roti[coordinate_mask],
            'timestamps': filtered_timestamps[coordinate_mask],
            'latitudes': filtered_latitudes[coordinate_mask],
            'longitudes': filtered_longitudes[coordinate_mask]
        }