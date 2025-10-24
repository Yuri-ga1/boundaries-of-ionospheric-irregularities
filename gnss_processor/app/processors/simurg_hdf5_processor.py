import numpy as np
import os
import h5py as h5
from config import *
from datetime import datetime as dt
import datetime
from collections import OrderedDict
from typing import Dict, Optional

from gnss_processor.app.services.satellite.satellite_data_processor import SatelliteDataProcessor


class SimurgHDF5Processor:
    """
    Обработчик для HDF5-файлов от сервиса SIMuRG, содержащих данные из RINEX-файлов за сутки.
    
    Создает два файла:
    - Карты ROTI с шагом 5 минут
    - Пролеты спутников, разделенные на отдельные проходы
    """
    
    def __init__(self, file_path: str):
        """
        Инициализация процессора HDF5 файлов от SIMuRG.
        
        Args:
            file_path: Путь к HDF5 файлу.
        """
        self.file_path = file_path
        self.filename = os.path.basename(file_path)
        self.file = None
        self.lon_condition = LON_CONDITION
        self.lat_condition = LAT_CONDITION
        
        self.stations_coords: Dict[str, Dict[str, float]] = {}
        self.map_data: Dict[str, Dict] = {}
        self.flybys: Dict[str, Dict] = {}
    
    def __enter__(self):
        """Контекстный менеджер для открытия файла."""
        self.file = h5.File(self.file_path, 'r')
        return self
        

    def __exit__(self, exc_type, exc_value, traceback):
        """Контекстный менеджер для закрытия файла."""
        if self.file:
            self.file.close()
    

    def _extract_station_coordinates(self, station_name: str) -> None:
        """
        Извлечение и сохранение координат станции.
        
        Args:
            station_name: Название станции
        """
        station = self.file[station_name]
        lat, lon = station.attrs['lat'], station.attrs['lon']
        
        if (COORDINATE_BOUNDS['min_lat'] <= lat <= COORDINATE_BOUNDS['max_lat'] and 
            COORDINATE_BOUNDS['min_lon'] <= lon <= COORDINATE_BOUNDS['max_lon']):
            self.stations_coords[station_name] = {'lat': lat, 'lon': lon}
            

    def _split_satellite_data_into_flybys(self, station_name: str, satellite_name: str, 
                                        roti: np.ndarray, timestamps: np.ndarray, 
                                        latitudes: np.ndarray, longitudes: np.ndarray) -> None:
        """
        Разделение данных спутника на отдельные пролеты.
        
        Args:
            station_name: Название станции
            satellite_name: Название спутника
            roti: Массив значений ROTI
            timestamps: Массив временных меток
            latitudes: Массив широт
            longitudes: Массив долгот
        """
        time_differences = np.diff(timestamps)
        split_indices = np.where(time_differences >= TIME_DIFF_THRESHOLD_SECONDS)[0] + 1
        flyby_segments = np.split(np.arange(len(timestamps)), split_indices)

        if station_name not in self.flybys:
            self.flybys[station_name] = {}
        if satellite_name not in self.flybys[station_name]:
            self.flybys[station_name][satellite_name] = {}

        for flyby_number, indices in enumerate(flyby_segments):
            flyby_data = {
                'roti': roti[indices],
                'timestamps': timestamps[indices],
                'lat': latitudes[indices],
                'lon': longitudes[indices]
            }

            self.flybys[station_name][satellite_name][f'flyby{flyby_number}'] = flyby_data
            

    def _process_single_satellite(self, station_name: str, satellite_name: str) -> Optional[Dict[str, np.ndarray]]:
        """
        Обработка данных одного спутника.
        
        Args:
            station_name: Название станции
            satellite_name: Название спутника
            
        Returns:
            Optional[Dict]: Отфильтрованные данные спутника или None если данные невалидны
        """
        satellite_data = self.file[station_name][satellite_name]
        
        roti = satellite_data['roti'][:]
        azimuths = satellite_data['azimuth'][:]
        elevations = satellite_data['elevation'][:]
        timestamps = satellite_data['timestamp'][:]
        
        station_coords = self.stations_coords[station_name]
        data_processor = SatelliteDataProcessor(station_coords)
        
        latitudes, longitudes = data_processor.calculate_satellite_coordinates(azimuths, elevations)
        
        self._split_satellite_data_into_flybys(
            station_name, satellite_name, roti, timestamps, latitudes, longitudes
        )

        filtered_data = data_processor.apply_data_filters(
            roti, elevations, timestamps, latitudes, longitudes
        )
        
        return filtered_data if len(filtered_data['roti']) > 0 else None


    def _sort_dictionary_recursively(self, dictionary: Dict) -> OrderedDict:
        """
        Рекурсивная сортировка словаря по ключам.
        
        Args:
            dictionary: Словарь для сортировки (может содержать вложенные словари)
            
        Returns:
            OrderedDict: Отсортированный словарь
        """
        if isinstance(dictionary, dict):
            return OrderedDict(
                sorted((key, self._sort_dictionary_recursively(value)) for key, value in dictionary.items())
            )
        return dictionary
    

    def _create_output_files(self, map_file_path: str, flyby_file_path: str) -> None:
        """
        Создание выходных HDF5 файлов с картами и пролетами.
        
        Args:
            map_file_path: Путь для файла карт
            flyby_file_path: Путь для файла пролетов
        """
        logger.info(f'Creating HDF5 files. Map: {map_file_path}\t Flyby: {flyby_file_path}')
        
        with h5.File(map_file_path, 'w') as map_file, h5.File(flyby_file_path, 'w') as flyby_file:
            self._write_map_data(map_file)
            logger.info(f'Map file: {map_file_path} was successfully created')
            self._write_flyby_data(flyby_file)
            logger.info(f'Flyby file: {flyby_file_path} was successfully created')
    

    def _write_map_data(self, map_file: h5.File) -> None:
        """
        Запись данных карт в HDF5 файл.
        
        Args:
            map_file: Открытый HDF5 файл для записи карт
        """
        data_group = map_file.create_group('data')
        
        for timestamp, station_satellites in self.map_data.items():
            all_latitudes = []
            all_longitudes = []
            all_values = []

            for satellite_data in station_satellites.values():
                all_latitudes.append(satellite_data['lat'])
                all_longitudes.append(satellite_data['lon'])
                all_values.append(satellite_data['vals'])

            timestamp_group = data_group.create_group(timestamp)
            timestamp_group.create_dataset('lat', data=np.array(all_latitudes).flatten())
            timestamp_group.create_dataset('lon', data=np.array(all_longitudes).flatten())
            timestamp_group.create_dataset('vals', data=np.array(all_values).flatten())
    

    def _write_flyby_data(self, flyby_file: h5.File) -> None:
        """
        Запись данных пролетов в HDF5 файл.
        
        Args:
            flyby_file: Открытый HDF5 файл для записи пролетов
        """
        processed_data_group = flyby_file.create_group('processed_data')
        flybys_group = flyby_file.create_group('flybys')

        for timestamp, station_satellites in self.map_data.items():
            timestamp_group = processed_data_group.create_group(timestamp)
            for station_name, satellite_data in station_satellites.items():
                station_group = timestamp_group.create_group(station_name)
                station_group.create_dataset('lat', data=satellite_data['lat'])
                station_group.create_dataset('lon', data=satellite_data['lon'])
                station_group.create_dataset('vals', data=satellite_data['vals'])

        for station_name, satellites in self.flybys.items():
            station_group = flybys_group.create_group(station_name)

            for satellite_name, flyby_data in satellites.items():
                satellite_group = station_group.create_group(satellite_name)

                for flyby_name, flyby_info in flyby_data.items():
                    flyby_group = satellite_group.create_group(flyby_name)
                    flyby_group.create_dataset('roti', data=flyby_info['roti'])
                    flyby_group.create_dataset('timestamps', data=flyby_info['timestamps'])
                    flyby_group.create_dataset('lat', data=flyby_info['lat'])
                    flyby_group.create_dataset('lon', data=flyby_info['lon'])
    

    def restore_processed_data(self, flyby_file_path: str) -> None:
        """
        Восстановление обработанных данных из HDF5 файла.
        
        Args:
            flyby_file_path: Путь к файлу с пролетами
        """
        logger.info(f'Restoring data from {flyby_file_path}')
        processed_data = {}
        flybys_data = {}

        with h5.File(flyby_file_path, 'r') as file:
            if 'processed_data' in file:
                processed_data_group = file['processed_data']
                for timestamp in processed_data_group:
                    timestamp_group = processed_data_group[timestamp]
                    entries = {}
                    for station_name in timestamp_group:
                        station_group = timestamp_group[station_name]
                        entries[station_name] = {
                            'lat': station_group['lat'][()],
                            'lon': station_group['lon'][()],
                            'vals': station_group['vals'][()]
                        }
                    processed_data[timestamp] = entries

            if 'flybys' in file:
                flybys_group = file['flybys']
                for station_name in flybys_group:
                    station_group = flybys_group[station_name]
                    flybys_data[station_name] = {}
                    for satellite_name in station_group:
                        satellite_group = station_group[satellite_name]
                        flybys_data[station_name][satellite_name] = {}
                        for flyby_name in satellite_group:
                            flyby_group = satellite_group[flyby_name]
                            flybys_data[station_name][satellite_name][flyby_name] = {
                                'roti': flyby_group['roti'][()],
                                'timestamps': flyby_group['timestamps'][()],
                                'lat': flyby_group['lat'][()],
                                'lon': flyby_group['lon'][()]
                            }

        self.map_data = self._sort_dictionary_recursively(processed_data)
        self.flybys = self._sort_dictionary_recursively(flybys_data)


    def process(self, output_map_name: str) -> None:
        """
        Основной метод обработки HDF5 файла от SIMuRG.
        
        Args:
            output_map_name: Имя выходного файла карт
        """
        map_file_path = os.path.join(MAP_PATH, output_map_name)
        flyby_file_path = os.path.join(FLYBYS_PATH, output_map_name)
        
        if os.path.exists(map_file_path) and os.path.exists(flyby_file_path):
            logger.info(f"Map and flyby file already exists: {map_file_path},\t{flyby_file_path}")
            self.restore_processed_data(flyby_file_path)
            return
        
        processed_data = {}
        
        for station in self.file:
            self._extract_station_coordinates(station)
        
        for station_name in self.stations_coords:
            logger.info(f"Processing station: {station_name}")
            
            for satellite_name in self.file[station_name]:
                satellite_result = self._process_single_satellite(station_name, satellite_name)
                
                if satellite_result is None:
                    continue
                
                station_satellite_key = f"{station_name}_{satellite_name}"
                
                for i in range(len(satellite_result['timestamps'])):
                    timestamp_str = dt.fromtimestamp(
                        float(satellite_result['timestamps'][i]), datetime.UTC
                    ).strftime('%Y-%m-%d %H:%M:%S.%f')
                    
                    data_entry = {
                        'vals': satellite_result['roti'][i] / 3,  # ????
                        'lat': satellite_result['latitudes'][i],
                        'lon': satellite_result['longitudes'][i]
                    }
                    
                    if timestamp_str not in processed_data:
                        processed_data[timestamp_str] = {}
                        
                    processed_data[timestamp_str][station_satellite_key] = data_entry
                    
        self.map_data = self._sort_dictionary_recursively(processed_data)
        self._create_output_files(map_file_path, flyby_file_path)