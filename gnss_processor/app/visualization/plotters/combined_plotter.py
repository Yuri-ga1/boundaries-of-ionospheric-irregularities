import os
import numpy as np
import h5py as h5

import matplotlib.pyplot as plt
from matplotlib.gridspec import GridSpec

from typing import Dict, List, Any, Optional
from config import FRAME_GRAPHS_PATH, COMMON_X_LIMITS, COMMON_Y_LIMITS, logger

from app.visualization.plotters.polygon_plotter import PolygonPlotter
from app.visualization.plotters.map_plotter import MapPlotter
from app.visualization.plotters.timeseries_plotter import TimeSeriesPlotter
from app.visualization.plotters.satellite_plotter import SatellitePlotter


class CombinedPlotter:
    """
    Класс для создания комбинированных визуализаций, объединяющих несколько графиков.
    """
    
    def __init__(self):
        self.polygon_plotter = PolygonPlotter()
        self.map_plotter = MapPlotter()
        self.timeseries_plotter = TimeSeriesPlotter()
        self.satellite_plotter = SatellitePlotter()
    
    def create_combined_visualization(
        self,
        map_points: Dict[str, Any],
        sliding_windows: Dict[str, Any],
        boundary_data: Dict[str, Any],
        boundary_condition: float,
        time_point: str,
        boundary_clusters: Dict[str, Any],
        roti_file: str,
        flyby_idx: str,
        flyby_roti: np.ndarray,
        flyby_times: List,
        flyby_events_times: List,
        flyby_events_types: List,
        station: str,
        satellite: str,
        save_to_file: bool = False
    ) -> Optional[plt.Figure]:
        """
        Создание комбинированной визуализации, объединяющей несколько графиков.
        
        Args:
            map_points: Данные карты ROTI
            sliding_windows: Данные скользящего окна
            boundary_data: Граничные данные
            boundary_condition: Условие границы
            time_point: Временная метка
            boundary_clusters: Кластеры границ
            roti_file: Путь к файлу ROTI
            flyby_idx: Идентификатор пролета
            flyby_roti: ROTI пролета
            flyby_times: Времена пролета
            flyby_events_times: Времена событий пролета
            flyby_events_types: Типы событий пролета
            station: Станция
            satellite: Спутник
            save_to_file: Сохранять ли в файл
            
        Returns:
            Optional[plt.Figure]: Объект figure или None при ошибке
        """
        fig = plt.figure(figsize=(16, 12))
        gs = GridSpec(2, 2, figure=fig)
        
        # Создание осей для всех графиков
        map_ax = fig.add_subplot(gs[0, 0])
        sliding_window_ax = fig.add_subplot(gs[0, 1])
        polygon_ax = fig.add_subplot(gs[1, 0])
        dynamics_ax = fig.add_subplot(gs[1, 1])
        
        # Установка общих пределов для карт
        for ax in [map_ax, sliding_window_ax, polygon_ax, dynamics_ax]:
            ax.set_xlim(COMMON_X_LIMITS)
            ax.set_ylim(COMMON_Y_LIMITS)
        
        try:
            # 1. Карта ROTI
            self.map_plotter.create_roti_map_plot(
                roti_points=map_points,
                time_point=time_point,
                ax=map_ax
            )
            
            # 2. Скользящее окно с границами
            self.map_plotter.create_sliding_window_plot(
                sliding_windows=sliding_windows,
                boundary_data=boundary_data,
                boundary_condition=boundary_condition,
                time_point=time_point,
                ax=sliding_window_ax
            )
            
            # 3. Полигоны
            self.polygon_plotter.plot_polygon(
                boundary_clusters=boundary_clusters,
                time_point=time_point,
                ax=polygon_ax
            )
            
            # 4. Пролет с событиями
            with h5.File(roti_file, 'r') as roti_h5file:
                if station not in roti_h5file.keys():
                    logger.warning(f'Station {station} not in {roti_file}')
                    plt.close(fig)
                    return None
                    
                if satellite not in roti_h5file[station].keys():
                    logger.warning(f'Satellite {satellite} not in {roti_file}')
                    plt.close(fig)
                    return None
                    
                self.timeseries_plotter.create_flyby_plot(
                    roti=flyby_roti,
                    times=flyby_times,
                    station=station,
                    satellite=satellite,
                    cleaned_times=flyby_events_times,
                    cleaned_types=flyby_events_types,
                    time_point=time_point,
                    ax=dynamics_ax
                )
                
                # Добавление траектории спутника
                self.satellite_plotter.add_satellite_trajectory(
                    station_lat=roti_h5file[station].attrs['lat'],
                    station_lon=roti_h5file[station].attrs['lon'],
                    satellite_azimuths=roti_h5file[station][satellite]['azimuth'][:],
                    satellite_elevations=roti_h5file[station][satellite]['elevation'][:],
                    satellite_times=roti_h5file[station][satellite]['timestamp'][:],
                    time_point=time_point,
                    ax_list=[map_ax, sliding_window_ax, polygon_ax]
                )

            fig.suptitle(f'Graphs for {station}_{satellite} at {time_point}')
            fig.tight_layout()
            
            # Корректировка размеров для лучшего отображения
            self._adjust_subplot_sizes(fig, map_ax, polygon_ax, dynamics_ax)

            if save_to_file:
                self._save_plot_to_file(fig, station, satellite, flyby_idx, time_point)
                self.satellite_plotter.remove_trajectory_lines()
            else:
                fig.canvas.draw()
                plt.pause(60)
                self.satellite_plotter.remove_trajectory_lines()
                        
            if not save_to_file:
                plt.show()
            else:
                plt.close(fig)
                
            return fig
            
        except Exception as e:
            logger.error(f"Error creating combined visualization: {e}")
            plt.close(fig)
            return None
    
    def _adjust_subplot_sizes(
        self, 
        fig: plt.Figure, 
        map_ax: plt.Axes, 
        polygon_ax: plt.Axes, 
        dynamics_ax: plt.Axes
    ) -> None:
        """
        Корректировка размеров подграфиков для лучшего отображения.
        
        Args:
            fig: Объект figure
            map_ax: Ось карты
            polygon_ax: Ось полигонов
            dynamics_ax: Ось динамики
        """
        map_box = map_ax.get_position()
        poly_box = polygon_ax.get_position()
        dynamic_box = dynamics_ax.get_position()
        
        polygon_ax.set_position([poly_box.x0, poly_box.y0, map_box.width, poly_box.height])
        dynamics_ax.set_position([dynamic_box.x0, dynamic_box.y0, map_box.width, dynamic_box.height])
    
    def _save_plot_to_file(
        self, 
        fig: plt.Figure, 
        station: str, 
        satellite: str, 
        flyby_idx: str, 
        time_point: str
    ) -> None:
        """
        Сохранение графика в файл.
        
        Args:
            fig: Объект figure для сохранения
            station: Станция
            satellite: Спутник
            flyby_idx: Идентификатор пролета
            time_point: Временная метка
        """
        output_dir = os.path.join(FRAME_GRAPHS_PATH, station, satellite, flyby_idx)
        os.makedirs(output_dir, exist_ok=True)
        filename = f"{time_point.replace(':', '_')}.png"
        plt.savefig(os.path.join(output_dir, filename))