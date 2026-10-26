import numpy as np
import pytest
from osgeo import gdal, osr

from wps_sfms import generate_fuel_cog
from wps_sfms.interpolation.common import SFMS_NO_DATA


@pytest.fixture
def fuel_raster(tmp_path):
    path = tmp_path / "fuel.tif"
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(3005)
    values = np.tile(np.array([2010, 2030, 500, 102, -10000], dtype=np.float32), (600, 120))
    with gdal.GetDriverByName("GTiff").Create(str(path), 600, 600, 1, gdal.GDT_Float32) as ds:
        ds.SetGeoTransform((1000000, 2000, 0, 1000000, 0, -2000))
        ds.SetProjection(srs.ExportToWkt())
        ds.GetRasterBand(1).SetNoDataValue(-10000)
        ds.GetRasterBand(1).WriteArray(values)
    return path


@pytest.mark.parametrize("explicit_output", [False, True])
def test_convert_fuel_cog(fuel_raster, tmp_path, explicit_output):
    output = tmp_path / ("custom.tif" if explicit_output else "fuel_3857_cog.tif")
    args = ["--input", str(fuel_raster)]
    if explicit_output:
        args.extend(["--output", str(output)])

    generate_fuel_cog.main(args)

    with gdal.Open(str(output)) as ds:
        srs = osr.SpatialReference()
        srs.ImportFromEPSG(3857)
        assert ds.GetSpatialRef().IsSame(srs)
        x_resolution = ds.GetGeoTransform()[1]
        y_resolution = ds.GetGeoTransform()[5]
        assert 2000 < x_resolution < 5000
        assert y_resolution == pytest.approx(-x_resolution)
        assert ds.GetMetadata("IMAGE_STRUCTURE")["LAYOUT"] == "COG"
        assert ds.GetMetadata("IMAGE_STRUCTURE")["COMPRESSION"] == "LZW"
        band = ds.GetRasterBand(1)
        assert band.DataType == gdal.GDT_Float32
        assert band.GetNoDataValue() == float(np.float32(SFMS_NO_DATA))
        expected = {np.float32(SFMS_NO_DATA), 2010, 2030, 500, 102}
        assert set(np.unique(band.ReadAsArray())) == expected
        assert band.GetOverviewCount() > 0
        for index in range(band.GetOverviewCount()):
            assert set(np.unique(band.GetOverview(index).ReadAsArray())) <= expected


def test_convert_geographic_fuel_cog(fuel_raster):
    geographic = osr.SpatialReference()
    geographic.ImportFromEPSG(4326)
    with gdal.Open(str(fuel_raster), gdal.GA_Update) as source:
        source.SetProjection(geographic.ExportToWkt())
        source.SetGeoTransform((-126, 0.01, 0, 55, 0, -0.01))

    generate_fuel_cog.main(["--input", str(fuel_raster)])

    output = fuel_raster.with_name("fuel_3857_cog.tif")
    with gdal.Open(str(output)) as ds:
        web_mercator = osr.SpatialReference()
        web_mercator.ImportFromEPSG(3857)
        assert ds.GetSpatialRef().IsSame(web_mercator)
        x_resolution = ds.GetGeoTransform()[1]
        y_resolution = ds.GetGeoTransform()[5]
        assert 1000 < x_resolution < 3000
        assert y_resolution == pytest.approx(-x_resolution)
        assert 200 < ds.RasterXSize < 1200
        assert 200 < ds.RasterYSize < 1200
        band = ds.GetRasterBand(1)
        assert band.GetNoDataValue() == float(np.float32(SFMS_NO_DATA))
        assert set(np.unique(band.ReadAsArray())) == {
            np.float32(SFMS_NO_DATA),
            2010,
            2030,
            500,
            102,
        }


@pytest.mark.parametrize("args", [[], ["--input", "missing.tif"]])
def test_missing_input(args):
    with pytest.raises(SystemExit) as error:
        generate_fuel_cog.main(args)
    assert error.value.code != 0


def test_identical_paths(fuel_raster):
    original = fuel_raster.read_bytes()
    with pytest.raises(SystemExit) as error:
        generate_fuel_cog.main(["--input", str(fuel_raster), "--output", str(fuel_raster)])
    assert error.value.code == 2
    assert fuel_raster.read_bytes() == original


def test_unwritable_output(fuel_raster, tmp_path):
    with pytest.raises(SystemExit) as error:
        generate_fuel_cog.main(
            ["--input", str(fuel_raster), "--output", str(tmp_path / "missing" / "out.tif")]
        )
    assert error.value.code == 1
