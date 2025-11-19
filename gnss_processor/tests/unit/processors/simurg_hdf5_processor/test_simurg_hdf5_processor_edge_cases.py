import pytest
import numpy as np
import h5py as h5
import os
import tempfile
from unittest.mock import Mock, patch

from app.processors.simurg_hdf5_processor import SimurgHDF5Processor


class TestSimurgHDF5ProcessorEdgeCases:
    """Edge case tests for SimurgHDF5Processor."""
    
    def test_empty_hdf5_file(self, mock_config, tmp_path):
        """
        Test processing of an empty HDF5 file.

        Verifies that the processor handles empty files gracefully
        without raising exceptions.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            empty_file = f.name

        # Create empty HDF5 file
        with h5.File(empty_file, 'w'):
            pass

        try:
            maps_dir = tmp_path / "maps"
            flybys_dir = tmp_path / "flybys"
            maps_dir.mkdir(parents=True, exist_ok=True)
            flybys_dir.mkdir(parents=True, exist_ok=True)

            with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
                patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)):

                with SimurgHDF5Processor(empty_file) as processor:
                    processor.process('test_output.h5')

                    assert processor.map_data == {}
                    assert processor.flybys == {}
        finally:
            if os.path.exists(empty_file):
                os.unlink(empty_file)
    
    def test_missing_satellite_datasets(self, mock_config, tmp_path):
        """
        Test processing of HDF5 file with missing datasets.
        
        Verifies that the processor handles missing required datasets
        gracefully without crashing.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            file_path = f.name

        maps_dir = tmp_path / "maps"
        flybys_dir = tmp_path / "flybys"
        maps_dir.mkdir(parents=True, exist_ok=True)
        flybys_dir.mkdir(parents=True, exist_ok=True)

        with h5.File(file_path, 'w') as h5file:
            station_group = h5file.create_group('station1')
            station_group.attrs['lat'] = 60.0
            station_group.attrs['lon'] = 30.0

            sat_group = station_group.create_group('G01')
            sat_group.create_dataset('roti', data=np.array([0.1, 0.2]))

        try:
            with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
                patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)):

                with SimurgHDF5Processor(file_path) as processor:
                    with patch.object(processor, '_process_single_satellite') as mock_process:
                        mock_process.return_value = None 

                        processor.process('test_output.h5')
                        
                        assert 'station1' in processor.stations_coords
                        mock_process.assert_called()
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_corrupted_timestamps(self, mock_config, tmp_path):
        """
        Test processing with corrupted timestamp data.

        Verifies that the processor handles invalid timestamp data
        without crashing.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            file_path = f.name
        
        maps_dir = tmp_path / "maps"
        flybys_dir = tmp_path / "flybys"
        maps_dir.mkdir(parents=True, exist_ok=True)
        flybys_dir.mkdir(parents=True, exist_ok=True)

        with h5.File(file_path, 'w') as h5file:
            station_group = h5file.create_group('station1')
            station_group.attrs['lat'] = 60.0
            station_group.attrs['lon'] = 30.0
            
            sat_group = station_group.create_group('G01')
            sat_group.create_dataset('roti', data=np.array([0.1, 0.2, 0.3]))
            sat_group.create_dataset('azimuth', data=np.array([45, 90, 135]))
            sat_group.create_dataset('elevation', data=np.array([30, 45, 60]))
            sat_group.create_dataset('timestamp', data=np.array([-100, 0, 1609459200]))
        
        try:
            with patch('app.processors.simurg_hdf5_processor.MAP_PATH', str(maps_dir)), \
                patch('app.processors.simurg_hdf5_processor.FLYBYS_PATH', str(flybys_dir)):
                
                with SimurgHDF5Processor(file_path) as processor:
                    processor.process('test_output.h5')
                    
                    assert processor.stations_coords is not None
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)