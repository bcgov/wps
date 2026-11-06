"""Tests for generating web COGs that exclude Non-fuel and Water pixels."""

import numpy as np
import pytest
from osgeo import gdal

from wps_sfms.non_fuel_cog import generate_non_fuel_cog
from wps_sfms.tests.raster_test_utils import create_test_wps_dataset


def test_non_fuel_does_not_lower_adjacent_fuel_values(tmp_path):
    """Non-fuel pixels become NoData, so their zeros don't lower nearby fuel values in the COG."""
    values = np.full((16, 16), 1, dtype=np.float32)
    non_fuel = np.zeros(values.shape, dtype=bool)

    # Left half is Non-fuel (0) and right half is fuel (1).
    # Any valid output value below 1 would mean Non-fuel was blended into fuel.
    non_fuel[:, :8] = True
    values[non_fuel] = 0

    source_path = str(tmp_path / "source.tif")
    output_path = str(tmp_path / "output.tif")
    with create_test_wps_dataset("source.tif", values) as source:
        source.export_to_geotiff(source_path)

    generate_non_fuel_cog(source_path, output_path, non_fuel)

    # The original GeoTIFF is not modified.
    with gdal.Open(source_path) as source:
        np.testing.assert_array_equal(source.ReadAsArray(), values)

    # Only the full-resolution image is checked. GDAL also skips NoData when building overviews.
    # The masked array contains every output pixel, with NoData pixels hidden from calculations.
    with gdal.Open(output_path) as output:
        actual = output.GetRasterBand(1).ReadAsMaskedArray()

    # count() is the number of valid pixels and size is all pixels (including NoData).
    # Some pixels must be valid fuel, while the rest are Non-fuel or outside the source area.
    assert 0 < actual.count() < actual.size
    # compressed() returns only valid pixel values, so every remaining fuel value must still be 1.
    np.testing.assert_allclose(actual.compressed(), 1)


@pytest.mark.parametrize("non_fuel", [False, True])
def test_all_zero_raster_distinguishes_valid_zero_from_non_fuel(tmp_path, non_fuel):
    """Zeros are excluded only when the mask marks them as Non-fuel and zero fuel values are kept."""
    values = np.zeros((8, 8), dtype=np.float32)
    source_path = str(tmp_path / "source.tif")
    output_path = str(tmp_path / "output.tif")
    with create_test_wps_dataset("source.tif", values) as source:
        source.export_to_geotiff(source_path)

    generate_non_fuel_cog(source_path, output_path, np.full(values.shape, non_fuel))

    # The masked array contains every output pixel, with NoData pixels hidden from calculations.
    with gdal.Open(output_path) as output:
        actual = output.GetRasterBand(1).ReadAsMaskedArray()

    if non_fuel:
        # count() is the number of valid pixels, so Non-fuel zeros must all be NoData.
        assert actual.count() == 0
    else:
        # Fuel zeros stay valid. compressed() returns only those valid values.
        assert actual.count() > 0
        np.testing.assert_array_equal(actual.compressed(), 0)


@pytest.mark.parametrize(
    "mask, message",
    [
        (np.zeros((2, 3), dtype=bool), "shape"),
        (np.zeros((2, 2), dtype=np.uint8), "boolean"),
    ],
)
def test_invalid_classification_is_rejected(tmp_path, mask, message):
    """Reject masks that are the wrong shape or not boolean."""
    source_path = str(tmp_path / "source.tif")
    with create_test_wps_dataset("source.tif", np.zeros((2, 2))) as source:
        source.export_to_geotiff(source_path)

    with pytest.raises(ValueError, match=message):
        generate_non_fuel_cog(source_path, str(tmp_path / "output.tif"), mask)


@pytest.mark.parametrize(
    "band_count, nodata, message",
    [(2, -9999.0, "single-band"), (1, None, "NoData")],
    ids=["multi-band", "no-nodata"],
)
def test_unsupported_source_is_rejected(tmp_path, band_count, nodata, message):
    """Reject multi-band sources and sources without NoData, since excluded pixels are set to NoData."""
    source_path = str(tmp_path / "source.tif")
    with gdal.GetDriverByName("GTiff").Create(
        source_path, 2, 2, band_count, gdal.GDT_Float32
    ) as source:
        if nodata is not None:
            for band_number in range(1, band_count + 1):
                source.GetRasterBand(band_number).SetNoDataValue(nodata)

    with pytest.raises(ValueError, match=message):
        generate_non_fuel_cog(
            source_path, str(tmp_path / "output.tif"), np.zeros((2, 2), dtype=bool)
        )


def test_missing_source_raises_gdal_error_without_changing_exception_mode(tmp_path):
    """A missing source raises a GDAL error and leaves the global GDAL exception setting unchanged."""
    exceptions_enabled = gdal.GetUseExceptions()

    with pytest.raises(RuntimeError, match="missing.tif"):
        generate_non_fuel_cog(
            str(tmp_path / "missing.tif"),
            str(tmp_path / "output.tif"),
            np.zeros((2, 2), dtype=bool),
        )

    assert gdal.GetUseExceptions() == exceptions_enabled
