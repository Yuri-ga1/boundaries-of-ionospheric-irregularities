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


@pytest.fixture
def map_processor():
    """
    Create a MapProcessor instance for testing.
    """
    from app.processors.map_processor import MapProcessor
    
    processor = MapProcessor(
        lon_condition=-60,
        lat_condition=40,
        segment_lon_step=5.0,
        segment_lat_step=5.0,
        boundary_condition=0.5
    )
    
    return processor

@pytest.fixture
def sample_map_hdf5_file():
    """
    Create a temporary HDF5 file with sample map data structure.
    """
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        file_path = f.name
    
    # Create sample HDF5 structure for map data
    with h5.File(file_path, 'w') as h5file:
        data_group = h5file.create_group("data")
        
        # Create multiple time points
        time_points = ['2024-01-01 00:00:00.000000', '2024-01-01 00:05:00.000000']
        
        for time_point in time_points:
            time_group = data_group.create_group(time_point)
            
            # Create sample coordinate data
            n_points = 50
            lon = np.random.uniform(-180, 180, n_points)
            lat = np.random.uniform(40, 90, n_points)  # Focus on northern hemisphere
            vals = np.random.uniform(0, 2, n_points)   # ROTI values
            
            time_group.create_dataset('lon', data=lon)
            time_group.create_dataset('lat', data=lat)
            time_group.create_dataset('vals', data=vals)
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def mock_map_config():
    """
    Mock configuration for MapProcessor testing.
    """
    with patch('app.processors.map_processor.WINDOW_AREA') as mock_area, \
         patch('app.processors.map_processor.WINDOW_WIDTH') as mock_width, \
         patch('app.processors.map_processor.logger') as mock_logger:
        
        mock_area.return_value = 100.0
        mock_width.return_value = 10.0
        
        yield {
            'window_area': mock_area,
            'window_width': mock_width,
            'logger': mock_logger
        }

@pytest.fixture
def large_map_hdf5_file():
    """
    Create a large HDF5 file with extensive map data for performance testing.
    """
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        file_path = f.name
    
    # Create large HDF5 structure for performance testing
    with h5.File(file_path, 'w') as h5file:
        data_group = h5file.create_group("data")
        
        # Create multiple time points for comprehensive testing
        n_time_points = 24  # 24 time points (e.g., hourly data)
        n_points_per_time = 5000  # Large number of points per time point
        
        for i in range(n_time_points):
            time_point = f"2024-01-01 {i:02d}:00:00.000000"
            time_group = data_group.create_group(time_point)
            
            # Create realistic coordinate data for performance testing
            # Focus on northern hemisphere where auroral oval processing occurs
            lon = np.random.uniform(-180, 180, n_points_per_time)
            lat = np.random.uniform(40, 90, n_points_per_time)
            
            # Create realistic ROTI values with some structure
            # Higher values near typical auroral oval regions
            base_vals = np.random.uniform(0, 1, n_points_per_time)
            # Add some spatial correlation to simulate real data
            auroral_mask = (lat > 60) & (lat < 75) & ((lon > -150) | (lon < 30))
            base_vals[auroral_mask] += np.random.uniform(0, 1, np.sum(auroral_mask))
            
            vals = np.clip(base_vals, 0, 2)
            
            time_group.create_dataset('lon', data=lon)
            time_group.create_dataset('lat', data=lat)
            time_group.create_dataset('vals', data=vals)
    
    yield file_path
    
    # Cleanup
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def complex_map_hdf5_file():
    """
    Create a complex HDF5 file with challenging data patterns for stress testing.
    """
    with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
        file_path = f.name
    
    with h5.File(file_path, 'w') as h5file:
        data_group = h5file.create_group("data")
        
        # Create time points with different data characteristics
        time_configs = [
            ("dense_data", 10000, 0.1),      # Very dense data
            ("sparse_data", 100, 0.8),       # Very sparse data
            ("high_values", 2000, 0.3),      # Mostly high ROTI values
            ("low_values", 2000, 0.01),      # Mostly low ROTI values
            ("mixed_pattern", 5000, 0.5),    # Mixed pattern
        ]
        
        for time_name, n_points, value_scale in time_configs:
            time_group = data_group.create_group(time_name)
            
            # Create specialized data patterns
            if time_name == "dense_data":
                lon = np.random.uniform(-120, -60, n_points)
                lat = np.random.uniform(50, 80, n_points)
            elif time_name == "sparse_data":
                lon = np.random.uniform(-180, 180, n_points)
                lat = np.random.uniform(40, 90, n_points)
            elif time_name == "high_values":
                lon = np.random.uniform(-100, -40, n_points)
                lat = np.random.uniform(60, 75, n_points)
            elif time_name == "low_values":
                lon = np.random.uniform(-180, 180, n_points)
                lat = np.random.uniform(40, 90, n_points)
            else:  # mixed_pattern
                lon = np.concatenate([
                    np.random.uniform(-150, -50, n_points // 2),
                    np.random.uniform(50, 150, n_points // 2)
                ])
                lat = np.concatenate([
                    np.random.uniform(60, 80, n_points // 2),
                    np.random.uniform(40, 60, n_points // 2)
                ])
            
            vals = np.random.uniform(0, value_scale * 2, n_points)
            
            time_group.create_dataset('lon', data=lon)
            time_group.create_dataset('lat', data=lat)
            time_group.create_dataset('vals', data=vals)
    
    yield file_path
    
    if os.path.exists(file_path):
        os.unlink(file_path)

@pytest.fixture
def mock_cluster_config():
    """
    Mock configuration for ClusterProcessor testing.
    """
    with patch('app.services.auroral_oval.cluster_processor.MIN_CLUSTER_SIZE') as mock_min_size, \
         patch('app.services.auroral_oval.cluster_processor.DBSCAN_EPS') as mock_eps, \
         patch('app.services.auroral_oval.cluster_processor.DBSCAN_MIN_SAMPLES') as mock_min_samples, \
         patch('app.services.auroral_oval.cluster_processor.MAX_LATITUDE') as mock_max_lat:
        
        mock_min_size.return_value = 10
        mock_eps.return_value = 0.5
        mock_min_samples.return_value = 5
        mock_max_lat.return_value = 80.0
        
        yield {
            'min_cluster_size': mock_min_size,
            'dbscan_eps': mock_eps,
            'dbscan_min_samples': mock_min_samples,
            'max_latitude': mock_max_lat
        }