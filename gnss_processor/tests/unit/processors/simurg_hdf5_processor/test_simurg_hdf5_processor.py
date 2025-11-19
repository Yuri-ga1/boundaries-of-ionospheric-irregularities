import pytest
import numpy as np
import h5py as h5
import os
from unittest.mock import Mock, patch

from app.processors.simurg_hdf5_processor import SimurgHDF5Processor


class TestSimurgHDF5Processor:
    """Test cases for SimurgHDF5Processor functionality."""
    
    def test_initialization(self, sample_hdf5_file, mock_config):
        """
        Test that SimurgHDF5Processor initializes correctly.
        
        Verifies that the processor properly initializes with file path
        and sets up necessary attributes.
        """
        processor = SimurgHDF5Processor(sample_hdf5_file)
        
        assert processor.file_path == sample_hdf5_file
        assert processor.filename == os.path.basename(sample_hdf5_file)
        assert processor.file is None
        assert processor.stations_coords == {}
        assert processor.map_data == {}
        assert processor.flybys == {}
    
    def test_context_manager(self, sample_hdf5_file, mock_config):
        """
        Test context manager functionality.
        
        Verifies that the file is properly opened and closed
        when using the processor as a context manager.
        """
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            assert processor.file is not None
            assert isinstance(processor.file, h5.File)
            assert processor.file.mode == 'r'
        
        assert not processor.file
    
    def test_extract_station_coordinates_valid(self, sample_hdf5_file, mock_config):
        """
        Test station coordinate extraction with valid coordinates.
        
        Verifies that valid station coordinates are properly extracted
        and stored in the stations_coords dictionary.
        """
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            processor._extract_station_coordinates('station1')
            
            assert 'station1' in processor.stations_coords
            assert processor.stations_coords['station1']['lat'] == 60.0
            assert processor.stations_coords['station1']['lon'] == 30.0
    
    def test_extract_station_coordinates_out_of_bounds(self, sample_hdf5_file, mock_config):
        """
        Test station coordinate extraction with out-of-bounds coordinates.

        Verifies that stations with coordinates outside the defined bounds
        are not added to the stations_coords dictionary.
        """
        
        bounds_dict = {
            'min_lat': -90, 'max_lat': 50,
            'min_lon': -180, 'max_lon': 180
        }
        
        
        mock_config['bounds'].__getitem__.side_effect = bounds_dict.__getitem__
        
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            processor._extract_station_coordinates('station1')


            assert 'station1' not in processor.stations_coords

    def test_split_satellite_data_into_flybys_continuous(self, sample_hdf5_file, mock_config):
        """
        Test flyby segmentation with continuous data.
        
        Verifies that continuous timestamp data creates a single flyby segment.
        """
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            n_points = 10
            timestamps = np.array([1609459200 + i * 300 for i in range(n_points)])
            roti = np.random.uniform(0, 1, n_points)
            latitudes = np.random.uniform(50, 70, n_points)
            longitudes = np.random.uniform(20, 40, n_points)
            
            processor._split_satellite_data_into_flybys(
                'station1', 'G01', roti, timestamps, latitudes, longitudes
            )
            
            assert 'station1' in processor.flybys
            assert 'G01' in processor.flybys['station1']
            assert len(processor.flybys['station1']['G01']) == 1
            assert 'flyby0' in processor.flybys['station1']['G01']
    
    def test_split_satellite_data_into_flybys_segmented(self, sample_hdf5_file, mock_config):
        """
        Test flyby segmentation with segmented data.
        
        Verifies that large time gaps create multiple flyby segments.
        """
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            timestamps = np.array([1609459200, 1609459500, 1609462800, 1609463100])
            roti = np.random.uniform(0, 1, 4)
            latitudes = np.random.uniform(50, 70, 4)
            longitudes = np.random.uniform(20, 40, 4)
            
            processor._split_satellite_data_into_flybys(
                'station1', 'G01', roti, timestamps, latitudes, longitudes
            )
            
            assert len(processor.flybys['station1']['G01']) == 2
            assert 'flyby0' in processor.flybys['station1']['G01']
            assert 'flyby1' in processor.flybys['station1']['G01']
    
    def test_process_single_satellite_valid(self, sample_hdf5_file, mock_config):
        """
        Test processing of a single satellite with valid data.
        
        Verifies that valid satellite data is processed correctly
        and returns the expected filtered data structure.
        """
        with patch('app.processors.simurg_hdf5_processor.SatelliteDataProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            mock_processor.calculate_satellite_coordinates.return_value = (
                np.random.uniform(50, 70, 100),
                np.random.uniform(20, 40, 100)
            )
            
            mock_processor.apply_data_filters.return_value = {
                'roti': np.array([0.1, 0.2, 0.3]),
                'timestamps': np.array([1609459200, 1609459500, 1609462800]),
                'latitudes': np.array([60.1, 60.2, 60.3]),
                'longitudes': np.array([30.1, 30.2, 30.3])
            }
            
            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                processor.stations_coords['station1'] = {'lat': 60.0, 'lon': 30.0}
                
                result = processor._process_single_satellite('station1', 'G01')
                
                assert result is not None
                assert 'roti' in result
                assert 'timestamps' in result
                assert 'latitudes' in result
                assert 'longitudes' in result
                assert len(result['roti']) == 3
    
    def test_process_single_satellite_no_valid_data(self, sample_hdf5_file, mock_config):
        """
        Test processing of a single satellite with no valid data.
        
        Verifies that the method returns None when no valid data points
        remain after filtering.
        """
        with patch('app.processors.simurg_hdf5_processor.SatelliteDataProcessor') as mock_processor_class:
            mock_processor = Mock()
            mock_processor_class.return_value = mock_processor
            
            mock_processor.calculate_satellite_coordinates.return_value = (
                np.random.uniform(50, 70, 100),
                np.random.uniform(20, 40, 100)
            )
            
            mock_processor.apply_data_filters.return_value = {
                'roti': np.array([]),
                'timestamps': np.array([]),
                'latitudes': np.array([]),
                'longitudes': np.array([])
            }
            
            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                processor.stations_coords['station1'] = {'lat': 60.0, 'lon': 30.0}
                
                result = processor._process_single_satellite('station1', 'G01')
                
                assert result is None
    
    def test_sort_dictionary_recursively(self, sample_hdf5_file, mock_config):
        """
        Test recursive dictionary sorting.
        
        Verifies that nested dictionaries are sorted correctly
        at all levels.
        """
        with SimurgHDF5Processor(sample_hdf5_file) as processor:
            test_dict = {
                'z_key': {
                    'b_key': 2,
                    'a_key': 1
                },
                'a_key': {
                    'y_key': 4,
                    'x_key': 3
                }
            }
            
            sorted_dict = processor._sort_dictionary_recursively(test_dict)
            
            keys = list(sorted_dict.keys())
            assert keys == ['a_key', 'z_key']
            
            assert list(sorted_dict['a_key'].keys()) == ['x_key', 'y_key']
            assert list(sorted_dict['z_key'].keys()) == ['a_key', 'b_key']
    
    def test_create_output_files(self, sample_hdf5_file, mock_config, tmp_path):
        """
        Test creation of output HDF5 files.
        
        Verifies that map and flyby files are created with correct structure
        and contain the expected data.
        """
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', tmp_path / "maps"), \
             patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', tmp_path / "flybys"):
            
            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                processor.map_data = {
                    '2024-01-01 00:00:00.000000': {
                        'station1_G01': {
                            'vals': np.array([0.1]),
                            'lat': np.array([60.1]),
                            'lon': np.array([30.1])
                        }
                    }
                }
                
                processor.flybys = {
                    'station1': {
                        'G01': {
                            'flyby0': {
                                'roti': np.array([0.1, 0.2]),
                                'timestamps': np.array([1609459200, 1609459500]),
                                'lat': np.array([60.1, 60.2]),
                                'lon': np.array([30.1, 30.2])
                            }
                        }
                    }
                }
                
                map_file_path = tmp_path / "maps" / "test_output.h5"
                flyby_file_path = tmp_path / "flybys" / "test_output.h5"
                
                processor._create_output_files(str(map_file_path), str(flyby_file_path))
                
                assert map_file_path.exists()
                assert flyby_file_path.exists()
                
                with h5.File(map_file_path, 'r') as f:
                    assert 'data' in f
                    assert '2024-01-01 00:00:00.000000' in f['data']
                    timestamp_group = f['data']['2024-01-01 00:00:00.000000']
                    assert 'lat' in timestamp_group
                    assert 'lon' in timestamp_group
                    assert 'vals' in timestamp_group
                
                with h5.File(flyby_file_path, 'r') as f:
                    assert 'processed_data' in f
                    assert 'flybys' in f
                    assert 'station1' in f['flybys']
                    assert 'G01' in f['flybys']['station1']
                    assert 'flyby0' in f['flybys']['station1']['G01']
    
    def test_restore_processed_data(self, sample_hdf5_file, mock_config, tmp_path):
        """
        Test restoration of processed data from HDF5 file.

        Verifies that previously processed data can be correctly
        restored from the flyby output file.
        """
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', tmp_path / "maps"), \
            patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', tmp_path / "flybys"):

            flyby_file_path = tmp_path / "flybys" / "test_restore.h5"
            
            flyby_file_path.parent.mkdir(parents=True, exist_ok=True)

            with h5.File(flyby_file_path, 'w') as f:
                processed_group = f.create_group('processed_data')
                timestamp_group = processed_group.create_group('2024-01-01 00:00:00.000000')
                station_group = timestamp_group.create_group('station1_G01')
                station_group.create_dataset('lat', data=np.array([60.1]))
                station_group.create_dataset('lon', data=np.array([30.1]))
                station_group.create_dataset('vals', data=np.array([0.1]))
                
                flybys_group = f.create_group('flybys')
                station_flyby_group = flybys_group.create_group('station1')
                satellite_group = station_flyby_group.create_group('G01')
                flyby_group = satellite_group.create_group('flyby0')
                flyby_group.create_dataset('roti', data=np.array([0.1, 0.2]))
                flyby_group.create_dataset('timestamps', data=np.array([1609459200, 1609459500]))
                flyby_group.create_dataset('lat', data=np.array([60.1, 60.2]))
                flyby_group.create_dataset('lon', data=np.array([30.1, 30.2]))
            
            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                processor.restore_processed_data(str(flyby_file_path))
                
                assert '2024-01-01 00:00:00.000000' in processor.map_data
                assert 'station1_G01' in processor.map_data['2024-01-01 00:00:00.000000']
                assert 'station1' in processor.flybys
                assert 'G01' in processor.flybys['station1']
                assert 'flyby0' in processor.flybys['station1']['G01']
    
    def test_create_output_files(self, sample_hdf5_file, mock_config, tmp_path):
        """
        Test creation of output HDF5 files.

        Verifies that map and flyby files are created with correct structure
        and contain the expected data.
        """
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', tmp_path / "maps"), \
            patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', tmp_path / "flybys"):

            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                processor.map_data = {
                    '2024-01-01 00:00:00.000000': {
                        'station1_G01': {
                            'vals': np.array([0.1]),
                            'lat': np.array([60.1]),
                            'lon': np.array([30.1])
                        }
                    }
                }

                processor.flybys = {
                    'station1': {
                        'G01': {
                            'flyby0': {
                                'roti': np.array([0.1, 0.2]),
                                'timestamps': np.array([1609459200, 1609459500]),
                                'lat': np.array([60.1, 60.2]),
                                'lon': np.array([30.1, 30.2])
                            }
                        }
                    }
                }

                map_file_path = tmp_path / "maps" / "test_output.h5"
                flyby_file_path = tmp_path / "flybys" / "test_output.h5"
                
                map_file_path.parent.mkdir(parents=True, exist_ok=True)
                flyby_file_path.parent.mkdir(parents=True, exist_ok=True)

                processor._create_output_files(str(map_file_path), str(flyby_file_path))
                
                assert map_file_path.exists()
                assert flyby_file_path.exists()
                
                with h5.File(map_file_path, 'r') as f:
                    assert 'data' in f
                    assert '2024-01-01 00:00:00.000000' in f['data']
                    timestamp_group = f['data']['2024-01-01 00:00:00.000000']
                    assert 'lat' in timestamp_group
                    assert 'lon' in timestamp_group
                    assert 'vals' in timestamp_group
                
                with h5.File(flyby_file_path, 'r') as f:
                    assert 'processed_data' in f
                    assert 'flybys' in f
                    assert 'station1' in f['flybys']
                    assert 'G01' in f['flybys']['station1']
                    assert 'flyby0' in f['flybys']['station1']['G01']
    
    def test_process_method_existing_files(self, sample_hdf5_file, mock_config, tmp_path):
        """
        Test the main process method when files already exist.
        
        Verifies that the processor restores data from existing files
        instead of reprocessing when output files already exist.
        """
        with patch('app.processors.simurg_hdf5_processor.MAP_PATH', tmp_path / "maps"), \
             patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', tmp_path / "flybys"):
            
            map_file = tmp_path / "maps" / "test_output.h5"
            flyby_file = tmp_path / "flybys" / "test_output.h5"
            
            map_file.parent.mkdir(parents=True, exist_ok=True)
            flyby_file.parent.mkdir(parents=True, exist_ok=True)
            
            with h5.File(map_file, 'w'):
                pass
            with h5.File(flyby_file, 'w'):
                pass
            
            with SimurgHDF5Processor(sample_hdf5_file) as processor:
                with patch.object(processor, 'restore_processed_data') as mock_restore:
                    processor.process('test_output.h5')
                    
                    mock_restore.assert_called_once_with(str(flyby_file))
