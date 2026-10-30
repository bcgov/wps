"""Check Non-fuel exclusion without changing valid fuel values or source rasters."""

import numpy as np
import pytest
from osgeo import gdal
from wps_shared.geospatial.cog import generate_web_optimized_cog

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.non_fuel_cog import generate_non_fuel_cog
from wps_sfms.tests.raster_test_utils import create_test_wps_dataset


def test_non_fuel_boundaries_and_bilinear_values_survive_resampling_and_overviews(tmp_path):
    """Keep valid fuel zeros and NoData while excluding Non-fuel at every resolution."""
    # Large enough to exercise multiple COG overviews, not just the full-resolution image.
    size = 1024
    half = size // 2
    values = np.full((size, size), 0.5, dtype=np.float32)
    non_fuel = np.zeros(values.shape, dtype=bool)

    # Four quadrants: Non-fuel | positive fuel
    #                 NoData   | zero-valued fuel
    non_fuel[:half, :half] = True
    values[non_fuel] = 0
    values[half:, :half] = SFMS_NO_DATA
    values[half:, half:] = 0
    source_path = str(tmp_path / "source.tif")
    output_path = str(tmp_path / "output.tif")
    ordinary_path = str(tmp_path / "ordinary.tif")
    with create_test_wps_dataset("source.tif", values) as source:
        source.as_gdal_ds().GetRasterBand(1).SetNoDataValue(SFMS_NO_DATA)
        source.export_to_geotiff(source_path)

    generate_non_fuel_cog(source_path, output_path, non_fuel)
    generate_web_optimized_cog(source_path, ordinary_path)

    with gdal.Open(source_path) as source, gdal.Open(output_path) as output:
        np.testing.assert_array_equal(source.ReadAsArray(), values)
        assert output.GetMetadata("IMAGE_STRUCTURE")["LAYOUT"] == "COG"
        assert output.RasterCount == 1
        base_band = output.GetRasterBand(1)
        assert base_band.GetOverviewCount() >= 2
        # Compare against an independently masked input using the ordinary COG generator.
        with gdal.Translate("", source, format="MEM") as reference_source:
            masked_values = values.copy()
            masked_values[non_fuel] = SFMS_NO_DATA
            reference_source.GetRasterBand(1).WriteArray(masked_values)
            reference_path = str(tmp_path / "reference.tif")
            gdal.Translate(reference_path, reference_source).Close()
        reference_cog = str(tmp_path / "reference_cog.tif")
        generate_web_optimized_cog(reference_path, reference_cog)
        with gdal.Open(reference_cog) as reference:
            reference_base_band = reference.GetRasterBand(1)
            actual_bands = [base_band] + [
                base_band.GetOverview(level) for level in range(base_band.GetOverviewCount())
            ]
            reference_bands = [reference_base_band] + [
                reference_base_band.GetOverview(level)
                for level in range(reference_base_band.GetOverviewCount())
            ]
            for actual_band, reference_band in zip(actual_bands, reference_bands, strict=True):
                actual = actual_band.ReadAsArray()
                np.testing.assert_array_equal(actual, reference_band.ReadAsArray())
                assert np.any(actual == SFMS_NO_DATA)
                assert np.any(actual == 0)
                assert np.all((actual == SFMS_NO_DATA) | (actual >= 0))

        with gdal.Open(ordinary_path) as ordinary:
            raw = ordinary.ReadAsArray()
            masked = output.ReadAsArray()
            # At the Non-fuel boundary, ordinary resampling lowers otherwise constant fuel values.
            positive_fuel = np.isclose(masked, 0.5)
            assert np.any(positive_fuel & (raw > 0) & (raw < masked) & ~np.isclose(raw, masked))


@pytest.mark.parametrize("non_fuel", [False, True])
def test_all_zero_raster_distinguishes_valid_zero_from_non_fuel(tmp_path, non_fuel):
    """The classification, not the numeric zero, determines whether pixels are excluded."""
    values = np.zeros((8, 8), dtype=np.float32)
    source_path = str(tmp_path / "source.tif")
    output_path = str(tmp_path / "output.tif")
    with create_test_wps_dataset("source.tif", values) as source:
        source.export_to_geotiff(source_path)

    generate_non_fuel_cog(source_path, output_path, np.full(values.shape, non_fuel))

    with gdal.Open(output_path) as output:
        assert output.GetRasterBand(1).GetOverviewCount() == 0
        actual = output.ReadAsArray()
        valid = actual != output.GetRasterBand(1).GetNoDataValue()
        if non_fuel:
            assert not np.any(valid)
        else:
            assert np.any(valid)
            np.testing.assert_array_equal(actual[valid], np.zeros(np.sum(valid)))


@pytest.mark.parametrize(
    "mask, message",
    [
        (np.zeros((2, 3), dtype=bool), "shape"),
        (np.zeros((2, 2), dtype=np.uint8), "boolean"),
    ],
)
def test_invalid_classification_is_rejected(tmp_path, mask, message):
    """Reject masks that cannot safely identify source pixels."""
    source_path = str(tmp_path / "source.tif")
    with create_test_wps_dataset("source.tif", np.zeros((2, 2))) as source:
        source.export_to_geotiff(source_path)
    with pytest.raises(ValueError, match=message):
        generate_non_fuel_cog(source_path, str(tmp_path / "output.tif"), mask)


def test_missing_source_raises_gdal_error_without_changing_exception_mode(tmp_path):
    """Surface file errors without changing GDAL settings for other callers."""
    exceptions_enabled = gdal.GetUseExceptions()
    with pytest.raises(RuntimeError, match="missing.tif"):
        generate_non_fuel_cog(
            str(tmp_path / "missing.tif"),
            str(tmp_path / "output.tif"),
            np.zeros((2, 2), dtype=bool),
        )
    assert gdal.GetUseExceptions() == exceptions_enabled
