import numpy as np
from osgeo import gdal, osr

from app.auto_spatial_advisory.local.generate_classified_tpi import write_classified_tpi


def test_write_classified_tpi_preserves_grid_and_uses_tiled_storage(tmp_path):
    values = np.array(
        [
            [-2, -1, -0.5],
            [-0.3, 0, 0.3],
            [0.5, 1, 2],
        ],
        dtype=np.float32,
    )
    expected_classes = np.array(
        [
            [0, 1, 1],
            [2, 2, 2],
            [3, 4, 4],
        ],
        dtype=np.uint8,
    )
    transform = (100, 50, 0, 200, 0, -50)
    spatial_reference = osr.SpatialReference()
    spatial_reference.ImportFromEPSG(3005)

    source = gdal.GetDriverByName("MEM").Create("", 3, 3, 1, gdal.GDT_Float32)
    source.SetGeoTransform(transform)
    source.SetProjection(spatial_reference.ExportToWkt())
    source.GetRasterBand(1).WriteArray(values)
    output_path = str(tmp_path / "classified_tpi.tif")

    write_classified_tpi(source, output_path)

    output = gdal.Open(output_path, gdal.GA_ReadOnly)
    output_band = output.GetRasterBand(1)
    np.testing.assert_array_equal(output_band.ReadAsArray(), expected_classes)
    assert output_band.DataType == gdal.GDT_Byte
    assert output_band.GetNoDataValue() == 4
    assert output_band.GetBlockSize() == [256, 256]
    assert output.GetGeoTransform() == transform
    assert output.GetSpatialRef().IsSame(spatial_reference)
    assert output.GetMetadata("IMAGE_STRUCTURE")["COMPRESSION"] == "DEFLATE"
    output = None
