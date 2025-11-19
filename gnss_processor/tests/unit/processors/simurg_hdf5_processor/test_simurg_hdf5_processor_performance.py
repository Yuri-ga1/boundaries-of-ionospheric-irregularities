import pytest
import numpy as np
import h5py as h5
import os
import tempfile
from unittest.mock import Mock, patch

from app.processors.simurg_hdf5_processor import SimurgHDF5Processor


class TestSimurgHDF5ProcessorPerformance:
    """Performance tests for SimurgHDF5Processor."""
    
    def test_performance_file_processing(self, large_hdf5_file, mock_config, performance_recorder, tmp_path):
        """
        Performance test for complete file processing.
        
        Measures execution time of the main process method
        to establish performance baseline for large files.
        """
        maps_dir = tmp_path / "maps"
        flybys_dir = tmp_path / "flybys"
        maps_dir.mkdir(parents=True, exist_ok=True)
        flybys_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
             patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)), \
             patch('app.processors.simurg_hdf5_processor.SatelliteDataProcessor') as mock_processor_class:
            
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            def mock_apply_filters(roti, elevations, timestamps, latitudes, longitudes):
                valid_indices = elevations > 30
                return {
                    'roti': roti[valid_indices],
                    'timestamps': timestamps[valid_indices],
                    'latitudes': latitudes[valid_indices],
                    'longitudes': longitudes[valid_indices]
                }
            
            mock_processor.calculate_satellite_coordinates.return_value = (
                np.random.uniform(50, 70, 1000),
                np.random.uniform(20, 40, 1000)
            )
            mock_processor.apply_data_filters.side_effect = mock_apply_filters
            
            with SimurgHDF5Processor(large_hdf5_file) as processor:
                @performance_recorder.measure_function("process_large_file", "SimurgHDF5Processor")
                def timed_processing():
                    return processor.process('performance_test.h5')
                
                result = timed_processing()
                
                assert result is None
                
                performance_recorder.save_to_history("large_file_processing")
    
    def test_performance_coordinate_extraction(self, large_hdf5_file, mock_config, performance_recorder, tmp_path):
        """
        Performance test for station coordinate extraction.
        
        Measures execution time of coordinate extraction from
        multiple stations in a large file.
        """
        maps_dir = tmp_path / "maps"
        flybys_dir = tmp_path / "flybys"
        maps_dir.mkdir(parents=True, exist_ok=True)
        flybys_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
             patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)):
            
            with SimurgHDF5Processor(large_hdf5_file) as processor:
                @performance_recorder.measure_function("extract_all_coordinates", "SimurgHDF5Processor")
                def timed_extraction():
                    for station_name in processor.file:
                        processor._extract_station_coordinates(station_name)
                    return len(processor.stations_coords)
                
                station_count = timed_extraction()
                
                assert station_count == 5
                performance_recorder.save_to_history("coordinate_extraction")
    
    def test_performance_flyby_segmentation(self, large_hdf5_file, mock_config, performance_recorder, tmp_path):
        """
        Performance test for flyby segmentation.
        
        Measures execution time of segmenting large satellite
        datasets into flybys.
        """
        maps_dir = tmp_path / "maps"
        flybys_dir = tmp_path / "flybys"
        maps_dir.mkdir(parents=True, exist_ok=True)
        flybys_dir.mkdir(parents=True, exist_ok=True)
        
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
             patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)):
            
            with SimurgHDF5Processor(large_hdf5_file) as processor:
                n_points = 10000
                timestamps = np.array([1609459200 + i * 300 for i in range(n_points)])
                timestamps[5000:6000] += 3600
                
                roti = np.random.uniform(0, 1, n_points)
                latitudes = np.random.uniform(50, 70, n_points)
                longitudes = np.random.uniform(20, 40, n_points)
                
                @performance_recorder.measure_function("segment_large_flyby", "SimurgHDF5Processor")
                def timed_segmentation():
                    processor._split_satellite_data_into_flybys(
                        'test_station', 'G01', roti, timestamps, latitudes, longitudes
                    )
                    return len(processor.flybys['test_station']['G01'])
                
                flyby_count = timed_segmentation()
                
                assert flyby_count > 1
                performance_recorder.save_to_history("flyby_segmentation")
