import numpy as np

import matplotlib.pyplot as plt

from typing import Dict, Tuple, Optional


class MapPlotter:
    """Класс для визуализации карт ROTI и данных скользящего окна."""
    
    def create_roti_map_plot(
        self, 
        roti_points: Dict[str, np.ndarray], 
        time_point: str, 
        ax: Optional[plt.Axes] = None, 
        cmap: str = 'coolwarm'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Создание карты ROTI на основе предоставленных точек.
        
        Args:
            roti_points: Данные точек {'lon', 'lat', 'vals'}
            time_point: Временная метка
            ax: Ось для отрисовки (опционально)
            cmap: Цветовая карта
            
        Returns:
            Tuple: Объекты figure и axes
        """
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            fig = ax.figure
        
        cmap_obj = plt.get_cmap(cmap)
        norm = plt.Normalize(0, 0.1)
        
        lons = roti_points['lon'][()]
        lats = roti_points['lat'][()]
        rotis = roti_points['vals'][()]
        
        scatter = ax.scatter(lons, lats, c=rotis, cmap=cmap_obj, norm=norm, 
                           marker='o', edgecolors='grey')
        
        ax.set_xlabel('Longitude')
        ax.set_ylabel('Latitude')
        ax.grid(True)
        fig.colorbar(scatter, ax=ax, label='ROTI')
        
        if created_fig:
            ax.set_title(f'ROTI Map (irregular) at {time_point}')
            plt.show()
        else:
            ax.set_title(f'ROTI Map (irregular)')
            return fig, ax
    
    def create_sliding_window_plot(
        self,
        sliding_windows: Dict[str, np.ndarray],
        boundary_data: Dict[str, np.ndarray],
        boundary_condition: float,
        ax: Optional[plt.Axes] = None,
        time_point: Optional[str] = None,
        cmap: str = 'coolwarm'
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Визуализация данных скользящего окна с граничными данными.
        
        Args:
            sliding_windows: Данные скользящего окна
            boundary_data: Граничные точки
            boundary_condition: Условие границы
            ax: Ось для отрисовки (опционально)
            time_point: Временная метка
            cmap: Цветовая карта
            
        Returns:
            Tuple: Объекты figure и axes
        """
        created_fig = False
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
        else:
            fig = ax.figure
        
        cmap_obj = plt.get_cmap(cmap)
        norm = plt.Normalize(0, 0.1)
        
        lon = np.array(sliding_windows['lon'])
        lat = np.array(sliding_windows['lat'])
        vals = np.array(sliding_windows['vals'])
        
        scatter_sliding = ax.scatter(lon, lat, c=vals, cmap=cmap_obj, norm=norm)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        fig.colorbar(scatter_sliding, ax=ax, label='ROTI')    
        
        if boundary_data['lon'].size > 0 and boundary_data['lat'].size > 0:
            ax.scatter(
                boundary_data['lon'],
                boundary_data['lat'], 
                color='grey',
                label=f'{boundary_condition} boundary'
            )
            ax.legend()

        if created_fig:
            ax.set_title(f"ROTI Map (regular) at {time_point}")
            plt.show()
        else:
            ax.set_title(f"ROTI Map (regular)")
            return fig, ax