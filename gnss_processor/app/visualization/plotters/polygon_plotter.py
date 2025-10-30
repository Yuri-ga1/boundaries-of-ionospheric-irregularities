import numpy as np
import matplotlib.pyplot as plt
from shapely.geometry import Polygon, MultiPolygon
from typing import Dict, List, Tuple, Optional, Any
from config import logger


class PolygonPlotter:
    """Класс для визуализации полигонов и кластеров границ."""
    
    def plot_clusters(self, cluster_dict: Dict[str, np.ndarray], time_point: str) -> None:
        """
        Визуализация кластеров границ.
        
        Args:
            cluster_dict: Словарь с данными кластеров
            time_point: Временная метка для заголовка
        """
        fig, ax = plt.subplots()
        
        for label, cluster in cluster_dict.items():
            cluster_array = np.array(cluster)
            ax.scatter(cluster_array[:, 0], cluster_array[:, 1], label=label)
            
        ax.set_xlim(-120, -70)
        ax.set_ylim(40, 90)
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        ax.set_title(f"Clusters at {time_point}")
        ax.legend()
        plt.show()

    def compute_polygons(
        self, 
        boundary_clusters: Dict[str, Any], 
        time_point: str
    ) -> Tuple[Optional[List], Optional[Any], Optional[Any]]:
        """
        Вычисление полигонов и их пересечений на основе кластеров границ.
        
        Args:
            boundary_clusters: Данные кластеров границ
            time_point: Временная метка
            
        Returns:
            Tuple: Полигоны, пересечение и одиночный полигон кластера
        """
        if boundary_clusters is None:
            return None, None, None
        
        entry = boundary_clusters.get(time_point)
        if entry is None:
            return None, None, None
        
        if len(entry) == 0:
            return None, None, None
        
        if entry.get('relation') == "single-cluster":
            polygon = Polygon(np.array(entry["border1"])).buffer(0)
            return [(polygon, 'r', "Polygon")], None, polygon
        
        if entry.get('relation') == "left-right":
            return None, None, None
        
        clusters = [np.array(entry[f"border{i+1}"]) for i in range(len(entry) - 1)]
        
        if entry['relation'] == "top-bottom":
            polygon1 = Polygon(clusters[0]).buffer(0)
            polygon2 = Polygon(clusters[1]).buffer(0)
            intersection = polygon1.intersection(polygon2)
            
            return [(polygon1, 'b', "Polygon 1"), (polygon2, 'r', "Polygon 2")], intersection, None
        
        return None, None, None

    def plot_polygon(
        self, 
        boundary_clusters: Dict[str, Any], 
        time_point: str, 
        ax: Optional[plt.Axes] = None
    ) -> Tuple[plt.Figure, plt.Axes]:
        """
        Визуализация полигонов границ на основе кластеров.
        
        Args:
            boundary_clusters: Данные кластеров границ
            time_point: Временная метка
            ax: Ось для отрисовки (опционально)
            
        Returns:
            Tuple: Объекты figure и axes
        """
        if ax is None:
            fig, ax = plt.subplots()
            created_fig = True
            ax.set_title(f"Polygon at {time_point}")
        else:
            fig = ax.figure
            created_fig = False
            ax.set_title(f"Region of ionospheric irregulations")
        
        ax.set_xlabel("Longitude")
        ax.set_ylabel("Latitude")
        
        polygons, intersection, single_cluster_polygon = self.compute_polygons(boundary_clusters, time_point)
        
        if polygons is None:
            ax.text(0.5, 0.5, "No Data for Polygon", fontsize=12, color='red', alpha=0.7, 
                   ha='center', va='center', rotation=45, transform=ax.transAxes)
            if created_fig:
                plt.show()
            return fig, ax
        
        self._draw_polygons(ax, polygons, single_cluster_polygon, intersection)
        
        if created_fig:
            plt.show()
        else:
            return fig, ax
    
    def _draw_polygons(
        self, 
        ax: plt.Axes, 
        polygons: List[Tuple], 
        single_cluster_polygon: Any, 
        intersection: Any
    ) -> None:
        """
        Отрисовка полигонов на графике.
        
        Args:
            ax: Ось для отрисовки
            polygons: Список полигонов
            single_cluster_polygon: Одиночный полигон кластера
            intersection: Пересечение полигонов
        """
        for poly, color, _ in polygons:
            if isinstance(poly, Polygon):
                x, y = poly.exterior.xy
                ax.plot(x, y, f'{color}--')
            elif isinstance(poly, MultiPolygon):
                for part in poly.geoms:
                    x, y = part.exterior.xy
                    ax.plot(x, y, f'{color}--')
        
        if single_cluster_polygon:
            self._fill_single_cluster(ax, single_cluster_polygon)
        
        if intersection and not intersection.is_empty:
            self._fill_intersection(ax, intersection)
    
    def _fill_single_cluster(self, ax: plt.Axes, polygon: Any) -> None:
        """
        Заливка одиночного полигона кластера.
        
        Args:
            ax: Ось для отрисовки
            polygon: Полигон для заливки
        """
        if isinstance(polygon, MultiPolygon):
            for poly in polygon.geoms:
                x, y = poly.exterior.xy
                ax.fill(x, y, 'purple', alpha=0.5, label="Polygon area")
        else:
            x, y = polygon.exterior.xy
            ax.fill(x, y, 'purple', alpha=0.5, label="Polygon area")
    
    def _fill_intersection(self, ax: plt.Axes, intersection: Any) -> None:
        """
        Заливка области пересечения полигонов.
        
        Args:
            ax: Ось для отрисовки
            intersection: Область пересечения
        """
        for poly in ([intersection] if isinstance(intersection, Polygon) else intersection.geoms):
            x, y = poly.exterior.xy
            ax.fill(x, y, 'purple', alpha=0.5, label="AORI")