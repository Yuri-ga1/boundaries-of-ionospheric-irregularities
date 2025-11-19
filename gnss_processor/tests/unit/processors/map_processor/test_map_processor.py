import pytest
import numpy as np
import h5py as h5
import os
import tempfile
from unittest.mock import Mock, patch, MagicMock
from pathlib import Path

from app.processors.map_processor import MapProcessor


class TestMapProcessor:
    """Test cases for MapProcessor functionality."""
    
    def test_initialization(self, map_processor):
        """
        Test that MapProcessor initializes correctly.
        """
        assert map_processor.lon_condition == -60
        assert map_processor.lat_condition == 40
        assert map_processor.segment_lon_step == 5.0
        assert map_processor.segment_lat_step == 5.0
        assert map_processor.boundary_condition == 0.5
        assert map_processor.file_name is None
        
        # Check that sub-processors are initialized
        assert hasattr(map_processor, 'boundary_detector')
        assert hasattr(map_processor, 'sliding_window_processor')
        assert hasattr(map_processor, 'cluster_processor')
    
    def test_filter_coordinate_points_valid(self, map_processor, sample_map_hdf5_file):
        """
        Test coordinate point filtering with valid data.
        """
        with h5.File(sample_map_hdf5_file, 'r') as h5file:
            data_group = h5file["data"]
            time_point = list(data_group.keys())[0]
            points_group = data_group[time_point]
            
            filtered_points = map_processor._filter_coordinate_points(points_group)
            
            assert 'lon' in filtered_points
            assert 'lat' in filtered_points
            assert 'vals' in filtered_points
            
            # Check that filtering conditions are applied
            lon_condition = map_processor.lon_condition
            lat_condition = map_processor.lat_condition
            
            assert np.all(filtered_points['lon'] >= -120)
            assert np.all(filtered_points['lon'] <= lon_condition)
            assert np.all(filtered_points['lat'] >= lat_condition)
    
    def test_filter_coordinate_points_empty_result(self, map_processor):
        """
        Test coordinate point filtering when no points match conditions.
        """
        # Create a temporary HDF5 file with data that won't pass filters
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            file_path = f.name
        
        try:
            with h5.File(file_path, 'w') as h5file:
                group = h5file.create_group("test_group")
                # Create data that doesn't meet filtering conditions
                group.create_dataset('lon', data=np.array([-130, -140]))  # Outside lon range
                group.create_dataset('lat', data=np.array([30, 35]))      # Below lat condition
                group.create_dataset('vals', data=np.array([0.1, 0.2]))
            
            with h5.File(file_path, 'r') as h5file:
                points_group = h5file["test_group"]
                filtered_points = map_processor._filter_coordinate_points(points_group)
                
                # Should return empty arrays but maintain structure
                assert len(filtered_points['lon']) == 0
                assert len(filtered_points['lat']) == 0
                assert len(filtered_points['vals']) == 0
        finally:
            if os.path.exists(file_path):
                os.unlink(file_path)
    
    def test_save_raw_points(self, map_processor, tmp_path):
        """
        Test saving raw points to HDF5 file.
        """
        # Create a temporary HDF5 file
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            # Create mock points group
            with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
                points_file = f.name
            
            try:
                with h5.File(points_file, 'w') as pf:
                    pf.create_dataset('lon', data=np.array([10.0, 20.0, 30.0]))
                    pf.create_dataset('lat', data=np.array([40.0, 50.0, 60.0]))
                    pf.create_dataset('vals', data=np.array([0.1, 0.2, 0.3]))
                
                with h5.File(points_file, 'r') as pf:
                    points_group = pf
                    map_processor._save_raw_points(points_group, time_group)
                    
                    # Verify data was saved correctly
                    assert "points" in time_group
                    points_subgroup = time_group["points"]
                    assert "lon" in points_subgroup
                    assert "lat" in points_subgroup
                    assert "vals" in points_subgroup
                    
                    assert np.array_equal(points_subgroup['lon'][()], np.array([10.0, 20.0, 30.0]))
                    assert np.array_equal(points_subgroup['lat'][()], np.array([40.0, 50.0, 60.0]))
                    assert np.array_equal(points_subgroup['vals'][()], np.array([0.1, 0.2, 0.3]))
            finally:
                if os.path.exists(points_file):
                    os.unlink(points_file)
    
    def test_save_filtered_points(self, map_processor, tmp_path):
        """
        Test saving filtered points to HDF5 file.
        """
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            filtered_points = {
                'lon': np.array([15.0, 25.0]),
                'lat': np.array([45.0, 55.0]),
                'vals': np.array([0.15, 0.25])
            }
            
            map_processor._save_filtered_points(filtered_points, time_group)
            
            # Verify data was saved correctly
            assert "filtered_points" in time_group
            filtered_subgroup = time_group["filtered_points"]
            assert "lon" in filtered_subgroup
            assert "lat" in filtered_subgroup
            assert "vals" in filtered_subgroup
            
            assert np.array_equal(filtered_subgroup['lon'][()], np.array([15.0, 25.0]))
            assert np.array_equal(filtered_subgroup['lat'][()], np.array([45.0, 55.0]))
            assert np.array_equal(filtered_subgroup['vals'][()], np.array([0.15, 0.25]))
    
    def test_save_sliding_windows(self, map_processor, tmp_path):
        """
        Test saving sliding windows data to HDF5 file.
        """
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            sliding_windows = [
                {'lon': 10.0, 'lat': 50.0, 'vals': 0.1},
                {'lon': 20.0, 'lat': 55.0, 'vals': 0.2},
                {'lon': 30.0, 'lat': 60.0, 'vals': 0.3}
            ]
            
            map_processor._save_sliding_windows(sliding_windows, time_group)
            
            # Verify data was saved correctly
            assert "sliding_windows" in time_group
            sliding_subgroup = time_group["sliding_windows"]
            assert "lon" in sliding_subgroup
            assert "lat" in sliding_subgroup
            assert "vals" in sliding_subgroup
            
            expected_lon = [10.0, 20.0, 30.0]
            expected_lat = [50.0, 55.0, 60.0]
            expected_vals = [0.1, 0.2, 0.3]
            
            assert np.array_equal(sliding_subgroup['lon'][()], expected_lon)
            assert np.array_equal(sliding_subgroup['lat'][()], expected_lat)
            assert np.array_equal(sliding_subgroup['vals'][()], expected_vals)
    
    def test_save_boundary_data(self, map_processor, tmp_path):
        """
        Test saving boundary data to HDF5 file.
        """
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            boundary_data = {
                'lon': [15.0, 25.0, 35.0],
                'lat': [45.0, 55.0, 65.0]
            }
            
            map_processor._save_boundary_data(boundary_data, time_group)
            
            # Verify data was saved correctly
            assert "boundary" in time_group
            boundary_subgroup = time_group["boundary"]
            assert "lon" in boundary_subgroup
            assert "lat" in boundary_subgroup
            
            expected_lon = [15.0, 25.0, 35.0]
            expected_lat = [45.0, 55.0, 65.0]
            
            assert np.array_equal(boundary_subgroup['lon'][()], expected_lon)
            assert np.array_equal(boundary_subgroup['lat'][()], expected_lat)
    
    def test_save_boundary_clusters(self, map_processor, tmp_path):
        """
        Test saving boundary clusters to HDF5 file.
        """
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            boundary_clusters = {
                'relation': 'test_relation',
                'cluster1': [[10.0, 50.0], [15.0, 55.0]],
                'cluster2': [[20.0, 60.0], [25.0, 65.0]]
            }
            
            map_processor._save_boundary_clusters(boundary_clusters, time_group)
            
            # Verify data was saved correctly
            assert "boundary_clusters" in time_group
            clusters_subgroup = time_group["boundary_clusters"]
            
            # Check relation attribute
            assert clusters_subgroup.attrs["relation"] == "test_relation"
            
            # Check cluster data
            assert "cluster1" in clusters_subgroup
            assert "cluster2" in clusters_subgroup
            
            cluster1_subgroup = clusters_subgroup["cluster1"]
            assert "lon" in cluster1_subgroup
            assert "lat" in cluster1_subgroup
            
            expected_cluster1_lon = [10.0, 15.0]
            expected_cluster1_lat = [50.0, 55.0]
            
            assert np.array_equal(cluster1_subgroup['lon'][()], expected_cluster1_lon)
            assert np.array_equal(cluster1_subgroup['lat'][()], expected_cluster1_lat)
    
    def test_save_boundary_clusters_none(self, map_processor, tmp_path):
        """
        Test saving None boundary clusters (should not create group).
        """
        test_file = tmp_path / "test_output.h5"
        
        with h5.File(test_file, 'w') as h5file:
            time_group = h5file.create_group("test_time")
            
            # Pass None, should not create the group
            map_processor._save_boundary_clusters(None, time_group)
            
            # Verify no boundary_clusters group was created
            assert "boundary_clusters" not in time_group
    
    def test_process_single_time_point(self, map_processor, sample_map_hdf5_file, mock_map_config, tmp_path):
        """
        Test processing of a single time point.
        """
        output_file = tmp_path / "test_output.h5"
        
        with patch.object(map_processor.boundary_detector, 'extract_boundary_contours') as mock_boundary, \
             patch.object(map_processor.sliding_window_processor, 'apply_sliding_window_segmentation') as mock_sliding, \
             patch.object(map_processor.cluster_processor, 'create_boundary_clusters') as mock_cluster:
            
            # Mock the return values
            mock_sliding.return_value = [
                {'lon': 10.0, 'lat': 50.0, 'vals': 0.1},
                {'lon': 20.0, 'lat': 55.0, 'vals': 0.2}
            ]
            
            mock_boundary.return_value = {
                'lon': [15.0, 25.0],
                'lat': [45.0, 55.0]
            }
            
            mock_cluster.return_value = {
                'relation': 'test_relation',
                'cluster1': [[10.0, 50.0], [15.0, 55.0]]
            }
            
            with h5.File(sample_map_hdf5_file, 'r') as h5file:
                data_group = h5file["data"]
                time_point = list(data_group.keys())[0]
                
                with h5.File(output_file, 'w') as output_h5:
                    map_processor._process_single_time_point(data_group, time_point, output_h5)
                    
                    # Verify the time group was created
                    assert time_point in output_h5
                    time_group = output_h5[time_point]
                    
                    # Verify all subgroups were created
                    assert "points" in time_group
                    assert "filtered_points" in time_group
                    assert "sliding_windows" in time_group
                    assert "boundary" in time_group
                    assert "boundary_clusters" in time_group
                    
                    # Verify mocks were called
                    mock_sliding.assert_called_once()
                    mock_boundary.assert_called_once()
                    mock_cluster.assert_called_once()
    
    def test_process_map_file_new(self, map_processor, sample_map_hdf5_file, mock_map_config, tmp_path):
        """
        Test processing of map file when output doesn't exist.
        """
        output_file = tmp_path / "boundary_output.h5"
        
        with patch.object(map_processor, '_process_single_time_point') as mock_process_time:
            map_processor.process_map_file(
                map_path=str(sample_map_hdf5_file),
                output_path=str(output_file)
            )
            
            # Verify output file was created
            assert output_file.exists()
            
            # Verify process_single_time_point was called for each time point
            assert mock_process_time.call_count == 2
    
    def test_process_map_file_existing(self, map_processor, sample_map_hdf5_file, mock_map_config, tmp_path):
        """
        Test processing of map file when output already exists.
        """
        output_file = tmp_path / "boundary_output.h5"
        
        # Create existing output file
        with h5.File(output_file, 'w'):
            pass
        
        with patch.object(map_processor, '_process_single_time_point') as mock_process_time:
            map_processor.process_map_file(
                map_path=str(sample_map_hdf5_file),
                output_path=str(output_file)
            )
            
            # Verify process_single_time_point was NOT called (file exists)
            mock_process_time.assert_not_called()
    
    def test_process_map_file_specific_time_points(self, map_processor, sample_map_hdf5_file, mock_map_config, tmp_path):
        """
        Test processing of map file with specific time points.
        """
        output_file = tmp_path / "boundary_output.h5"
        
        with patch.object(map_processor, '_process_single_time_point') as mock_process_time:
            specific_time_points = ['2024-01-01 00:00:00.000000']
            
            map_processor.process_map_file(
                map_path=str(sample_map_hdf5_file),
                output_path=str(output_file),
                time_points=specific_time_points
            )
            
            # Verify process_single_time_point was called only for specified time points
            assert mock_process_time.call_count == 1
            
            # Verify the correct time point was processed
            call_args = mock_process_time.call_args[0]
            assert call_args[1] == specific_time_points[0]  # time_point argument


class TestMapProcessorEdgeCases:
    """Edge case tests for MapProcessor."""
    
    def test_empty_map_file(self, map_processor, mock_map_config, tmp_path):
        """
        Test processing of empty map file.
        """
        # Create empty HDF5 file
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            empty_file = f.name
        
        try:
            with h5.File(empty_file, 'w') as h5file:
                h5file.create_group("data")  # Empty data group
            
            output_file = tmp_path / "output.h5"
            
            # Should complete without errors
            map_processor.process_map_file(
                map_path=empty_file,
                output_path=str(output_file)
            )
            
            # Output file should be created
            assert output_file.exists()
            
        finally:
            if os.path.exists(empty_file):
                os.unlink(empty_file)
    
    def test_missing_data_group(self, map_processor, mock_map_config, tmp_path):
        """
        Test processing of map file with missing data group.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            invalid_file = f.name
        
        try:
            # Create HDF5 file without "data" group
            with h5.File(invalid_file, 'w'):
                pass
            
            output_file = tmp_path / "output.h5"
            
            # Should handle the error gracefully
            with pytest.raises(KeyError):
                map_processor.process_map_file(
                    map_path=invalid_file,
                    output_path=str(output_file)
                )
            
        finally:
            if os.path.exists(invalid_file):
                os.unlink(invalid_file)
    
    def test_missing_datasets_in_time_point(self, map_processor, mock_map_config, tmp_path):
        """
        Test processing of time point with missing datasets.
        
        Verifies that the processor handles missing required datasets
        gracefully without crashing.
        """
        with tempfile.NamedTemporaryFile(suffix='.h5', delete=False) as f:
            map_file = f.name

        try:
            with h5.File(map_file, 'w') as h5file:
                data_group = h5file.create_group("data")
                time_group = data_group.create_group("test_time")

            output_file = tmp_path / "output.h5"

            try:
                map_processor.process_map_file(
                    map_path=map_file,
                    output_path=str(output_file),
                    time_points=["test_time"]
                )
                
                assert output_file.exists()
                
            except (KeyError, OSError) as e:
                assert "lon" in str(e) or "lat" in str(e) or "vals" in str(e) or "Unable to open object" in str(e)
            
        finally:
            if os.path.exists(map_file):
                os.unlink(map_file)
