import os
import numpy as np
import h5py as h5
import traceback

from datetime import datetime as dt
import datetime

from typing import Dict, List, Optional, Tuple

from config import *

from app.processors.map_processor import MapProcessor
from app.processors.simurg_hdf5_processor import SimurgHDF5Processor

from gnss_processor.app.services.auroral_oval.crossing_detector import BoundaryCrossingDetector
from app.services.satellite.flyby_processor import SatelliteFlybyProcessor

from app.utils.time_utils import generate_5min_timestamps

from app.visualization.plotters.combined_plotter import CombinedPlotter
from app.visualization.png_to_video_converter import PngToVideoConverter


class DataProcessingPipeline:
    """
    Основной класс пайплайна для координации обработки данных.
    """
    
    def __init__(self):
        self.map_processor = MapProcessor(
            lon_condition=LON_CONDITION,
            lat_condition=LAT_CONDITION,
            segment_lon_step=SEGMENT_LON_STEP,
            segment_lat_step=SEGMENT_LAT_STEP,
            boundary_condition=BOUNDARY_CONDITION
        )
        
        self.crossing_detector = BoundaryCrossingDetector()
        self.flyby_processor = SatelliteFlybyProcessor()
        self.combined_plotter = CombinedPlotter()
        self.video_converter = PngToVideoConverter(
            input_dir=FRAME_GRAPHS_PATH, 
            output_dir=SAVE_VIDEO_PATH
        )
    
    def process_date(self, date_str: str) -> bool:
        """
        Основной метод обработки данных для конкретной даты.
        
        Args:
            date_str: Строка с датой в формате YYYYMMDD
            
        Returns:
            bool: Успешно ли выполнена обработка
        """
        try:
            logger.info(f"Starting processing for date: {date_str}")
            
            # Определение путей к файлам
            rinex_file_path = self._get_rinex_file_path(date_str)
            map_file_path = self._get_map_file_path(date_str)
            boundary_file_path = self._get_boundary_file_path(date_str)
            flyby_file_path = self._get_flyby_file_path(date_str)
            processed_flyby_path = self._get_processed_flyby_path(date_str)
            
            # Обработка RINEX файла
            satellite_data, flybys_data = self._process_rinex_file(
                rinex_file_path, date_str
            )
            
            if not satellite_data:
                logger.warning(f"No satellite data found for {date_str}")
                return False
            
            # Обработка карт и границ
            boundary_clusters = self._process_map_and_boundaries(
                map_file_path, boundary_file_path, date_str
            )
            
            if not boundary_clusters:
                logger.warning(f"No boundary data found for {date_str}")
                return False
            
            # Обработка пролетов
            self._process_flybys(
                boundary_clusters, satellite_data, flybys_data, 
                date_str, processed_flyby_path
            )
            
            # Генерация визуализаций
            self._generate_visualizations(
                boundary_file_path, processed_flyby_path, 
                rinex_file_path, date_str
            )
            
            logger.info(f"Successfully completed processing for {date_str}")
            return True
            
        except Exception as e:
            logger.error(f"Error processing date {date_str}: {e}")
            logger.error(traceback.format_exc())
            return False
    
    def _get_rinex_file_path(self, date_str: str) -> str:
        """Получение пути к RINEX файлу."""
        return os.path.join(RAW_DATA_PATH, f"{date_str}.h5")
    
    def _get_map_file_path(self, date_str: str) -> str:
        """Получение пути к файлу карт."""
        return os.path.join(MAP_PATH, f"{date_str}.h5")
    
    def _get_boundary_file_path(self, date_str: str) -> str:
        """Получение пути к файлу границ."""
        return os.path.join(BOUNDARY_PATH, f"{date_str}.h5")
    
    def _get_flyby_file_path(self, date_str: str) -> str:
        """Получение пути к файлу пролетов."""
        return os.path.join(FLYBYS_PATH, f"{date_str}.h5")
    
    def _get_processed_flyby_path(self, date_str: str) -> str:
        """Получение пути к обработанному файлу пролетов."""
        return os.path.join(PROCESSED_FLYBYS_PATH, f"{date_str}.h5")
    
    def _process_rinex_file(
        self, 
        rinex_file_path: str, 
        date_str: str
    ) -> Tuple[Optional[Dict], Optional[Dict]]:
        """
        Обработка RINEX файла.
        
        Args:
            rinex_file_path: Путь к RINEX файлу
            date_str: Дата для обработки
            
        Returns:
            Tuple: Данные спутников и пролетов
        """
        if not os.path.exists(rinex_file_path):
            logger.warning(f"RINEX file not found: {rinex_file_path}")
            return None, None
        
        try:
            with SimurgHDF5Processor(rinex_file_path) as processor:
                processor.process(f"{date_str}.h5")
                return processor.map_data, processor.flybys
                
        except Exception as e:
            logger.error(f"Error processing RINEX file {rinex_file_path}: {e}")
            return None, None
    
    def _process_map_and_boundaries(
        self, 
        map_file_path: str, 
        boundary_file_path: str, 
        date_str: str
    ) -> Optional[Dict]:
        """
        Обработка карт и извлечение границ.
        
        Args:
            map_file_path: Путь к файлу карт
            boundary_file_path: Путь для сохранения границ
            date_str: Дата для обработки
            
        Returns:
            Optional[Dict]: Данные кластеров границ
        """
        if not os.path.exists(map_file_path):
            logger.warning(f"Map file not found: {map_file_path}")
            return None
        
        try:
            # Обработка карты для извлечения границ
            self.map_processor.process_map_file(
                map_path=map_file_path,
                output_path=boundary_file_path
            )
            
            # Загрузка кластеров границ
            return self._load_boundary_clusters(boundary_file_path)
            
        except Exception as e:
            logger.error(f"Error processing map file {map_file_path}: {e}")
            return None
    
    def _load_boundary_clusters(self, boundary_file_path: str) -> Optional[Dict]:
        """
        Загрузка кластеров границ из файла.
        
        Args:
            boundary_file_path: Путь к файлу с границами
            
        Returns:
            Optional[Dict]: Данные кластеров границ
        """
        boundary_clusters = {}
        
        try:
            with h5.File(boundary_file_path, 'r') as boundary_file:
                time_points = list(boundary_file.keys())
                
                for time_point in time_points:
                    time_group = boundary_file[time_point]
                    
                    if "boundary_clusters" in time_group:
                        clusters_group = time_group['boundary_clusters']
                        boundary_clusters[time_point] = {
                            'relation': clusters_group.attrs['relation']
                        }
                        
                        for cluster_key in clusters_group:
                            cluster_group = clusters_group[cluster_key]
                            boundary_clusters[time_point][cluster_key] = np.column_stack((
                                cluster_group['lon'][()],
                                cluster_group['lat'][()]
                            )).tolist()
            
            return boundary_clusters
            
        except Exception as e:
            logger.error(f"Error loading boundary clusters from {boundary_file_path}: {e}")
            return None
    
    def _process_flybys(
        self,
        boundary_clusters: Dict,
        satellite_data: Dict,
        flybys_data: Dict,
        date_str: str,
        processed_flyby_path: str
    ) -> None:
        """
        Обработка пролетов спутников.
        
        Args:
            boundary_clusters: Кластеры границ
            satellite_data: Данные спутников
            flybys_data: Данные пролетов
            date_str: Дата для обработки
            processed_flyby_path: Путь для сохранения обработанных пролетов
        """
        if os.path.exists(processed_flyby_path):
            logger.info(f"Processed flyby file already exists: {processed_flyby_path}")
            return
        
        try:
            self.flyby_processor.process_flyby_data(
                boundary_clusters=boundary_clusters,
                satellite_data=satellite_data,
                flybys_data=flybys_data,
                date_str=date_str,
                output_path=processed_flyby_path
            )
            
        except Exception as e:
            logger.error(f"Error processing flybys for {date_str}: {e}")
    
    def _generate_visualizations(
        self,
        boundary_file_path: str,
        processed_flyby_path: str,
        rinex_file_path: str,
        date_str: str
    ) -> None:
        """
        Генерация визуализаций для данных.
        
        Args:
            boundary_file_path: Путь к файлу границ
            processed_flyby_path: Путь к обработанным пролетам
            rinex_file_path: Путь к RINEX файлу
            date_str: Дата для обработки
        """
        try:
            with h5.File(processed_flyby_path, 'r') as flyby_file:
                # stations = list(flyby_file.keys())
                stations = ['picl']
                
                for station in stations:
                    # satellites = list(flyby_file[station].keys())
                    satellites = ['G01']
                    
                    for satellite in satellites:
                        sat_flybys = list(flyby_file[station][satellite].keys())
                        
                        for sat_flyby in sat_flybys:
                            self._generate_flyby_visualizations(
                                boundary_file_path, flyby_file, rinex_file_path,
                                station, satellite, sat_flyby
                            )
                    
                    # Создание видео после обработки всех спутников станции
                    self.video_converter.process_images_to_video()
                    
        except Exception as e:
            logger.error(f"Error generating visualizations for {date_str}: {e}")
    
    def _generate_flyby_visualizations(
        self,
        boundary_file_path: str,
        flyby_file: h5.File,
        rinex_file_path: str,
        station: str,
        satellite: str,
        flyby_key: str
    ) -> None:
        """
        Генерация визуализаций для конкретного пролета.
        
        Args:
            boundary_file_path: Путь к файлу границ
            flyby_file: Открытый HDF5 файл с пролетами
            rinex_file_path: Путь к RINEX файлу
            station: Станция
            satellite: Спутник
            flyby_key: Ключ пролета
        """
        try:
            flyby_group = flyby_file[station][satellite][flyby_key]
            
            # Извлечение данных пролета
            flyby_roti = flyby_group['roti'][:]
            flyby_timestamps = flyby_group['timestamps'][:]
            cleaned_times = flyby_group.attrs['times']
            cleaned_types = flyby_group.attrs['types']
            
            # Преобразование временных меток
            timestamp_datetimes = [
                dt.fromtimestamp(float(ts), datetime.UTC) for ts in flyby_timestamps
            ]
            
            # Генерация 5-минутных временных точек
            time_points = generate_5min_timestamps(timestamp_datetimes)
            
            # Генерация графиков для каждой временной точки
            for time_point in time_points:
                self._generate_single_visualization(
                    boundary_file_path, rinex_file_path,
                    station, satellite, flyby_key,
                    flyby_roti, timestamp_datetimes,
                    cleaned_times, cleaned_types, time_point
                )
                
        except Exception as e:
            logger.error(f"Error generating visualization for {station}_{satellite}_{flyby_key}: {e}")
    
    def _generate_single_visualization(
        self,
        boundary_file_path: str,
        rinex_file_path: str,
        station: str,
        satellite: str,
        flyby_key: str,
        flyby_roti: np.ndarray,
        timestamp_datetimes: List[dt],
        cleaned_times: List[str],
        cleaned_types: List[str],
        time_point: str
    ) -> None:
        """
        Генерация одиночной визуализации для конкретного времени.
        
        Args:
            boundary_file_path: Путь к файлу границ
            rinex_file_path: Путь к RINEX файлу
            station: Станция
            satellite: Спутник
            flyby_key: Ключ пролета
            flyby_roti: Данные ROTI пролета
            timestamp_datetimes: Временные метки
            cleaned_times: Очищенные времена событий
            cleaned_types: Типы событий
            time_point: Временная точка
        """
        try:
            with h5.File(boundary_file_path, 'r') as boundary_file:
                if time_point not in boundary_file:
                    logger.debug(f"Time point {time_point} not found in boundary file")
                    return
                
                time_group = boundary_file[time_point]
                
                # Извлечение данных для визуализации
                filtered_points = {
                    'lon': time_group['filtered_points']['lon'][()],
                    'lat': time_group['filtered_points']['lat'][()],
                    'vals': time_group['filtered_points']['vals'][()],
                }
                
                sliding_windows = {
                    'lon': time_group['sliding_windows']['lon'][()],
                    'lat': time_group['sliding_windows']['lat'][()],
                    'vals': time_group['sliding_windows']['vals'][()],
                }
                
                boundary_data = {
                    'lon': time_group['boundary']['lon'][()],
                    'lat': time_group['boundary']['lat'][()],
                }
                
                # Загрузка boundary_clusters (нужно будет добавить в boundary_file)
                boundary_clusters = self._load_boundary_clusters_for_timepoint(
                    boundary_file, time_point
                )
                
                # Создание комбинированного графика
                self.combined_plotter.create_combined_visualization(
                    map_points=filtered_points,
                    sliding_windows=sliding_windows,
                    boundary_data=boundary_data,
                    boundary_condition=BOUNDARY_CONDITION,
                    time_point=time_point,
                    boundary_clusters=boundary_clusters,
                    roti_file=rinex_file_path,
                    flyby_idx=flyby_key,
                    flyby_roti=flyby_roti,
                    flyby_times=timestamp_datetimes,
                    flyby_events_times=cleaned_times,
                    flyby_events_types=cleaned_types,
                    station=station,
                    satellite=satellite,
                    save_to_file=True
                )
                
        except Exception as e:
            logger.error(f"Error generating visualization for time point {time_point}: {e}")
    
    def _load_boundary_clusters_for_timepoint(
        self, 
        boundary_file: h5.File, 
        time_point: str
    ) -> Optional[Dict]:
        """
        Загрузка кластеров границ для конкретной временной точки.
        
        Args:
            boundary_file: Открытый HDF5 файл с границами
            time_point: Временная точка
            
        Returns:
            Optional[Dict]: Данные кластеров для временной точки
        """
        try:
            time_group = boundary_file[time_point]
            
            if "boundary_clusters" not in time_group:
                return None
            
            clusters_group = time_group['boundary_clusters']
            boundary_clusters = {
                'relation': clusters_group.attrs['relation']
            }
            
            for cluster_key in clusters_group:
                cluster_group = clusters_group[cluster_key]
                boundary_clusters[cluster_key] = np.column_stack((
                    cluster_group['lon'][()],
                    cluster_group['lat'][()]
                )).tolist()
            
            return {time_point: boundary_clusters}
            
        except Exception as e:
            logger.error(f"Error loading boundary clusters for {time_point}: {e}")
            return None