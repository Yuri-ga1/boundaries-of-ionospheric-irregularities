import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
import tempfile
import os

from app.services.auroral_oval.boundary_detector import BoundaryDetector


class TestBoundaryDetector:
    """Test cases for BoundaryDetector functionality."""
    
    @pytest.fixture
    def boundary_detector(self):
        """Create a BoundaryDetector instance for testing."""
        return BoundaryDetector(
            lon_condition=-60,
            lat_condition=40,
            boundary_condition=0.5
        )
    
    @pytest.fixture
    def sample_sliding_windows(self):
        """Create sample sliding windows data for testing."""
        return [
            {'lon': -100.0, 'lat': 60.0, 'vals': 0.3},
            {'lon': -90.0, 'lat': 62.0, 'vals': 0.6},
            {'lon': -80.0, 'lat': 64.0, 'vals': 0.4},
            {'lon': -70.0, 'lat': 66.0, 'vals': 0.7},
            {'lon': -60.0, 'lat': 68.0, 'vals': 0.5},
        ]
    
    @pytest.fixture
    def mock_matplotlib(self):
        """Mock matplotlib to avoid GUI issues."""
        with patch('app.services.auroral_oval.boundary_detector.plt') as mock_plt:
            # Mock figure and contour
            mock_fig = Mock()
            mock_contour = Mock()
            
            # Configure contour mock to return empty segments by default
            mock_contour.allsegs = [[]]  # No contour segments
            mock_plt.contour.return_value = mock_contour
            mock_plt.figure.return_value = mock_fig
            
            yield mock_plt
    
    def test_initialization(self, boundary_detector):
        """Test that BoundaryDetector initializes correctly."""
        assert boundary_detector.lon_condition == -60
        assert boundary_detector.lat_condition == 40
        assert boundary_detector.boundary_condition == 0.5
    
    def test_extract_boundary_contours_basic(self, boundary_detector, sample_sliding_windows, mock_matplotlib):
        """
        Test basic boundary contour extraction.
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata to return a simple grid
            xi = np.linspace(-100, -60, 50)
            yi = np.linspace(60, 68, 50)
            zi = np.random.uniform(0, 1, (50, 50))
            mock_griddata.return_value = zi
            
            boundary_data = boundary_detector.extract_boundary_contours(sample_sliding_windows)
            
            # Verify the structure of returned data
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data
            assert isinstance(boundary_data['lat'], list)
            assert isinstance(boundary_data['lon'], list)
            
            # Verify matplotlib was called
            mock_matplotlib.figure.assert_called_once()
            mock_matplotlib.contour.assert_called_once()
    
    def test_extract_boundary_contours_with_contours(self, boundary_detector, sample_sliding_windows, mock_matplotlib):
        """
        Test boundary contour extraction when contours are found.
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata
            zi = np.random.uniform(0, 1, (50, 50))
            mock_griddata.return_value = zi
            
            # Mock contour to return some segments
            contour_segments = [
                np.array([[ -90.0, 62.0 ], [ -85.0, 63.0 ], [ -80.0, 64.0 ]]),
                np.array([[ -70.0, 66.0 ], [ -65.0, 67.0 ]])
            ]
            mock_matplotlib.contour.return_value.allsegs = [contour_segments]
            
            boundary_data = boundary_detector.extract_boundary_contours(sample_sliding_windows)
            
            # Verify boundary data contains the contour points
            assert len(boundary_data['lon']) == 5  # 3 points from first segment + 2 from second
            assert len(boundary_data['lat']) == 5
            
            # Verify the points are correctly extracted
            expected_lons = [-90.0, -85.0, -80.0, -70.0, -65.0]
            expected_lats = [62.0, 63.0, 64.0, 66.0, 67.0]
            
            assert boundary_data['lon'] == expected_lons
            assert boundary_data['lat'] == expected_lats
    
    def test_extract_boundary_contours_all_nan(self, boundary_detector, sample_sliding_windows, mock_matplotlib):
        """
        Test boundary contour extraction when interpolation returns all NaN values.
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata to return all NaN
            zi = np.full((50, 50), np.nan)
            mock_griddata.return_value = zi
            
            boundary_data = boundary_detector.extract_boundary_contours(sample_sliding_windows)
            
            # Should return empty boundary data
            assert boundary_data['lat'] == []
            assert boundary_data['lon'] == []
            
            # matplotlib should not be called since all values are NaN
            mock_matplotlib.figure.assert_not_called()
            mock_matplotlib.contour.assert_not_called()
    
    def test_extract_boundary_contours_empty_input(self, boundary_detector, mock_matplotlib):
        """
        Test boundary contour extraction with empty input data.
        """
        empty_windows = []
        
        boundary_data = boundary_detector.extract_boundary_contours(empty_windows)
        
        # Should return empty boundary data
        assert boundary_data['lat'] == []
        assert boundary_data['lon'] == []
        
        # matplotlib should not be called with empty data
        mock_matplotlib.figure.assert_not_called()
        mock_matplotlib.contour.assert_not_called()
    
    def test_extract_boundary_contours_single_point(self, boundary_detector, mock_matplotlib):
        """
        Test boundary contour extraction with only one data point.
        """
        single_window = [{'lon': -80.0, 'lat': 65.0, 'vals': 0.5}]
        
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata - with single point, interpolation might still work
            zi = np.random.uniform(0, 1, (50, 50))
            mock_griddata.return_value = zi
            
            boundary_data = boundary_detector.extract_boundary_contours(single_window)
            
            # Should have the structure even if no contours found
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data
            
            # matplotlib should be called
            mock_matplotlib.figure.assert_called_once()
            mock_matplotlib.contour.assert_called_once()


class TestBoundaryDetectorEdgeCases:
    """Edge case tests for BoundaryDetector."""
    
    @pytest.fixture
    def boundary_detector(self):
        return BoundaryDetector(-60, 40, 0.5)
    
    @pytest.fixture
    def mock_matplotlib(self):
        with patch('app.services.auroral_oval.boundary_detector.plt') as mock_plt:
            mock_fig = Mock()
            mock_contour = Mock()
            mock_contour.allsegs = [[]]
            mock_plt.contour.return_value = mock_contour
            mock_plt.figure.return_value = mock_fig
            yield mock_plt
    
    def test_extract_boundary_contours_identical_points(self, boundary_detector, mock_matplotlib):
        """
        Test with identical coordinate points (edge case for interpolation).
        """
        identical_windows = [
            {'lon': -80.0, 'lat': 65.0, 'vals': 0.5},
            {'lon': -80.0, 'lat': 65.0, 'vals': 0.6},  # Same coordinates, different values
            {'lon': -80.0, 'lat': 65.0, 'vals': 0.4}
        ]
        
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # griddata might handle this or raise warning, but should not crash
            zi = np.random.uniform(0, 1, (50, 50))
            mock_griddata.return_value = zi
            
            boundary_data = boundary_detector.extract_boundary_contours(identical_windows)
            
            # Should complete without crashing
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data
    
    def test_extract_boundary_contours_extreme_values(self, boundary_detector, mock_matplotlib):
        """
        Test with extreme ROTI values.
        """
        extreme_windows = [
            {'lon': -100.0, 'lat': 60.0, 'vals': 0.0},   # Very low
            {'lon': -90.0, 'lat': 62.0, 'vals': 10.0},   # Very high
            {'lon': -80.0, 'lat': 64.0, 'vals': -5.0},   # Negative (shouldn't happen but test robustness)
        ]
        
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 50), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            zi = np.array([[0.0, 10.0, -5.0]])
            mock_griddata.return_value = zi
            
            boundary_data = boundary_detector.extract_boundary_contours(extreme_windows)
            
            # Should complete without crashing
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data


class TestBoundaryDetectorPerformance:
    """Performance tests for BoundaryDetector."""
    
    @pytest.fixture
    def boundary_detector(self):
        return BoundaryDetector(-60, 40, 0.5)
    
    @pytest.fixture
    def large_sliding_windows(self):
        """Create large sliding windows dataset for performance testing."""
        n_points = 10000
        lon = np.random.uniform(-120, -60, n_points)
        lat = np.random.uniform(50, 80, n_points)
        vals = np.random.uniform(0, 2, n_points)
        
        return [{'lon': lon[i], 'lat': lat[i], 'vals': vals[i]} for i in range(n_points)]
    
    @pytest.fixture
    def mock_matplotlib(self):
        with patch('app.services.auroral_oval.boundary_detector.plt') as mock_plt:
            mock_fig = Mock()
            mock_contour = Mock()
            mock_contour.allsegs = [[]]  # Empty contours for performance tests
            mock_plt.contour.return_value = mock_contour
            mock_plt.figure.return_value = mock_fig
            yield mock_plt
    
    def test_performance_large_dataset(self, boundary_detector, large_sliding_windows, mock_matplotlib, performance_recorder):
        """
        Performance test with large sliding windows dataset.
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 100), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata to return realistic data quickly
            zi = np.random.uniform(0, 1, (100, 100))
            mock_griddata.return_value = zi
            
            @performance_recorder.measure_function("extract_boundary_large_dataset", "BoundaryDetector")
            def timed_extraction():
                return boundary_detector.extract_boundary_contours(large_sliding_windows)
            
            boundary_data = timed_extraction()
            
            # Verify the result structure
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data
            
            performance_recorder.save_to_history("large_dataset_boundary_detection")
    
    def test_performance_high_resolution_grid(self, boundary_detector, large_sliding_windows, mock_matplotlib, performance_recorder):
        """
        Performance test with high-resolution grid (many grid points).
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 500), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            # Mock griddata for high-resolution grid
            zi = np.random.uniform(0, 1, (500, 500))
            mock_griddata.return_value = zi
            
            @performance_recorder.measure_function("extract_boundary_high_res", "BoundaryDetector")
            def timed_extraction():
                return boundary_detector.extract_boundary_contours(large_sliding_windows)
            
            boundary_data = timed_extraction()
            
            assert 'lat' in boundary_data
            assert 'lon' in boundary_data
            
            performance_recorder.save_to_history("high_resolution_boundary_detection")
    
    def test_performance_multiple_contours(self, boundary_detector, large_sliding_windows, mock_matplotlib, performance_recorder):
        """
        Performance test when multiple contours are found.
        """
        with patch('app.services.auroral_oval.boundary_detector.GRID_POINTS', 100), \
             patch('app.services.auroral_oval.boundary_detector.griddata') as mock_griddata:
            
            zi = np.random.uniform(0, 1, (100, 100))
            mock_griddata.return_value = zi
            
            # Mock multiple contour segments
            contour_segments = [
                np.random.uniform(-100, -60, (100, 2)),  # 100 points
                np.random.uniform(-100, -60, (50, 2)),   # 50 points
                np.random.uniform(-100, -60, (75, 2))    # 75 points
            ]
            mock_matplotlib.contour.return_value.allsegs = [contour_segments]
            
            @performance_recorder.measure_function("extract_boundary_multiple_contours", "BoundaryDetector")
            def timed_extraction():
                return boundary_detector.extract_boundary_contours(large_sliding_windows)
            
            boundary_data = timed_extraction()
            
            # Should have many boundary points (100 + 50 + 75 = 225)
            assert len(boundary_data['lon']) == 225
            assert len(boundary_data['lat']) == 225
            
            performance_recorder.save_to_history("multiple_contours_boundary_detection")