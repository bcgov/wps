"""Tests for the generic windowed multi-raster processing engine."""

import numpy as np
import pytest
from osgeo import gdal, osr

from wps_shared.geospatial.raster_processor import (
    RasterStep,
    TileConfig,
    create_output_dataset,
    iter_tiles,
    process_raster_chain,
    warp_to_match_vrt,
)

WGS84_WKT = osr.GetUserInputAsWKT("EPSG:4326")


def write_geotiff(
    path: str,
    array: np.ndarray,
    geotransform=(-120.0, 1.0, 0, 55.0, 0, -1.0),
    projection: str = WGS84_WKT,
) -> gdal.Dataset:
    height, width = array.shape
    driver = gdal.GetDriverByName("GTiff")
    ds = driver.Create(path, width, height, 1, gdal.GDT_Float32)
    ds.SetGeoTransform(geotransform)
    ds.SetProjection(projection)
    ds.GetRasterBand(1).WriteArray(array.astype(np.float32))
    ds.FlushCache()
    return ds


class TestIterTiles:
    def test_single_band_reassembles_to_original_array(self, tmp_path):
        data = np.arange(20, dtype=np.float32).reshape(4, 5)
        ds = write_geotiff(str(tmp_path / "a.tif"), data)
        band = ds.GetRasterBand(1)

        result = np.zeros_like(data)
        for col_off, row_off, w, h, (tile,) in iter_tiles(
            [band], ds.RasterXSize, ds.RasterYSize, TileConfig(tile_width=2, tile_height=3)
        ):
            result[row_off : row_off + h, col_off : col_off + w] = tile

        np.testing.assert_array_equal(result, data)

    def test_multiple_bands_read_the_same_window(self, tmp_path):
        a_data = np.arange(20, dtype=np.float32).reshape(4, 5)
        b_data = (a_data * 10).astype(np.float32)
        a_ds = write_geotiff(str(tmp_path / "a.tif"), a_data)
        b_ds = write_geotiff(str(tmp_path / "b.tif"), b_data)

        a_result = np.zeros_like(a_data)
        b_result = np.zeros_like(b_data)
        for col_off, row_off, w, h, (a_tile, b_tile) in iter_tiles(
            [a_ds.GetRasterBand(1), b_ds.GetRasterBand(1)],
            a_ds.RasterXSize,
            a_ds.RasterYSize,
            TileConfig(tile_width=2, tile_height=2),
        ):
            a_result[row_off : row_off + h, col_off : col_off + w] = a_tile
            b_result[row_off : row_off + h, col_off : col_off + w] = b_tile

        np.testing.assert_array_equal(a_result, a_data)
        np.testing.assert_array_equal(b_result, b_data)

    def test_tile_larger_than_raster_yields_a_single_window(self, tmp_path):
        data = np.ones((3, 3), dtype=np.float32)
        ds = write_geotiff(str(tmp_path / "a.tif"), data)
        windows = list(
            iter_tiles([ds.GetRasterBand(1)], ds.RasterXSize, ds.RasterYSize, TileConfig(100, 100))
        )
        assert len(windows) == 1
        col_off, row_off, w, h, (tile,) = windows[0]
        assert (col_off, row_off, w, h) == (0, 0, 3, 3)
        np.testing.assert_array_equal(tile, data)

    def test_uneven_dimensions_cover_every_pixel_exactly_once(self, tmp_path):
        data = np.arange(35, dtype=np.float32).reshape(7, 5)
        ds = write_geotiff(str(tmp_path / "a.tif"), data)

        covered = np.zeros(data.shape, dtype=int)
        for col_off, row_off, w, h, (tile,) in iter_tiles(
            [ds.GetRasterBand(1)],
            ds.RasterXSize,
            ds.RasterYSize,
            TileConfig(tile_width=3, tile_height=3),
        ):
            covered[row_off : row_off + h, col_off : col_off + w] += 1
            assert tile.shape == (h, w)

        assert np.all(covered == 1)


class TestCreateOutputDataset:
    def test_matches_source_extent_and_projection(self, tmp_path):
        src_ds = write_geotiff(str(tmp_path / "src.tif"), np.zeros((4, 6), dtype=np.float32))
        out_ds = create_output_dataset(str(tmp_path / "out.tif"), src_ds)

        assert (out_ds.RasterXSize, out_ds.RasterYSize) == (6, 4)
        assert out_ds.GetGeoTransform() == src_ds.GetGeoTransform()
        assert out_ds.GetProjection() == src_ds.GetProjection()
        assert out_ds.GetRasterBand(1).DataType == gdal.GDT_Byte

    def test_is_tiled_and_compressed(self, tmp_path):
        src_ds = write_geotiff(str(tmp_path / "src.tif"), np.zeros((4, 4), dtype=np.float32))
        out_path = str(tmp_path / "out.tif")
        out_ds = create_output_dataset(out_path, src_ds)
        out_ds.GetRasterBand(1).Fill(0)
        out_ds.FlushCache()
        out_ds = None

        # COMPRESSION only shows up in IMAGE_STRUCTURE metadata once the GTiff directory is
        # finalized, which GDAL only does on close - so reopen rather than reuse the write handle.
        reopened = gdal.Open(out_path)
        metadata = reopened.GetMetadata("IMAGE_STRUCTURE")
        assert metadata.get("COMPRESSION") == "LZW"


class TestWarpToMatchVrt:
    def test_returns_a_vrt_dataset(self, tmp_path):
        """Confirms the result is a virtual (lazy) dataset, not a materialized raster."""
        src_ds = write_geotiff(str(tmp_path / "src.tif"), np.ones((4, 4), dtype=np.float32))
        match_ds = write_geotiff(str(tmp_path / "match.tif"), np.zeros((4, 4), dtype=np.float32))

        warped = warp_to_match_vrt(src_ds, match_ds)

        assert warped.GetDriver().ShortName == "VRT"

    def test_matches_reference_grid(self, tmp_path):
        src_ds = write_geotiff(str(tmp_path / "src.tif"), np.ones((4, 4), dtype=np.float32))
        # match_ds covers a different extent/resolution than src_ds
        match_ds = write_geotiff(
            str(tmp_path / "match.tif"),
            np.zeros((2, 2), dtype=np.float32),
            geotransform=(-120.0, 2.0, 0, 55.0, 0, -2.0),
        )

        warped = warp_to_match_vrt(src_ds, match_ds)

        assert (warped.RasterXSize, warped.RasterYSize) == (
            match_ds.RasterXSize,
            match_ds.RasterYSize,
        )
        assert warped.GetGeoTransform() == match_ds.GetGeoTransform()

    def test_tile_reads_match_an_eager_warp(self, tmp_path):
        """Reading the lazy VRT tile by tile must produce the same pixels as gdal.Warp()'ing
        the whole raster eagerly - laziness is a read-time optimization, not a different
        result."""
        rng = np.random.default_rng(seed=3)
        src_data = rng.uniform(0, 100, size=(6, 6)).astype(np.float32)
        src_ds = write_geotiff(
            str(tmp_path / "src.tif"), src_data, geotransform=(-120.0, 0.5, 0, 55.0, 0, -0.5)
        )
        match_ds = write_geotiff(
            str(tmp_path / "match.tif"),
            np.zeros((4, 4), dtype=np.float32),
            geotransform=(-120.0, 1.0, 0, 55.0, 0, -1.0),
        )

        eager_path = str(tmp_path / "eager.tif")
        gdal.Warp(
            eager_path,
            src_ds,
            dstSRS=match_ds.GetProjection(),
            outputBounds=[-120.0, 51.0, -116.0, 55.0],
            xRes=1.0,
            yRes=1.0,
            resampleAlg=gdal.GRA_NearestNeighbour,
        )
        eager_ds = gdal.Open(eager_path)
        eager_array = eager_ds.GetRasterBand(1).ReadAsArray()

        warped = warp_to_match_vrt(src_ds, match_ds)
        result = np.zeros((4, 4), dtype=np.float32)
        for col_off, row_off, w, h, (tile,) in iter_tiles(
            [warped.GetRasterBand(1)], 4, 4, TileConfig(tile_width=2, tile_height=2)
        ):
            result[row_off : row_off + h, col_off : col_off + w] = tile

        np.testing.assert_array_equal(result, eager_array)

    def test_combines_with_iter_tiles_for_multi_raster_windowed_read(self, tmp_path):
        """End-to-end: a raster already on the target grid and a raster warped lazily onto it
        can be read together tile by tile, with neither one fully materialized up front."""
        a_data = np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32)
        a_ds = write_geotiff(
            str(tmp_path / "a.tif"), a_data, geotransform=(-120.0, 1.0, 0, 55.0, 0, -1.0)
        )
        # b is on a finer grid covering the same extent/projection
        b_data = np.full((4, 4), 2.0, dtype=np.float32)
        b_ds = write_geotiff(
            str(tmp_path / "b.tif"), b_data, geotransform=(-120.0, 0.5, 0, 55.0, 0, -0.5)
        )

        warped_b = warp_to_match_vrt(b_ds, a_ds)

        combined = np.zeros((2, 2), dtype=np.float32)
        for col_off, row_off, w, h, (a_tile, b_tile) in iter_tiles(
            [a_ds.GetRasterBand(1), warped_b.GetRasterBand(1)],
            2,
            2,
            TileConfig(tile_width=1, tile_height=1),
        ):
            combined[row_off : row_off + h, col_off : col_off + w] = a_tile * b_tile

        np.testing.assert_array_equal(combined, a_data * 2.0)


class TestProcessRasterChain:
    def test_two_step_chain_classifies_then_masks(self, tmp_path):
        a_ds = write_geotiff(str(tmp_path / "a.tif"), np.array([[3.0, 7.0]], dtype=np.float32))
        b_ds = write_geotiff(str(tmp_path / "b.tif"), np.array([[1.0, 0.0]], dtype=np.float32))

        def classify(tile, _accumulated):
            return np.where(tile >= 5, 2, 1).astype(np.uint8)

        def mask(tile, accumulated):
            return (accumulated * tile).astype(np.uint8)

        output_path = str(tmp_path / "out.tif")
        process_raster_chain(
            output_path,
            [RasterStep(a_ds, classify), RasterStep(b_ds, mask)],
        )

        out_ds = gdal.Open(output_path)
        # a=[3,7] -> classified [1,2]; b=[1,0] -> masked [1*1, 2*0] = [1, 0]
        assert out_ds.GetRasterBand(1).ReadAsArray().tolist() == [[1, 0]]

    def test_three_step_chain_applies_steps_in_order(self, tmp_path):
        a_ds = write_geotiff(str(tmp_path / "a.tif"), np.array([[2.0]], dtype=np.float32))
        b_ds = write_geotiff(str(tmp_path / "b.tif"), np.array([[3.0]], dtype=np.float32))
        c_ds = write_geotiff(str(tmp_path / "c.tif"), np.array([[4.0]], dtype=np.float32))

        def start(tile, _accumulated):
            return tile

        def add(tile, accumulated):
            return accumulated + tile

        output_path = str(tmp_path / "out.tif")
        process_raster_chain(
            output_path,
            [RasterStep(a_ds, start), RasterStep(b_ds, add), RasterStep(c_ds, add)],
            output_dtype=gdal.GDT_Float32,
        )

        out_ds = gdal.Open(output_path)
        assert out_ds.GetRasterBand(1).ReadAsArray().tolist() == [[9.0]]

    def test_second_raster_on_a_different_grid_is_aligned_automatically(self, tmp_path):
        """The reference (first) raster's grid drives the output; other rasters are warped to
        match it automatically, without the caller pre-aligning them."""
        a_ds = write_geotiff(
            str(tmp_path / "a.tif"),
            np.array([[10.0, 20.0], [30.0, 40.0]], dtype=np.float32),
            geotransform=(-120.0, 1.0, 0, 55.0, 0, -1.0),
        )
        # b is on a finer grid covering the same extent
        b_ds = write_geotiff(
            str(tmp_path / "b.tif"),
            np.full((4, 4), 2.0, dtype=np.float32),
            geotransform=(-120.0, 0.5, 0, 55.0, 0, -0.5),
        )

        def start(tile, _accumulated):
            return tile

        def multiply(tile, accumulated):
            return accumulated * tile

        output_path = str(tmp_path / "out.tif")
        process_raster_chain(
            output_path,
            [RasterStep(a_ds, start), RasterStep(b_ds, multiply)],
            output_dtype=gdal.GDT_Float32,
        )

        out_ds = gdal.Open(output_path)
        np.testing.assert_array_equal(
            out_ds.GetRasterBand(1).ReadAsArray(), [[20.0, 40.0], [60.0, 80.0]]
        )

    def test_output_nodata_value_is_set(self, tmp_path):
        a_ds = write_geotiff(str(tmp_path / "a.tif"), np.array([[1.0]], dtype=np.float32))
        b_ds = write_geotiff(str(tmp_path / "b.tif"), np.array([[1.0]], dtype=np.float32))

        output_path = str(tmp_path / "out.tif")
        process_raster_chain(
            output_path,
            [RasterStep(a_ds, lambda tile, _acc: tile), RasterStep(b_ds, lambda tile, acc: acc)],
            output_nodata=255,
        )

        out_ds = gdal.Open(output_path)
        assert out_ds.GetRasterBand(1).GetNoDataValue() == 255

    def test_requires_at_least_two_steps(self, tmp_path):
        a_ds = write_geotiff(str(tmp_path / "a.tif"), np.array([[1.0]], dtype=np.float32))

        with pytest.raises(ValueError):
            process_raster_chain(
                str(tmp_path / "out.tif"), [RasterStep(a_ds, lambda tile, _acc: tile)]
            )

    def test_tiling_matches_untiled_result(self, tmp_path):
        rng = np.random.default_rng(seed=5)
        a_data = rng.uniform(0, 10, size=(7, 5)).astype(np.float32)
        b_data = rng.uniform(0, 10, size=(7, 5)).astype(np.float32)
        a_ds = write_geotiff(str(tmp_path / "a.tif"), a_data)
        b_ds = write_geotiff(str(tmp_path / "b.tif"), b_data)

        def start(tile, _accumulated):
            return tile

        def add(tile, accumulated):
            return accumulated + tile

        whole_path = str(tmp_path / "whole.tif")
        process_raster_chain(
            whole_path,
            [RasterStep(a_ds, start), RasterStep(b_ds, add)],
            tile_config=TileConfig(tile_width=100, tile_height=100),
            output_dtype=gdal.GDT_Float32,
        )

        tiled_path = str(tmp_path / "tiled.tif")
        process_raster_chain(
            tiled_path,
            [RasterStep(a_ds, start), RasterStep(b_ds, add)],
            tile_config=TileConfig(tile_width=2, tile_height=3),
            output_dtype=gdal.GDT_Float32,
        )

        whole_ds = gdal.Open(whole_path)
        tiled_ds = gdal.Open(tiled_path)
        np.testing.assert_array_equal(
            whole_ds.GetRasterBand(1).ReadAsArray(), tiled_ds.GetRasterBand(1).ReadAsArray()
        )
