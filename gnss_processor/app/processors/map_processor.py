import numpy as np
import h5py as h5
import os
from typing import Dict, List, Optional, Any

from config import *
from gnss_processor.app.services.auroral_oval.boundary_detector import BoundaryDetector
from gnss_processor.app.services.auroral_oval.cluster_processor import ClusterProcessor
from gnss_processor.app.services.auroral_oval.sliding_window_processor import SlidingWindowProcessor


class MapProcessor:
    """
    Основной класс для обработки карт ROTI и обнаружения границ аврорального овала.
    
    Обрабатывает HDF5 файлы с данными карт, применяет фильтрацию, скользящее окно,
    интерполяцию и кластеризацию для выделения границ.
    """
    
    def __init__(
        self,
        lon_condition: float,
        lat_condition: float,
        segment_lon_step: float,
        segment_lat_step: float,
        boundary_condition: float
    ):
        """
        Инициализация процессора карт.
        
        Args:
            lon_condition: Условие по долготе для близости к полюсу
            lat_condition: Условие по широте для близости к полюсу
            segment_lon_step: Шаг скользящего окна по долготе
            segment_lat_step: Шаг скользящего окна по широте
            boundary_condition: Пороговое значение для определения границы
        """
        self.lon_condition = lon_condition
        self.lat_condition = lat_condition
        self.segment_lon_step = segment_lon_step
        self.segment_lat_step = segment_lat_step
        self.boundary_condition = boundary_condition
        
        self.file_name = None
        
        # Инициализация процессоров
        self.boundary_detector = BoundaryDetector(
            lon_condition=lon_condition,
            lat_condition=lat_condition,
            boundary_condition=boundary_condition
        )
        
        self.sliding_window_processor = SlidingWindowProcessor(
            lon_step=segment_lon_step,
            lat_step=segment_lat_step
        )
        
        self.cluster_processor = ClusterProcessor(
            lat_condition=lat_condition
        )
    

    def _filter_coordinate_points(self, points_group: h5.Group) -> Dict[str, np.ndarray]:
        """
        Фильтрация точек по координатным условиям.
        
        Args:
            points_group: HDF5 группа с данными точек
            
        Returns:
            Dict[str, np.ndarray]: Отфильтрованные точки {'lon', 'lat', 'vals'}
        """
        lon = points_group['lon'][()]
        lat = points_group['lat'][()]
        vals = points_group['vals'][()]
        
        mask = (lon >= -120) & (lon <= self.lon_condition) & (lat >= self.lat_condition)
        
        filtered_points = {
            'lon': lon[mask],
            'lat': lat[mask],
            'vals': vals[mask]
        }
        
        return filtered_points
    

    def process_map_file(
        self, 
        map_path: str, 
        output_path: str, 
        time_points: Optional[List[str]] = None
    ) -> None:
        """
        Основной метод обработки файла карты.
        
        Args:
            map_path: Путь к входному HDF5 файлу с картами
            output_path: Путь для сохранения обработанных данных
            time_points: Список временных точек для обработки (None = все точки)
        """
        self.file_name = os.path.basename(map_path)
        
        if os.path.exists(output_path):
            logger.info(f"Boundary file already exists: {output_path}")
            return
            
        with h5.File(map_path, 'r') as input_file, h5.File(output_path, 'w') as output_file:
            data_group = input_file["data"]
            
            if time_points is None:
                time_points = list(data_group.keys())

            for time_point in time_points:
                logger.info(f"Processing {time_point} in {self.file_name}.")
                self._process_single_time_point(data_group, time_point, output_file)
    

    def _process_single_time_point(
        self, 
        data_group: h5.Group, 
        time_point: str, 
        output_file: h5.File
    ) -> None:
        """
        Обработка одной временной точки.
        
        Args:
            data_group: Группа с данными из входного файла
            time_point: Идентификатор временной точки
            output_file: Выходной HDF5 файл
        """
        points_group = data_group[time_point]
        
        # Создание группы для временной точки в выходном файле
        time_group = output_file.create_group(str(time_point))
        
        # 1. Сохранение исходных точек
        self._save_raw_points(points_group, time_group)
        
        # 2. Фильтрация точек
        filtered_points = self._filter_coordinate_points(points_group)
        self._save_filtered_points(filtered_points, time_group)
        
        # 3. Применение скользящего окна
        window_height = WINDOW_AREA / WINDOW_WIDTH
        sliding_windows = self.sliding_window_processor.apply_sliding_window_segmentation(
            filtered_points=filtered_points,
            window_size=(window_height, WINDOW_WIDTH),
        )
        self._save_sliding_windows(sliding_windows, time_group)
        
        # 4. Обнаружение границ
        boundary_data = self.boundary_detector.extract_boundary_contours(sliding_windows)
        self._save_boundary_data(boundary_data, time_group)
        
        # 5. Кластеризация границ
        boundary_clusters = self.cluster_processor.create_boundary_clusters(
            lat_list=boundary_data['lat'],
            lon_list=boundary_data['lon']
        )
        self._save_boundary_clusters(boundary_clusters, time_group)
    

    def _save_raw_points(self, points_group: h5.Group, time_group: h5.Group) -> None:
        """
        Сохранение исходных точек данных.
        
        Args:
            points_group: Группа с исходными точками
            time_group: Группа для сохранения в выходном файле
        """
        lon = points_group['lon'][()]
        lat = points_group['lat'][()]
        vals = points_group['vals'][()]
        
        points_subgroup = time_group.create_group("points")
        points_subgroup.create_dataset("lon", data=lon)
        points_subgroup.create_dataset("lat", data=lat)
        points_subgroup.create_dataset("vals", data=vals)
    

    def _save_filtered_points(
        self, 
        filtered_points: Dict[str, np.ndarray], 
        time_group: h5.Group
    ) -> None:
        """
        Сохранение отфильтрованных точек.
        
        Args:
            filtered_points: Отфильтрованные данные точек
            time_group: Группа для сохранения в выходном файле
        """
        filtered_subgroup = time_group.create_group("filtered_points")
        filtered_subgroup.create_dataset("lon", data=filtered_points["lon"])
        filtered_subgroup.create_dataset("lat", data=filtered_points["lat"])
        filtered_subgroup.create_dataset("vals", data=filtered_points["vals"])
    
    def _save_sliding_windows(
        self, 
        sliding_windows: List[Dict[str, float]], 
        time_group: h5.Group
    ) -> None:
        """
        Сохранение данных скользящего окна.
        
        Args:
            sliding_windows: Данные сегментов скользящего окна
            time_group: Группа для сохранения в выходном файле
        """
        sliding_subgroup = time_group.create_group("sliding_windows")
        sliding_subgroup.create_dataset("lon", data=[p["lon"] for p in sliding_windows])
        sliding_subgroup.create_dataset("lat", data=[p["lat"] for p in sliding_windows])
        sliding_subgroup.create_dataset("vals", data=[p["vals"] for p in sliding_windows])
    

    def _save_boundary_data(
        self, 
        boundary_data: Dict[str, List[float]], 
        time_group: h5.Group
    ) -> None:
        """
        Сохранение данных границ.
        
        Args:
            boundary_data: Данные обнаруженных границ
            time_group: Группа для сохранения в выходном файле
        """
        boundary_subgroup = time_group.create_group("boundary")
        boundary_subgroup.create_dataset("lon", data=boundary_data["lon"])
        boundary_subgroup.create_dataset("lat", data=boundary_data["lat"])
    

    def _save_boundary_clusters(
        self, 
        boundary_clusters: Optional[Dict[str, Any]], 
        time_group: h5.Group
    ) -> None:
        """
        Сохранение кластеризованных границ.
        
        Args:
            boundary_clusters: Данные кластеров границ
            time_group: Группа для сохранения в выходном файле
        """
        if boundary_clusters is not None:
            clusters_subgroup = time_group.create_group("boundary_clusters")
            clusters_subgroup.attrs["relation"] = boundary_clusters["relation"]
            
            for key, cluster_points in boundary_clusters.items():
                if key == "relation":
                    continue
                cluster_subgroup = clusters_subgroup.create_group(key)
                cluster_points_array = np.array(cluster_points)
                cluster_subgroup.create_dataset("lon", data=cluster_points_array[:, 0])
                cluster_subgroup.create_dataset("lat", data=cluster_points_array[:, 1])