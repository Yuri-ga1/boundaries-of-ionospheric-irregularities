import numpy as np

import matplotlib.pyplot as plt

from datetime import datetime as dt
import datetime

from typing import List
from app.services.satellite.trajectory_calculator import SatelliteTrajectory


class SatellitePlotter:
    """Класс для визуализации траекторий спутников."""
    
    def __init__(self):
        self.trajectory_elements = []
    
    def remove_trajectory_lines(self) -> None:
        """Удаление линий траекторий с графиков."""
        if self.trajectory_elements:
            for line, scatter in self.trajectory_elements:
                line.remove()
                scatter.remove()
            self.trajectory_elements.clear()
    
    def add_satellite_trajectory(
        self,
        station_lat: float,
        station_lon: float,
        satellite_azimuths: np.ndarray,
        satellite_elevations: np.ndarray, 
        satellite_times: np.ndarray,
        time_point: str,
        ax_list: List[plt.Axes]
    ) -> None:
        """
        Добавление траектории спутника на графики.
        
        Args:
            station_lat: Широта станции
            station_lon: Долгота станции
            satellite_azimuths: Азимуты спутника
            satellite_elevations: Углы возвышения спутника
            satellite_times: Временные метки спутника
            time_point: Временная точка для выделения
            ax_list: Список осей для отрисовки
        """
        trajectory = SatelliteTrajectory(
            lat_site=station_lat,
            lon_site=station_lon,
        )

        trajectory.process(
            azimuths=satellite_azimuths,
            elevations=satellite_elevations,
            timestamps=satellite_times
        )

        if trajectory.traj_lat.size > 0 and trajectory.traj_lon.size > 0:
            color = 'black'
            for ax in ax_list:
                self._add_trajectory_to_axis(ax, trajectory, time_point, color)
    
    def _add_trajectory_to_axis(
        self, 
        ax: plt.Axes, 
        trajectory: SatelliteTrajectory, 
        time_point: str, 
        color: str
    ) -> None:
        """
        Добавление траектории на конкретную ось.
        
        Args:
            ax: Ось для отрисовки
            trajectory: Объект траектории
            time_point: Временная точка
            color: Цвет траектории
        """
        handles, labels = ax.get_legend_handles_labels()
        
        # Фильтрация дублирующихся легенд
        seen = set()
        filtered = [(h, l) for h, l in zip(handles, labels) if l not in seen and not seen.add(l)]
        handles, labels = list(zip(*filtered)) if filtered else ([], [])
        handles, labels = list(handles), list(labels)
        
        # Поиск позиции спутника в заданное время
        try:
            time_point_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S.%f").replace(tzinfo=datetime.UTC)
        except ValueError:
            time_point_dt = dt.strptime(time_point, "%Y-%m-%d %H:%M:%S").replace(tzinfo=datetime.UTC)

        time_point_ts = time_point_dt.timestamp()
        closest_idx = np.argmin(np.abs(np.array(trajectory.timestamps) - time_point_ts))
        
        try:
            scatter = ax.scatter(
                trajectory.traj_lon[closest_idx], trajectory.traj_lat[closest_idx],
                color='green', marker='o', s=40, edgecolor=color
            )
        except Exception:
            scatter = ax.scatter(trajectory.traj_lon[0], trajectory.traj_lat[0], 
                               color='green', marker='o', s=40, edgecolor=color, alpha=0)
        
        # Отрисовка траектории
        line, = ax.plot(trajectory.traj_lon, trajectory.traj_lat, color=color, linewidth=2)
        self.trajectory_elements.append((line, scatter))
        
        # Обновление легенды
        handles.append(scatter)
        labels.append("Time Point")
        handles.append(line)
        labels.append("Trajectory")
        
        ax.legend(handles, labels, loc='upper right', bbox_to_anchor=(1, 1))