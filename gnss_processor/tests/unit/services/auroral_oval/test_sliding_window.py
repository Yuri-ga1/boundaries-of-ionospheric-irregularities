import pytest
import numpy as np
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

from app.services.auroral_oval.sliding_window_processor import SlidingWindowProcessor
from tests.performance.performance_recorder import PerformanceRecorder


class TestSlidingWindowProcessor:
    """Test cases for SlidingWindowProcessor functionality."""
    
    @pytest.fixture
    def sliding_window_processor(self):
        """
        Create a SlidingWindowProcessor instance for testing.
        
        Returns:
            SlidingWindowProcessor: Processor instance
        """
        return SlidingWindowProcessor(lon_step=1.0, lat_step=1.0)
    
    @pytest.fixture
    def sample_filtered_points(self):
        """
        Create sample filtered points data for testing.
        
        Returns:
            Dict[str, np.ndarray]: Sample filtered points
        """
        return {
            'lon': np.array([10.0, 11.0, 12.0, 13.0, 14.0]),
            'lat': np.array([50.0, 51.0, 52.0, 53.0, 54.0]),
            'vals': np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        }
    
    @pytest.fixture
    def dense_filtered_points(self):
        """
        Create dense filtered points for testing window segmentation.
        
        Returns:
            Dict[str, np.ndarray]: Dense filtered points
        """
        np.random.seed(42)  # For reproducible tests
        n_points = 100
        return {
            'lon': np.random.uniform(10.0, 20.0, n_points),
            'lat': np.random.uniform(50.0, 60.0, n_points),
            'vals': np.random.uniform(0.0, 10.0, n_points)
        }

    def test_apply_sliding_window_segmentation_no_points(self, sliding_window_processor):
        """
        Test sliding window segmentation with no input points.

        Verifies that the method handles empty input gracefully
        and returns an empty list.
        """
        empty_points = {
            'lon': np.array([]),
            'lat': np.array([]),
            'vals': np.array([])
        }
        window_size = (2.0, 2.0)

        # This should not raise an error and return empty list
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            empty_points, window_size
        )

        assert windows == []

    def test_apply_sliding_window_segmentation_partially_empty(self, sliding_window_processor):
        """
        Test sliding window segmentation with partially empty data.
        
        Verifies that the method handles cases where some arrays are empty.
        """
        # Test with empty longitude array
        empty_lon_points = {
            'lon': np.array([]),
            'lat': np.array([50.0, 51.0]),
            'vals': np.array([1.0, 2.0])
        }
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            empty_lon_points, (2.0, 2.0)
        )
        assert windows == []

        # Test with empty latitude array
        empty_lat_points = {
            'lon': np.array([10.0, 11.0]),
            'lat': np.array([]),
            'vals': np.array([1.0, 2.0])
        }
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            empty_lat_points, (2.0, 2.0)
        )
        assert windows == []

        # Test with empty values array
        empty_vals_points = {
            'lon': np.array([10.0, 11.0]),
            'lat': np.array([50.0, 51.0]),
            'vals': np.array([])
        }
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            empty_vals_points, (2.0, 2.0)
        )
        assert windows == []

    def test_initialization(self, sliding_window_processor):
        """
        Test that SlidingWindowProcessor initializes correctly.
        
        Verifies that the processor properly initializes with step parameters
        and sets up necessary attributes.
        """
        assert sliding_window_processor.lon_step == 1.0
        assert sliding_window_processor.lat_step == 1.0
    
    def test_initialization_with_different_steps(self):
        """
        Test initialization with different step values.
        
        Verifies that the processor accepts and stores different
        longitude and latitude step values.
        """
        processor = SlidingWindowProcessor(lon_step=2.5, lat_step=1.5)
        assert processor.lon_step == 2.5
        assert processor.lat_step == 1.5
    
    def test_create_window_mask_single_point_inside(self, sliding_window_processor):
        """
        Test window mask creation with a single point inside the window.
        
        Verifies that the mask correctly identifies points within
        the specified window boundaries.
        """
        lon = np.array([15.0])
        lat = np.array([55.0])
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        mask = sliding_window_processor._create_window_mask(
            lon, lat, current_lon, current_lat, window_size
        )
        
        assert mask.shape == (1,)
        assert mask[0] == True
    
    def test_create_window_mask_single_point_outside(self, sliding_window_processor):
        """
        Test window mask creation with a single point outside the window.
        
        Verifies that the mask correctly excludes points outside
        the specified window boundaries.
        """
        lon = np.array([25.0])  # Outside window (10-20)
        lat = np.array([55.0])
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        mask = sliding_window_processor._create_window_mask(
            lon, lat, current_lon, current_lat, window_size
        )
        
        assert mask.shape == (1,)
        assert mask[0] == False
    
    def test_create_window_mask_multiple_points(self, sliding_window_processor):
        """
        Test window mask creation with multiple points.
        
        Verifies that the mask correctly identifies which points
        are inside and which are outside the window.
        """
        lon = np.array([12.0, 18.0, 22.0, 8.0])  # Inside, inside, outside, outside
        lat = np.array([52.0, 58.0, 55.0, 55.0])
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        mask = sliding_window_processor._create_window_mask(
            lon, lat, current_lon, current_lat, window_size
        )
        
        expected_mask = np.array([True, True, False, False])
        np.testing.assert_array_equal(mask, expected_mask)
    
    def test_create_window_mask_edge_cases(self, sliding_window_processor):
        """
        Test window mask creation with edge cases.
        
        Verifies behavior with points exactly on window boundaries
        and empty input arrays.
        """
        # Test with empty arrays
        lon = np.array([])
        lat = np.array([])
        mask = sliding_window_processor._create_window_mask(
            lon, lat, 10.0, 50.0, (10.0, 10.0)
        )
        assert mask.shape == (0,)
        
        # Test with points on boundaries
        lon = np.array([10.0, 20.0])  # On lower bound, on upper bound (excluded)
        lat = np.array([50.0, 60.0])  # On lower bound, on upper bound (excluded)
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        mask = sliding_window_processor._create_window_mask(
            lon, lat, current_lon, current_lat, window_size
        )
        
        # First point should be included, second excluded (upper bound is exclusive)
        expected_mask = np.array([True, False])
        np.testing.assert_array_equal(mask, expected_mask)
    
    def test_create_window_data_basic(self, sliding_window_processor):
        """
        Test window data creation with basic input.
        
        Verifies that window data is correctly computed including
        center coordinates and median values.
        """
        values = np.array([1.0, 2.0, 3.0, 4.0, 5.0])
        mask = np.array([True, True, False, True, False])  # Values 1, 2, 4
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        window_data = sliding_window_processor._create_window_data(
            values, mask, current_lon, current_lat, window_size
        )
        
        expected_center_lon = 15.0  # 10 + 10/2
        expected_center_lat = 55.0  # 50 + 10/2
        expected_median = 2.0  # median of [1, 2, 4]
        
        assert window_data['lon'] == expected_center_lon
        assert window_data['lat'] == expected_center_lat
        assert window_data['vals'] == expected_median
    
    def test_create_window_data_single_point(self, sliding_window_processor):
        """
        Test window data creation with a single point.
        
        Verifies that median calculation works correctly
        with single-element arrays.
        """
        values = np.array([7.5])
        mask = np.array([True])
        current_lon = 5.0
        current_lat = 45.0
        window_size = (5.0, 5.0)
        
        window_data = sliding_window_processor._create_window_data(
            values, mask, current_lon, current_lat, window_size
        )
        
        expected_center_lon = 7.5  # 5 + 5/2
        expected_center_lat = 47.5  # 45 + 5/2
        
        assert window_data['lon'] == expected_center_lon
        assert window_data['lat'] == expected_center_lat
        assert window_data['vals'] == 7.5
    
    def test_create_window_data_empty_mask(self, sliding_window_processor):
        """
        Test window data creation with empty mask.
        
        Verifies that the method handles empty masks correctly
        by computing median of empty slice.
        """
        values = np.array([1.0, 2.0, 3.0])
        mask = np.array([False, False, False])  # No points selected
        current_lon = 10.0
        current_lat = 50.0
        window_size = (10.0, 10.0)
        
        window_data = sliding_window_processor._create_window_data(
            values, mask, current_lon, current_lat, window_size
        )
        
        # Should still compute center coordinates
        assert window_data['lon'] == 15.0
        assert window_data['lat'] == 55.0
        # Median of empty array should be nan
        assert np.isnan(window_data['vals'])
    
    def test_apply_sliding_window_segmentation_basic(self, sliding_window_processor, sample_filtered_points):
        """
        Test basic sliding window segmentation.
        
        Verifies that the segmentation method produces the expected
        number of windows and correct data structure.
        """
        window_size = (2.0, 2.0)
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            sample_filtered_points, window_size
        )
        
        # Should produce at least one window
        assert len(windows) > 0
        
        # Check structure of each window
        for window in windows:
            assert 'lon' in window
            assert 'lat' in window
            assert 'vals' in window
            assert isinstance(window['lon'], float)
            assert isinstance(window['lat'], float)
            assert isinstance(window['vals'], float)
    
    def test_apply_sliding_window_segmentation_different_step_sizes(self):
        """
        Test sliding window segmentation with different step sizes.
        
        Verifies that different longitude and latitude step sizes
        affect the number and density of generated windows.
        """
        # Small step size should produce more windows
        small_step_processor = SlidingWindowProcessor(lon_step=0.5, lat_step=0.5)
        large_step_processor = SlidingWindowProcessor(lon_step=2.0, lat_step=2.0)
        
        points = {
            'lon': np.array([10.0, 11.0, 12.0, 13.0]),
            'lat': np.array([50.0, 51.0, 52.0, 53.0]),
            'vals': np.array([1.0, 2.0, 3.0, 4.0])
        }
        window_size = (2.0, 2.0)
        
        small_step_windows = small_step_processor.apply_sliding_window_segmentation(
            points, window_size
        )
        large_step_windows = large_step_processor.apply_sliding_window_segmentation(
            points, window_size
        )
        
        # Small step should produce more windows than large step
        assert len(small_step_windows) > len(large_step_windows)
    
    def test_apply_sliding_window_segmentation_window_coverage(self, sliding_window_processor, dense_filtered_points):
        """
        Test that sliding windows cover the entire data range.
        
        Verifies that windows are generated to cover the complete
        spatial extent of the input data.
        """
        window_size = (3.0, 3.0)
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            dense_filtered_points, window_size
        )
        
        # Should have multiple windows
        assert len(windows) > 1
        
        # Extract window centers
        window_lons = [window['lon'] for window in windows]
        window_lats = [window['lat'] for window in windows]
        
        # Window centers should cover the data range
        data_lon_min, data_lon_max = np.min(dense_filtered_points['lon']), np.max(dense_filtered_points['lon'])
        data_lat_min, data_lat_max = np.min(dense_filtered_points['lat']), np.max(dense_filtered_points['lat'])
        
        assert min(window_lons) <= data_lon_min + window_size[1] / 2
        assert max(window_lons) >= data_lon_max - window_size[1] / 2
        assert min(window_lats) <= data_lat_min + window_size[0] / 2
        assert max(window_lats) >= data_lat_max - window_size[0] / 2
    
    def test_apply_sliding_window_segmentation_median_calculation(self, sliding_window_processor):
        """
        Test that median values are correctly calculated for windows.
        
        Verifies that the median computation for each window
        correctly represents the central tendency of values.
        """
        # Create points with known median
        points = {
            'lon': np.array([10.0, 10.1, 10.2, 15.0, 15.1]),  # Two distinct groups
            'lat': np.array([50.0, 50.1, 50.2, 55.0, 55.1]),
            'vals': np.array([1.0, 2.0, 3.0, 10.0, 20.0])    # Medians: 2.0 and 15.0
        }
        window_size = (1.0, 1.0)
        
        windows = sliding_window_processor.apply_sliding_window_segmentation(
            points, window_size
        )
        
        # Should create at least two windows
        assert len(windows) >= 2
        
        # Find windows and check their median values
        for window in windows:
            if 9.5 <= window['lon'] <= 11.5 and 49.5 <= window['lat'] <= 51.5:
                # First group window
                assert window['vals'] == 2.0  # median of [1, 2, 3]
            elif 14.5 <= window['lon'] <= 16.5 and 54.5 <= window['lat'] <= 56.5:
                # Second group window
                assert window['vals'] == 15.0  # median of [10, 20]
