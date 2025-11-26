import pytest
import numpy as np
from typing import Dict, List, Tuple
from unittest.mock import Mock, patch

from app.services.auroral_oval.sliding_window_processor import SlidingWindowProcessor
from tests.performance.performance_recorder import PerformanceRecorder

class TestSlidingWindowProcessorPerformance:
    """Performance tests for SlidingWindowProcessor."""
    
    @pytest.fixture
    def large_dataset(self):
        """
        Create a large dataset for performance testing.
        
        Returns:
            Dict[str, np.ndarray]: Large filtered points dataset
        """
        np.random.seed(42)  # For reproducible performance tests
        n_points = 10000
        return {
            'lon': np.random.uniform(0.0, 50.0, n_points),
            'lat': np.random.uniform(0.0, 50.0, n_points),
            'vals': np.random.uniform(0.0, 100.0, n_points)
        }
    
    @pytest.fixture
    def performance_processor(self):
        """
        Create processor with performance-optimized step sizes.
        
        Returns:
            SlidingWindowProcessor: Processor for performance tests
        """
        return SlidingWindowProcessor(lon_step=2.0, lat_step=2.0)
    
    def test_performance_sliding_window_segmentation_large_dataset(
        self, performance_processor, large_dataset, performance_recorder
    ):
        """
        Performance test for sliding window segmentation with large dataset.
        
        Measures execution time of the segmentation method with large input
        to establish performance baseline.
        """
        window_size = (5.0, 5.0)
        
        @performance_recorder.measure_function(
            "apply_sliding_window_segmentation_large", "SlidingWindowProcessor"
        )
        def timed_segmentation():
            return performance_processor.apply_sliding_window_segmentation(
                large_dataset, window_size
            )
        
        windows = timed_segmentation()
        
        # Verify results are correct
        assert len(windows) > 0
        for window in windows[:10]:  # Check first 10 windows
            assert 'lon' in window
            assert 'lat' in window
            assert 'vals' in window
        
        # Record performance
        performance_recorder.save_to_history("large_dataset_segmentation")
    
    def test_performance_window_mask_creation(self, performance_processor, performance_recorder):
        """
        Performance test for window mask creation.
        
        Measures execution time of mask creation with large arrays.
        """
        # Create large arrays
        n_points = 50000
        lon = np.random.uniform(0.0, 50.0, n_points)
        lat = np.random.uniform(0.0, 50.0, n_points)
        
        @performance_recorder.measure_function("create_window_mask_large", "SlidingWindowProcessor")
        def timed_mask_creation():
            return performance_processor._create_window_mask(
                lon, lat, 10.0, 10.0, (5.0, 5.0)
            )
        
        mask = timed_mask_creation()
        
        # Verify mask properties
        assert mask.shape == (n_points,)
        assert mask.dtype == bool
        
        performance_recorder.save_to_history("window_mask_creation")
    
    def test_performance_window_data_creation(self, performance_processor, performance_recorder):
        """
        Performance test for window data creation.
        
        Measures execution time of window data computation
        with large value arrays.
        """
        # Create large arrays
        n_points = 100000
        values = np.random.uniform(0.0, 100.0, n_points)
        mask = np.random.choice([True, False], n_points, p=[0.1, 0.9])  # 10% True
        
        @performance_recorder.measure_function("create_window_data_large", "SlidingWindowProcessor")
        def timed_data_creation():
            return performance_processor._create_window_data(
                values, mask, 10.0, 10.0, (5.0, 5.0)
            )
        
        window_data = timed_data_creation()
        
        # Verify window data structure
        assert 'lon' in window_data
        assert 'lat' in window_data
        assert 'vals' in window_data
        
        performance_recorder.save_to_history("window_data_creation")
    
    def test_performance_different_window_sizes(self, performance_processor, large_dataset, performance_recorder):
        """
        Performance test with different window sizes.
        
        Measures how window size affects performance
        for comparison and optimization purposes.
        """
        window_sizes = [(2.0, 2.0), (5.0, 5.0), (10.0, 10.0)]
        
        for i, window_size in enumerate(window_sizes):
            @performance_recorder.measure_function(
                f"segmentation_window_size_{i}", "SlidingWindowProcessor"
            )
            def timed_segmentation():
                return performance_processor.apply_sliding_window_segmentation(
                    large_dataset, window_size
                )
            
            windows = timed_segmentation()
            assert len(windows) > 0
        
        performance_recorder.save_to_history("different_window_sizes")

