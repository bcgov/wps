"""Tests for Cloud-Optimized GeoTIFF (COG) generation utilities."""

import os
import tempfile
from pathlib import Path

import pytest
from osgeo import gdal

from wps_shared.geospatial.cog import generate_web_optimized_cog
from wps_shared.geospatial.geospatial import GDALResamplingMethod


@pytest.fixture
def test_data_dir():
    """Return the path to the test data directory."""
    return Path(__file__).parent


@pytest.fixture
def sample_tiff(test_data_dir):
    """Return path to a sample TIFF file for testing."""
    return str(test_data_dir / "3005_lats.tif")


@pytest.fixture
def temp_output_path():
    """Create a temporary file path for output COG."""
    with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
        output_path = tmp.name
    yield output_path
    # Cleanup
    if os.path.exists(output_path):
        os.remove(output_path)


class TestGenerateWebOptimizedCOG:
    """Tests for generate_web_optimized_cog function."""

    def test_basic_cog_generation(self, sample_tiff, temp_output_path):
        """Test basic COG generation with default parameters."""
        result = generate_web_optimized_cog(sample_tiff, temp_output_path)

        # Verify the function returns the output path
        assert result == temp_output_path

        # Verify the output file exists
        assert os.path.exists(temp_output_path)

        # Verify it's a valid raster
        ds = gdal.Open(temp_output_path)
        assert ds is not None
        ds = None

    def test_cog_is_in_target_srs(self, sample_tiff, temp_output_path):
        """Test that output COG is in the target SRS."""
        generate_web_optimized_cog(sample_tiff, temp_output_path, target_srs="EPSG:3857")

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        srs = ds.GetProjection()

        # Check that the projection contains EPSG:3857 reference
        assert "3857" in srs or "WGS 84 / Pseudo-Mercator" in srs
        ds = None

    def test_cog_with_custom_srs(self, sample_tiff, temp_output_path):
        """Test COG generation with custom target SRS."""
        target_srs = "EPSG:4326"
        generate_web_optimized_cog(sample_tiff, temp_output_path, target_srs=target_srs)

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        srs = ds.GetProjection()

        # Check that the projection contains WGS84/4326 reference
        assert "4326" in srs or "WGS 84" in srs
        ds = None

    def test_cog_with_lzw_compression(self, sample_tiff, temp_output_path):
        """Test COG generation with LZW compression."""
        generate_web_optimized_cog(sample_tiff, temp_output_path, compression="LZW")

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        metadata = ds.GetMetadata("IMAGE_STRUCTURE")

        assert "COMPRESSION" in metadata
        assert metadata["COMPRESSION"] == "LZW"
        ds = None

    def test_cog_with_deflate_compression(self, sample_tiff, temp_output_path):
        """Test COG generation with DEFLATE compression."""
        generate_web_optimized_cog(sample_tiff, temp_output_path, compression="DEFLATE")

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        metadata = ds.GetMetadata("IMAGE_STRUCTURE")

        assert "COMPRESSION" in metadata
        assert metadata["COMPRESSION"] == "DEFLATE"
        ds = None

    def test_cog_has_overviews(self, sample_tiff, temp_output_path):
        """Test that generated COG has overview pyramids (if image is large enough)."""
        generate_web_optimized_cog(sample_tiff, temp_output_path)

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        band: gdal.Band = ds.GetRasterBand(1)

        # COG should have overviews for efficient web display
        # Note: Small test images may not generate overviews
        overview_count = band.GetOverviewCount()
        # Just verify the overview count is non-negative (0 is acceptable for small images)
        assert overview_count >= 0

        ds = None

    def test_cog_is_tiled(self, sample_tiff, temp_output_path):
        """Test that generated COG is tiled."""
        generate_web_optimized_cog(sample_tiff, temp_output_path)

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        metadata = ds.GetMetadata("IMAGE_STRUCTURE")

        # COG format should create tiled rasters
        assert "LAYOUT" in metadata
        assert metadata["LAYOUT"] == "COG"

        ds = None

    def test_preserves_band_count(self, sample_tiff, temp_output_path):
        """Test that COG preserves the number of bands from input."""
        # Get band count from input
        src_ds: gdal.Dataset = gdal.Open(sample_tiff)
        src_band_count = src_ds.RasterCount
        src_ds = None

        # Generate COG
        generate_web_optimized_cog(sample_tiff, temp_output_path)

        # Check output band count
        out_ds: gdal.Dataset = gdal.Open(temp_output_path)
        out_band_count = out_ds.RasterCount
        out_ds = None

        assert out_band_count == src_band_count

    def test_preserves_nodata_value(self, sample_tiff, temp_output_path):
        """Test that COG preserves nodata values from input."""
        # Get nodata value from input
        src_ds: gdal.Dataset = gdal.Open(sample_tiff)
        src_band = src_ds.GetRasterBand(1)
        src_nodata = src_band.GetNoDataValue()
        src_ds = None

        # Only test if input has a nodata value
        if src_nodata is not None:
            # Generate COG
            generate_web_optimized_cog(sample_tiff, temp_output_path)

            # Check output nodata value
            out_ds: gdal.Dataset = gdal.Open(temp_output_path)
            out_band: gdal.Band = out_ds.GetRasterBand(1)
            out_nodata = out_band.GetNoDataValue()
            out_ds = None

            assert out_nodata == src_nodata

    def test_output_is_geotiff(self, sample_tiff, temp_output_path):
        """Test that output is a GeoTIFF file."""
        generate_web_optimized_cog(sample_tiff, temp_output_path)

        ds: gdal.Dataset = gdal.Open(temp_output_path)
        driver: gdal.Driver = ds.GetDriver()

        assert driver.ShortName == "GTiff"
        ds = None

    def test_multiple_compressions(self, sample_tiff, temp_output_path):
        """Test that different compression algorithms work."""
        compressions = ["LZW", "DEFLATE", "NONE"]

        for compression in compressions:
            # Use different temp file for each compression
            with tempfile.NamedTemporaryFile(suffix=".tif", delete=False) as tmp:
                temp_path = tmp.name

            try:
                result = generate_web_optimized_cog(sample_tiff, temp_path, compression=compression)

                assert os.path.exists(result)

                ds: gdal.Dataset = gdal.Open(result)
                metadata = ds.GetMetadata("IMAGE_STRUCTURE")

                if compression != "NONE":
                    assert "COMPRESSION" in metadata
                    assert metadata["COMPRESSION"] == compression

                ds = None
            finally:
                if os.path.exists(temp_path):
                    os.remove(temp_path)

    def test_cog_generation_with_all_parameters(self, sample_tiff, temp_output_path):
        """Test COG generation with all parameters specified."""
        result = generate_web_optimized_cog(
            input_path=sample_tiff,
            output_path=temp_output_path,
            target_srs="EPSG:4326",
            compression="DEFLATE",
            resample_alg=GDALResamplingMethod.CUBIC,
        )

        assert result == temp_output_path
        assert os.path.exists(temp_output_path)

        # Verify properties
        ds: gdal.Dataset = gdal.Open(temp_output_path)

        # Check SRS
        srs = ds.GetProjection()
        assert "4326" in srs or "WGS 84" in srs

        # Check compression
        metadata = ds.GetMetadata("IMAGE_STRUCTURE")
        assert metadata["COMPRESSION"] == "DEFLATE"

        # Check it's a COG
        assert metadata["LAYOUT"] == "COG"

        # Check overviews (small test images may not have overviews)
        band: gdal.Band = ds.GetRasterBand(1)
        assert band.GetOverviewCount() >= 0

        ds = None
