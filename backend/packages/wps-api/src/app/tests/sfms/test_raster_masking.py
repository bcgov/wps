"""
Unit tests for WPSDataset.apply_mask method.
"""

import numpy as np
from typing import Optional, cast
from unittest.mock import Mock, patch, MagicMock
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset


def create_mock_wps_dataset_for_mask(mask_data: np.ndarray, nodata: Optional[float] = None):
    """
    Create a mock WPSDataset for mask tests.

    :param mask_data: 2D numpy array of mask values
    :param nodata: NoData value for the mask
    :return: Mock WPSDataset
    """
    mock_band = cast(gdal.Band, Mock())
    mock_band.ReadAsArray.return_value = mask_data
    mock_band.GetNoDataValue.return_value = nodata

    mock_resampled = Mock()
    mock_resampled.ds.GetRasterBand.return_value = mock_band

    mock_ds = Mock()
    mock_ds.warp_to_match = Mock(return_value=mock_resampled)

    return mock_ds


class TestWPSDatasetApplyMask:
    """Tests for WPSDataset.apply_mask method."""

    def test_basic_mask_application(self):
        """Test basic mask application with valid and masked pixels."""
        # Mask data: center pixel masked (0), others valid (1)
        mask_data = np.array([[1, 1, 1], [1, 0, 1], [1, 1, 1]], dtype=np.float32)

        mock_mask_ds = create_mock_wps_dataset_for_mask(mask_data)

        # Create a real-ish ref_ds mock with the apply_mask method
        ref_ds = Mock(spec=WPSDataset)
        ref_ds.apply_mask = WPSDataset.apply_mask.__get__(ref_ds, WPSDataset)

        with patch("wps_shared.geospatial.wps_dataset.gdal.Unlink"):
            # Mock warp_to_match on the mask_ds
            result = ref_ds.apply_mask(mock_mask_ds)

            # Center pixel should be masked (False)
            assert result[1, 1] == False
            # All other pixels should be valid (True)
            assert np.sum(result) == 8

    def test_mask_with_nodata(self):
        """Test mask application with nodata values."""
        # Mask data with nodata value (-9999)
        mask_data = np.array([[1, 1, -9999], [1, 0, 1], [1, 1, 1]], dtype=np.float32)

        mock_mask_ds = create_mock_wps_dataset_for_mask(mask_data, nodata=-9999)

        ref_ds = Mock(spec=WPSDataset)
        ref_ds.apply_mask = WPSDataset.apply_mask.__get__(ref_ds, WPSDataset)

        with patch("wps_shared.geospatial.wps_dataset.gdal.Unlink"):
            result = ref_ds.apply_mask(mock_mask_ds)

            # Center pixel (0) and top-right pixel (nodata) should be masked
            assert result[1, 1] == False
            assert result[0, 2] == False
            assert np.sum(result) == 7

    def test_all_valid_mask(self):
        """Test when entire mask is valid."""
        mask_data = np.ones((3, 3), dtype=np.float32)

        mock_mask_ds = create_mock_wps_dataset_for_mask(mask_data)

        ref_ds = Mock(spec=WPSDataset)
        ref_ds.apply_mask = WPSDataset.apply_mask.__get__(ref_ds, WPSDataset)

        with patch("wps_shared.geospatial.wps_dataset.gdal.Unlink"):
            result = ref_ds.apply_mask(mock_mask_ds)

            assert np.all(result)
            assert np.sum(result) == 9

    def test_all_masked(self):
        """Test when entire mask is masked."""
        mask_data = np.zeros((3, 3), dtype=np.float32)

        mock_mask_ds = create_mock_wps_dataset_for_mask(mask_data)

        ref_ds = Mock(spec=WPSDataset)
        ref_ds.apply_mask = WPSDataset.apply_mask.__get__(ref_ds, WPSDataset)

        with patch("wps_shared.geospatial.wps_dataset.gdal.Unlink"):
            result = ref_ds.apply_mask(mock_mask_ds)

            assert not np.any(result)
            assert np.sum(result) == 0
