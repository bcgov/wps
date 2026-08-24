import numpy as np
import pytest
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_test_dataset

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.raster_output import create_masked_output_dataset

EXTENT = (-121.0, -119.0, 48.0, 50.0)


def make_dataset(values: np.ndarray, nodata_value: float = SFMS_NO_DATA) -> WPSDataset:
    rows, columns = values.shape
    dataset = create_test_dataset(
        "test.tif",
        columns,
        rows,
        EXTENT,
        4326,
        no_data_value=nodata_value,
    )
    dataset.GetRasterBand(1).WriteArray(values)
    return WPSDataset(ds_path=None, ds=dataset)


def test_applies_zero_and_nodata_mask_pixels_without_mutating_values():
    values = np.array([[7, 0], [3, 5]], dtype=np.float32)
    original_values = values.copy()
    reference = make_dataset(np.ones((2, 2), dtype=np.float32))
    mask = make_dataset(np.array([[1, 0], [SFMS_NO_DATA, 1]], dtype=np.float32))
    with create_masked_output_dataset(
        values,
        reference,
        mask,
        SFMS_NO_DATA,
    ) as output:
        output_values = output.as_gdal_ds().GetRasterBand(1).ReadAsArray()

    np.testing.assert_array_equal(
        output_values,
        np.array([[7, SFMS_NO_DATA], [SFMS_NO_DATA, 5]], dtype=np.float32),
    )
    np.testing.assert_array_equal(values, original_values)


def test_rejects_output_array_shape_that_does_not_match_reference():
    reference = make_dataset(np.ones((2, 2), dtype=np.float32))
    mask = make_dataset(np.ones((2, 2), dtype=np.float32))
    values = np.ones((1, 1), dtype=np.float32)
    with pytest.raises(ValueError, match="Output array shape does not match reference grid"):
        with create_masked_output_dataset(
            values,
            reference,
            mask,
            SFMS_NO_DATA,
        ):
            pass


def test_rejects_mask_grid_that_does_not_match_reference():
    reference = make_dataset(np.ones((2, 2), dtype=np.float32))
    mask = make_dataset(np.ones((1, 1), dtype=np.float32))
    values = np.ones((2, 2), dtype=np.float32)
    with pytest.raises(ValueError, match="Mask grid does not match reference grid"):
        with create_masked_output_dataset(
            values,
            reference,
            mask,
            SFMS_NO_DATA,
        ):
            pass
