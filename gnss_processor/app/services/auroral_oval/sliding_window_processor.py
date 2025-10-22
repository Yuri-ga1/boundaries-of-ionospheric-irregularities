import numpy as np
from typing import Dict, List, Tuple


class SlidingWindowProcessor:
    """
    Класс для применения метода скользящего окна к пространственным данным.
    """
    
    def __init__(self, lon_step: float, lat_step: float):
        """
        Инициализация процессора скользящего окна.
        
        Args:
            lon_step: Шаг окна по долготе
            lat_step: Шаг окна по широте
        """
        self.lon_step = lon_step
        self.lat_step = lat_step
    

    def apply_sliding_window_segmentation(
        self, 
        filtered_points: Dict[str, np.ndarray], 
        window_size: Tuple[float, float] = (5, 10)
    ) -> List[Dict[str, float]]:
        """
        Применение метода скользящего окна для сегментации данных.
        
        Args:
            filtered_points: Отфильтрованные данные точек
            window_size: Размер окна (широта, долгота)
            
        Returns:
            List[Dict[str, float]]: Сегменты данных скользящего окна
        """
        lon = filtered_points['lon']
        lat = filtered_points['lat']
        vals = filtered_points['vals']
        
        min_lon, max_lon = np.min(lon), np.max(lon)
        min_lat, max_lat = np.min(lat), np.max(lat)
        
        windows = []
        current_lat = min_lat
        
        while current_lat + window_size[0] <= max_lat:
            current_lon = min_lon
            while current_lon + window_size[1] <= max_lon:
                mask = self._create_window_mask(
                    lon, lat, current_lon, current_lat, window_size
                )
                
                if np.any(mask):
                    window_data = self._create_window_data(
                        vals, mask, current_lon, current_lat, window_size
                    )
                    windows.append(window_data)
                
                current_lon += self.lon_step
            
            current_lat += self.lat_step
            
        return windows
    

    def _create_window_mask(
        self, 
        lon: np.ndarray, 
        lat: np.ndarray, 
        current_lon: float, 
        current_lat: float, 
        window_size: Tuple[float, float]
    ) -> np.ndarray:
        """
        Создание маски для текущего окна.
        
        Args:
            lon: Долготы точек
            lat: Широты точек
            current_lon: Текущая долгота окна
            current_lat: Текущая широта окна
            window_size: Размер окна
            
        Returns:
            np.ndarray: Булева маска точек в окне
        """
        return (lon >= current_lon) & (lon < current_lon + window_size[1]) & \
               (lat >= current_lat) & (lat < current_lat + window_size[0])
    

    def _create_window_data(
        self, 
        values: np.ndarray, 
        mask: np.ndarray, 
        current_lon: float, 
        current_lat: float, 
        window_size: Tuple[float, float]
    ) -> Dict[str, float]:
        """
        Создание данных для окна.
        
        Args:
            values: Значения точек
            mask: Маска точек в окне
            current_lon: Текущая долгота окна
            current_lat: Текущая широта окна
            window_size: Размер окна
            
        Returns:
            Dict[str, float]: Данные окна {'lon', 'lat', 'vals'}
        """
        center_lon = current_lon + window_size[1] / 2
        center_lat = current_lat + window_size[0] / 2
        
        return {
            'lon': center_lon,
            'lat': center_lat,
            'vals': np.median(values[mask])
        }