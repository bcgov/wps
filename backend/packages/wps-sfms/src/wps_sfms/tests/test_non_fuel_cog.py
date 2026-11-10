"""Tests for web COGs that preserve Non-fuel and Water without blending into fuel."""

import numpy as np
import pytest
from osgeo import gdal, osr
from wps_shared.geospatial.cog import generate_and_store_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod
from wps_shared.geospatial.wps_dataset import WPSDataset

from wps_sfms.interpolation.common import SFMS_NO_DATA
from wps_sfms.non_fuel_cog import generate_non_fuel_cog
from wps_sfms.tests.raster_test_utils import create_test_wps_dataset

# Large enough that the COG driver builds overviews.
SIZE = 600


def read_levels(path: str) -> list[np.ma.MaskedArray]:
    """Full resolution followed by every overview, with NoData masked."""
    with gdal.Open(path) as output:
        band = output.GetRasterBand(1)
        assert band.GetOverviewCount() > 0
        return [band.ReadAsMaskedArray()] + [
            band.GetOverview(i).ReadAsMaskedArray() for i in range(band.GetOverviewCount())
        ]


@pytest.mark.parametrize("non_fuel_value, fuel_value", [(0, 1), (120, 85)])
def test_non_fuel_values_are_restored_without_blending_into_fuel(
    tmp_path, non_fuel_value, fuel_value
):
    """Source values are preserved at every zoom level, including nonzero FMC over Non-fuel."""
    values = np.full((SIZE, SIZE), fuel_value, dtype=np.float32)
    non_fuel = np.zeros(values.shape, dtype=bool)
    non_fuel[:, : SIZE // 2] = True
    values[non_fuel] = non_fuel_value
    output_path = str(tmp_path / "output.tif")

    with create_test_wps_dataset("source.tif", values) as source:
        generate_non_fuel_cog(source, output_path, non_fuel)
        # The source dataset is not modified.
        np.testing.assert_array_equal(source.read_array(), values)

    for level in read_levels(output_path):
        # Any blended value would add a third value, so exactly two means nothing was averaged.
        assert set(np.unique(level.compressed())) == {non_fuel_value, fuel_value}


def test_non_fuel_outside_source_footprint_stays_nodata(tmp_path):
    """Non-fuel pixels with no source value (e.g. outside BC) stay NoData instead of being restored."""
    values = np.zeros((SIZE, SIZE), dtype=np.float32)
    values[:, : SIZE // 2] = -9999.0
    output_path = str(tmp_path / "output.tif")

    with create_test_wps_dataset("source.tif", values, nodata=-9999.0) as source:
        generate_non_fuel_cog(source, output_path, np.ones(values.shape, dtype=bool))

    with gdal.Open(output_path) as output:
        actual = output.GetRasterBand(1).ReadAsMaskedArray()
    # Only the half with source data is valid.
    assert 0.4 < actual.count() / actual.size < 0.6
    np.testing.assert_array_equal(actual.compressed(), 0)


def test_float32_nodata_does_not_blend_into_neighbouring_fuel(tmp_path):
    """SFMS's NoData literal rounds in Float32; GDAL must exclude that stored value."""
    non_fuel = np.random.default_rng(42).random((200, 200)) < 0.5
    values = np.where(non_fuel, 0, 0.25).astype(np.float32)
    values[:10] = SFMS_NO_DATA
    output_path = str(tmp_path / "output.tif")
    nearest_path = str(tmp_path / "nearest.tif")

    with create_test_wps_dataset("source.tif", values, nodata=SFMS_NO_DATA) as source:
        # Match the production Lambert grid rather than the test helper's Albers grid.
        srs = osr.SpatialReference()
        srs.SetWellKnownGeogCS("NAD83")
        srs.SetLCC(49, 77, 49, -125, 0, 0)
        dataset = source.as_gdal_ds()
        dataset.SetProjection(srs.ExportToWkt())
        dataset.SetGeoTransform((-758000, 2000, 0, 1290000, 0, -2000))
        generate_non_fuel_cog(source, output_path, non_fuel)
        generate_and_store_cog(
            dataset, nearest_path, resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR
        )

    with gdal.Open(output_path) as output, gdal.Open(nearest_path) as nearest:
        actual = output.GetRasterBand(1).ReadAsMaskedArray()
        expected = nearest.ReadAsArray()
    expected_valid = expected != np.float32(SFMS_NO_DATA)
    assert not np.any(np.ma.getmaskarray(actual) & expected_valid)
    assert np.all(np.isin(actual.compressed(), [0, 0.25]))


def test_value_and_fuel_cogs_share_a_grid(tmp_path):
    """Insights reads value and fuel COGs per pixel, so their grids and overviews must match."""
    values = np.ones((SIZE, SIZE), dtype=np.float32)
    value_path = str(tmp_path / "value.tif")
    fuel_path = str(tmp_path / "fuel.tif")

    with create_test_wps_dataset("source.tif", values) as source:
        generate_non_fuel_cog(source, value_path, np.zeros(values.shape, dtype=bool))
    with create_test_wps_dataset("fuel.tif", values) as fuel:
        generate_and_store_cog(
            fuel.as_gdal_ds(), fuel_path, resample_alg=GDALResamplingMethod.NEAREST_NEIGHBOUR
        )

    with gdal.Open(value_path) as value_cog, gdal.Open(fuel_path) as fuel_cog:
        assert value_cog.GetGeoTransform() == fuel_cog.GetGeoTransform()
        assert (value_cog.RasterXSize, value_cog.RasterYSize) == (
            fuel_cog.RasterXSize,
            fuel_cog.RasterYSize,
        )
        assert (
            value_cog.GetRasterBand(1).GetOverviewCount()
            == fuel_cog.GetRasterBand(1).GetOverviewCount()
        )


@pytest.mark.parametrize(
    "mask, message",
    [
        (np.zeros((2, 3), dtype=bool), "shape"),
        (np.zeros((2, 2), dtype=np.uint8), "boolean"),
    ],
)
def test_invalid_classification_is_rejected(tmp_path, mask, message):
    """Reject masks that are the wrong shape or not boolean."""
    with create_test_wps_dataset("source.tif", np.zeros((2, 2))) as source:
        with pytest.raises(ValueError, match=message):
            generate_non_fuel_cog(source, str(tmp_path / "output.tif"), mask)


@pytest.mark.parametrize(
    "band_count, nodata, message",
    [(2, -9999.0, "single-band"), (1, None, "nodata")],
    ids=["multi-band", "no-nodata"],
)
def test_unsupported_source_is_rejected(tmp_path, band_count, nodata, message):
    """Reject multi-band sources and sources without NoData, since Non-fuel is masked as NoData."""
    source_ds = gdal.GetDriverByName("MEM").Create("", 2, 2, band_count, gdal.GDT_Float32)
    if nodata is not None:
        for band_number in range(1, band_count + 1):
            source_ds.GetRasterBand(band_number).SetNoDataValue(nodata)

    with WPSDataset(ds_path=None, ds=source_ds) as source:
        with pytest.raises(ValueError, match=message):
            generate_non_fuel_cog(
                source, str(tmp_path / "output.tif"), np.zeros((2, 2), dtype=bool)
            )
