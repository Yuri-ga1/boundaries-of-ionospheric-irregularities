import numpy as np
from datetime import datetime, timedelta

from dataset_labeling.src.utils.mag_converter import bilinear_interpolate, read_geomagnetic_grid
from config import MAG_GRID_FILE

class CalculationManager:
    def __init__(self, logger, symh_file_path, mag_grid_file=MAG_GRID_FILE):
        self.logger = logger
        self.symh_file_path = symh_file_path
        self.mag_grid_file = mag_grid_file
        self._mag_grid = None

    def _load_magnetic_grid(self):
        """Ленивая загрузка геомагнитной сетки"""
        if self._mag_grid is None:
            try:
                self._mag_grid = read_geomagnetic_grid(self.mag_grid_file)
            except Exception as e:
                self.logger.error(f"Ошибка загрузки магнитной сетки: {e}")
                self._mag_grid = {}
        return self._mag_grid

    def calculate_roti_parameters(self, roti):
        """Вычисляет amplitude, spectrum и gradient для ROTI"""
        try:
            if roti is None or len(roti) == 0:
                return None, None, None

            window_size = 10
            amplitude = np.array([
                np.ptp(roti[max(0, i - window_size // 2): min(len(roti), i + window_size // 2)])
                for i in range(len(roti))
            ])

            spectrum = np.fft.fft(roti)
            gradient = np.gradient(roti)
            
            return amplitude, spectrum, gradient
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления параметров ROTI: {e}")
            return None, None, None

    def calculate_time_parameters(self, timestamps, lon):
        """Вычисляет sin_time и cos_time"""
        try:
            if timestamps is None or lon is None:
                return None, None

            local_times = []
            for ts, lo in zip(timestamps, lon):
                utc_time = datetime.fromtimestamp(ts, datetime.UTC)
                offset_hours = lo / 15.0
                local_time = utc_time + timedelta(hours=offset_hours)
                local_hour = local_time.hour + local_time.minute / 60 + local_time.second / 3600
                local_times.append(local_hour)

            local_times = np.array(local_times)
            angles = 2 * np.pi * (local_times / 24.0)

            return np.sin(angles), np.cos(angles)
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления временных параметров: {e}")
            return None, None

    def calculate_magnetic_coordinates(self, lat, lon):
        """Вычисляет магнитные координаты mlat, mlon"""
        try:
            if lat is None or lon is None:
                return None, None

            grid = self._load_magnetic_grid()
            if not grid:
                return None, None

            vec_interpolate = np.vectorize(
                lambda la, lo: bilinear_interpolate(la, lo, grid),
                otypes=[float, float]
            )
            return vec_interpolate(lat, lon)
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления магнитных координат: {e}")
            return None, None

    def _ydhm_to_timestamps(self, years, doys, hours, minutes):
        """Векторное преобразование в UNIX timestamp"""
        try:
            base_dates = np.array([f'{y}-01-01' for y in years], dtype='datetime64[D]')

            dates = base_dates + (doys - 1).astype('timedelta64[D]') + \
                    hours.astype('timedelta64[h]') + minutes.astype('timedelta64[m]')
            
            timestamps = dates.astype('datetime64[s]').astype(np.int64)

            return timestamps.astype(float)
        except Exception as e:
            self.logger.error(f"Ошибка преобразования времени: {e}")
            return None

    def _extract_symh_by_date(self, date_str, target_col_index=41):
        """Извлекает SYMH данные по дате"""
        try:
            def get_doy(date_str):
                date = datetime.strptime(date_str, "%Y-%m-%d")
                return date.year, date.timetuple().tm_yday
            
            year, doy = get_doy(date_str)
            
            data = np.loadtxt(self.symh_file_path)

            mask = (data[:, 0] == year) & (data[:, 1] == doy)
            filtered = data[mask]

            y = filtered[:, 0].astype(int)
            d = filtered[:, 1].astype(int)
            h = filtered[:, 2].astype(int)
            m = filtered[:, 3].astype(int)

            timestamps = self._ydhm_to_timestamps(y, d, h, m)
            values = filtered[:, target_col_index]

            return np.column_stack((timestamps, values))
            
        except Exception as e:
            self.logger.error(f"Ошибка извлечения SYMH для даты {date_str}: {e}")
            return None

    def calculate_symh(self, date, timestamps):
        """Вычисляет SYMH значения для заданных временных меток"""
        try:
            if date is None or timestamps is None:
                return None

            timestamp_with_symh = self._extract_symh_by_date(date)
            if timestamp_with_symh is None:
                return None

            symh_timestamps = timestamp_with_symh[:, 0]
            symh_values = timestamp_with_symh[:, 1]
            mask = np.isin(symh_timestamps, timestamps)
            
            return symh_values[mask]
            
        except Exception as e:
            self.logger.error(f"Ошибка вычисления SYMH: {e}")
            return None