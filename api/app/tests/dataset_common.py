import numpy as np
from osgeo import osr, gdal
import uuid
from app.geospatial.wps_dataset import WPSDataset


def create_test_dataset(filename, width, height, extent, projection, data_type=gdal.GDT_Float32, fill_value=None, no_data_value=None) -> gdal.Dataset:
    """
    Create a test GDAL dataset.
    """
    # Create a new GDAL dataset
    driver: gdal.Driver = gdal.GetDriverByName("MEM")
    dataset: gdal.Dataset = driver.Create(filename, width, height, 1, data_type)

    # Set the geotransform
    xmin, xmax, ymin, ymax = extent
    xres = (xmax - xmin) / width
    yres = (ymax - ymin) / height
    geotransform = (xmin, xres, 0, ymax, 0, -yres)  # Top-left corner
    dataset.SetGeoTransform(geotransform)

    # Set the projection
    srs = osr.SpatialReference()
    srs.ImportFromEPSG(projection)
    dataset.SetProjection(srs.ExportToWkt())

    # Create some test data (e.g., random values)
    rng = np.random.default_rng(seed=42)  # Reproducible random generator
    fill_data = rng.random((height, width)).astype(np.float32)

    if fill_value is not None:
        fill_data = np.full((height, width), fill_value)

    if no_data_value is not None:
        dataset.GetRasterBand(1).SetNoDataValue(no_data_value)
    dataset.GetRasterBand(1).WriteArray(fill_data)

    return dataset


def create_mock_gdal_dataset():
    extent = (-1, 1, -1, 1)  # xmin, xmax, ymin, ymax
    return create_test_dataset(f"{str(uuid.uuid4())}.tif", 1, 1, extent, 4326, data_type=gdal.GDT_Byte, fill_value=1)


# Create a mock for the WPSDataset class
def create_mock_wps_dataset():
    mock_ds = create_mock_gdal_dataset()
    return WPSDataset(ds=mock_ds, ds_path=None)
