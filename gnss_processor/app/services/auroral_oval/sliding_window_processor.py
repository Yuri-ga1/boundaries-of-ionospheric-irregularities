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
        
        # Проверка на пустые массивы
        if len(lon) == 0 or len(lat) == 0 or len(vals) == 0:
            return []
        
        min_lon, max_lon = np.min(lon), np.max(lon)
        min_lat, max_lat = np.min(lat), np.max(lat)
        
        windows = []
        
        # Добавляем небольшие эпсилоны для учета ошибок округления с плавающей точкой
        epsilon = 1e-10
        
        # Вычисляем количество шагов для полного покрытия диапазона
        lat_steps = int(np.ceil((max_lat - min_lat + window_size[0]) / self.lat_step)) + 1
        lon_steps = int(np.ceil((max_lon - min_lon + window_size[1]) / self.lon_step)) + 1
        
        # Генерируем центры окон
        for i in range(lat_steps):
            current_lat = min_lat - window_size[0] / 2 + i * self.lat_step
            
            for j in range(lon_steps):
                current_lon = min_lon - window_size[1] / 2 + j * self.lon_step
                
                mask = self._create_window_mask(
                    lon, lat, current_lon, current_lat, window_size
                )
                
                if np.any(mask):
                    window_data = self._create_window_data(
                        vals, mask, current_lon, current_lat, window_size
                    )
                    windows.append(window_data)
            
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