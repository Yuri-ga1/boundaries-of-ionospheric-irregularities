import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from copy import deepcopy
from sklearn.cluster import DBSCAN

from app.services.auroral_oval.cluster_processor import ClusterProcessor

class TestClusterProcessorPerformance:
    """Performance tests for ClusterProcessor."""
    
    @pytest.fixture
    def cluster_processor(self):
        return ClusterProcessor(lat_condition=40.0)
    
    @pytest.fixture
    def large_dataset(self):
        """Create a large dataset for performance testing."""
        n_points = 10000
        # Create more structured data that will form valid clusters
        lon_list = np.concatenate([
            np.random.uniform(-120, -100, n_points // 2),  # Western cluster
            np.random.uniform(-80, -60, n_points // 2)     # Eastern cluster
        ]).tolist()
        lat_list = np.concatenate([
            np.random.uniform(60, 70, n_points // 2),      # Northern part
            np.random.uniform(55, 65, n_points // 2)       # Southern part  
        ]).tolist()
        return lon_list, lat_list
    
    def test_performance_large_dataset(self, cluster_processor, large_dataset, performance_recorder):
        """Performance test with large dataset."""
        lon_list, lat_list = large_dataset
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
             patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', 100), \
             patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            
            # Mock DBSCAN to return two large valid clusters
            n_points = len(lon_list)
            cluster_labels = np.concatenate([
                np.zeros(n_points // 2),  # First half in cluster 0
                np.ones(n_points // 2)    # Second half in cluster 1
            ])
            mock_dbscan_instance.fit_predict.return_value = cluster_labels
            
            @performance_recorder.measure_function("create_boundary_clusters_large", "ClusterProcessor")
            def timed_clustering():
                return cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            result = timed_clustering()
            
            # Should complete without errors and return valid clusters
            assert result is not None
            assert 'relation' in result
            assert len(result) > 1  # Should have clusters plus relation
            
            performance_recorder.save_to_history("large_dataset_clustering")
    
    def test_performance_many_small_clusters(self, cluster_processor, performance_recorder):
        """Performance test with many small clusters."""
        n_points = 5000
        n_clusters = 20  # Reduced from 100 to ensure clusters are large enough
        
        # Create structured data that will form valid clusters
        cluster_size = n_points // n_clusters
        lon_list = []
        lat_list = []
        
        for i in range(n_clusters):
            # Create each cluster in a different region
            center_lon = -100 + i * 5  # Spread clusters along longitude
            center_lat = 60 + i * 0.5  # Slight variation in latitude
            
            cluster_lon = np.random.uniform(center_lon - 2, center_lon + 2, cluster_size)
            cluster_lat = np.random.uniform(center_lat - 2, center_lat + 2, cluster_size)
            
            lon_list.extend(cluster_lon.tolist())
            lat_list.extend(cluster_lat.tolist())
        
        # Trim to exact n_points
        lon_list = lon_list[:n_points]
        lat_list = lat_list[:n_points]
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
             patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', cluster_size // 2), \
             patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            
            # Create cluster labels that match our structured data
            cluster_labels = np.repeat(range(n_clusters), cluster_size)[:n_points]
            mock_dbscan_instance.fit_predict.return_value = cluster_labels
            
            @performance_recorder.measure_function("create_boundary_clusters_many", "ClusterProcessor")
            def timed_clustering():
                return cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            result = timed_clustering()
            
            # Should handle many clusters efficiently and return valid result
            assert result is not None
            assert 'relation' in result
            
            performance_recorder.save_to_history("many_clusters_processing")