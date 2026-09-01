import os
import tempfile
from datetime import date
from types import SimpleNamespace

import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.snow import MASKED_HFI_PATH_NAME, apply_snow_mask, classify_snow_mask
from wps_shared.geospatial.wps_dataset import WPSDataset


def _make_raster(path: str, values, datatype, geotransform, projection_wkt, np_dtype=np.uint8):
    ds = gdal.GetDriverByName("GTiff").Create(path, 2, 2, 1, datatype)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection_wkt)
    ds.GetRasterBand(1).WriteArray(np.array(values, dtype=np_dtype))
    ds.FlushCache()
    return ds


def test_classify_snow_mask():
    """0 = snow covered (10 < NDSI <= 100), 1 = snow free / QA, preserving georeferencing."""
    with tempfile.TemporaryDirectory() as temp_dir:
        source_path = os.path.join(temp_dir, "snow.tif")
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        # values: 5 (below threshold), 50 (snow), 100 (snow, inclusive), 101 (above range/QA)
        source_ds = _make_raster(
            source_path,
            [[5, 50], [100, 101]],
            gdal.GDT_Float32,
            (0, 1, 0, 0, 0, -1),
            srs.ExportToWkt(),
            np_dtype=np.float32,
        )
        geotransform = source_ds.GetGeoTransform()
        projection = source_ds.GetProjection()
        source_ds = None

        with WPSDataset(source_path) as source, classify_snow_mask(source) as result:
            raw = result.as_gdal_ds()
            assert raw.GetRasterBand(1).ReadAsArray().tolist() == [[1, 0], [0, 1]]
            assert raw.GetRasterBand(1).DataType == gdal.GDT_Byte
            assert raw.GetGeoTransform() == geotransform
            assert raw.GetProjection() == projection


def test_apply_snow_mask_closes_the_masked_dataset_before_returning(mocker):
    """Regression test: `hfi_source * snow_mask` writes directly to masked_hfi_path, since
    hfi_source is opened with output_path=masked_hfi_path. If that multiply result isn't closed
    before apply_snow_mask returns, callers reopening masked_hfi_path right away (as
    process_hfi.py does) can hit a malformed GeoTIFF - GDAL doesn't finalize a GTiff's directory
    structure until the writing dataset is closed. Same class of bug as
    test_raster_mul_disk_backed_corrupt_read_if_not_closed_before_reopen in test_wps_dataset.py."""
    with tempfile.TemporaryDirectory() as temp_dir:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(4326)
        geotransform = (0, 1, 0, 0, 0, -1)

        hfi_path = os.path.join(temp_dir, "hfi.tif")
        _make_raster(
            hfi_path,
            [[5000, 8000], [12000, 3000]],
            gdal.GDT_Float32,
            geotransform,
            srs.ExportToWkt(),
            np_dtype=np.float32,
        )

        # apply_snow_mask reads the snow coverage raster from a /vsis3/ path - substitute a real
        # local raster for it instead of hitting S3.
        snow_path = os.path.join(temp_dir, "snow.tif")
        _make_raster(
            snow_path,
            [[50, 5], [90, 20]],
            gdal.GDT_Float32,
            geotransform,
            srs.ExportToWkt(),
            np_dtype=np.float32,
        )
        real_gdal_open = gdal.Open
        mocker.patch.object(
            gdal,
            "Open",
            side_effect=lambda path, *args, **kwargs: real_gdal_open(
                snow_path if path.startswith("/vsis3/") else path, *args, **kwargs
            ),
        )

        mul_spy = mocker.spy(WPSDataset, "__mul__")

        result_path = apply_snow_mask(
            hfi_path, SimpleNamespace(for_date=date(2024, 1, 1)), temp_dir
        )

        assert result_path == os.path.join(temp_dir, MASKED_HFI_PATH_NAME)
        # closed sets .ds to None, so a non-None .ds here means it leaked.
        assert mul_spy.spy_return.ds is None

        # confirm the file is actually readable, not left with a malformed/incomplete directory
        with WPSDataset(result_path) as reopened:
            assert (reopened.ds.RasterXSize, reopened.ds.RasterYSize) == (2, 2)
