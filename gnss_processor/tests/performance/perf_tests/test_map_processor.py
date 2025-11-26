import pytest
import numpy as np
import h5py as h5
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.processors.map_processor import MapProcessor

class TestMapProcessorPerformance:
    """Performance tests for MapProcessor."""
    
    def test_performance_full_processing(self, map_processor, large_map_hdf5_file, mock_map_config, performance_recorder, tmp_path):
        """
        Performance test for complete map file processing.
        
        Measures execution time of processing large map files with multiple time points.
        """
        output_file = tmp_path / "performance_output.h5"
        
        with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
             patch('app.processors.map_processor.WINDOW_WIDTH', 10.0):
            
            @performance_recorder.measure_function("process_large_map_file", "MapProcessor")
            def timed_processing():
                return map_processor.process_map_file(
                    map_path=str(large_map_hdf5_file),
                    output_path=str(output_file)
                )
            
            result = timed_processing()
            
            # Verify processing completed
            assert result is None  # process_map_file returns None
            assert output_file.exists()
            
            # Record performance
            performance_recorder.save_to_history("large_map_processing")
    
    def test_performance_single_time_point_processing(self, map_processor, large_map_hdf5_file, mock_map_config, performance_recorder, tmp_path):
        """
        Performance test for processing single time point.
        
        Measures execution time of _process_single_time_point method.
        """
        output_file = tmp_path / "single_time_output.h5"
        
        with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
             patch('app.processors.map_processor.WINDOW_WIDTH', 10.0), \
             h5.File(large_map_hdf5_file, 'r') as input_file, \
             h5.File(output_file, 'w') as output_h5:
            
            data_group = input_file["data"]
            time_points = list(data_group.keys())
            
            # Test first time point
            time_point = time_points[0]
            
            @performance_recorder.measure_function("process_single_time_point", "MapProcessor")
            def timed_single_processing():
                return map_processor._process_single_time_point(
                    data_group, time_point, output_h5
                )
            
            result = timed_single_processing()
            
            # Verify processing completed
            assert result is None
            assert time_point in output_h5
            
            performance_recorder.save_to_history("single_time_point_processing")
    
    def test_performance_coordinate_filtering(self, map_processor, large_map_hdf5_file, performance_recorder):
        """
        Performance test for coordinate filtering.
        
        Measures execution time of _filter_coordinate_points method.
        """
        with h5.File(large_map_hdf5_file, 'r') as h5file:
            data_group = h5file["data"]
            time_point = list(data_group.keys())[0]
            points_group = data_group[time_point]
            
            @performance_recorder.measure_function("filter_coordinate_points", "MapProcessor")
            def timed_filtering():
                return map_processor._filter_coordinate_points(points_group)
            
            filtered_points = timed_filtering()
            
            # Verify filtering produced results
            assert 'lon' in filtered_points
            assert 'lat' in filtered_points
            assert 'vals' in filtered_points
            
            performance_recorder.save_to_history("coordinate_filtering")
    
    def test_performance_sliding_window_processing(self, map_processor, large_map_hdf5_file, mock_map_config, performance_recorder):
        """
        Performance test for sliding window processing.
        
        Measures execution time of sliding window segmentation with large datasets.
        """
        with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
             patch('app.processors.map_processor.WINDOW_WIDTH', 10.0), \
             h5.File(large_map_hdf5_file, 'r') as h5file:
            
            data_group = h5file["data"]
            time_point = list(data_group.keys())[0]
            points_group = data_group[time_point]
            
            # Get filtered points first
            filtered_points = map_processor._filter_coordinate_points(points_group)
            
            window_height = 100.0 / 10.0  # WINDOW_AREA / WINDOW_WIDTH
            
            @performance_recorder.measure_function("sliding_window_segmentation", "MapProcessor")
            def timed_sliding_window():
                return map_processor.sliding_window_processor.apply_sliding_window_segmentation(
                    filtered_points=filtered_points,
                    window_size=(window_height, 10.0),
                )
            
            sliding_windows = timed_sliding_window()
            
            # Verify sliding windows were created
            assert isinstance(sliding_windows, list)
            if len(sliding_windows) > 0:
                assert 'lon' in sliding_windows[0]
                assert 'lat' in sliding_windows[0]
                assert 'vals' in sliding_windows[0]
            
            performance_recorder.save_to_history("sliding_window_processing")
    
    def test_performance_boundary_detection(self, map_processor, large_map_hdf5_file, mock_map_config, performance_recorder):
        """
        Performance test for boundary detection.
        
        Measures execution time of boundary contour extraction.
        """
        with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
             patch('app.processors.map_processor.WINDOW_WIDTH', 10.0), \
             h5.File(large_map_hdf5_file, 'r') as h5file:
            
            data_group = h5file["data"]
            time_point = list(data_group.keys())[0]
            points_group = data_group[time_point]
            
            # Get filtered points and sliding windows
            filtered_points = map_processor._filter_coordinate_points(points_group)
            window_height = 100.0 / 10.0
            sliding_windows = map_processor.sliding_window_processor.apply_sliding_window_segmentation(
                filtered_points=filtered_points,
                window_size=(window_height, 10.0),
            )
            
            @performance_recorder.measure_function("boundary_detection", "MapProcessor")
            def timed_boundary_detection():
                return map_processor.boundary_detector.extract_boundary_contours(sliding_windows)
            
            boundary_data = timed_boundary_detection()
            
            # Verify boundary data structure
            assert 'lon' in boundary_data
            assert 'lat' in boundary_data
            
            performance_recorder.save_to_history("boundary_detection")
    
    def test_performance_clustering(self, map_processor, large_map_hdf5_file, mock_map_config, performance_recorder):
        """
        Performance test for boundary clustering.
        
        Measures execution time of cluster processing with boundary data.
        """
        with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
             patch('app.processors.map_processor.WINDOW_WIDTH', 10.0), \
             h5.File(large_map_hdf5_file, 'r') as h5file:
            
            data_group = h5file["data"]
            time_point = list(data_group.keys())[0]
            points_group = data_group[time_point]
            
            # Get all processed data up to clustering
            filtered_points = map_processor._filter_coordinate_points(points_group)
            window_height = 100.0 / 10.0
            sliding_windows = map_processor.sliding_window_processor.apply_sliding_window_segmentation(
                filtered_points=filtered_points,
                window_size=(window_height, 10.0),
            )
            boundary_data = map_processor.boundary_detector.extract_boundary_contours(sliding_windows)
            
            @performance_recorder.measure_function("boundary_clustering", "MapProcessor")
            def timed_clustering():
                return map_processor.cluster_processor.create_boundary_clusters(
                    lat_list=boundary_data['lat'],
                    lon_list=boundary_data['lon']
                )
            
            clusters = timed_clustering()
            
            # Clusters might be None if no valid boundaries found
            # Just verify the method completed
            
            performance_recorder.save_to_history("boundary_clustering")
    
    def test_stress_high_density_data(self, map_processor, mock_map_config, performance_recorder, tmp_path):
        """
        Stress test with extremely high density data.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            stress_file = f.name
        
        try:
            # Create extremely dense data
            with h5.File(stress_file, 'w') as h5file:
                data_group = h5file.create_group("data")
                time_group = data_group.create_group("stress_test")
                
                n_points = 50000  # Very high density
                lon = np.random.uniform(-120, -60, n_points)
                lat = np.random.uniform(50, 80, n_points)
                vals = np.random.uniform(0, 2, n_points)
                
                time_group.create_dataset('lon', data=lon)
                time_group.create_dataset('lat', data=lat)
                time_group.create_dataset('vals', data=vals)
            
            output_file = tmp_path / "stress_output.h5"
            
            with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
                 patch('app.processors.map_processor.WINDOW_WIDTH', 10.0):
                
                @performance_recorder.measure_function("stress_test_high_density", "MapProcessor")
                def timed_stress():
                    return map_processor.process_map_file(
                        map_path=stress_file,
                        output_path=str(output_file)
                    )
                
                result = timed_stress()
                assert result is None
                performance_recorder.save_to_history("high_density_stress")
        
        finally:
            if os.path.exists(stress_file):
                os.unlink(stress_file)
    
    def test_stress_multiple_time_points(self, map_processor, mock_map_config, performance_recorder, tmp_path):
        """
        Stress test with large number of time points.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            stress_file = f.name

        try:
            with h5.File(stress_file, 'w') as h5file:
                data_group = h5file.create_group("data")

                # Create many time points
                for i in range(100):  # 100 time points
                    time_point = f"2024-01-01 {i:02d}:00:00.000000"
                    time_group = data_group.create_group(time_point)

                    n_points = 1000
                    lon = np.random.uniform(-120, -60, n_points)
                    lat = np.random.uniform(50, 80, n_points)
                    vals = np.random.uniform(0, 2, n_points)

                    time_group.create_dataset('lon', data=lon)
                    time_group.create_dataset('lat', data=lat)
                    time_group.create_dataset('vals', data=vals)

            output_file = tmp_path / "multiple_times_output.h5"

            with patch('app.processors.map_processor.WINDOW_AREA', 100.0), \
                patch('app.processors.map_processor.WINDOW_WIDTH', 10.0), \
                patch('app.services.auroral_oval.boundary_detector.plt') as mock_plt:  # Mock matplotlib
                
                # Configure matplotlib mock
                mock_fig = Mock()
                mock_ax = Mock()
                mock_plt.figure.return_value = mock_fig
                mock_plt.subplots.return_value = (mock_fig, mock_ax)
                mock_plt.contour.return_value = Mock()

                @performance_recorder.measure_function("stress_test_multiple_times", "MapProcessor")
                def timed_multiple_times():
                    return map_processor.process_map_file(
                        map_path=stress_file,
                        output_path=str(output_file)
                    )

                result = timed_multiple_times()
                assert result is None
                performance_recorder.save_to_history("multiple_time_points_stress")

        finally:
            if os.path.exists(stress_file):
                os.unlink(stress_file)