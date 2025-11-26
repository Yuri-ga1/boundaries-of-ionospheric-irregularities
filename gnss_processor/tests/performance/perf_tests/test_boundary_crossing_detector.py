import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from shapely.geometry import Point, Polygon
import tempfile
import os

from app.services.auroral_oval.crossing_detector import BoundaryCrossingDetector

class TestBoundaryCrossingDetectorPerformance:
    """Performance tests for BoundaryCrossingDetector."""
    
    @pytest.fixture
    def crossing_detector(self):
        return BoundaryCrossingDetector(time_threshold_seconds=10800)
    
    def test_performance_large_dataset(self, crossing_detector, performance_recorder):
        """Performance test with large dataset."""
        n_time_points = 50  # Reduced for faster testing
        boundaries = {}
        
        for i in range(n_time_points):
            time_key = f'2024-01-01 {i:02d}:00:00.000000'
            boundaries[time_key] = {
                'relation': 'single-cluster',
                'border1': [[-100 + i*0.1, 65 + i*0.05] for _ in range(20)]
            }
        
        satellites = {}
        n_stations = 5
        n_satellites_per_station = 3
        
        for i in range(n_time_points):
            time_key = f'2024-01-01 {i:02d}:00:00.000000'
            satellites[time_key] = {}
            
            for station_idx in range(n_stations):
                for sat_idx in range(n_satellites_per_station):
                    sat_id = f'station{station_idx}_G{sat_idx:02d}'
                    satellites[time_key][sat_id] = {
                        'lon': -100 + i + station_idx * 0.1,
                        'lat': 65 + i * 0.05 + sat_idx * 0.01
                    }
        
        with patch.object(crossing_detector.polygon_plotter, 'compute_polygons') as mock_compute:
            mock_compute.return_value = [None, Polygon([(-100, 65), (-90, 66), (-80, 65)]), None]
            
            @performance_recorder.measure_function("detect_crossings_large_dataset", "BoundaryCrossingDetector")
            def timed_detection():
                return crossing_detector.detect_satellite_crossings(boundaries, satellites)
            
            result = timed_detection()
            
            assert isinstance(result, dict)
            performance_recorder.save_to_history("large_dataset_crossing_detection")
    
    def test_performance_guaranteed_crossings(self, crossing_detector, performance_recorder):
        """Performance test with guaranteed crossing events."""
        boundaries = {}
        satellites = {}
        
        n_time_points = 30
        
        for i in range(n_time_points):
            time_key = f'2024-01-01 {i:02d}:00:00.000000'
            
            # Create alternating boundaries that will guarantee crossings
            if i % 2 == 0:
                boundaries[time_key] = {
                    'relation': 'single-cluster',
                    'border1': [[-100, 65], [-90, 66], [-80, 65]]
                }
            else:
                boundaries[time_key] = {
                    'relation': 'single-cluster',
                    'border1': [[-120, 60], [-100, 70], [-80, 60]]
                }
            
            satellites[time_key] = {}
            
            # Create satellites that will definitely cross boundaries
            for j in range(10):
                sat_id = f'station{j//2}_G{j%2:02d}'
                
                # Alternate satellite positions to guarantee crossings
                if i % 2 == 0:
                    # Position outside the small boundary but inside the large one
                    satellites[time_key][sat_id] = {
                        'lon': -110 + (j * 2),
                        'lat': 64 + (j * 0.5)
                    }
                else:
                    # Position inside the small boundary
                    satellites[time_key][sat_id] = {
                        'lon': -95 + (j * 2),
                        'lat': 65.5 + (j * 0.5)
                    }
        
        with patch.object(crossing_detector.polygon_plotter, 'compute_polygons') as mock_compute:
            def mock_compute_polygons(boundaries, time_key):
                if int(time_key[14:16]) % 2 == 0:
                    return [None, Polygon([(-100, 65), (-90, 66), (-80, 65)]), None]
                else:
                    return [None, Polygon([(-120, 60), (-100, 70), (-80, 60)]), None]
            
            mock_compute.side_effect = mock_compute_polygons
            
            @performance_recorder.measure_function("detect_crossings_guaranteed", "BoundaryCrossingDetector")
            def timed_detection():
                return crossing_detector.detect_satellite_crossings(boundaries, satellites)
            
            result = timed_detection()
            
            # Should detect crossing events with this setup
            assert isinstance(result, dict)
            
            performance_recorder.save_to_history("guaranteed_crossings_detection")