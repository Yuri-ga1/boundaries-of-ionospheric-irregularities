import pytest
import numpy as np
import h5py as h5
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

@pytest.fixture
def mock_config():
    """
    Mock configuration for testing.
    
    Returns:
        Mock: Mocked configuration object
    """
    with patch('app.processors.simurg_hdf5_processor.LON_CONDITION', -60), \
         patch('app.processors.simurg_hdf5_processor.LAT_CONDITION', 40), \
         patch('app.processors.simurg_hdf5_processor.COORDINATE_BOUNDS') as mock_bounds, \
         patch('app.processors.simurg_hdf5_processor.TIME_DIFF_THRESHOLD_SECONDS', 1800), \
         patch('app.processors.simurg_hdf5_processor.MAP_PATH') as mock_map_path, \
         patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH') as mock_flybys_path, \
         patch('app.processors.simurg_hdf5_processor.logger') as mock_logger:
        
        # Правильная настройка COORDINATE_BOUNDS
        bounds_dict = {
            'min_lat': -90, 'max_lat': 90,
            'min_lon': -180, 'max_lon': 180
        }
        # Настраиваем мок так, чтобы он возвращал реальные значения при обращении по ключам
        mock_bounds.__getitem__.side_effect = bounds_dict.__getitem__

        FILES_PATH = 'files'
        MAP_PATH = os.path.join(FILES_PATH, "map")
        FLYBYS_PATH = os.path.join(FILES_PATH, "flybys")

        mock_map_path.return_value = MAP_PATH
        mock_flybys_path.return_value = FLYBYS_PATH
        
        yield {
            'lon_condition': -60,
            'lat_condition': 40,
            'bounds': mock_bounds,
            'time_threshold': 1800,
            'map_path': mock_map_path,
            'flybys_path': mock_flybys_path,
            'logger': mock_logger
        }

@pytest.fixture
def sample_hdf5_file():
    """
    Create a temporary HDF5 file with sample SIMuRG data structure.
    
    Returns:
        str: Path to the temporary HDF5 file
    """
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        file_path = f.name
    
    # Create sample HDF5 structure
    with h5.File(file_path, 'w') as h5file:
        # Create station groups
        for i, station in enumerate(['station1', 'station2']):
            station_group = h5file.create_group(station)
            station_group.attrs['lat'] = 60.0 + i * 5.0
            station_group.attrs['lon'] = 30.0 + i * 5.0
            station_group.attrs['latitude'] = 60.0 + i * 5.0
            station_group.attrs['longitude'] = 30.0 + i * 5.0
            station_group.attrs['station_name'] = station
            
            # Create satellite data for each station
            for sat in ['G01', 'G02']:
                sat_group = station_group.create_group(sat)
                
                # Create sample datasets
                n_points = 100
                timestamps = np.array([1609459200 + i * 300 for i in range(n_points)])  # 5 min intervals
                roti = np.random.uniform(0, 1, n_points)
                azimuth = np.random.uniform(0, 360, n_points)
                elevation = np.random.uniform(5, 90, n_points)
                
                sat_group.create_dataset('roti', data=roti)
                sat_group.create_dataset('azimuth', data=azimuth)
                sat_group.create_dataset('elevation', data=elevation)
                sat_group.create_dataset('timestamp', data=timestamps)
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def large_hdf5_file():
    """
    Create a large HDF5 file for performance testing.
    
    Returns:
        str: Path to the temporary large HDF5 file
    """
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        file_path = f.name
    
    # Create large HDF5 structure
    with h5.File(file_path, 'w') as h5file:
        # Create multiple stations
        for station_idx in range(5):
            station_name = f'station{station_idx}'
            station_group = h5file.create_group(station_name)
            station_group.attrs['lat'] = 60.0 + station_idx
            station_group.attrs['lon'] = 30.0 + station_idx
            
            # Create multiple satellites per station
            for sat_idx in range(10):
                sat_name = f'G{sat_idx:02d}'
                sat_group = station_group.create_group(sat_name)
                
                # Create large datasets
                n_points = 1000  # Large dataset for performance testing
                timestamps = np.array([1609459200 + i * 300 for i in range(n_points)])
                roti = np.random.uniform(0, 1, n_points)
                azimuth = np.random.uniform(0, 360, n_points)
                elevation = np.random.uniform(5, 90, n_points)
                
                sat_group.create_dataset('roti', data=roti)
                sat_group.create_dataset('azimuth', data=azimuth)
                sat_group.create_dataset('elevation', data=elevation)
                sat_group.create_dataset('timestamp', data=timestamps)
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def performance_recorder():
    """
    Fixture for performance recording in tests.
    
    Returns:
        PerformanceRecorder: Instance of performance recorder
    """
    from tests.performance.performance_recorder import PerformanceRecorder
    return PerformanceRecorder()

@pytest.fixture
def sample_output_files(tmp_path):
    """
    Create temporary output directories and file paths.
    
    Returns:
        dict: Dictionary with output paths
    """
    map_path = tmp_path / "maps"
    flybys_path = tmp_path / "flybys"
    map_path.mkdir(parents=True, exist_ok=True)
    flybys_path.mkdir(parents=True, exist_ok=True)
    
    return {
        'map_path': str(map_path),
        'flybys_path': str(flybys_path),
        'output_name': 'test_output.h5'
    }