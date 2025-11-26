import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from copy import deepcopy
from sklearn.cluster import DBSCAN

from app.services.auroral_oval.cluster_processor import ClusterProcessor


class TestClusterProcessor:
    """Test cases for ClusterProcessor functionality."""
    
    @pytest.fixture
    def cluster_processor(self):
        """Create a ClusterProcessor instance for testing."""
        return ClusterProcessor(lat_condition=40.0)
    
    @pytest.fixture
    def sample_coordinates(self):
        """Create sample coordinates for testing."""
        # Create two distinct clusters
        cluster1_lon = np.random.uniform(-120, -100, 50)
        cluster1_lat = np.random.uniform(60, 70, 50)
        
        cluster2_lon = np.random.uniform(-80, -60, 50)
        cluster2_lat = np.random.uniform(55, 65, 50)
        
        lon_list = np.concatenate([cluster1_lon, cluster2_lon]).tolist()
        lat_list = np.concatenate([cluster1_lat, cluster2_lat]).tolist()
        
        return lon_list, lat_list
    
    @pytest.fixture
    def single_cluster_coordinates(self):
        """Create coordinates for a single cluster."""
        lon_list = np.random.uniform(-100, -80, 100).tolist()
        lat_list = np.random.uniform(60, 70, 100).tolist()
        return lon_list, lat_list
    
    def test_initialization(self, cluster_processor):
        """Test that ClusterProcessor initializes correctly."""
        assert cluster_processor.lat_condition == 40.0
    
    def test_create_boundary_clusters_empty_input(self, cluster_processor):
        """Test cluster creation with empty input data."""
        # Test empty lat list
        result = cluster_processor.create_boundary_clusters([], [1, 2, 3])
        assert result is None
        
        # Test empty lon list
        result = cluster_processor.create_boundary_clusters([1, 2, 3], [])
        assert result is None
        
        # Test both empty
        result = cluster_processor.create_boundary_clusters([], [])
        assert result is None
    
    def test_create_boundary_clusters_single_cluster(self, cluster_processor):
        """Test cluster creation with a single cluster."""
        n_points = 120  # More points to ensure cluster remains large enough
        lon_list = np.linspace(-100, -80, n_points).tolist()  # Linear range for predictable behavior
        lat_list = np.linspace(60, 70, n_points).tolist()
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
            patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', 10), \
            patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            
            # Mock DBSCAN to return a single cluster
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            mock_dbscan_instance.fit_predict.return_value = np.zeros(len(lon_list))  # All points in cluster 0
            
            result = cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            # Should return a single cluster with relation
            assert result is not None
            assert result['relation'] == 'single-cluster'
            assert 'border1' in result
            # Should have added boundary points
            assert len(result['border1']) > len(lon_list)  # May have added boundary points
    
    def test_create_boundary_clusters_multiple_clusters(self, cluster_processor):
        """Test cluster creation with multiple clusters."""
        # Create two well-separated clusters
        n_points_per_cluster = 120
        
        # Cluster 1: centered around (-100, 65)
        cluster1_lon = np.random.uniform(-110, -90, n_points_per_cluster)
        cluster1_lat = np.random.uniform(60, 70, n_points_per_cluster)
        
        # Cluster 2: centered around (-70, 60) 
        cluster2_lon = np.random.uniform(-80, -60, n_points_per_cluster)
        cluster2_lat = np.random.uniform(55, 65, n_points_per_cluster)
        
        lon_list = np.concatenate([cluster1_lon, cluster2_lon]).tolist()
        lat_list = np.concatenate([cluster1_lat, cluster2_lat]).tolist()
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
            patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', 10), \
            patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            
            # Mock DBSCAN to return two clusters
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            
            # Create cluster labels: first 30 points in cluster 0, next 30 in cluster 1
            cluster_labels = np.concatenate([np.zeros(n_points_per_cluster), np.ones(n_points_per_cluster)])
            mock_dbscan_instance.fit_predict.return_value = cluster_labels
            
            result = cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            # Should return multiple clusters
            assert result is not None
            assert 'relation' in result
            assert 'border1' in result
            assert 'border2' in result
    
    def test_create_boundary_clusters_all_noise(self, cluster_processor, sample_coordinates):
        """Test cluster creation when DBSCAN identifies all points as noise."""
        lon_list, lat_list = sample_coordinates
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
             patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', 10):
            
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            
            # All points marked as noise (-1)
            mock_dbscan_instance.fit_predict.return_value = np.full(len(lon_list), -1)
            
            result = cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            # Should return None when no valid clusters
            assert result is None
    
    def test_create_boundary_clusters_small_clusters(self, cluster_processor, sample_coordinates):
        """Test cluster creation when clusters are smaller than minimum size."""
        lon_list, lat_list = sample_coordinates
        
        with patch('app.services.auroral_oval.cluster_processor.DBSCAN') as mock_dbscan, \
             patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE', 100):  # Large minimum size
            
            mock_dbscan_instance = Mock()
            mock_dbscan.return_value = mock_dbscan_instance
            
            # Create clusters smaller than minimum size
            cluster_labels = np.concatenate([np.zeros(50), np.ones(50)])
            mock_dbscan_instance.fit_predict.return_value = cluster_labels
            
            result = cluster_processor.create_boundary_clusters(lat_list, lon_list)
            
            # Should return None when no clusters meet minimum size
            assert result is None
    
    def test_extract_cluster_points(self, cluster_processor):
        """Test extraction of cluster points from coordinates and labels."""
        coordinates = np.array([
            [1.0, 2.0], [1.1, 2.1], [1.2, 2.2],  # Cluster 0
            [3.0, 4.0], [3.1, 4.1], [3.2, 4.2],  # Cluster 1
            [5.0, 6.0]  # Noise (-1)
        ])
        
        labels = np.array([0, 0, 0, 1, 1, 1, -1])
        valid_labels = [0, 1]
        
        cluster_dict = cluster_processor._extract_cluster_points(coordinates, labels, valid_labels)
        
        assert 'border1' in cluster_dict
        assert 'border2' in cluster_dict
        assert len(cluster_dict['border1']) == 3  # Cluster 0 has 3 points
        assert len(cluster_dict['border2']) == 3  # Cluster 1 has 3 points
        
        # Verify points are correctly assigned
        assert cluster_dict['border1'] == [[1.0, 2.0], [1.1, 2.1], [1.2, 2.2]]
        assert cluster_dict['border2'] == [[3.0, 4.0], [3.1, 4.1], [3.2, 4.2]]
    
    def test_determine_cluster_relation_left_right(self, cluster_processor):
        """Test cluster relation determination for left-right relationship."""
        # Clusters separated primarily in longitude
        cluster1 = np.array([[1.0, 10.0], [1.1, 10.1], [1.2, 10.2]])  # Left cluster
        cluster2 = np.array([[5.0, 10.0], [5.1, 10.1], [5.2, 10.2]])  # Right cluster
        
        relation = cluster_processor._determine_cluster_relation(cluster1, cluster2)
        
        assert relation == 'left-right'
    
    def test_determine_cluster_relation_top_bottom(self, cluster_processor):
        """Test cluster relation determination for top-bottom relationship."""
        # Clusters separated primarily in latitude
        cluster1 = np.array([[1.0, 10.0], [1.1, 10.1], [1.2, 10.2]])  # Bottom cluster
        cluster2 = np.array([[1.0, 15.0], [1.1, 15.1], [1.2, 15.2]])  # Top cluster
        
        relation = cluster_processor._determine_cluster_relation(cluster1, cluster2)
        
        assert relation == 'top-bottom'
    
    def test_add_boundary_points(self, cluster_processor):
        """Test adding boundary points to clusters."""
        top_cluster = np.array([[1.0, 60.0], [2.0, 61.0], [3.0, 62.0]])
        bottom_cluster = np.array([[1.5, 55.0], [2.5, 56.0], [3.5, 57.0]])
        
        top_edge = 65.0
        bottom_edge = 50.0
        
        new_top, new_bottom = cluster_processor._add_boundary_points(
            top_cluster, bottom_cluster, top_edge, bottom_edge
        )
        
        # Check that boundary points were added
        assert len(new_top) > len(top_cluster)
        assert len(new_bottom) > len(bottom_cluster)
        
        # Check that boundary points have the correct edge values
        assert any(point[1] == top_edge for point in new_top)
        assert any(point[1] == bottom_edge for point in new_bottom)
    
    def test_remove_circular_points_increasing(self, cluster_processor):
        """Test removal of circular points with increasing pattern."""
        # Create data with increasing absolute longitude
        data = np.array([
            [1.0, 10.0],
            [2.0, 11.0], 
            [3.0, 12.0],
            [2.0, 13.0],  # This should be removed (decreasing)
            [1.0, 14.0]   # This should be removed (decreasing)
        ])
        
        condition = 15.0
        
        filtered_data = cluster_processor._remove_circular_points(data, condition)
        
        # Should keep points until the maximum (index 2)
        assert len(filtered_data) == 3
        assert np.array_equal(filtered_data, data[:3])
    
    def test_remove_circular_points_decreasing(self, cluster_processor):
        """Test removal of circular points with decreasing pattern."""
        # Create data with decreasing absolute longitude
        data = np.array([
            [3.0, 10.0],
            [2.0, 11.0],
            [1.0, 12.0], 
            [2.0, 13.0],  # This should be removed (increasing)
            [3.0, 14.0]   # This should be removed (increasing)
        ])
        
        condition = 15.0
        
        filtered_data = cluster_processor._remove_circular_points(data, condition)
        
        # Should keep points until the minimum (index 2)
        assert len(filtered_data) == 3
        assert np.array_equal(filtered_data, data[:3])
    
    def test_process_single_cluster_valid(self, cluster_processor):
        """Test processing of a single valid cluster."""
        # Create a cluster with enough points that won't be reduced too much
        cluster_points = [[-100.0 + i, 60.0 + i * 0.1] for i in range(20)]  # 20 points in a line
        
        cluster_dict = {'border1': cluster_points}
        
        with patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            result = cluster_processor._process_single_cluster(cluster_dict, min_cluster_size=10)
            
            assert result is not None
            assert result['relation'] == 'single-cluster'
            assert 'border1' in result
            # Should have added boundary points
            assert len(result['border1']) > len(cluster_points)
    
    def test_process_single_cluster_too_small(self, cluster_processor):
        """Test processing of a single cluster that's too small."""
        cluster_dict = {
            'border1': [[1.0, 60.0], [2.0, 61.0]]  # Only 2 points
        }
        
        with patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE', 80.0):
            result = cluster_processor._process_single_cluster(cluster_dict, min_cluster_size=5)
            
            # Should return None when cluster is too small after processing
            assert result is None
