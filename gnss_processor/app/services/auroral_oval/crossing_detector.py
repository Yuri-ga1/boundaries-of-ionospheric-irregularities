from datetime import datetime as dt
from shapely.geometry import Point
from typing import Dict, Any

from app.visualization.plotters.polygon_plotter import PolygonPlotter


class BoundaryCrossingDetector:
    """
    Класс для обнаружения моментов пересечения спутниками границ.
    """
    
    def __init__(self, time_threshold_seconds: int = 10800):
        """
        Инициализация детектора пересечений.
        
        Args:
            time_threshold_seconds: Временной порог для группировки пересечений (в секундах)
        """
        self.time_threshold = time_threshold_seconds
        self.polygon_plotter = PolygonPlotter()
    
    def detect_satellite_crossings(
        self, 
        boundaries: Dict[str, Any], 
        satellites: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Обнаружение моментов, когда спутники пересекают границы.
        
        Args:
            boundaries: Данные границ для каждой временной метки
            satellites: Данные спутников с координатами для каждой временной метки
            
        Returns:
            Dict: Словарь с событиями пересечений для каждого спутника
        """
        crossings = {}

        if boundaries is None:
            return crossings
        
        time_keys = sorted(boundaries.keys())

        for i in range(len(time_keys) - 1):
            current_time = time_keys[i]
            next_time = time_keys[i + 1]
            
            if not boundaries[current_time] or not boundaries[next_time]:
                continue

            # Вычисление полигонов для текущего и следующего времени
            current_polygons = self.polygon_plotter.compute_polygons(boundaries, current_time)
            next_polygons = self.polygon_plotter.compute_polygons(boundaries, next_time)

            boundary_current = current_polygons[1] if current_polygons[1] else current_polygons[2]  # intersection или single_cluster
            boundary_next = next_polygons[1] if next_polygons[1] else next_polygons[2]

            if not boundary_current or not boundary_next:
                continue

            # Проверка пересечений для каждого спутника
            self._check_satellite_crossings_for_time(
                crossings, satellites, current_time, next_time,
                boundary_current, boundary_next
            )

        return crossings
    
    def _check_satellite_crossings_for_time(
        self,
        crossings: Dict[str, Any],
        satellites: Dict[str, Any],
        current_time: str,
        next_time: str,
        boundary_current: Any,
        boundary_next: Any
    ) -> None:
        """
        Проверка пересечений для конкретного временного интервала.
        
        Args:
            crossings: Словарь для сохранения результатов
            satellites: Данные спутников
            current_time: Текущее время
            next_time: Следующее время
            boundary_current: Граница текущего времени
            boundary_next: Граница следующего времени
        """
        for satellite_id, data_current in satellites.get(current_time, {}).items():
            position_current = Point(data_current['lon'], data_current['lat'])
            position_next = None
            
            # Получение позиции спутника в следующее время
            if satellite_id in satellites.get(next_time, {}):
                data_next = satellites[next_time][satellite_id]
                position_next = Point(data_next['lon'], data_next['lat'])

            if position_next:
                was_inside = boundary_current.contains(position_current)
                is_inside = boundary_next.contains(position_next)

                # Определение типа события
                if was_inside and not is_inside:
                    event_type = "exited"
                elif not was_inside and is_inside:
                    event_type = "entered"
                else:
                    continue
                
                # Сохранение события пересечения
                self._store_crossing_event(
                    crossings, satellite_id, next_time, event_type
                )
    
    def _store_crossing_event(
        self,
        crossings: Dict[str, Any],
        satellite_id: str,
        event_time: str,
        event_type: str
    ) -> None:
        """
        Сохранение события пересечения в структуру результатов.
        
        Args:
            crossings: Словарь для сохранения результатов
            satellite_id: Идентификатор спутника (формат: "station_satellite")
            event_time: Время события
            event_type: Тип события ("entered" или "exited")
        """
        station, satellite = satellite_id.split('_')

        if station not in crossings:
            crossings[station] = {}
        if satellite not in crossings[station]:
            crossings[station][satellite] = []

        # Проверка временного порога для группировки событий
        events_list = crossings[station][satellite]
        
        if not events_list:
            events_list.append([])
        else:
            last_event_time = events_list[-1][-1]['time'] if events_list[-1] else None
            if last_event_time:
                time_diff = (dt.strptime(event_time, "%Y-%m-%d %H:%M:%S.%f") - 
                           dt.strptime(last_event_time, "%Y-%m-%d %H:%M:%S.%f")).total_seconds()
                
                if time_diff > self.time_threshold:
                    events_list.append([])

        # Добавление события
        events_list[-1].append({
            "time": event_time, 
            "event": event_type
        })