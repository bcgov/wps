from contextlib import ExitStack, contextmanager
from typing import Iterator, List, Optional, Tuple, Union
from osgeo import gdal, osr
import numpy as np
import io

from wps_shared.geospatial.geospatial import GDALResamplingMethod

gdal.UseExceptions()


class WPSDataset:
    """
    A wrapper around gdal datasets for common operations
    """

    def __init__(
        self,
        ds_path: Optional[str],
        ds=None,
        band: int = 1,
        chunk_size: int = 256,
        access=gdal.GA_ReadOnly,
    ):
        self.ds = ds
        self.ds_path = ds_path
        self.band = band
        self.chunk_size = chunk_size
        self.access = access

    def __enter__(self):
        if self.ds is None:
            self.ds: gdal.Dataset = gdal.Open(self.ds_path, self.access)

        return self

    def __exit__(self, *_):
        self.ds = None

    @classmethod
    def from_array(
        cls,
        array: np.ndarray,
        geotransform: Tuple[float, float, float, float, float, float],
        projection: str,
        nodata_value: Optional[Union[float, int]] = None,
        datatype=gdal.GDT_Float32,
    ) -> "WPSDataset":
        """
        Create a WPSDataset from a NumPy array, geotransform, and projection.

        :param array: NumPy array representing the raster data
        :param geotransform: A tuple defining the geotransform
        :param projection: WKT string of the projection
        :param nodata_value: Optional nodata value to set for the dataset
        :param datatype gdal datatype
        :return: An instance of WPSDataset containing the created dataset
        """
        rows, cols = array.shape

        driver: gdal.Driver = gdal.GetDriverByName("MEM")
        output_dataset: gdal.Dataset = driver.Create("memory", cols, rows, 1, datatype)

        # Set the geotransform and projection
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.SetProjection(projection)

        # Write the array to the dataset
        output_band: gdal.Band = output_dataset.GetRasterBand(1)
        output_band.WriteArray(array)

        # Set the NoData value if provided
        if nodata_value is not None:
            output_band.SetNoDataValue(nodata_value)

        # Flush cache to ensure all data is written
        output_band.FlushCache()

        return cls(ds_path=None, ds=output_dataset)

    @classmethod
    def from_bytes(cls, raster_bytes: bytes) -> "WPSDataset":
        """
        Create a WPSDataset from raw bytes.

        :param bytes: bytes representing the raster data
        :param datatype gdal datatype
        :return: An instance of WPSDataset containing the created dataset
        """
        with io.BytesIO(raster_bytes) as buffer:
            buffer.seek(0)  # rewind buffer to read from beginning
            path = "/vsimem/bytes_temp.tif"
            gdal.FileFromMemBuffer(path, buffer.read())
            dataset = gdal.Open(path)
            gdal.Unlink(path)
            return cls(ds_path=None, ds=dataset)

    def __mul__(self, other):
        """
        Multiplies this WPSDataset with the other WPSDataset

        :param other: WPSDataset
        :raises ValueError: Raised if this and other WPSDataset have mismatched raster dimensions
        :return: a new WPSDataset
        """
        # Get raster dimensions
        x_size = self.ds.RasterXSize
        y_size = self.ds.RasterYSize

        # Check if the dimensions of both rasters match
        if x_size != other.ds.RasterXSize or y_size != other.ds.RasterYSize:
            raise ValueError("The dimensions of the two rasters do not match.")

        # Get the geotransform and projection from the first raster
        geotransform = self.ds.GetGeoTransform()
        projection = self.ds.GetProjection()

        # Check if projection matches
        if projection != other.ds.GetProjection():
            raise ValueError("The projections of the two rasters do not match.")

        # Check if origin matches
        if (
            geotransform[0] != other.ds.GetGeoTransform()[0]
            or geotransform[3] != other.ds.GetGeoTransform()[3]
        ):
            raise ValueError("The origins of the two rasters do not match.")

        self_band: gdal.Band = self.ds.GetRasterBand(self.band)
        other_band: gdal.Band = other.ds.GetRasterBand(self.band)

        datatype = self_band.DataType

        # Create the output raster
        driver: gdal.Driver = gdal.GetDriverByName("MEM")
        out_ds: gdal.Dataset = driver.Create("memory", x_size, y_size, 1, datatype)

        # Set the geotransform and projection
        out_ds.SetGeoTransform(geotransform)
        out_ds.SetProjection(projection)

        # Process in chunks
        for y in range(0, y_size, self.chunk_size):
            y_chunk_size = min(self.chunk_size, y_size - y)

            for x in range(0, x_size, self.chunk_size):
                x_chunk_size = min(self.chunk_size, x_size - x)

                # Read chunks from both rasters
                self_chunk = self_band.ReadAsArray(x, y, x_chunk_size, y_chunk_size)
                other_chunk = other_band.ReadAsArray(x, y, x_chunk_size, y_chunk_size)
                wider_type = np.promote_types(self_chunk.dtype, other_chunk.dtype)

                self_chunk = self_chunk.astype(wider_type)
                other_chunk = other_chunk.astype(wider_type)

                other_chunk[other_chunk >= 1] = 1
                other_chunk[other_chunk < 1] = 0

                # Multiply the chunks
                self_chunk *= other_chunk

                # Write the result to the output raster
                out_ds.GetRasterBand(self.band).WriteArray(self_chunk, x, y)
                self_chunk = None
                other_chunk = None

        return WPSDataset(ds_path=None, ds=out_ds)

    def warp_to_match(
        self,
        other: "WPSDataset",
        output_path: str,
        resample_method: GDALResamplingMethod = GDALResamplingMethod.NEAREST_NEIGHBOUR,
        max_value: float | None = None,
    ):
        """
        Warp the dataset to match the extent, pixel size, and projection of the other dataset.

        :param other: the reference WPSDataset raster to match the source against
        :param output_path: output path of the resulting raster
        :param resample_method: gdal resampling algorithm
        :return: warped raster dataset
        """
        dest_geotransform = other.ds.GetGeoTransform()
        x_res = dest_geotransform[1]
        y_res = -dest_geotransform[5]
        minx = dest_geotransform[0]
        maxy = dest_geotransform[3]
        maxx = minx + dest_geotransform[1] * other.ds.RasterXSize
        miny = maxy + dest_geotransform[5] * other.ds.RasterYSize
        extent = [minx, miny, maxx, maxy]

        # we need the output to be a geotiff, since we cannot update grib files
        if not output_path.endswith(".tif"):
            output_path += ".tif"

        # Warp to match input option parameters
        warped_ds = gdal.Warp(
            output_path,
            self.ds,
            options=gdal.WarpOptions(
                dstSRS=other.ds.GetProjection(),
                outputBounds=extent,
                xRes=x_res,
                yRes=y_res,
                resampleAlg=resample_method.value,
            ),
        )

        if max_value is not None and warped_ds is not None:
            band = warped_ds.GetRasterBand(1)
            array = band.ReadAsArray()
            if (array > max_value).any():
                array = np.minimum(
                    array, max_value
                )  # clamp any value above the max_value to the max_value
                band.WriteArray(array)
                band.FlushCache()

        return WPSDataset(ds_path=None, ds=warped_ds)

    def replace_nodata_with(self, new_no_data_value: int = 0):
        """
        Reads the first band of a dataset, replaces NoData values with new_no_data_value, returns the array and the nodata value.
        :param new_no_data_value: the new nodata value
        """

        band: gdal.Band = self.ds.GetRasterBand(1)
        nodata_value = band.GetNoDataValue()
        array = band.ReadAsArray()

        array[array == nodata_value] = new_no_data_value

        return array, new_no_data_value

    def generate_latitude_array(self):
        """
        Transforms this dataset to 4326 to compute the latitude coordinates

        :return: array of latitude coordinates
        """
        geotransform = self.ds.GetGeoTransform()
        projection = self.ds.GetProjection()

        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(projection)

        x_size = self.ds.RasterXSize
        y_size = self.ds.RasterYSize

        tgt_srs = osr.SpatialReference()
        tgt_srs.ImportFromEPSG(4326)

        transform = osr.CoordinateTransformation(src_srs, tgt_srs)

        # empty array to store latitude values
        latitudes = np.zeros((y_size, x_size))

        for y in range(y_size):
            for x in range(x_size):
                x_coord = geotransform[0] + x * geotransform[1] + y * geotransform[2]
                y_coord = geotransform[3] + x * geotransform[4] + y * geotransform[5]

                _, lat, _ = transform.TransformPoint(x_coord, y_coord)

                latitudes[y, x] = lat

        return latitudes

    def export_to_geotiff(self, output_path: str):
        """
        Exports the dataset to a geotiff with the given path

        :param output_path: path to export the geotiff to
        """
        driver: gdal.Driver = gdal.GetDriverByName("GTiff")

        geotransform = self.ds.GetGeoTransform()
        projection = self.ds.GetProjection()

        band: gdal.Band = self.ds.GetRasterBand(self.band)
        datatype = band.DataType
        nodata_value = band.GetNoDataValue()
        array = band.ReadAsArray()

        rows, cols = array.shape
        output_dataset: gdal.Dataset = driver.Create(
            output_path, cols, rows, 1, datatype, options=["COMPRESS=LZW"]
        )
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.SetProjection(projection)

        output_band: gdal.Band = output_dataset.GetRasterBand(self.band)
        output_band.WriteArray(array)

        if nodata_value is not None:
            output_band.SetNoDataValue(nodata_value)

        output_band.FlushCache()
        output_dataset = None
        del output_dataset
        output_band = None
        del output_band

    def get_nodata_mask(self) -> Tuple[Optional[np.ndarray], Optional[Union[float, int]]]:
        band = self.ds.GetRasterBand(self.band)
        nodata_value = band.GetNoDataValue()

        if nodata_value is not None:
            nodata_mask = band.ReadAsArray() == nodata_value
            return nodata_mask, nodata_value

        return None, None

    def as_gdal_ds(self) -> gdal.Dataset:
        return self.ds

    def close(self):
        self.ds = None


@contextmanager
def multi_wps_dataset_context(dataset_paths: List[str]) -> Iterator[List[WPSDataset]]:
    """
    Context manager to handle multiple WPSDataset instances.

    :param dataset_paths: List of dataset paths to open as WPSDataset instances
    :yield: List of WPSDataset instances, one for each path
    """
    datasets = [WPSDataset(path) for path in dataset_paths]
    try:
        # Enter each dataset's context and yield the list of instances
        with ExitStack() as stack:
            yield [stack.enter_context(ds) for ds in datasets]
    finally:
        # Close all datasets to ensure cleanup
        for ds in datasets:
            ds.close()
