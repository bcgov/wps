import io
import math
from contextlib import ExitStack, contextmanager
from typing import Iterator, List, NamedTuple, Optional, Tuple

import numpy as np
from osgeo import gdal, gdal_array, ogr, osr
from wps_shared.geospatial.geospatial import GDALResamplingMethod, rasters_match

from wps_dataset.raster_processor import (
    RasterStep,
    TileConfig,
    create_output_dataset,
    iter_tiles,
    map_tile_array,
    process_raster_chain,
    warp_to_match_vrt,
)

gdal.UseExceptions()


class Georeference(NamedTuple):
    """A dataset's geotransform and projection, e.g. to pass straight to `WPSDataset.from_array`."""

    geotransform: Tuple[float, float, float, float, float, float]
    projection: str


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
        """
        Every result a WPSDataset method derives (`*`, `warp_to_match`, `clip_to_geometry`,
        `from_array`, ...) stays in memory - a lazy VRT where possible, an in-memory MEM
        dataset otherwise. `export_to_geotiff()` is the only way to put a WPSDataset on disk.
        """
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
        self.close()

    def read_array(self) -> np.ndarray:
        """Read this dataset's band into a NumPy array, one tile at a time."""
        band = self.ds.GetRasterBand(self.band)
        dtype = gdal_array.GDALTypeCodeToNumericTypeCode(band.DataType)
        return map_tile_array(
            band, self.ds.RasterXSize, self.ds.RasterYSize, lambda tile: tile, dtype
        )

    @classmethod
    def from_array(
        cls,
        array: np.ndarray,
        georeference: "WPSDataset | Georeference",
        nodata_value: float | int | None = None,
        datatype=gdal.GDT_Float32,
    ) -> "WPSDataset":
        """
        Create an in-memory WPSDataset from a NumPy array, georeferenced to match either an
        existing WPSDataset or an explicit Georeference. Use export_to_geotiff() on the result
        if you need it on disk.

        :param array: NumPy array representing the raster data
        :param georeference: A WPSDataset to take the geotransform/projection from, or an
            explicit Georeference(geotransform, projection) - e.g. when the source dataset
            has already been closed, or there never was a WPSDataset to begin with.
        :param nodata_value: Optional nodata value to set for the dataset
        :param datatype gdal datatype
        :return: An instance of WPSDataset containing the created dataset
        """
        geotransform, projection = (
            georeference.georeference if isinstance(georeference, WPSDataset) else georeference
        )
        rows, cols = array.shape

        output_dataset: gdal.Dataset = gdal.GetDriverByName("MEM").Create(
            "", cols, rows, 1, datatype
        )

        # Set the geotransform and projection
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.SetProjection(projection)

        # Write the array to the dataset, one tile at a time. Note: `array` is already fully
        # in memory here (the caller had to build it to pass it in) - tiling the write doesn't
        # reduce memory for this method, it just avoids a bare WriteArray() call.
        output_band: gdal.Band = output_dataset.GetRasterBand(1)
        config = TileConfig()
        for row_off in range(0, rows, config.tile_height):
            h = min(config.tile_height, rows - row_off)
            for col_off in range(0, cols, config.tile_width):
                w = min(config.tile_width, cols - col_off)
                output_band.WriteArray(
                    array[row_off : row_off + h, col_off : col_off + w], col_off, row_off
                )

        # Set the NoData value if provided
        if nodata_value is not None:
            output_band.SetNoDataValue(nodata_value)

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
        Multiplies this WPSDataset with the other WPSDataset. The result is always an
        in-memory MEM dataset - export_to_geotiff() is the only way to put a WPSDataset on
        disk. Runs as a 2-step process_raster_chain (non-aligning: both rasters must already
        share the same grid, same as this method always required) so neither raster is ever
        held in memory as a whole - only one `chunk_size`×`chunk_size` tile of each at a time.

        :param other: WPSDataset
        :raises ValueError: Raised if this and other WPSDataset have mismatched raster dimensions
        :return: a new WPSDataset
        """
        self_band: gdal.Band = self.ds.GetRasterBand(self.band)
        datatype = self_band.DataType

        def multiply(tile: np.ndarray, accumulated: np.ndarray) -> np.ndarray:
            wider_type = np.promote_types(accumulated.dtype, tile.dtype)
            accumulated = accumulated.astype(wider_type)
            other_tile = tile.astype(wider_type)
            other_tile[other_tile >= 1] = 1
            other_tile[other_tile < 1] = 0
            return accumulated * other_tile

        out_ds = process_raster_chain(
            None,
            [
                RasterStep(self.ds, lambda tile, _acc: tile, align=False, band_index=self.band),
                RasterStep(other.ds, multiply, align=False, band_index=self.band),
            ],
            tile_config=TileConfig(tile_width=self.chunk_size, tile_height=self.chunk_size),
            output_dtype=datatype,
        )

        return WPSDataset(ds_path=None, ds=out_ds)

    def warp_to_match(
        self,
        other: "WPSDataset",
        resample_method: GDALResamplingMethod = GDALResamplingMethod.NEAREST_NEIGHBOUR,
        max_value: float | None = None,
    ):
        """
        Warp the dataset to match the extent, pixel size, and projection of the other dataset.

        The result is backed by a warped VRT - lazy: no source pixel is actually warped until
        something reads a window of it, so this composes with further WPSDataset operations
        (`*`, another warp_to_match, ...) without materializing anything. Passing max_value
        forces materialization into an in-memory MEM dataset instead (tile by tile, never as
        one whole-raster buffer) - a VRT is read-only, so clamping needs a writable raster.
        export_to_geotiff() is the only way to put a WPSDataset on disk.

        :param other: the reference WPSDataset raster to match the source against
        :param resample_method: gdal resampling algorithm
        :param max_value: clamp any warped value above this - forces materialization
        :return: warped raster dataset
        """
        warped_vrt_ds = warp_to_match_vrt(self.ds, other.ds, resample_alg=resample_method.value)

        if max_value is None:
            return WPSDataset(ds_path=None, ds=warped_vrt_ds)

        vrt_band = warped_vrt_ds.GetRasterBand(1)
        out_ds = create_output_dataset(None, warped_vrt_ds, dtype=vrt_band.DataType)
        out_band = out_ds.GetRasterBand(1)
        for col_off, row_off, w, h, (tile,) in iter_tiles(
            [vrt_band], warped_vrt_ds.RasterXSize, warped_vrt_ds.RasterYSize
        ):
            out_band.WriteArray(np.minimum(tile, max_value), col_off, row_off)

        return WPSDataset(ds_path=None, ds=out_ds)

    def clip_to_geometry(self, cutline: ogr.Geometry | str) -> "WPSDataset":
        """
        Clip this dataset to a cutline using GDAL's cutline warp.

        The result is backed by a lazy, read-only VRT - no source pixel is actually clipped
        until something reads a window of it, so this composes with further WPSDataset
        operations without materializing anything. export_to_geotiff() is the only way to put
        a WPSDataset on disk.

        :param cutline: An ogr.Geometry (with its spatial reference set) to cut to, or a path
            to a vector file (e.g. GeoJSON) to use as the cutline instead.
        :return: a new WPSDataset clipped to the cutline
        """
        if isinstance(cutline, str):
            warp_options = gdal.WarpOptions(format="VRT", cutlineDSName=cutline, cropToCutline=True)
        else:
            warp_options = gdal.WarpOptions(
                format="VRT",
                cutlineWKT=cutline,
                cutlineSRS=cutline.GetSpatialReference(),
                cropToCutline=True,
            )

        clipped_ds = gdal.Warp("", self.ds, options=warp_options)
        return WPSDataset(ds_path=None, ds=clipped_ds)

    def replace_nodata_with(self, new_no_data_value: int = 0):
        """
        Reads the first band of a dataset, replaces NoData values with new_no_data_value, returns the array and the nodata value.
        :param new_no_data_value: the new nodata value
        """

        band: gdal.Band = self.ds.GetRasterBand(1)
        nodata_value = band.GetNoDataValue()

        dtype = gdal_array.GDALTypeCodeToNumericTypeCode(band.DataType)
        if np.isnan(new_no_data_value) and not np.issubdtype(dtype, np.floating):
            dtype = np.float64

        def replace(tile: np.ndarray) -> np.ndarray:
            tile = tile.astype(dtype)
            if nodata_value is not None:
                tile[tile == nodata_value] = new_no_data_value
            return tile

        array = map_tile_array(band, self.ds.RasterXSize, self.ds.RasterYSize, replace, dtype)

        return array, new_no_data_value

    def generate_latitude_array(self):
        """
        Transforms this dataset to 4326 to compute the latitude coordinates.

        Note: This method is slow for large rasters. Consider using
        get_lat_lon_coords() for vectorized coordinate transformation.

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

    def get_lat_lon_coords(
        self, valid_mask: Optional[np.ndarray] = None
    ) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
        """
        Get WGS84 lat/lon coordinates for pixels, with optional masking.

        Uses vectorized transformation for fast coordinate conversion.

        :param valid_mask: Optional boolean mask (y_size, x_size) of valid pixels.
                          If None, uses nodata mask from the raster band.
        :return: Tuple of (lats, lons, yi_indices, xi_indices) for valid pixels.
                 - lats: 1D array of latitudes
                 - lons: 1D array of longitudes
                 - yi_indices: 1D array of y (row) indices
                 - xi_indices: 1D array of x (column) indices
        """
        geotransform = self.ds.GetGeoTransform()
        projection = self.ds.GetProjection()
        x_size = self.ds.RasterXSize
        y_size = self.ds.RasterYSize

        # Setup coordinate transformation
        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(projection)
        # Use traditional GIS order (lon, lat) for consistent axis ordering
        src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        tgt_srs = osr.SpatialReference()
        tgt_srs.ImportFromEPSG(4326)
        tgt_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)
        transform = osr.CoordinateTransformation(src_srs, tgt_srs)

        # Create coordinate grids for all pixels
        xi_grid, yi_grid = np.meshgrid(np.arange(x_size), np.arange(y_size))

        # Calculate pixel center coordinates in raster projection
        x_coords = geotransform[0] + (xi_grid + 0.5) * geotransform[1]
        y_coords = geotransform[3] + (yi_grid + 0.5) * geotransform[5]

        # Build valid mask if not provided
        if valid_mask is None:
            valid_mask = self.get_valid_mask()

        # Get indices and coordinates for valid pixels only
        valid_yi, valid_xi = np.nonzero(valid_mask)
        valid_x_coords = x_coords[valid_mask]
        valid_y_coords = y_coords[valid_mask]

        # Transform all coordinates at once
        coords_to_transform = list(zip(valid_x_coords.astype(float), valid_y_coords.astype(float)))
        transformed = transform.TransformPoints(coords_to_transform)

        # Extract lat/lon (TransformPoints returns (x, y, z) in target SRS)
        lats = np.array([t[1] for t in transformed])
        lons = np.array([t[0] for t in transformed])

        return lats, lons, valid_yi, valid_xi

    def export_to_geotiff(self, output_path: str):
        """
        Exports the dataset to a geotiff with the given path. This is the only WPSDataset
        method that writes to a real file - every other method's result stays in memory.

        :param output_path: path to export the geotiff to
        """
        driver: gdal.Driver = gdal.GetDriverByName("GTiff")

        geotransform = self.ds.GetGeoTransform()
        projection = self.ds.GetProjection()

        band: gdal.Band = self.ds.GetRasterBand(self.band)
        datatype = band.DataType
        nodata_value = band.GetNoDataValue()
        x_size, y_size = self.ds.RasterXSize, self.ds.RasterYSize

        output_dataset: gdal.Dataset = driver.Create(
            output_path, x_size, y_size, 1, datatype, options=["COMPRESS=LZW"]
        )
        output_dataset.SetGeoTransform(geotransform)
        output_dataset.SetProjection(projection)

        output_band: gdal.Band = output_dataset.GetRasterBand(self.band)
        for col_off, row_off, w, h, (tile,) in iter_tiles([band], x_size, y_size):
            output_band.WriteArray(tile, col_off, row_off)
        output_band.SetDescription(band.GetDescription())
        output_band.SetUnitType(band.GetUnitType())

        if nodata_value is not None:
            output_band.SetNoDataValue(nodata_value)

        output_band.FlushCache()
        output_dataset = None
        del output_dataset
        output_band = None
        del output_band

    def apply_mask(self, mask_ds: "WPSDataset") -> np.ndarray:
        """
        Apply a mask from another dataset to get a valid mask array.

        The mask dataset's grid must match this dataset (size, geotransform, projection).
        The caller is responsible for reprojecting the mask to match (see warp_to_match)
        before calling this method.
        Pixels are valid where the mask value is non-zero and not nodata.

        :param mask_ds: WPSDataset containing mask (0 = masked, non-zero = valid)
        :return: Boolean array where True = valid, False = masked
        :raises ValueError: If the mask grid does not match this dataset's grid
        """
        if not rasters_match(self.ds, mask_ds.ds):
            raise ValueError("Mask grid does not match reference grid")

        mask_band: gdal.Band = mask_ds.ds.GetRasterBand(1)
        mask_nodata = mask_band.GetNoDataValue()

        def valid(tile: np.ndarray) -> np.ndarray:
            # Mask is valid where value is non-zero and not nodata
            tile_valid = tile != 0
            if mask_nodata is not None:
                tile_valid = tile_valid & (tile != mask_nodata)
            return tile_valid

        return map_tile_array(
            mask_band, mask_ds.ds.RasterXSize, mask_ds.ds.RasterYSize, valid, dtype=bool
        )

    def get_valid_mask(self) -> np.ndarray:
        """
        Get a boolean mask indicating valid (non-nodata) pixels.

        :return: Boolean array where True = valid, False = nodata
        """
        band: gdal.Band = self.ds.GetRasterBand(self.band)
        nodata = band.GetNoDataValue()
        x_size, y_size = self.ds.RasterXSize, self.ds.RasterYSize

        if nodata is None:
            return np.ones((y_size, x_size), dtype=bool)

        return map_tile_array(band, x_size, y_size, lambda tile: tile != nodata, dtype=bool)

    def get_nodata_mask(self) -> Tuple[Optional[np.ndarray], float | int | None]:
        band = self.ds.GetRasterBand(self.band)
        nodata_value = band.GetNoDataValue()

        if nodata_value is None:
            return None, None

        nodata_mask = map_tile_array(
            band,
            self.ds.RasterXSize,
            self.ds.RasterYSize,
            lambda tile: tile == nodata_value,
            dtype=bool,
        )
        return nodata_mask, nodata_value

    def as_gdal_ds(self) -> gdal.Dataset:
        return self.ds

    @property
    def georeference(self) -> Georeference:
        """This dataset's geotransform and projection, e.g. to pass straight to `from_array`."""
        return Georeference(self.ds.GetGeoTransform(), self.ds.GetProjection())

    def extract_value_at_point(self, lat: float, lon: float) -> Optional[float]:
        """Return the raster value at a WGS84 lat/lon coordinate, or None if out of bounds or nodata."""
        geotransform = self.ds.GetGeoTransform()

        src_srs = osr.SpatialReference()
        src_srs.ImportFromWkt(self.ds.GetProjection())
        src_srs.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        wgs84 = osr.SpatialReference()
        wgs84.ImportFromEPSG(4326)
        wgs84.SetAxisMappingStrategy(osr.OAMS_TRADITIONAL_GIS_ORDER)

        x, y, _ = osr.CoordinateTransformation(wgs84, src_srs).TransformPoint(lon, lat)

        # Use GDAL's own inverse transform rather than manual division: it handles
        # rotated/sheared geotransforms, and floor() (vs int() truncation) correctly
        # sends points fractionally outside the raster (e.g. col == -0.0003) to a
        # negative pixel coordinate instead of rounding them into bounds at 0.
        inverse_geotransform = gdal.InvGeoTransform(geotransform)
        pixel_x, pixel_y = gdal.ApplyGeoTransform(inverse_geotransform, x, y)
        col = math.floor(pixel_x)
        row = math.floor(pixel_y)

        if row < 0 or row >= self.ds.RasterYSize or col < 0 or col >= self.ds.RasterXSize:
            return None

        band = self.ds.GetRasterBand(1)
        nodata = band.GetNoDataValue()
        value = float(band.ReadAsArray(col, row, 1, 1)[0][0])

        if nodata is not None and math.isclose(value, nodata, rel_tol=1e-9):
            return None

        return value

    def close(self):
        # Nothing this class creates internally is ever backed by a real file. Every
        # derived result is a lazy VRT or an in-memory MEM dataset, and export_to_geotiff() (the
        # only method that writes to a real path) doesn't return a WPSDataset to close. So
        # there's nothing to gdal.Unlink() here; a dataset merely opened via WPSDataset(path)
        # is the caller's file regardless, and was never something close() should delete.
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
