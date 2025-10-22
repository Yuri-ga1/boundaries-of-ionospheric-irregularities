import numpy as np
from copy import deepcopy
from sklearn.cluster import DBSCAN
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any
from config import MIN_CLUSTER_SIZE, DBSCAN_EPS, DBSCAN_MIN_SAMPLES, MAX_LATITUDE


class ClusterProcessor:
    """
    Класс для обработки кластеров граничных точек.
    """
    
    def __init__(self, lat_condition: float):
        """
        Инициализация процессора кластеров.
        
        Args:
            lat_condition: Условие по широте
        """
        self.lat_condition = lat_condition
    

    def create_boundary_clusters(
        self, 
        lat_list: List[float], 
        lon_list: List[float], 
        min_cluster_size: int = MIN_CLUSTER_SIZE
    ) -> Optional[Dict[str, Any]]:
        """
        Создание кластеров из граничных точек с использованием DBSCAN.
        
        Args:
            lat_list: Список широт
            lon_list: Список долгот
            min_cluster_size: Минимальный размер кластера
            
        Returns:
            Optional[Dict]: Словарь с кластерами и их отношениями
        """
        if not lat_list or not lon_list:
            return None
        
        coordinates = np.column_stack((lon_list, lat_list))
        
        # Применение DBSCAN кластеризации
        dbscan = DBSCAN(eps=DBSCAN_EPS, min_samples=DBSCAN_MIN_SAMPLES)
        cluster_labels = dbscan.fit_predict(coordinates)
        
        # Подсчет точек в кластерах (исключая шум)
        label_counts = Counter(cluster_labels)
        label_counts.pop(-1, None)  # Удаление шумовых точек
        
        valid_clusters = {
            label: count for label, count in label_counts.items() 
            if count >= min_cluster_size
        }
        
        if not valid_clusters:
            return None
        
        # Сортировка кластеров по размеру
        sorted_clusters = sorted(valid_clusters, key=valid_clusters.get, reverse=True)
        cluster_dict = self._extract_cluster_points(coordinates, cluster_labels, sorted_clusters)
        
        # Обработка отношений между кластерами
        if len(sorted_clusters) == 1:
            return self._process_single_cluster(cluster_dict, min_cluster_size)
        else:
            return self._process_multiple_clusters(cluster_dict, sorted_clusters, min_cluster_size)
    

    def _extract_cluster_points(
        self, 
        coordinates: np.ndarray, 
        labels: np.ndarray, 
        valid_labels: List[int]
    ) -> Dict[str, List[List[float]]]:
        """
        Извлечение точек для каждого валидного кластера.
        
        Args:
            coordinates: Массив координат
            labels: Метки кластеров
            valid_labels: Список валидных меток
            
        Returns:
            Dict[str, List[List[float]]]: Словарь с точками кластеров
        """
        cluster_dict = {}
        for idx, label in enumerate(valid_labels):
            cluster_points = coordinates[labels == label].tolist()
            cluster_dict[f"border{idx+1}"] = cluster_points
        return cluster_dict
    

    def _process_single_cluster(
        self, 
        cluster_dict: Dict[str, List[List[float]]], 
        min_cluster_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Обработка случая с одним кластером.
        
        Args:
            cluster_dict: Словарь с кластерами
            min_cluster_size: Минимальный размер кластера
            
        Returns:
            Optional[Dict]: Обработанный кластер или None если невалидный
        """
        single_cluster = cluster_dict['border1']
        
        # Добавление граничных точек
        left_edge = deepcopy(min(single_cluster, key=lambda p: p[0]))
        right_edge = deepcopy(max(single_cluster, key=lambda p: p[0]))
        
        left_edge[1] = right_edge[1] = MAX_LATITUDE
        
        single_cluster = np.insert(single_cluster, 0, left_edge, axis=0)
        single_cluster = np.insert(single_cluster, len(single_cluster), right_edge, axis=0)
        
        # Удаление циклических точек
        single_cluster = self._remove_circular_points(single_cluster, MAX_LATITUDE)
        
        if len(single_cluster) < min_cluster_size:
            return None
        
        cluster_dict["border1"] = single_cluster.tolist()
        return {"relation": "single-cluster", **cluster_dict}
    

    def _process_multiple_clusters(
        self, 
        cluster_dict: Dict[str, List[List[float]]], 
        sorted_clusters: List[int], 
        min_cluster_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Обработка случая с несколькими кластерами.
        
        Args:
            cluster_dict: Словарь с кластерами
            sorted_clusters: Отсортированный список меток кластеров
            min_cluster_size: Минимальный размер кластера
            
        Returns:
            Optional[Dict]: Обработанные кластеры с отношениями
        """
        top_clusters = sorted_clusters[:2]
        
        cluster1 = np.array(cluster_dict[f"border{sorted_clusters.index(top_clusters[0]) + 1}"])
        cluster2 = np.array(cluster_dict[f"border{sorted_clusters.index(top_clusters[1]) + 1}"])
        
        # Определение отношения между кластерами
        relation = self._determine_cluster_relation(cluster1, cluster2)
        
        if relation == "top-bottom":
            return self._process_top_bottom_clusters(
                cluster1, cluster2, cluster_dict, sorted_clusters, top_clusters, min_cluster_size
            )
        else:
            return {
                "relation": relation,
                **cluster_dict
            }
    

    def _determine_cluster_relation(
        self, 
        cluster1: np.ndarray, 
        cluster2: np.ndarray
    ) -> str:
        """
        Определение пространственного отношения между двумя кластерами.
        
        Args:
            cluster1: Первый кластер
            cluster2: Второй кластер
            
        Returns:
            str: Тип отношения ('left-right' или 'top-bottom')
        """
        cluster1_center = np.mean(cluster1, axis=0)
        cluster2_center = np.mean(cluster2, axis=0)
        
        if abs(cluster1_center[0] - cluster2_center[0]) > abs(cluster1_center[1] - cluster2_center[1]):
            return "left-right"
        else:
            return "top-bottom"
    

    def _process_top_bottom_clusters(
        self,
        cluster1: np.ndarray,
        cluster2: np.ndarray,
        cluster_dict: Dict[str, List[List[float]]],
        sorted_clusters: List[int],
        top_clusters: List[int],
        min_cluster_size: int
    ) -> Optional[Dict[str, Any]]:
        """
        Обработка кластеров с отношением 'top-bottom'.
        
        Args:
            cluster1: Первый кластер
            cluster2: Второй кластер
            cluster_dict: Словарь с кластерами
            sorted_clusters: Отсортированные метки кластеров
            top_clusters: Верхние кластеры
            min_cluster_size: Минимальный размер кластера
            
        Returns:
            Optional[Dict]: Обработанные кластеры или None если невалидные
        """
        cluster1_center = np.mean(cluster1, axis=0)
        cluster2_center = np.mean(cluster2, axis=0)
        
        # Определение верхнего и нижнего кластеров
        if cluster1_center[1] > cluster2_center[1]:
            top_cluster, bottom_cluster = cluster1, cluster2
            top_idx, bottom_idx = sorted_clusters.index(top_clusters[0]) + 1, sorted_clusters.index(top_clusters[1]) + 1
        else:
            top_cluster, bottom_cluster = cluster2, cluster1
            top_idx, bottom_idx = sorted_clusters.index(top_clusters[1]) + 1, sorted_clusters.index(top_clusters[0]) + 1
        
        # Добавление граничных точек
        top_cluster, bottom_cluster = self._add_boundary_points(
            top_cluster, bottom_cluster, self.lat_condition, MAX_LATITUDE
        )
        
        # Удаление циклических точек
        top_cluster = self._remove_circular_points(top_cluster, self.lat_condition)
        bottom_cluster = self._remove_circular_points(bottom_cluster, MAX_LATITUDE)

        if len(top_cluster) < min_cluster_size or len(bottom_cluster) < min_cluster_size:
            return None

        cluster_dict[f"border{top_idx}"] = top_cluster.tolist()
        cluster_dict[f"border{bottom_idx}"] = bottom_cluster.tolist()
        
        return {
            "relation": "top-bottom",
            **cluster_dict
        }
    

    def _add_boundary_points(
        self, 
        top_cluster: np.ndarray, 
        bottom_cluster: np.ndarray,
        top_edge: float, 
        bottom_edge: float
    ) -> Tuple[np.ndarray, np.ndarray]:
        """
        Добавление граничных точек к кластерам.
        
        Args:
            top_cluster: Верхний кластер
            bottom_cluster: Нижний кластер
            top_edge: Верхняя граница
            bottom_edge: Нижняя граница
            
        Returns:
            Tuple[np.ndarray, np.ndarray]: Кластеры с добавленными граничными точками
        """
        left_edge_top = deepcopy(min(top_cluster, key=lambda p: p[0]))
        right_edge_top = deepcopy(max(top_cluster, key=lambda p: p[0]))
        left_edge_bottom = deepcopy(min(bottom_cluster, key=lambda p: p[0]))
        right_edge_bottom = deepcopy(max(bottom_cluster, key=lambda p: p[0]))
        
        # Корректировка границ
        if abs(left_edge_bottom[0]) > abs(left_edge_top[0]):
            left_edge_top[0] = left_edge_bottom[0]
            top_cluster = np.insert(top_cluster, len(top_cluster), left_edge_top, axis=0)
        
        if abs(right_edge_top[0]) > abs(right_edge_bottom[0]):
            right_edge_top[0] = right_edge_bottom[0]
            top_cluster = np.insert(top_cluster, 0, right_edge_top, axis=0)
        
        # Установка граничных координат
        left_edge_top[1] = right_edge_top[1] = top_edge
        left_edge_bottom[1] = right_edge_bottom[1] = bottom_edge
        
        # Вставка граничных точек
        top_cluster = np.insert(top_cluster, len(top_cluster), left_edge_top, axis=0)
        top_cluster = np.insert(top_cluster, len(top_cluster), right_edge_top, axis=0)
        bottom_cluster = np.insert(bottom_cluster, 0, left_edge_bottom, axis=0)
        bottom_cluster = np.insert(bottom_cluster, len(bottom_cluster), right_edge_bottom, axis=0)
        
        return top_cluster, bottom_cluster
    

    def _remove_circular_points(self, data: np.ndarray, condition: float) -> np.ndarray:
        """
        Удаление циклических точек из данных.
        
        Args:
            data: Массив данных
            condition: Условие для фильтрации
            
        Returns:
            np.ndarray: Отфильтрованные данные
        """
        first_col_abs = np.abs(data[:, 0])
        
        increasing = first_col_abs[1] > first_col_abs[0]
        
        if increasing:
            max_index = np.argmax(first_col_abs)
            mask = (np.arange(len(data)) <= max_index) | np.any(data == condition, axis=1)
        else:
            min_index = np.argmin(first_col_abs)
            mask = (np.arange(len(data)) <= min_index) | np.any(data == condition, axis=1)
        
        return data[mask]