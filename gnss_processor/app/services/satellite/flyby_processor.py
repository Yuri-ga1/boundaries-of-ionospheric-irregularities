import h5py as h5
from datetime import datetime as dt
import datetime
from typing import Dict, List, Any

from config import PROCESSED_FLYBYS_PATH, logger
from app.services.boundary.crossing_detector import BoundaryCrossingDetector
from app.visualization.plotters.timeseries_plotter import TimeSeriesPlotter


class SatelliteFlybyProcessor:
    """
    Класс для обработки пролетов спутников и сохранения результатов в HDF5.
    """
    
    def __init__(self):
        self.crossing_detector = BoundaryCrossingDetector()
        self.timeseries_plotter = TimeSeriesPlotter()
    
    def process_flyby_data(
        self,
        boundary_clusters: Dict[str, Any],
        satellite_data: Dict[str, Any],
        flybys_data: Dict[str, Any],
        date_str: str,
        output_path: str
    ) -> None:
        """
        Обработка данных пролетов и сохранение результатов.
        
        Args:
            boundary_clusters: Кластеры границ
            satellite_data: Данные спутников
            flybys_data: Данные пролетов
            date_str: Дата для обработки
            output_path: Путь для сохранения результатов
        """
        try:
            # Обнаружение пересечений
            crossings = self.crossing_detector.detect_satellite_crossings(
                boundary_clusters, satellite_data
            )
            
            stations = flybys_data.keys()

            with h5.File(output_path, 'a') as h5file:
                for station in stations:
                    satellites = flybys_data[station].keys()
                    
                    for satellite in satellites:
                        self._process_single_satellite_flybys(
                            h5file, station, satellite, flybys_data,
                            crossings, date_str
                        )
                        
            logger.info(f"Successfully processed flybys for {date_str}")
            
        except Exception as e:
            logger.error(f"Error processing flyby data for {date_str}: {e}")
            raise
    
    def _process_single_satellite_flybys(
        self,
        h5file: h5.File,
        station: str,
        satellite: str,
        flybys_data: Dict[str, Any],
        crossings: Dict[str, Any],
        date_str: str
    ) -> None:
        """
        Обработка пролетов для отдельного спутника.
        
        Args:
            h5file: Открытый HDF5 файл для записи
            station: Станция
            satellite: Спутник
            flybys_data: Данные пролетов
            crossings: Данные пересечений
            date_str: Дата для обработки
        """
        flyby_keys = list(flybys_data[station][satellite].keys())
        crossing_events = crossings.get(station, {}).get(satellite, [])

        for flyby_index, flyby_key in enumerate(flyby_keys):
            logger.debug(f"Processing {station}_{satellite}_{flyby_key}")

            if flyby_index < len(crossing_events):
                self._save_flyby_with_events(
                    h5file, station, satellite, flyby_index,
                    flybys_data, crossing_events, flyby_key
                )
            else:
                logger.warning(f'No crossing events for {station}_{satellite}_{flyby_key}')
                break
    
    def _save_flyby_with_events(
        self,
        h5file: h5.File,
        station: str,
        satellite: str,
        flyby_index: int,
        flybys_data: Dict[str, Any],
        crossing_events: List[List[Dict]],
        flyby_key: str
    ) -> None:
        """
        Сохранение пролета с событиями пересечения.
        
        Args:
            h5file: Открытый HDF5 файл для записи
            station: Станция
            satellite: Спутник
            flyby_index: Индекс пролета
            flybys_data: Данные пролетов
            crossing_events: События пересечений
            flyby_key: Ключ пролета
        """
        events = sorted(
            crossing_events[flyby_index],
            key=lambda e: dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f")
        )
        
        event_times = [
            dt.strptime(e['time'], "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
            for e in events
        ]
        event_types = [e['event'] for e in events]

        # Очистка событий
        cleaned_times, cleaned_types = self.timeseries_plotter.clean_events(
            event_times, event_types
        )

        # Создание группы для пролета
        group_path = f"{station}/{satellite}/flyby_{flyby_index}"
        flyby_group = h5file.create_group(group_path)

        # Сохранение атрибутов
        flyby_group.attrs['times'] = [t.isoformat() for t in cleaned_times]
        flyby_group.attrs['types'] = cleaned_types

        # Сохранение данных пролета
        flyby_data = flybys_data[station][satellite][flyby_key]
        flyby_group.create_dataset('roti', data=flyby_data['roti'])
        flyby_group.create_dataset('timestamps', data=flyby_data['timestamps'])
        flyby_group.create_dataset('lat', data=flyby_data['lat'])
        flyby_group.create_dataset('lon', data=flyby_data['lon'])
        
        logger.info(f'Successfully processed and added new flyby: {station}_{satellite}_{flyby_key}')