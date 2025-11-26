import pytest
import numpy as np
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from shapely.geometry import Point, Polygon
import tempfile
import os

from app.services.auroral_oval.crossing_detector import BoundaryCrossingDetector


class TestBoundaryCrossingDetector:
    """Test cases for BoundaryCrossingDetector functionality."""
    
    @pytest.fixture
    def crossing_detector(self):
        """Create a BoundaryCrossingDetector instance for testing."""
        return BoundaryCrossingDetector(time_threshold_seconds=10800)  # 3 hours
    
    @pytest.fixture
    def sample_boundaries(self):
        """Create sample boundaries data for testing."""
        return {
            '2024-01-01 00:00:00.000000': {
                'relation': 'single-cluster',
                'border1': [[-100, 65], [-90, 66], [-80, 65], [-90, 64]]
            },
            '2024-01-01 01:00:00.000000': {
                'relation': 'single-cluster', 
                'border1': [[-105, 66], [-95, 67], (-85, 66), (-95, 65)]
            },
            '2024-01-01 02:00:00.000000': {
                'relation': 'single-cluster',
                'border1': [[-110, 67], [-100, 68], (-90, 67), (-100, 66)]
            }
        }
    
    @pytest.fixture
    def sample_satellites(self):
        """Create sample satellites data for testing."""
        return {
            '2024-01-01 00:00:00.000000': {
                'station1_G01': {'lon': -95.0, 'lat': 66.0},  # Inside boundary
                'station1_G02': {'lon': -120.0, 'lat': 60.0}, # Outside boundary
                'station2_G01': {'lon': -85.0, 'lat': 66.0}   # Inside boundary
            },
            '2024-01-01 01:00:00.000000': {
                'station1_G01': {'lon': -100.0, 'lat': 60.0}, # Moved outside (exit event)
                'station1_G02': {'lon': -95.0, 'lat': 66.0},  # Moved inside (enter event)
                'station2_G01': {'lon': -90.0, 'lat': 67.0}   # Still inside
            },
            '2024-01-01 02:00:00.000000': {
                'station1_G01': {'lon': -110.0, 'lat': 65.0}, # Still outside
                'station1_G02': {'lon': -100.0, 'lat': 68.0}, # Still inside
                'station2_G01': {'lon': -120.0, 'lat': 60.0}  # Moved outside (exit event)
            }
        }
    
    def test_initialization(self, crossing_detector):
        """Test that BoundaryCrossingDetector initializes correctly."""
        assert crossing_detector.time_threshold == 10800
        assert hasattr(crossing_detector, 'polygon_plotter')
    
    def test_detect_satellite_crossings_none_boundaries(self, crossing_detector, sample_satellites):
        """Test detection with None boundaries."""
        result = crossing_detector.detect_satellite_crossings(None, sample_satellites)
        assert result == {}
    
    def test_detect_satellite_crossings_empty_boundaries(self, crossing_detector, sample_satellites):
        """Test detection with empty boundaries."""
        result = crossing_detector.detect_satellite_crossings({}, sample_satellites)
        assert result == {}
    
    def test_detect_satellite_crossings_single_time_point(self, crossing_detector):
        """Test detection with only one time point (insufficient for detection)."""
        single_time_boundaries = {
            '2024-01-01 00:00:00.000000': {'relation': 'single-cluster', 'border1': [[-100, 65], [-90, 66]]}
        }
        satellites = {
            '2024-01-01 00:00:00.000000': {'station1_G01': {'lon': -95.0, 'lat': 66.0}}
        }
        
        with patch.object(crossing_detector.polygon_plotter, 'compute_polygons') as mock_compute:
            mock_compute.return_value = [None, Polygon([(-100, 65), (-90, 66), (-80, 65)]), None]
            
            result = crossing_detector.detect_satellite_crossings(single_time_boundaries, satellites)
            
            assert result == {}
    
    def test_detect_satellite_crossings_with_events(self, crossing_detector, sample_boundaries, sample_satellites):
        """Test detection with actual crossing events."""
        with patch.object(crossing_detector.polygon_plotter, 'compute_polygons') as mock_compute:
            def mock_compute_polygons(boundaries, time_key):
                if time_key == '2024-01-01 00:00:00.000000':
                    return [None, Polygon([(-100, 65), (-90, 66), (-80, 65), (-90, 64)]), None]
                elif time_key == '2024-01-01 01:00:00.000000':
                    return [None, Polygon([(-105, 66), (-95, 67), (-85, 66), (-95, 65)]), None]
                elif time_key == '2024-01-01 02:00:00.000000':
                    return [None, Polygon([(-110, 67), (-100, 68), (-90, 67), (-100, 66)]), None]
                else:
                    return [None, None, None]
            
            mock_compute.side_effect = mock_compute_polygons
            
            result = crossing_detector.detect_satellite_crossings(sample_boundaries, sample_satellites)
            
            # Should detect at least some crossing events
            assert isinstance(result, dict)
            
            # Check that we have at least one station with events
            assert len(result) > 0
            
            # Check that station1 exists and has at least one satellite with events
            assert 'station1' in result
            assert len(result['station1']) > 0
            
            # Verify that we have the expected satellite with events
            # Based on the test data, station1_G02 should have events
            assert 'G02' in result['station1']
            
            station1_g02_events = result['station1']['G02']
            assert len(station1_g02_events) > 0
            assert len(station1_g02_events[0]) > 0
            
            # Verify the first event for station1_G02
            first_event = station1_g02_events[0][0]
            assert 'time' in first_event
            assert 'event' in first_event
            assert first_event['event'] in ['entered', 'exited']
    
    def test_detect_satellite_crossings_no_events(self, crossing_detector):
        """Test detection when no crossing events occur."""
        boundaries = {
            '2024-01-01 00:00:00.000000': {'relation': 'single-cluster', 'border1': [[-100, 65], [-90, 66]]},
            '2024-01-01 01:00:00.000000': {'relation': 'single-cluster', 'border1': [[-105, 66], [-95, 67]]}
        }
        
        satellites = {
            '2024-01-01 00:00:00.000000': {
                'station1_G01': {'lon': -95.0, 'lat': 66.0}
            },
            '2024-01-01 01:00:00.000000': {
                'station1_G01': {'lon': -100.0, 'lat': 66.5}
            }
        }
        
        with patch.object(crossing_detector.polygon_plotter, 'compute_polygons') as mock_compute:
            mock_compute.return_value = [None, Polygon([(-100, 65), (-90, 66), (-80, 65)]), None]
            
            result = crossing_detector.detect_satellite_crossings(boundaries, satellites)
            
            assert result == {}
    
    def test_store_crossing_event_new_satellite(self, crossing_detector):
        """Test storing crossing event for a new satellite."""
        crossings = {}
        
        crossing_detector._store_crossing_event(
            crossings, 'station1_G01', '2024-01-01 01:00:00.000000', 'entered'
        )
        
        assert 'station1' in crossings
        assert 'G01' in crossings['station1']
        assert len(crossings['station1']['G01']) == 1
        assert len(crossings['station1']['G01'][0]) == 1
        assert crossings['station1']['G01'][0][0]['time'] == '2024-01-01 01:00:00.000000'
        assert crossings['station1']['G01'][0][0]['event'] == 'entered'
    
    def test_store_crossing_event_existing_satellite(self, crossing_detector):
        """Test storing crossing event for an existing satellite."""
        crossings = {
            'station1': {
                'G01': [[
                    {'time': '2024-01-01 00:30:00.000000', 'event': 'entered'}
                ]]
            }
        }
        
        crossing_detector._store_crossing_event(
            crossings, 'station1_G01', '2024-01-01 01:00:00.000000', 'exited'
        )
        
        assert len(crossings['station1']['G01']) == 1
        assert len(crossings['station1']['G01'][0]) == 2
        assert crossings['station1']['G01'][0][1]['time'] == '2024-01-01 01:00:00.000000'
        assert crossings['station1']['G01'][0][1]['event'] == 'exited'
    
    def test_store_crossing_event_time_threshold(self, crossing_detector):
        """Test that events beyond time threshold create new groups."""
        crossings = {
            'station1': {
                'G01': [[
                    {'time': '2024-01-01 00:00:00.000000', 'event': 'entered'}
                ]]
            }
        }
        
        crossing_detector._store_crossing_event(
            crossings, 'station1_G01', '2024-01-01 04:00:00.000000', 'exited'
        )
        
        assert len(crossings['station1']['G01']) == 2
        assert len(crossings['station1']['G01'][0]) == 1
        assert len(crossings['station1']['G01'][1]) == 1
        assert crossings['station1']['G01'][1][0]['time'] == '2024-01-01 04:00:00.000000'
