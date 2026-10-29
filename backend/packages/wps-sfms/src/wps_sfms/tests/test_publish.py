import hashlib
from unittest.mock import AsyncMock, MagicMock

import numpy as np
import pytest
from osgeo import gdal
from wps_shared.geospatial.wps_dataset import WPSDataset
from wps_shared.tests.geospatial.dataset_common import create_test_dataset

from wps_sfms.publish import publish_dataset
from wps_sfms.sfmsng_raster_addresser import SFMSNGRasterAddresser


@pytest.mark.anyio
async def test_publish_dataset_uploads_raster_and_generates_cog_by_default(mocker):
    output_key = "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
    expected_cog_key = SFMSNGRasterAddresser().get_cog_key(output_key)
    generate_cog_spy = mocker.patch(
        "wps_sfms.publish.generate_web_optimized_cog",
        return_value=expected_cog_key,
    )

    mock_s3_client = MagicMock()
    mock_s3_client.put_object = AsyncMock()

    gdal_ds = create_test_dataset(
        "temperature_20240704.tif",
        1,
        1,
        (-1.0, 1.0, -1.0, 1.0),
        4326,
        fill_value=12.5,
        no_data_value=-9999.0,
    )

    with WPSDataset(ds_path=None, ds=gdal_ds) as dataset:
        published = await publish_dataset(mock_s3_client, dataset, output_key)

    mock_s3_client.put_object.assert_awaited_once()
    assert mock_s3_client.put_object.await_args.kwargs["key"] == output_key
    assert isinstance(mock_s3_client.put_object.await_args.kwargs["body"], bytes)
    assert mock_s3_client.put_object.await_args.kwargs["body"]

    generate_cog_spy.assert_called_once()
    assert generate_cog_spy.call_args.kwargs["output_path"] == expected_cog_key
    assert generate_cog_spy.call_args.kwargs["input_path"].endswith("temperature_20240704.tif")

    assert published.output_key == output_key
    assert published.cog_key == expected_cog_key
    assert (
        published.content_hash
        == hashlib.sha256(mock_s3_client.put_object.await_args.kwargs["body"]).hexdigest()
    )


@pytest.mark.anyio
async def test_publish_dataset_can_skip_cog_generation(mocker):
    output_key = "sfms_ng/actual/2024/07/04/temperature_20240704.tif"
    generate_cog_spy = mocker.patch("wps_sfms.publish.generate_web_optimized_cog")

    mock_s3_client = MagicMock()
    mock_s3_client.put_object = AsyncMock()

    gdal_ds = create_test_dataset(
        "temperature_20240704.tif",
        1,
        1,
        (-1.0, 1.0, -1.0, 1.0),
        4326,
        fill_value=12.5,
        no_data_value=-9999.0,
    )

    with WPSDataset(ds_path=None, ds=gdal_ds) as dataset:
        published = await publish_dataset(
            mock_s3_client,
            dataset,
            output_key,
            generate_cog=False,
        )

    mock_s3_client.put_object.assert_awaited_once()
    generate_cog_spy.assert_not_called()
    assert published.output_key == output_key
    assert published.cog_key is None


@pytest.mark.anyio
async def test_non_fuel_mask_changes_only_the_cog_not_the_uploaded_geotiff(mocker, tmp_path):
    """Keep uploaded zeros unchanged while masking the same pixels in the real COG."""
    output_key = "sfms_ng/actual/2024/07/04/cfb_20240704.tif"
    cog_path = str(tmp_path / "cfb_cog.tif")

    # Keep both outputs local: generate the COG on disk and capture the S3 upload.
    mocker.patch.object(SFMSNGRasterAddresser, "get_cog_key", return_value=cog_path)
    unmasked_cog_generator = mocker.patch("wps_sfms.publish.generate_web_optimized_cog")
    s3_client = MagicMock()
    s3_client.put_object = AsyncMock()

    # All source pixels are zero and classified Non-fuel.
    source_values = np.zeros((8, 8), dtype=np.float32)
    non_fuel_mask = np.ones(source_values.shape, dtype=bool)
    gdal_ds = create_test_dataset(
        "cfb.tif",
        8,
        8,
        (-124, -122, 49, 51),
        4326,
        fill_value=0,
        no_data_value=-9999,
    )

    with WPSDataset(ds_path=None, ds=gdal_ds) as dataset:
        published = await publish_dataset(
            s3_client,
            dataset,
            output_key,
            cog_non_fuel_mask=non_fuel_mask,
        )
        np.testing.assert_array_equal(dataset.as_gdal_ds().ReadAsArray(), source_values)

    unmasked_cog_generator.assert_not_called()
    s3_client.put_object.assert_awaited_once()
    upload = s3_client.put_object.await_args.kwargs
    assert upload["key"] == output_key
    assert published.content_hash == hashlib.sha256(upload["body"]).hexdigest()
    assert published.cog_key == cog_path

    # The uploaded GeoTIFF must still contain zeros.
    uploaded_path = tmp_path / "uploaded.tif"
    uploaded_path.write_bytes(upload["body"])
    with gdal.Open(str(uploaded_path)) as uploaded:
        np.testing.assert_array_equal(uploaded.ReadAsArray(), source_values)

    # Only the COG should have those pixels replaced with its declared NoData value.
    with gdal.Open(cog_path) as cog:
        cog_band = cog.GetRasterBand(1)
        assert np.all(cog_band.ReadAsArray() == cog_band.GetNoDataValue())
