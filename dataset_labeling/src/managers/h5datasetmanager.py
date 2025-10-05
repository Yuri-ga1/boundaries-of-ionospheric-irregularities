import h5py

from dataset_labeling.src.managers.calculationmanager import CalculationManager


class H5DatasetManager:
    def __init__(self, logger, symh_file_path, mag_grid_file='lat_lon_geo_mag_v2010.csv'):
        self.logger = logger
        self.calc_manager = CalculationManager(logger, symh_file_path, mag_grid_file)
        self.expected_datasets = [
            'roti', 'roti_gradient', 'roti_amplitude', 'roti_spectrum',
            'sin_time', 'cos_time', 'symh', 'mlat', 'mlon', 'timestamps'
        ]

    def get_metadata_from_h5(self, file_path, station, satellite, fb):
        def _extract_dataset(group, dataset_name):
            """Извлекает dataset из группы с проверкой"""
            if dataset_name in group:
                dataset = group[dataset_name]
                return dataset[:] if hasattr(dataset, '__len__') else None
            return None 
        
        try:
            with h5py.File(file_path, 'r') as h5file:
                if station in h5file:
                    station_h5file = h5file[station]
                    if satellite in station_h5file:
                        satellite_h5file = station_h5file[satellite]
                        if fb in satellite_h5file:
                            group = satellite_h5file[fb]

                            times = group.attrs.get('times', [])
                            types = group.attrs.get('types', [])

                            roti = _extract_dataset(group, 'roti')
                            timestamps = _extract_dataset(group, 'timestamps')
                            lon = _extract_dataset(group, 'lon')
                            lat = _extract_dataset(group, 'lat')

                            return roti, timestamps, lon, lat, times, types
        except Exception as e:
            self.logger.error(f"Ошибка при чтении HDF5 файла: {station}_{satellite}_{fb}")
        return [], [], None, None

    def calculate_all_parameters(self, roti, timestamps, lat, lon, date):
        """
        Вычисляет все дополнительные параметры на основе базовых данных
        
        :return: словарь со всеми вычисленными параметрами
        """
        all_params = {}
        
        try:
            # Базовые параметры
            all_params['roti'] = roti
            all_params['timestamps'] = timestamps

            # Вычисляемые параметры ROTI
            amplitude, spectrum, gradient = self.calc_manager.calculate_roti_parameters(roti)
            all_params['roti_amplitude'] = amplitude
            all_params['roti_spectrum'] = spectrum
            all_params['roti_gradient'] = gradient

            # Временные параметры
            sin_time, cos_time = self.calc_manager.calculate_time_parameters(timestamps, lon)
            all_params['sin_time'] = sin_time
            all_params['cos_time'] = cos_time

            # Магнитные координаты
            mlat, mlon = self.calc_manager.calculate_magnetic_coordinates(lat, lon)
            all_params['mlat'] = mlat
            all_params['mlon'] = mlon

            # SYMH параметры
            symh = self.calc_manager.calculate_symh(date, timestamps)
            all_params['symh'] = symh

        except Exception as e:
            self.logger.error(f"Ошибка при вычислении всех параметров: {e}")

        return all_params

    def save_data_to_h5_dataset(self, new_file_path, group_path, times, types, **datasets):
        """
        Универсальная функция сохранения данных в HDF5
        """
        try:
            with h5py.File(new_file_path, 'a') as h5file:
                if group_path not in h5file:
                    group = h5file.create_group(group_path)
                    
                    # Сохраняем атрибуты
                    group.attrs['times'] = times
                    group.attrs['types'] = types

                    # Сохраняем все datasets с проверкой
                    for dataset_name, dataset_data in datasets.items():
                        if self._is_valid_dataset(dataset_data):
                            group.create_dataset(dataset_name, data=dataset_data)
                            self.logger.info(f"Сохранен dataset: {dataset_name} в {group_path}")
                        else:
                            self.logger.warning(f"{dataset_name} пусто или None, не сохраняем в {group_path}")
                            
        except Exception as e:
            self.logger.error(f"Ошибка при записи в HDF5 файл {group_path}: {e}")

    def _is_valid_dataset(self, data):
        """Проверяет, что данные подходят для сохранения в dataset"""
        if data is None:
            return False
        if hasattr(data, '__len__') and len(data) == 0:
            return False
        return True