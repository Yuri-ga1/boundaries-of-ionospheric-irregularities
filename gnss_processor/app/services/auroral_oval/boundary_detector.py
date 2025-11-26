import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import griddata
from typing import Dict, List
from config import GRID_POINTS


class BoundaryDetector:
    """
    Класс для обнаружения границ на основе интерполяции данных и извлечения контуров.
    """
    
    def __init__(
        self, 
        lon_condition: float, 
        lat_condition: float, 
        boundary_condition: float
    ):
        """
        Инициализация детектора границ.
        
        Args:
            lon_condition: Условие по долготе
            lat_condition: Условие по широте  
            boundary_condition: Пороговое значение для границы
        """
        self.lon_condition = lon_condition
        self.lat_condition = lat_condition
        self.boundary_condition = boundary_condition
    

    def extract_boundary_contours(
        self, 
        sliding_windows: List[Dict[str, float]]
    ) -> Dict[str, List[float]]:
        """
        Извлечение граничных контуров методом интерполяции и построения контуров.
        
        Args:
            sliding_windows: Данные сегментов скользящего окна
            
        Returns:
            Dict[str, List[float]]: Координаты граничных точек {'lat': [], 'lon': []}
        """
        if not sliding_windows:
            return {'lat': [], 'lon': []}
    
        lon = np.array([entry['lon'] for entry in sliding_windows])
        lat = np.array([entry['lat'] for entry in sliding_windows])
        vals = np.array([entry['vals'] for entry in sliding_windows])

        # Создание сетки для интерполяции
        xi = np.linspace(lon.min(), lon.max(), GRID_POINTS)
        yi = np.linspace(lat.min(), lat.max(), GRID_POINTS)
        
        # Интерполяция значений
        zi = griddata(
            (lon, lat), 
            vals, 
            (xi[None, :], yi[:, None]), 
            method='linear', 
            fill_value=np.nan
        )
        
        boundary_data = {'lat': [], 'lon': []}
            
        if np.all(np.isnan(zi)):
            return boundary_data
        
        # Построение контуров для заданного уровня
        plt.figure()
        contour_set = plt.contour(xi, yi, zi, levels=[self.boundary_condition])
        plt.close()

        # Извлечение сегментов контура
        if len(contour_set.allsegs) > 0:
            contour_segments = contour_set.allsegs[0]
            for segment in contour_segments:
                if len(segment) > 0:
                    boundary_data['lon'].extend(segment[:, 0].tolist())
                    boundary_data['lat'].extend(segment[:, 1].tolist())
        
        return boundary_data